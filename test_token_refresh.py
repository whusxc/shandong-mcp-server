#!/usr/bin/env python3
"""
测试MCP服务器的token自动刷新机制
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from shandong_mcp_server_enhanced import (
    refresh_intranet_token,
    call_api_with_timing,
    INTRANET_API_BASE_URL,
    INTRANET_AUTH_TOKEN
)

async def test_token_refresh():
    """测试token刷新功能"""
    print("🔍 测试Token刷新功能...")
    
    # 1. 测试手动刷新token
    print("\n1. 测试手动刷新token...")
    success, new_token = await refresh_intranet_token()
    
    if success:
        print(f"✅ Token刷新成功: {new_token[:50]}...")
        print(f"📝 Token长度: {len(new_token)}")
    else:
        print(f"❌ Token刷新失败: {new_token}")
        return False
    
    # 2. 测试自动token刷新机制
    print("\n2. 测试自动token刷新机制...")
    
    # 构建一个测试API调用
    test_payload = {
        "name": "FeatureCollection.runBigQuery",
        "args": {
            "query": "SELECT * FROM shp_guotubiangeng LIMIT 1",
            "geometryColumn": "geom"
        },
        "dockerImageSource": "DOCKER_HUB"
    }
    
    print("🚀 发起API调用测试...")
    api_result, execution_time = await call_api_with_timing(
        url=INTRANET_API_BASE_URL,
        json_data=test_payload,
        use_intranet_token=True
    )
    
    if "error" not in api_result:
        print(f"✅ API调用成功，耗时: {execution_time:.2f}s")
        print(f"📋 响应代码: {api_result.get('code', 'N/A')}")
        print(f"📋 响应消息: {api_result.get('msg', 'N/A')}")
        
        # 检查是否有数据返回
        if 'data' in api_result:
            data = api_result['data']
            print(f"📊 返回数据类型: {type(data)}")
            if isinstance(data, dict):
                print(f"📊 数据键: {list(data.keys())}")
        
        return True
    else:
        print(f"❌ API调用失败: {api_result.get('error')}")
        return False

async def test_token_expiry_simulation():
    """模拟token过期场景"""
    print("\n3. 模拟token过期场景...")
    
    # 备份原始token
    global INTRANET_AUTH_TOKEN
    original_token = INTRANET_AUTH_TOKEN
    
    try:
        # 设置一个无效的token来模拟过期
        INTRANET_AUTH_TOKEN = "Bearer invalid_token_for_testing"
        print(f"🔧 设置无效token进行测试...")
        
        # 构建测试API调用
        test_payload = {
            "name": "FeatureCollection.runBigQuery",
            "args": {
                "query": "SELECT * FROM shp_guotubiangeng LIMIT 1",
                "geometryColumn": "geom"
            },
            "dockerImageSource": "DOCKER_HUB"
        }
        
        print("🚀 使用无效token发起API调用...")
        api_result, execution_time = await call_api_with_timing(
            url=INTRANET_API_BASE_URL,
            json_data=test_payload,
            use_intranet_token=True
        )
        
        if "error" not in api_result:
            print(f"✅ API调用成功（token自动刷新生效），耗时: {execution_time:.2f}s")
            print(f"📋 响应代码: {api_result.get('code', 'N/A')}")
            return True
        else:
            print(f"⚠️ API调用失败: {api_result.get('error')}")
            return False
            
    finally:
        # 恢复原始token
        INTRANET_AUTH_TOKEN = original_token
        print(f"🔄 已恢复原始token")

async def main():
    """主测试函数"""
    print("🧪 MCP服务器Token刷新机制测试")
    print("=" * 50)
    
    try:
        # 测试1: 手动刷新token
        test1_success = await test_token_refresh()
        
        # 测试2: 模拟token过期
        test2_success = await test_token_expiry_simulation()
        
        print("\n" + "=" * 50)
        print("📊 测试结果摘要:")
        print(f"   ✅ 手动Token刷新: {'通过' if test1_success else '失败'}")
        print(f"   ✅ 自动Token刷新: {'通过' if test2_success else '失败'}")
        
        if test1_success and test2_success:
            print("\n🎉 所有测试通过！Token自动刷新机制工作正常。")
            return True
        else:
            print("\n⚠️ 部分测试失败，请检查配置和网络连接。")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 