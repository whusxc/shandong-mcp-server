#!/usr/bin/env python3
"""
检查MCP工具函数是否正确定义
"""

import inspect
import shandong_mcp_server_enhanced as server

def check_tools():
    """检查工具函数"""
    print("🔍 检查MCP工具函数...")
    print()
    
    expected_tools = [
        "coverage_aspect_analysis",
        "run_big_query", 
        "execute_code_to_dag",
        "submit_batch_task",
        "query_task_status", 
        "execute_dag_workflow"
    ]
    
    print("✅ 预期工具函数:")
    for i, tool_name in enumerate(expected_tools, 1):
        # 检查函数是否存在
        if hasattr(server, tool_name):
            func = getattr(server, tool_name)
            if inspect.iscoroutinefunction(func):
                print(f"  {i}. ✓ {tool_name} (异步函数)")
                
                # 获取函数签名
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if 'ctx' in params:
                    params.remove('ctx')  # 移除ctx参数显示
                print(f"     参数: {len(params)} 个 - {params[:3]}{'...' if len(params) > 3 else ''}")
            else:
                print(f"  {i}. ⚠️  {tool_name} (非异步函数)")
        else:
            print(f"  {i}. ✗ {tool_name} (未找到)")
    
    print()
    
    # 检查MCP服务器对象
    print("📋 MCP服务器信息:")
    print(f"  服务器名称: {server.mcp.name}")
    print(f"  服务器类型: {type(server.mcp)}")
    
    # 尝试获取工具数量（如果可能）
    try:
        if hasattr(server.mcp, '_tools'):
            print(f"  注册工具数量: {len(server.mcp._tools)}")
        elif hasattr(server.mcp, 'tools'):
            print(f"  注册工具数量: {len(server.mcp.tools)}")
        else:
            print("  无法获取工具数量")
    except Exception as e:
        print(f"  获取工具数量失败: {e}")

if __name__ == "__main__":
    check_tools() 