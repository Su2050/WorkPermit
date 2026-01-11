"""
测试数据初始化脚本
创建演示用的模拟数据:
- 2个工地
- 3个施工单位
- 100个作业人员
- 5个作业票
- 10个作业区域
- 5个培训视频
- 模拟培训记录和门禁授权
"""
import asyncio
import uuid
from datetime import date, datetime, time, timedelta
import random

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import bcrypt

# 配置
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/work_permit"

# 随机姓名生成
SURNAMES = ['张', '李', '王', '刘', '陈', '杨', '黄', '赵', '周', '吴', '徐', '孙', '马', '朱', '胡']
GIVEN_NAMES = ['伟', '强', '磊', '军', '勇', '杰', '涛', '明', '超', '华', '建', '志', '刚', '平', '国']


def generate_name():
    """生成随机姓名"""
    surname = random.choice(SURNAMES)
    given_name = ''.join(random.choices(GIVEN_NAMES, k=random.randint(1, 2)))
    return surname + given_name


def generate_id_card():
    """生成随机身份证号"""
    area = str(random.randint(110000, 659999))
    year = str(random.randint(1970, 2000))
    month = str(random.randint(1, 12)).zfill(2)
    day = str(random.randint(1, 28)).zfill(2)
    seq = str(random.randint(1, 999)).zfill(3)
    checksum = str(random.randint(0, 9))
    return f"{area}{year}{month}{day}{seq}{checksum}"


def generate_phone():
    """生成随机手机号"""
    prefix = random.choice(['138', '139', '137', '136', '135', '158', '159', '188', '189'])
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + suffix


def hash_password(password: str) -> str:
    """密码哈希（使用bcrypt）"""
    # 使用bcrypt生成密码哈希，与后端一致
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


async def init_demo_data():
    """初始化演示数据"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            print("=== 开始初始化演示数据 ===")
            
            # 1. 创建工地
            print("\n1. 创建工地...")
            sites = []
            site_data = [
                {"name": "A工地 - 新能源产业园", "description": "新能源汽车制造基地建设项目"},
                {"name": "B工地 - 智慧物流中心", "description": "智慧物流仓储中心建设项目"}
            ]
            for data in site_data:
                site_id = uuid.uuid4()
                site_code = f"SITE-{str(site_id)[:8].upper()}"
                await session.execute(text("""
                    INSERT INTO site (site_id, name, code, description, is_active, created_at, updated_at)
                    VALUES (:site_id, :name, :code, :description, true, now(), now())
                """), {"site_id": site_id, "code": site_code, **data})
                sites.append({"site_id": site_id, **data})
                print(f"  - 创建工地: {data['name']}")
            
            # 2. 创建施工单位
            print("\n2. 创建施工单位...")
            contractors = []
            contractor_data = [
                {"name": "建设工程集团有限公司", "contact_person": "张经理", "contact_phone": "13812345678"},
                {"name": "电力安装工程有限公司", "contact_person": "李主管", "contact_phone": "13987654321"},
                {"name": "管道工程技术有限公司", "contact_person": "王工程师", "contact_phone": "13611223344"}
            ]
            for i, data in enumerate(contractor_data):
                contractor_id = uuid.uuid4()
                site = sites[i % len(sites)]
                contractor_code = f"CTR-{str(contractor_id)[:8].upper()}"
                await session.execute(text("""
                    INSERT INTO contractor (contractor_id, site_id, name, code, contact_person, contact_phone, 
                        is_active, created_at, updated_at)
                    VALUES (:contractor_id, :site_id, :name, :code, :contact_person, :contact_phone,
                        true, now(), now())
                """), {"contractor_id": contractor_id, "site_id": site["site_id"], "code": contractor_code, **data})
                contractors.append({"contractor_id": contractor_id, "site_id": site["site_id"], **data})
                print(f"  - 创建施工单位: {data['name']}")
            
            # 3. 创建作业区域
            print("\n3. 创建作业区域...")
            areas = []
            area_data = [
                {"name": "焊接区A", "code": "AREA-001", "description": "一号厂房焊接作业区"},
                {"name": "组装区B", "code": "AREA-002", "description": "二号厂房组装作业区"},
                {"name": "配电室", "code": "AREA-003", "description": "高压配电室"},
                {"name": "管道区C", "code": "AREA-004", "description": "管道安装作业区"},
                {"name": "仓储区D", "code": "AREA-005", "description": "物料仓储区域"},
                {"name": "吊装区E", "code": "AREA-006", "description": "大型设备吊装区"},
                {"name": "喷涂区F", "code": "AREA-007", "description": "表面处理喷涂区"},
                {"name": "测试区G", "code": "AREA-008", "description": "设备测试验收区"},
                {"name": "办公区H", "code": "AREA-009", "description": "临时办公区"},
                {"name": "停车场", "code": "AREA-010", "description": "车辆停放区"}
            ]
            for i, data in enumerate(area_data):
                area_id = uuid.uuid4()
                site = sites[i % len(sites)]
                await session.execute(text("""
                    INSERT INTO work_area (area_id, site_id, name, code, description,
                        is_active, created_at, updated_at)
                    VALUES (:area_id, :site_id, :name, :code, :description,
                        true, now(), now())
                """), {
                    "area_id": area_id, 
                    "site_id": site["site_id"], 
                    **data
                })
                areas.append({"area_id": area_id, "site_id": site["site_id"], **data})
                print(f"  - 创建区域: {data['name']}")
            
            # 4. 创建培训视频
            print("\n4. 创建培训视频...")
            videos = []
            video_data = [
                {"title": "安全生产基础培训", "description": "安全生产基本知识和注意事项", "duration_sec": 300},
                {"title": "焊接作业安全规范", "description": "焊接作业中的安全防护措施", "duration_sec": 480},
                {"title": "高空作业安全培训", "description": "高空作业安全绳使用和注意事项", "duration_sec": 360},
                {"title": "电气作业安全须知", "description": "电气作业安全操作规程", "duration_sec": 420},
                {"title": "消防安全知识", "description": "消防设施使用和火灾逃生知识", "duration_sec": 240}
            ]
            for i, data in enumerate(video_data):
                video_id = uuid.uuid4()
                site = sites[i % len(sites)]
                await session.execute(text("""
                    INSERT INTO training_video (video_id, site_id, title, description, duration_sec,
                        file_url, file_size, created_at, updated_at)
                    VALUES (:video_id, :site_id, :title, :description, :duration_sec,
                        :file_url, :file_size, now(), now())
                """), {
                    "video_id": video_id,
                    "site_id": site["site_id"],
                    "file_url": f"/videos/{video_id}.mp4",
                    "file_size": random.randint(30000000, 100000000),
                    **data
                })
                videos.append({"video_id": video_id, "site_id": site["site_id"], **data})
                print(f"  - 创建视频: {data['title']}")
            
            # 5. 创建作业人员
            print("\n5. 创建作业人员...")
            workers = []
            for i in range(100):
                worker_id = uuid.uuid4()
                contractor = random.choice(contractors)
                name = generate_name()
                
                await session.execute(text("""
                    INSERT INTO worker (worker_id, site_id, contractor_id, name, id_no, phone,
                        is_bound, created_at, updated_at)
                    VALUES (:worker_id, :site_id, :contractor_id, :name, :id_no, :phone,
                        :is_bound, now(), now())
                """), {
                    "worker_id": worker_id,
                    "site_id": contractor["site_id"],
                    "contractor_id": contractor["contractor_id"],
                    "name": name,
                    "id_no": generate_id_card(),
                    "phone": generate_phone(),
                    "is_bound": random.random() > 0.3  # 70%已绑定
                })
                workers.append({
                    "worker_id": worker_id,
                    "site_id": contractor["site_id"],
                    "contractor_id": contractor["contractor_id"],
                    "name": name
                })
                
                if (i + 1) % 20 == 0:
                    print(f"  - 已创建 {i + 1}/100 个人员")
            
            # 6. 创建系统用户
            print("\n6. 创建系统用户...")
            # 系统管理员
            admin_id = uuid.uuid4()
            await session.execute(text("""
                INSERT INTO sys_user (user_id, username, password_hash, name, role,
                    is_active, created_at, updated_at)
                VALUES (:user_id, :username, :password_hash, :name, :role,
                    true, now(), now())
            """), {
                "user_id": admin_id,
                "username": "admin",
                "password_hash": hash_password("admin123"),
                "name": "系统管理员",
                "role": "SysAdmin"
            })
            print("  - 创建管理员: admin / admin123")
            
            # 施工单位管理员
            for i, contractor in enumerate(contractors):
                user_id = uuid.uuid4()
                await session.execute(text("""
                    INSERT INTO sys_user (user_id, contractor_id, username, password_hash, name, role,
                        is_active, created_at, updated_at)
                    VALUES (:user_id, :contractor_id, :username, :password_hash, :name, :role,
                        true, now(), now())
                """), {
                    "user_id": user_id,
                    "contractor_id": contractor["contractor_id"],
                    "username": f"contractor{i+1}",
                    "password_hash": hash_password("contractor123"),
                    "name": contractor["contact_person"],
                    "role": "ContractorAdmin"
                })
                print(f"  - 创建施工单位管理员: contractor{i+1} / contractor123")
            
            # 7. 创建作业票
            print("\n7. 创建作业票...")
            today = date.today()
            tickets = []
            ticket_data = [
                {"title": "A区焊接作业许可", "start_offset": 0, "end_offset": 7},
                {"title": "B区电气施工许可", "start_offset": 1, "end_offset": 3},
                {"title": "C区管道安装许可", "start_offset": -2, "end_offset": 5},
                {"title": "D区设备吊装许可", "start_offset": 2, "end_offset": 10},
                {"title": "E区喷涂作业许可", "start_offset": 0, "end_offset": 4}
            ]
            
            for i, data in enumerate(ticket_data):
                ticket_id = uuid.uuid4()
                contractor = contractors[i % len(contractors)]
                site_areas = [a for a in areas if a["site_id"] == contractor["site_id"]]
                site_videos = [v for v in videos if v["site_id"] == contractor["site_id"]]
                site_workers = [w for w in workers if w["site_id"] == contractor["site_id"]]
                
                start_date = today + timedelta(days=data["start_offset"])
                end_date = today + timedelta(days=data["end_offset"])
                
                # 确定状态
                if start_date > today:
                    status = "PUBLISHED"
                elif end_date < today:
                    status = "EXPIRED"
                else:
                    status = "IN_PROGRESS"
                
                await session.execute(text("""
                    INSERT INTO work_ticket (ticket_id, site_id, contractor_id, title, start_date, end_date,
                        default_training_deadline_time, default_access_start_time, default_access_end_time, status, remark,
                        created_by, created_at, updated_at)
                    VALUES (:ticket_id, :site_id, :contractor_id, :title, :start_date, :end_date,
                        :default_training_deadline_time, :default_access_start_time, :default_access_end_time, :status, :remark,
                        :created_by, now(), now())
                """), {
                    "ticket_id": ticket_id,
                    "site_id": contractor["site_id"],
                    "contractor_id": contractor["contractor_id"],
                    "title": data["title"],
                    "start_date": start_date,
                    "end_date": end_date,
                    "default_training_deadline_time": time(12, 0, 0),
                    "default_access_start_time": time(8, 0, 0),
                    "default_access_end_time": time(18, 0, 0),
                    "status": status,
                    "remark": f"演示作业票 #{i+1}",
                    "created_by": admin_id
                })
                
                # 关联区域
                selected_areas = random.sample(site_areas, min(3, len(site_areas)))
                for area in selected_areas:
                    await session.execute(text("""
                        INSERT INTO work_ticket_area (id, ticket_id, area_id, site_id, status, added_at, added_by, created_at, updated_at)
                        VALUES (:id, :ticket_id, :area_id, :site_id, 'ACTIVE', now(), :added_by, now(), now())
                    """), {
                        "id": uuid.uuid4(),
                        "ticket_id": ticket_id,
                        "area_id": area["area_id"],
                        "site_id": contractor["site_id"],
                        "added_by": admin_id
                    })
                
                # 关联视频
                selected_videos = random.sample(site_videos, min(2, len(site_videos)))
                for video in selected_videos:
                    await session.execute(text("""
                        INSERT INTO work_ticket_video (id, ticket_id, video_id, site_id, status, added_at, added_by, created_at)
                        VALUES (:id, :ticket_id, :video_id, :site_id, 'ACTIVE', now(), :added_by, now())
                    """), {
                        "id": uuid.uuid4(),
                        "ticket_id": ticket_id,
                        "video_id": video["video_id"],
                        "site_id": contractor["site_id"],
                        "added_by": admin_id
                    })
                
                # 关联人员
                selected_workers = random.sample(site_workers, min(20, len(site_workers)))
                for worker in selected_workers:
                    await session.execute(text("""
                        INSERT INTO work_ticket_worker (id, ticket_id, worker_id, site_id, status, added_at, added_by, created_at, updated_at)
                        VALUES (:id, :ticket_id, :worker_id, :site_id, 'ACTIVE', now(), :added_by, now(), now())
                    """), {
                        "id": uuid.uuid4(),
                        "ticket_id": ticket_id,
                        "worker_id": worker["worker_id"],
                        "site_id": contractor["site_id"],
                        "added_by": admin_id
                    })
                
                tickets.append({
                    "ticket_id": ticket_id,
                    "site_id": contractor["site_id"],
                    "areas": selected_areas,
                    "videos": selected_videos,
                    "workers": selected_workers,
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": status,
                    **data
                })
                print(f"  - 创建作业票: {data['title']} ({status})")
            
            # 8. 创建每日票据
            print("\n8. 创建每日票据...")
            for ticket in tickets:
                current_date = ticket["start_date"]
                while current_date <= ticket["end_date"]:
                    daily_ticket_id = uuid.uuid4()
                    
                    if current_date < today:
                        daily_status = "EXPIRED"
                    elif current_date == today:
                        daily_status = "IN_PROGRESS"
                    else:
                        daily_status = "PUBLISHED"
                    
                    await session.execute(text("""
                        INSERT INTO daily_ticket (daily_ticket_id, ticket_id, site_id, date, status,
                            training_deadline_time, access_start_time, access_end_time,
                            created_at, updated_at)
                        VALUES (:daily_ticket_id, :ticket_id, :site_id, :date, :status,
                            :training_deadline_time, :access_start_time, :access_end_time,
                            now(), now())
                    """), {
                        "daily_ticket_id": daily_ticket_id,
                        "ticket_id": ticket["ticket_id"],
                        "site_id": ticket["site_id"],
                        "date": current_date,
                        "status": daily_status,
                        "training_deadline_time": time(12, 0, 0),
                        "access_start_time": time(8, 0, 0),
                        "access_end_time": time(18, 0, 0)
                    })
                    
                    # 为每个人员创建每日记录
                    for worker in ticket["workers"]:
                        # 模拟培训状态
                        if current_date < today:
                            training_status = random.choice(["COMPLETED", "COMPLETED", "COMPLETED", "FAILED"])
                        elif current_date == today:
                            training_status = random.choice(["NOT_STARTED", "IN_LEARNING", "COMPLETED"])
                        else:
                            training_status = "NOT_STARTED"
                        
                        completed_count = len(ticket["videos"]) if training_status == "COMPLETED" else random.randint(0, len(ticket["videos"]) - 1)
                        authorized = training_status == "COMPLETED"
                        
                        await session.execute(text("""
                            INSERT INTO daily_ticket_worker (id, daily_ticket_id, worker_id, site_id,
                                total_video_count, completed_video_count, training_status, authorized, status,
                                created_at, updated_at)
                            VALUES (:id, :daily_ticket_id, :worker_id, :site_id,
                                :total_video_count, :completed_video_count, :training_status, :authorized, 'ACTIVE',
                                now(), now())
                        """), {
                            "id": uuid.uuid4(),
                            "daily_ticket_id": daily_ticket_id,
                            "worker_id": worker["worker_id"],
                            "site_id": ticket["site_id"],
                            "total_video_count": len(ticket["videos"]),
                            "completed_video_count": completed_count,
                            "training_status": training_status,
                            "authorized": authorized
                        })
                    
                    current_date += timedelta(days=1)
            
            print("\n9. 提交事务...")
            await session.commit()
            
            print("\n=== 演示数据初始化完成 ===")
            print(f"  - 工地: {len(sites)} 个")
            print(f"  - 施工单位: {len(contractors)} 个")
            print(f"  - 作业区域: {len(areas)} 个")
            print(f"  - 培训视频: {len(videos)} 个")
            print(f"  - 作业人员: {len(workers)} 个")
            print(f"  - 作业票: {len(tickets)} 个")
            print("\n登录账号:")
            print("  - 系统管理员: admin / admin123")
            print("  - 施工单位: contractor1 / contractor123")
            
        except Exception as e:
            print(f"\n错误: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_demo_data())

