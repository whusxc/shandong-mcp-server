#!/usr/bin/env python3
"""
简单测试MCP工具注册情况
"""

import asyncio
from shandong_mcp_server_enhanced import mcp

async def test_tools_registration():
    """测试工具注册情况"""
    print("🔍 测试MCP工具注册情况...")
    print(f"MCP服务器名称: {mcp.name}")
    print()
    
    # 获取所有注册的工具
    tools_result = await mcp._mcp_server.list_tools()
    
    print(f"📋 已注册的工具数量: {len(tools_result.tools)}")
    print()
    
    expected_tools = [
        "coverage_aspect_analysis",
        "run_big_query",
        "execute_code_to_dag", 
        "submit_batch_task",
        "query_task_status",
        "execute_dag_workflow"
    ]
    
    registered_tools = [tool.name for tool in tools_result.tools]
    
    print("✅ 预期工具:")
    for i, tool_name in enumerate(expected_tools, 1):
        status = "✓" if tool_name in registered_tools else "✗"
        print(f"  {i}. {status} {tool_name}")
    
    print()
    print("📝 实际注册的工具:")
    for i, tool in enumerate(tools_result.tools, 1):
        print(f"  {i}. {tool.name}")
        if tool.description:
            # 只显示描述的第一行
            first_line = tool.description.split('\n')[0].strip()
            print(f"     描述: {first_line}")
    
    print()
    
    # 检查是否完全匹配
    if set(registered_tools) == set(expected_tools):
        print("🎉 工具注册完全正确！")
        return True
    else:
        print("⚠️  工具注册不匹配")
        missing = set(expected_tools) - set(registered_tools)
        extra = set(registered_tools) - set(expected_tools)
        
        if missing:
            print(f"   缺少工具: {list(missing)}")
        if extra:
            print(f"   多余工具: {list(extra)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_tools_registration()) 