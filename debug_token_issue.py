#!/usr/bin/env python3
"""
Token问题诊断脚本
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

# 配置信息
INTRANET_API_BASE_URL = "http://172.20.70.142:16555/gateway/computation-api/process"
CURRENT_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjMyNCwidXNlcl9uYW1lIjoiZWR1X2FkbWluIiwic2NvcGUiOlsid2ViIl0sImV4cCI6MTc0OTkwNjkwMiwidXVpZCI6ImY5NTBjZmYyLTA3YzgtNDYxYS05YzI0LTE5MTYyZDU5ZTJlZjYiLCJhdXRob3JpdGllcyI6WyJBRE1JTklTVFJBVE9SUyJdLCJqdGkiOiJMUG4yUE04ZUZaQUQ4VDRQcTdlN0lpUXZkRkEiLCJjbGllbnRfaWQiOiJ0ZXN0IiwidXNlcm5hbWUiOiJlZHVfYWRtaW4ifQ.jFepdzkcDDlcH0v3Z_Ge35vbiTB3RVt8OQsHJ0o6qEU"

# 认证信息
USERNAME = "edu_admin"
PASSWORD = "123456"
CLIENT_ID = "test"
CLIENT_SECRET = "123456"

async def test_network_connectivity():
    """测试网络连接"""
    print("=== 网络连接测试 ===")
    
    base_url = "http://172.20.70.141"
    test_url = f"{base_url}/api/oauth/token"
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(base_url)
            print(f"✓ 基础URL可访问: {base_url} (状态码: {response.status_code})")
            
            # 测试OAuth端点
            response = await client.get(test_url)
            print(f"✓ OAuth端点可访问: {test_url} (状态码: {response.status_code})")
            
    except httpx.ConnectError as e:
        print(f"✗ 网络连接失败: {e}")
        print("  可能原因: 不在内网环境或服务器不可达")
        return False
    except httpx.TimeoutException:
        print(f"✗ 连接超时: {test_url}")
        return False
    except Exception as e:
        print(f"✗ 其他网络错误: {e}")
        return False
    
    return True

def analyze_current_token():
    """分析当前token"""
    print("\n=== 当前Token分析 ===")
    
    try:
        # 解析JWT token (不验证签名，仅解析payload)
        import base64
        
        # 去掉Bearer前缀，分割token
        token_str = CURRENT_TOKEN.replace('Bearer ', '')
        parts = token_str.split('.')
        
        if len(parts) != 3:
            print("✗ Token格式错误")
            return False
            
        # 解码payload (添加padding if needed)
        payload = parts[1]
        # JWT base64编码可能需要padding
        missing_padding = len(payload) % 4
        if missing_padding:
            payload += '=' * (4 - missing_padding)
            
        decoded = base64.b64decode(payload)
        payload_data = json.loads(decoded.decode('utf-8'))
        
        print("Token内容:")
        print(f"  用户名: {payload_data.get('user_name', 'N/A')}")
        print(f"  用户ID: {payload_data.get('uid', 'N/A')}")
        print(f"  权限: {payload_data.get('authorities', [])}")
        
        # 检查过期时间
        exp_timestamp = payload_data.get('exp', 0)
        if exp_timestamp:
            exp_time = datetime.fromtimestamp(exp_timestamp)
            current_time = datetime.now()
            
            print(f"  过期时间: {exp_time}")
            print(f"  当前时间: {current_time}")
            
            if current_time > exp_time:
                print("✗ Token已过期")
                return False
            else:
                time_left = exp_time - current_time
                print(f"✓ Token有效，剩余时间: {time_left}")
                return True
        else:
            print("⚠ 无法确定过期时间")
            return None
            
    except Exception as e:
        print(f"✗ Token分析失败: {e}")
        return False

async def test_token_endpoint():
    """测试token获取端点"""
    print("\n=== Token获取测试 ===")
    
    base_url = "http://172.20.70.141"
    token_url = f"{base_url}/api/oauth/token"
    
    # 构建请求参数
    params = {
        "scopes": "web",
        "client_secret": CLIENT_SECRET,
        "client_id": CLIENT_ID,
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password"
    }
    
    request_body = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    # 注意：获取token时不需要Authorization header
    
    print(f"请求URL: {token_url}")
    print(f"请求参数: {params}")
    print(f"请求体: {request_body}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                token_url,
                params=params,
                json=request_body,
                headers=headers
            )
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"响应内容: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                
                if response.status_code == 200 and 'access_token' in response_data:
                    print("✓ Token获取成功")
                    return response_data
                else:
                    print("✗ Token获取失败")
                    return None
                    
            except json.JSONDecodeError:
                print(f"响应内容 (非JSON): {response.text}")
                return None
                
    except Exception as e:
        print(f"✗ 请求异常: {e}")
        return None

async def test_different_approaches():
    """测试不同的请求方法"""
    print("\n=== 尝试不同请求方法 ===")
    
    base_url = "http://172.20.70.141"
    token_url = f"{base_url}/api/oauth/token"
    
    # 方法1: 标准OAuth2 password grant
    print("\n方法1: 标准OAuth2请求")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            data = {
                "grant_type": "password",
                "username": USERNAME,
                "password": PASSWORD,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "scope": "web"
            }
            
            response = await client.post(
                token_url,
                data=data,  # 使用form data而不是JSON
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"错误: {e}")
    
    # 方法2: 带Authorization header
    print("\n方法2: 带Authorization header")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # 使用基本认证
            import base64
            auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
            auth_bytes = auth_string.encode('ascii')
            auth_header = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "password",
                "username": USERNAME,
                "password": PASSWORD,
                "scope": "web"
            }
            
            response = await client.post(token_url, data=data, headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"错误: {e}")

async def main():
    """主函数"""
    print("开始Token问题诊断...\n")
    
    # 1. 分析当前token
    token_valid = analyze_current_token()
    
    # 2. 测试网络连接
    network_ok = await test_network_connectivity()
    
    if not network_ok:
        print("\n❌ 网络连接失败，请检查:")
        print("   1. 是否在正确的内网环境中")
        print("   2. 服务器地址是否正确")
        print("   3. 防火墙设置")
        return
    
    # 3. 测试token获取
    result = await test_token_endpoint()
    
    # 4. 如果标准方法失败，尝试其他方法
    if result is None:
        await test_different_approaches()
    
    print("\n=== 诊断总结 ===")
    if token_valid is False:
        print("📋 建议: 当前token已过期，需要获取新token")
    elif network_ok and result:
        print("✅ Token获取成功，问题已解决")
    elif network_ok:
        print("⚠️ 网络正常但token获取失败，可能是:")
        print("   1. 用户名密码错误")
        print("   2. 账户被禁用")
        print("   3. OAuth配置问题")
    else:
        print("🚫 网络连接问题，无法访问认证服务器")

if __name__ == "__main__":
    asyncio.run(main()) 