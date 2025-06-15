#!/usr/bin/env python3
"""
测试修复后的token获取功能
"""

import asyncio
import json
from shandong_mcp_server_enhanced import get_oauth_token

async def test_token_get():
    """测试token获取功能"""
    print("🚀 测试token获取功能（已修复Authorization header问题）...")
    
    try:
        # 调用修复后的token获取函数
        result_json = await get_oauth_token(
            username="edu_admin",
            password="123456",
            client_id="test", 
            client_secret="123456",
            scopes="web",
            grant_type="password"
        )
        
        result = json.loads(result_json)
        
        if result.get("success"):
            print("✅ Token获取成功!")
            
            token_data = result.get("data", {})
            print(f"   - Access Token: {token_data.get('access_token', '')[:50]}...")
            print(f"   - Token Type: {token_data.get('token_type', 'N/A')}")
            print(f"   - Expires In: {token_data.get('expires_in', 0)} seconds")
            print(f"   - Full Token: {token_data.get('full_token', '')[:50]}...")
            
            return True
        else:
            print("❌ Token获取失败:")
            print(f"   - 错误信息: {result.get('msg', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始测试修复后的token获取功能...\n")
    success = asyncio.run(test_token_get())
    
    if success:
        print("\n🎉 修复验证成功！现在可以正常获取token了。")
    else:
        print("\n⚠️ 如果仍然失败，请检查网络连接和内网环境。") 