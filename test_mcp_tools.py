#!/usr/bin/env python3
"""
测试MCP工具注册和功能
"""

import asyncio
import json
from shandong_mcp_server_enhanced import mcp, coverage_aspect_analysis

async def test_mcp_tools():
    """测试MCP工具"""
    print("🔍 测试MCP工具注册和功能...")
    
    # 1. 检查MCP实例
    print(f"MCP服务器名称: {mcp.name}")
    
    # 2. 列出所有注册的工具
    print("\n📋 已注册的工具:")
    tools = await mcp.list_tools()
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool.name}")
        print(f"   描述: {tool.description}")
        print(f"   参数: {len(tool.inputSchema.get('properties', {}))} 个")
    
    # 3. 测试坡向分析工具
    print("\n🧪 测试坡向分析工具...")
    try:
        # 测试参数
        test_bbox = [110.062408, 19.317623, 110.413971, 19.500253]
        
        print(f"测试边界框: {test_bbox}")
        
        # 直接调用函数测试
        result_json = await coverage_aspect_analysis(
            bbox=test_bbox,
            ctx=None
        )
        
        result = json.loads(result_json)
        print(f"✅ 工具调用结果:")
        print(f"   成功: {result.get('success')}")
        print(f"   消息: {result.get('msg')}")
        print(f"   操作: {result.get('operation')}")
        
        if result.get('success'):
            print("   ✅ 坡向分析工具工作正常")
        else:
            print("   ❌ 坡向分析工具执行失败")
            print(f"   错误详情: {result}")
            
    except Exception as e:
        print(f"❌ 工具测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_tools()) 