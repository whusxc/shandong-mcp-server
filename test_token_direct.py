#!/usr/bin/env python3
"""
直接测试token刷新功能
"""

import asyncio
import httpx
import time

async def test_token_refresh():
    """测试token刷新"""
    print("🔍 测试token刷新功能...")
    
    url = "http://172.20.70.141/api/oauth/token"
    
    params = {
        "scopes": "web",
        "client_secret": "123456",
        "client_id": "test",
        "grant_type": "password",
        "username": "edu_admin",
        "password": "123456"
    }
    
    body = {
        "username": "edu_admin",
        "password": "123456"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"请求URL: {url}")
    print(f"请求参数: {params}")
    print(f"请求体: {body}")
    
    try:
        start_time = time.perf_counter()
        
        # 测试不同的超时时间
        for timeout in [5, 10, 30]:
            print(f"\n⏱️ 测试超时时间: {timeout}秒")
            
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, params=params, json=body, headers=headers)
                    
                    execution_time = time.perf_counter() - start_time
                    
                    print(f"✅ 响应状态码: {response.status_code}")
                    print(f"⏱️ 执行时间: {execution_time:.2f}秒")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ 响应数据: {data}")
                        
                        if 'data' in data and 'token' in data['data']:
                            token = data['data']['token']
                            token_head = data['data'].get('tokenHead', 'Bearer')
                            full_token = f"{token_head} {token}"
                            print(f"🎉 Token获取成功: {full_token[:50]}...")
                            return True
                        else:
                            print(f"❌ 响应格式错误: {data}")
                    else:
                        print(f"❌ HTTP错误: {response.status_code} - {response.text}")
                        
            except httpx.TimeoutException:
                print(f"⏰ 请求超时 ({timeout}秒)")
            except Exception as e:
                print(f"❌ 请求异常: {str(e)}")
                
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return False

if __name__ == "__main__":
    asyncio.run(test_token_refresh()) 