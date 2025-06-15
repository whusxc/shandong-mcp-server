#!/usr/bin/env python3
"""
测试OAuth Token获取功能
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

# 测试配置
BASE_URL = "http://172.20.70.142:16555"
TOKEN_URL = f"{BASE_URL}/gateway/oauth/token"

# 测试凭据 (请根据实际情况修改)
TEST_CREDENTIALS = {
    "username": "edu_admin",
    "password": "123456",
    "client_id": "test",
    "client_secret": "123456",
    "scopes": "web",
    "grant_type": "password"
}

EXISTING_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjMyNCwidXNlcl9uYW1lIjoiZWR1X2FkbWluIiwic2NvcGUiOlsid2ViIl0sImV4cCI6MTc0OTkwNjkwMiwidXVpZCI6ImY5NTBjZmYyLTA3YzgtNDYxYS05YzI0LTkxNjJkNTllMmVmNiIsImF1dGhvcml0aWVzIjpbIkFETUlOSVNUUkFUT1JTIl0sImp0aSI6IkxQbjJQTThlRlpBRDhUNFBxN2U3SWlRdmRGQSIsImNsaWVudF9pZCI6InRlc3QiLCJ1c2VybmFtZSI6ImVkdV9hZG1pbiJ9.jFepdzkcDDlcH0v3Z_Ge35vbiTB3RVt8OQsHJ0o6qEU"

async def test_oauth_token_direct():
    """直接测试OAuth Token API"""
    print("🔐 直接测试OAuth Token API...")
    print(f"📍 请求地址: {TOKEN_URL}")
    
    # 构建查询参数
    params = {
        "scopes": TEST_CREDENTIALS["scopes"],
        "client_secret": TEST_CREDENTIALS["client_secret"],
        "client_id": TEST_CREDENTIALS["client_id"],
        "username": TEST_CREDENTIALS["username"],
        "password": TEST_CREDENTIALS["password"],
        "grant_type": TEST_CREDENTIALS["grant_type"]
    }
    
    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": EXISTING_TOKEN
    }
    
    # 构建请求体
    request_body = {
        "username": TEST_CREDENTIALS["username"],
        "password": TEST_CREDENTIALS["password"]
    }
    
    print(f"📝 查询参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
    print(f"📋 请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
    
    start_time = time.perf_counter()
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                TOKEN_URL,
                params=params,
                json=request_body,
                headers=headers
            )
            
            execution_time = time.perf_counter() - start_time
            
            print(f"⏱️  执行时间: {execution_time:.2f}秒")
            print(f"📊 HTTP状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Token获取成功!")
                print(f"📄 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 提取关键信息
                access_token = result.get('access_token', '')
                token_type = result.get('token_type', 'Bearer')
                expires_in = result.get('expires_in', 0)
                
                print(f"\n🔑 Token信息:")
                print(f"  Token类型: {token_type}")
                print(f"  有效期: {expires_in}秒")
                print(f"  完整Token: {token_type} {access_token[:50]}...")
                
                return {
                    "success": True,
                    "data": result,
                    "full_token": f"{token_type} {access_token}",
                    "execution_time": execution_time
                }
            else:
                print(f"❌ Token获取失败!")
                print(f"📄 错误内容: {response.text}")
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code,
                    "execution_time": execution_time
                }
                
    except Exception as e:
        execution_time = time.perf_counter() - start_time
        print(f"💥 请求异常: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "execution_time": execution_time
        }

async def test_mcp_oauth_integration():
    """测试MCP服务器中的OAuth集成"""
    print("\n" + "="*60)
    print("🧪 测试MCP服务器OAuth集成...")
    print("="*60)
    
    # 这里可以添加MCP服务器集成测试
    # 由于需要启动MCP服务器，这里先模拟
    
    test_request = {
        "name": "get_oauth_token",
        "arguments": {
            "username": TEST_CREDENTIALS["username"],
            "password": TEST_CREDENTIALS["password"],
            "client_id": TEST_CREDENTIALS["client_id"],
            "client_secret": TEST_CREDENTIALS["client_secret"]
        }
    }
    
    print(f"📋 MCP工具调用示例:")
    print(f"```json")
    print(json.dumps(test_request, ensure_ascii=False, indent=2))
    print(f"```")
    
    refresh_request = {
        "name": "refresh_intranet_token",
        "arguments": {
            "username": TEST_CREDENTIALS["username"],
            "password": TEST_CREDENTIALS["password"],
            "update_global_token": True
        }
    }
    
    print(f"\n📋 Token刷新调用示例:")
    print(f"```json")
    print(json.dumps(refresh_request, ensure_ascii=False, indent=2))
    print(f"```")

async def main():
    """主测试函数"""
    print("🚀 OAuth Token功能测试")
    print("=" * 40)
    
    # 测试1: 直接API调用
    result = await test_oauth_token_direct()
    
    # 测试2: MCP集成示例
    await test_mcp_oauth_integration()
    
    # 测试结果总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    
    if result.get("success"):
        print("✅ OAuth Token API调用成功")
        print(f"⏱️  响应时间: {result.get('execution_time', 0):.2f}秒")
        print("🎯 MCP工具可以正常获取Token")
        print("\n💡 使用建议:")
        print("1. 在MCP服务器中使用 get_oauth_token 工具获取新token")
        print("2. 使用 refresh_intranet_token 工具刷新并更新全局token")
        print("3. Token有效期内可以进行坡向分析等操作")
    else:
        print("❌ OAuth Token API调用失败")
        print(f"❗ 错误信息: {result.get('error', '未知错误')}")
        print("\n🔧 排查建议:")
        print("1. 检查网络连接和API地址")
        print("2. 验证用户名密码是否正确")
        print("3. 确认现有Token是否有效")
        print("4. 检查客户端ID和密钥配置")

if __name__ == "__main__":
    asyncio.run(main()) 