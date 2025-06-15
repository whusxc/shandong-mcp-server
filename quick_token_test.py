#!/usr/bin/env python3
"""
快速token获取测试 - 使用edu_admin/123456
"""

import asyncio
import httpx
import json

async def quick_token_test():
    """快速测试token获取 - 用于内网环境"""
    
    print("🔍 快速测试token获取 (edu_admin/123456)...")
    
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
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params, json=body, headers=headers)
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Token获取成功!")
                print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                # 提取token
                if 'data' in data and 'token' in data['data']:
                    token = data['data']['token']
                    token_head = data['data'].get('tokenHead', 'Bearer')
                    full_token = f"{token_head} {token}"
                    
                    print(f"完整Token: {full_token[:80]}...")
                    return full_token
                    
            else:
                print(f"❌ 请求失败: {response.text}")
                
    except Exception as e:
        print(f"❌ 连接异常: {str(e)}")
        print("   -> 可能原因: 不在内网环境或服务器不可达")
        
    return None

if __name__ == "__main__":
    token = asyncio.run(quick_token_test())
    
    if token:
        print(f"\n🎉 Token获取成功！可以用于后续API调用。")
    else:
        print(f"\n⚠️ Token获取失败。请确保在内网环境中运行此脚本。") 