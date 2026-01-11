"""
培训进度验证器 (P0-2: 防作弊可执行规则)
- 进度上报验证
- 随机活体校验调度
- 网络容错处理
"""
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ProgressData:
    """进度上报数据"""
    session_token: str
    position: int  # 当前播放位置(秒)
    played_seconds_delta: int  # 本次心跳新增播放秒数
    video_state: str  # playing/paused/background
    client_ts: int  # 客户端时间戳
    buffer_ranges: Optional[list] = None  # 已缓冲区间


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    reason: Optional[str] = None
    valid_watch_sec: int = 0
    suspicious_event: Optional[str] = None


class TrainingProgressValidator:
    """
    培训进度验证器 (P0-2)
    
    验证规则:
    1. 检查时间倒退（允许2秒误差）
    2. 检查跳跃幅度（不超过视频时长的5%）
    3. 检查播放速度异常（delta不应超过心跳间隔*1.2）
    4. 累积可疑事件（超过3次判定失败）
    """
    
    MAX_SKIP_PERCENT = settings.TRAINING_MAX_SKIP_PERCENT  # 允许跳跃5%
    HEARTBEAT_TIMEOUT = settings.TRAINING_HEARTBEAT_TIMEOUT  # 心跳超时60秒
    MAX_SUSPICIOUS_COUNT = settings.TRAINING_MAX_SUSPICIOUS_COUNT  # 最多3次可疑事件
    POSITION_ERROR_MARGIN = 2  # 位置误差容忍（秒）
    SPEED_TOLERANCE = 1.2  # 速度容忍倍数
    
    async def validate_progress(
        self, 
        session: Any,  # TrainingSession model
        progress_data: ProgressData,
        video_duration: int
    ) -> ValidationResult:
        """
        验证进度有效性
        
        Args:
            session: 学习会话对象
            progress_data: 进度上报数据
            video_duration: 视频时长（秒）
        
        Returns:
            ValidationResult: 验证结果
        """
        last_position = session.last_position or 0
        current_position = progress_data.position
        played_delta = progress_data.played_seconds_delta
        
        suspicious_event = None
        
        # 1. 检查时间倒退
        if current_position < last_position - self.POSITION_ERROR_MARGIN:
            suspicious_event = "POSITION_BACKWARD"
            logger.warning(
                f"Position backward detected: session={session.session_id}, "
                f"last={last_position}, current={current_position}"
            )
            await self._record_suspicious_event(session, suspicious_event)
            return ValidationResult(
                valid=False, 
                reason="POSITION_BACKWARD",
                suspicious_event=suspicious_event
            )
        
        # 2. 检查跳跃幅度
        skip_distance = current_position - last_position
        max_skip = video_duration * self.MAX_SKIP_PERCENT
        
        if skip_distance > max_skip:
            suspicious_event = "LARGE_SKIP"
            logger.warning(
                f"Large skip detected: session={session.session_id}, "
                f"skip={skip_distance}, max_allowed={max_skip}"
            )
            await self._record_suspicious_event(session, suspicious_event)
            # 不累加此次 delta
            played_delta = 0
        
        # 3. 检查播放速度异常
        if session.last_heartbeat_ts:
            time_since_last = progress_data.client_ts - session.last_heartbeat_ts
            if time_since_last > 0 and played_delta > time_since_last * self.SPEED_TOLERANCE:
                suspicious_event = "SPEED_ANOMALY"
                logger.warning(
                    f"Speed anomaly detected: session={session.session_id}, "
                    f"delta={played_delta}, time_since_last={time_since_last}"
                )
                await self._record_suspicious_event(session, suspicious_event)
                # 修正delta为合理值
                played_delta = min(played_delta, int(time_since_last))
        
        # 4. 更新会话数据
        session.valid_watch_sec = (session.valid_watch_sec or 0) + played_delta
        session.total_watch_sec = (session.total_watch_sec or 0) + max(0, skip_distance)
        session.last_position = current_position
        session.last_heartbeat_ts = progress_data.client_ts
        session.video_state = progress_data.video_state
        
        # 5. 检查可疑事件累积
        if session.suspicious_event_count >= self.MAX_SUSPICIOUS_COUNT:
            session.status = "FAILED"
            session.failure_reason = "TOO_MANY_SUSPICIOUS_EVENTS"
            logger.error(
                f"Session failed due to too many suspicious events: "
                f"session={session.session_id}, count={session.suspicious_event_count}"
            )
            return ValidationResult(
                valid=False, 
                reason="TOO_MANY_SUSPICIOUS_EVENTS",
                valid_watch_sec=session.valid_watch_sec
            )
        
        return ValidationResult(
            valid=True,
            valid_watch_sec=session.valid_watch_sec,
            suspicious_event=suspicious_event
        )
    
    async def _record_suspicious_event(self, session: Any, event_type: str) -> None:
        """记录可疑事件"""
        session.suspicious_event_count = (session.suspicious_event_count or 0) + 1
        logger.info(
            f"Suspicious event recorded: session={session.session_id}, "
            f"type={event_type}, total_count={session.suspicious_event_count}"
        )
    
    async def handle_heartbeat_timeout(self, session: Any) -> bool:
        """
        处理心跳超时（网络容错）
        
        Returns:
            bool: True表示会话失败，False表示继续等待
        """
        if not session.last_heartbeat_ts:
            return False
        
        now_ts = int(datetime.now().timestamp())
        time_since_last = now_ts - session.last_heartbeat_ts
        
        if time_since_last > self.HEARTBEAT_TIMEOUT:
            session.video_state = "paused"
            logger.info(
                f"Heartbeat timeout detected: session={session.session_id}, "
                f"time_since_last={time_since_last}"
            )
            
            # 超过5分钟自动结束session
            if time_since_last > 300:
                session.status = "FAILED"
                session.failure_reason = "HEARTBEAT_TIMEOUT"
                logger.error(
                    f"Session failed due to heartbeat timeout: session={session.session_id}"
                )
                return True
        
        return False
    
    def check_completion(
        self, 
        session: Any, 
        video_duration: int,
        required_percent: float = None
    ) -> bool:
        """
        检查视频是否完成
        
        Args:
            session: 学习会话对象
            video_duration: 视频时长（秒）
            required_percent: 要求观看比例（默认95%）
        
        Returns:
            bool: 是否完成
        """
        if required_percent is None:
            required_percent = settings.TRAINING_REQUIRED_WATCH_PERCENT
        
        required_watch_sec = int(video_duration * required_percent)
        position_reached = session.last_position >= (video_duration - 2)  # 允许2秒误差
        watch_time_met = session.valid_watch_sec >= required_watch_sec
        
        return position_reached and watch_time_met


class RandomCheckScheduler:
    """
    随机活体校验调度器 (P0-2)
    
    规则:
    - 3~7分钟随机弹窗
    - 连续2次失败判定session失败
    """
    
    MIN_INTERVAL = settings.TRAINING_RANDOM_CHECK_MIN_INTERVAL  # 3分钟
    MAX_INTERVAL = settings.TRAINING_RANDOM_CHECK_MAX_INTERVAL  # 7分钟
    MAX_CONSECUTIVE_FAILURES = settings.TRAINING_MAX_CONSECUTIVE_CHECK_FAILURES  # 2次
    
    def should_trigger_check(self, session: Any) -> bool:
        """
        判断是否触发随机校验
        
        Args:
            session: 学习会话对象
        
        Returns:
            bool: 是否需要触发校验
        """
        # 首次学习不校验（从开始计时）
        if not session.started_at:
            return False
        
        # 计算自上次校验或开始以来的时间
        reference_time = session.last_check_at or session.started_at
        elapsed = (datetime.now() - reference_time).total_seconds()
        
        # 随机确定下次校验时间
        next_check_interval = random.randint(self.MIN_INTERVAL, self.MAX_INTERVAL)
        
        return elapsed >= next_check_interval
    
    async def handle_check_result(self, session: Any, passed: bool) -> bool:
        """
        处理校验结果
        
        Args:
            session: 学习会话对象
            passed: 是否通过校验
        
        Returns:
            bool: True表示会话失败，False表示继续
        """
        session.last_check_at = datetime.now()
        
        if passed:
            session.random_check_passed = (session.random_check_passed or 0) + 1
            session.consecutive_check_failures = 0
            logger.info(
                f"Random check passed: session={session.session_id}, "
                f"total_passed={session.random_check_passed}"
            )
            return False
        else:
            session.random_check_failed = (session.random_check_failed or 0) + 1
            session.consecutive_check_failures = (
                session.consecutive_check_failures or 0
            ) + 1
            
            logger.warning(
                f"Random check failed: session={session.session_id}, "
                f"consecutive_failures={session.consecutive_check_failures}"
            )
            
            # 连续2次失败 → FAILED
            if session.consecutive_check_failures >= self.MAX_CONSECUTIVE_FAILURES:
                session.status = "FAILED"
                session.failure_reason = "CONSECUTIVE_CHECK_FAILURES"
                logger.error(
                    f"Session failed due to consecutive check failures: "
                    f"session={session.session_id}"
                )
                return True
            
            return False
    
    def get_next_check_time(self, session: Any) -> datetime:
        """获取下次校验时间"""
        reference_time = session.last_check_at or session.started_at or datetime.now()
        interval = random.randint(self.MIN_INTERVAL, self.MAX_INTERVAL)
        return reference_time + timedelta(seconds=interval)

