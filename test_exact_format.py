#!/usr/bin/env python3
"""
完全模拟Apifox成功请求格式的测试
"""

import asyncio
import httpx
import json

async def test_exact_apifox_format():
    """完全按照Apifox成功截图的格式测试"""
    
    print("🧪 模拟Apifox成功请求格式...")
    
    # 完全按照截图的格式
    url = "http://172.20.70.141/api/oauth/token"
    
    # 查询参数（完全按照截图）
    params = {
        "scopes": "web",
        "client_secret": "123456",
        "client_id": "test", 
        "grant_type": "password",
        "username": "edu_admin",
        "password": "123456"
    }
    
    # 请求体（完全按照截图）
    body = {
        "username": "edu_admin",
        "password": "123456"
    }
    
    # 请求头（不包含Authorization）
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"📤 URL: {url}")
    print(f"📤 Params: {params}")
    print(f"📤 Body: {json.dumps(body, indent=2)}")
    print(f"📤 Headers: {json.dumps(headers, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                params=params,
                json=body,
                headers=headers
            )
            
            print(f"\n📥 响应状态码: {response.status_code}")
            print(f"📥 响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"📥 响应内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    # 检查是否包含token - 根据截图，应该有 "token" 字段
                    if 'token' in data or 'access_token' in data:
                        token = data.get('token') or data.get('access_token')
                        print(f"✅ 成功获取token: {token[:50]}...")
                        return True
                    else:
                        print("⚠️ 响应成功但没有token字段")
                        print(f"   可用字段: {list(data.keys())}")
                        return False
                        
                except json.JSONDecodeError:
                    print(f"📥 响应内容 (非JSON): {response.text}")
                    return False
            else:
                print(f"❌ 请求失败: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始精确测试token获取...\n")
    success = asyncio.run(test_exact_apifox_format())
    
    if success:
        print("\n🎉 测试成功！格式正确。")
    else:
        print("\n❌ 测试失败，需要进一步调试。") 