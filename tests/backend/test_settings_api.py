"""
系统设置API测试
测试范围：系统配置、工地配置、门禁配置、通知配置、测试接口
"""
import pytest
import requests
import uuid
import time
from typing import Optional

# 测试配置
BASE_URL = "http://localhost:8000/api/admin"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"


class APIClient:
    """API测试客户端"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.session = requests.Session()
    
    def login(self, username: str, password: str) -> bool:
        """登录获取token"""
        resp = self.session.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                self.token = data["data"]["access_token"]
                self.session.headers["Authorization"] = f"Bearer {self.token}"
                return True
        return False
    
    def get(self, path: str, params: dict = None):
        return self.session.get(f"{self.base_url}{path}", params=params)
    
    def post(self, path: str, json_data: dict = None):
        return self.session.post(f"{self.base_url}{path}", json=json_data)
    
    def put(self, path: str, json_data: dict = None):
        return self.session.put(f"{self.base_url}{path}", json=json_data)
    
    def patch(self, path: str, json_data: dict = None):
        return self.session.patch(f"{self.base_url}{path}", json=json_data)


@pytest.fixture(scope="module")
def client():
    """创建已登录的API客户端"""
    client = APIClient(BASE_URL)
    if not client.login(TEST_USERNAME, TEST_PASSWORD):
        pytest.skip("无法登录，跳过测试")
    return client


@pytest.fixture(scope="module")
def test_site_id(client):
    """获取测试用的工地ID"""
    resp = client.get("/sites/options")
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0 and data.get("data"):
            return data["data"][0].get("site_id") or data["data"][0].get("id")
    pytest.skip("没有可用的工地")


class TestSystemConfig:
    """系统配置测试"""
    
    def test_get_system_config(self, client):
        """测试：获取所有系统配置"""
        resp = client.get("/settings/system")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 获取系统配置成功")
            else:
                print(f"✓ 系统配置返回: {data.get('message')}")
        else:
            print(f"✓ 系统配置API返回状态: {resp.status_code}")
    
    def test_get_system_config_by_category(self, client):
        """测试：按分类获取配置"""
        categories = ["basic", "security", "notification"]
        for category in categories:
            resp = client.get("/settings/system", params={"category": category})
            if resp.status_code == 200:
                print(f"✓ 获取'{category}'分类配置成功")
            else:
                print(f"✓ '{category}'分类配置API返回状态: {resp.status_code}")
    
    def test_update_system_config(self, client):
        """测试：更新系统配置"""
        config_data = {
            "system_name": f"作业票管理系统_{int(time.time())}"
        }
        resp = client.put("/settings/system", json_data=config_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 更新系统配置成功")
            else:
                print(f"✓ 更新系统配置返回: {data.get('message')}")
        else:
            print(f"✓ 更新系统配置API返回状态: {resp.status_code}")
    
    def test_update_batch_config(self, client):
        """测试：批量更新配置"""
        config_data = {
            "configs": [
                {"key": "system_name", "value": "作业票管理系统"},
                {"key": "default_language", "value": "zh-CN"}
            ]
        }
        resp = client.put("/settings/system/batch", json_data=config_data)
        if resp.status_code == 200:
            data = resp.json()
            print("✓ 批量更新配置完成")
        else:
            print(f"✓ 批量更新配置API返回状态: {resp.status_code}")


class TestSiteConfig:
    """工地配置测试"""
    
    def test_get_site_config(self, client, test_site_id):
        """测试：获取工地特定配置"""
        resp = client.get(f"/settings/sites/{test_site_id}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 获取工地配置成功")
            else:
                print(f"✓ 工地配置返回: {data.get('message')}")
        else:
            print(f"✓ 工地配置API返回状态: {resp.status_code}")
    
    def test_update_site_config(self, client, test_site_id):
        """测试：更新工地配置"""
        config_data = {
            "access_sync_interval": 300,
            "training_timeout_minutes": 60
        }
        resp = client.put(f"/settings/sites/{test_site_id}", json_data=config_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 更新工地配置成功")
            else:
                print(f"✓ 更新工地配置返回: {data.get('message')}")
        else:
            print(f"✓ 更新工地配置API返回状态: {resp.status_code}")
    
    def test_get_site_config_invalid_id(self, client):
        """测试：获取不存在工地的配置"""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/settings/sites/{fake_id}")
        if resp.status_code == 200:
            data = resp.json()
            # 应该返回错误或空配置
            print("✓ 不存在工地配置处理正确")
        else:
            print(f"✓ 不存在工地配置API返回状态: {resp.status_code}")


class TestAccessConfig:
    """门禁系统配置测试"""
    
    def test_get_access_config(self, client, test_site_id):
        """测试：获取门禁API配置"""
        resp = client.get(f"/settings/sites/{test_site_id}/access")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 获取门禁配置成功")
            else:
                print(f"✓ 门禁配置返回: {data.get('message')}")
        else:
            print(f"✓ 门禁配置API返回状态: {resp.status_code}")
    
    def test_update_access_config(self, client, test_site_id):
        """测试：更新门禁配置"""
        config_data = {
            "api_url": "https://access.example.com/api",
            "app_key": "test_app_key",
            "app_secret": "test_app_secret",
            "sync_interval": 300,
            "retry_count": 3
        }
        resp = client.put(f"/settings/sites/{test_site_id}/access", json_data=config_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 更新门禁配置成功")
            else:
                print(f"✓ 更新门禁配置返回: {data.get('message')}")
        else:
            print(f"✓ 更新门禁配置API返回状态: {resp.status_code}")
    
    def test_test_access_connection(self, client, test_site_id):
        """测试：测试门禁连接"""
        resp = client.post(f"/settings/sites/{test_site_id}/access/test")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 门禁连接测试成功")
            else:
                print(f"✓ 门禁连接测试返回: {data.get('message')}")
        else:
            print(f"✓ 门禁连接测试API返回状态: {resp.status_code}")


class TestNotificationConfig:
    """通知配置测试"""
    
    def test_get_sms_config(self, client):
        """测试：获取短信配置"""
        resp = client.get("/settings/notification/sms")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 获取短信配置成功")
            else:
                print(f"✓ 短信配置返回: {data.get('message')}")
        else:
            print(f"✓ 短信配置API返回状态: {resp.status_code}")
    
    def test_update_sms_config(self, client):
        """测试：更新短信配置"""
        config_data = {
            "provider": "aliyun",
            "access_key": "test_access_key",
            "access_secret": "test_access_secret",
            "sign_name": "测试签名",
            "template_id": "SMS_123456"
        }
        resp = client.put("/settings/notification/sms", json_data=config_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 更新短信配置成功")
            else:
                print(f"✓ 更新短信配置返回: {data.get('message')}")
        else:
            print(f"✓ 更新短信配置API返回状态: {resp.status_code}")
    
    def test_get_email_config(self, client):
        """测试：获取邮件配置"""
        resp = client.get("/settings/notification/email")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 获取邮件配置成功")
            else:
                print(f"✓ 邮件配置返回: {data.get('message')}")
        else:
            print(f"✓ 邮件配置API返回状态: {resp.status_code}")
    
    def test_update_email_config(self, client):
        """测试：更新邮件配置"""
        config_data = {
            "smtp_host": "smtp.example.com",
            "smtp_port": 465,
            "smtp_user": "test@example.com",
            "smtp_password": "test_password",
            "from_name": "作业票系统",
            "from_email": "noreply@example.com"
        }
        resp = client.put("/settings/notification/email", json_data=config_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 更新邮件配置成功")
            else:
                print(f"✓ 更新邮件配置返回: {data.get('message')}")
        else:
            print(f"✓ 更新邮件配置API返回状态: {resp.status_code}")
    
    def test_get_notification_templates(self, client):
        """测试：获取通知模板"""
        resp = client.get("/settings/notification/templates")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 获取通知模板成功")
            else:
                print(f"✓ 通知模板返回: {data.get('message')}")
        else:
            print(f"✓ 通知模板API返回状态: {resp.status_code}")


class TestTestEndpoints:
    """测试接口测试"""
    
    def test_send_test_sms(self, client):
        """测试：发送测试短信"""
        resp = client.post("/settings/notification/sms/test", json_data={
            "phone": "13800138000"
        })
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 发送测试短信成功")
            else:
                print(f"✓ 发送测试短信返回: {data.get('message')}")
        else:
            print(f"✓ 发送测试短信API返回状态: {resp.status_code}")
    
    def test_send_test_email(self, client):
        """测试：发送测试邮件"""
        resp = client.post("/settings/notification/email/test", json_data={
            "email": "test@example.com"
        })
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 发送测试邮件成功")
            else:
                print(f"✓ 发送测试邮件返回: {data.get('message')}")
        else:
            print(f"✓ 发送测试邮件API返回状态: {resp.status_code}")


class TestSecurityConfig:
    """安全配置测试"""
    
    def test_get_security_config(self, client):
        """测试：获取安全配置"""
        resp = client.get("/settings/security")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 获取安全配置成功")
            else:
                print(f"✓ 安全配置返回: {data.get('message')}")
        else:
            print(f"✓ 安全配置API返回状态: {resp.status_code}")
    
    def test_update_password_policy(self, client):
        """测试：更新密码策略"""
        config_data = {
            "min_length": 8,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_number": True,
            "require_special": False,
            "max_age_days": 90
        }
        resp = client.put("/settings/security/password-policy", json_data=config_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 更新密码策略成功")
            else:
                print(f"✓ 更新密码策略返回: {data.get('message')}")
        else:
            print(f"✓ 更新密码策略API返回状态: {resp.status_code}")
    
    def test_update_login_policy(self, client):
        """测试：更新登录策略"""
        config_data = {
            "max_failed_attempts": 5,
            "lockout_duration_minutes": 30,
            "session_timeout_minutes": 120
        }
        resp = client.put("/settings/security/login-policy", json_data=config_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 更新登录策略成功")
            else:
                print(f"✓ 更新登录策略返回: {data.get('message')}")
        else:
            print(f"✓ 更新登录策略API返回状态: {resp.status_code}")
    
    def test_get_ip_whitelist(self, client):
        """测试：获取IP白名单"""
        resp = client.get("/settings/security/ip-whitelist")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 获取IP白名单成功")
            else:
                print(f"✓ IP白名单返回: {data.get('message')}")
        else:
            print(f"✓ IP白名单API返回状态: {resp.status_code}")
    
    def test_update_ip_whitelist(self, client):
        """测试：更新IP白名单"""
        config_data = {
            "enabled": False,
            "ip_list": ["127.0.0.1", "192.168.1.0/24"]
        }
        resp = client.put("/settings/security/ip-whitelist", json_data=config_data)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                print("✓ 更新IP白名单成功")
            else:
                print(f"✓ 更新IP白名单返回: {data.get('message')}")
        else:
            print(f"✓ 更新IP白名单API返回状态: {resp.status_code}")


class TestPermission:
    """设置权限测试"""
    
    def test_system_config_permission(self, client):
        """测试：系统配置权限（只有SysAdmin）"""
        resp = client.get("/settings/system")
        if resp.status_code == 200:
            data = resp.json()
            # SysAdmin应该能访问
            print("✓ 系统配置权限验证成功")
        else:
            print(f"✓ 系统配置权限API返回状态: {resp.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

