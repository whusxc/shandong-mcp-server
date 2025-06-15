#!/usr/bin/env python3
"""
MCP (Model Context Protocol) 学习指南
通过代码注释深入理解MCP的工作原理和实现方式
"""

# ============ MCP基础概念 ============

"""
MCP (Model Context Protocol) 是什么？
- 一个开放标准协议，用于连接AI模型与外部工具、数据和服务
- 允许AI助手安全地访问外部资源
- 支持实时通信和状态更新
- 设计用于与各种AI模型和应用集成

核心组件：
1. Server: 提供工具和资源的服务端
2. Client: 消费工具和资源的客户端（通常是AI应用）
3. Transport: 通信层（stdio或HTTP）
4. Tools: AI可以调用的函数
5. Resources: AI可以访问的数据源
"""

# ============ 导入MCP相关模块 ============

from mcp.server.fastmcp import FastMCP, Context
# FastMCP: 简化的MCP服务器框架
# - 提供装饰器式的工具定义 (@mcp.tool())
# - 自动处理协议细节
# - 支持异步操作

# Context: MCP上下文对象
# - 提供与客户端通信的能力
# - 可以发送日志消息、进度更新等
# - 包含会话信息和客户端状态

from mcp.server.sse import SseServerTransport
# SSE (Server-Sent Events): 实时通信传输层
# - 支持服务器向客户端推送实时消息
# - 适用于长时间运行的任务
# - 提供双向通信能力

from mcp.server import Server
# MCP核心服务器类
# - 处理协议级别的通信
# - 管理工具和资源注册
# - 处理客户端连接和会话

# ============ 创建MCP服务器实例 ============

# 创建FastMCP服务器实例
mcp = FastMCP("my-mcp-server")
# 参数是服务器名称，客户端用此名称识别服务器

# ============ 定义MCP工具 ============

@mcp.tool()  # MCP工具装饰器
async def simple_calculator(
    operation: str,      # 参数类型注解帮助AI理解参数要求
    a: float,
    b: float,
    ctx: Context = None  # MCP上下文，提供与客户端通信的能力
) -> str:               # 返回类型必须是字符串
    """
    简单计算器工具 - 演示MCP工具的基本结构
    
    这是一个MCP工具的标准结构：
    1. 使用 @mcp.tool() 装饰器
    2. 函数必须是异步的 (async def)
    3. 返回类型必须是字符串
    4. 可选的Context参数用于与客户端通信
    
    Parameters:
    - operation: 运算类型 (add, subtract, multiply, divide)
    - a: 第一个数字
    - b: 第二个数字
    """
    
    # 向客户端发送开始消息
    if ctx:
        await ctx.session.send_log_message("info", f"开始计算: {a} {operation} {b}")
    
    # 执行计算
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            return json.dumps({"error": "除数不能为0"})
        result = a / b
    else:
        return json.dumps({"error": f"不支持的运算类型: {operation}"})
    
    # 向客户端发送完成消息
    if ctx:
        await ctx.session.send_log_message("info", f"计算完成，结果: {result}")
    
    # 返回JSON格式的结果
    return json.dumps({
        "operation": operation,
        "operands": [a, b],
        "result": result
    })

@mcp.tool()
async def external_api_call(
    api_url: str,
    method: str = "GET",
    ctx: Context = None
) -> str:
    """
    外部API调用工具 - 演示如何在MCP工具中集成外部服务
    
    这个例子展示了：
    1. 如何在MCP工具中进行异步HTTP请求
    2. 如何处理外部API的响应和错误
    3. 如何向客户端发送实时状态更新
    """
    import httpx
    import json
    
    if ctx:
        await ctx.session.send_log_message("info", f"调用外部API: {api_url}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, api_url)
            
            if response.status_code == 200:
                result = {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                }
            else:
                result = {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
    
    except Exception as e:
        result = {
            "success": False,
            "error": str(e)
        }
    
    if ctx:
        status = "成功" if result.get("success") else "失败"
        await ctx.session.send_log_message("info", f"API调用{status}")
    
    return json.dumps(result)

# ============ 定义MCP资源 ============

@mcp.resource(uri="data://config/{config_name}", description="访问配置数据")
def get_config_data(config_name: str) -> str:
    """
    MCP资源 - 提供对配置数据的访问
    
    资源与工具的区别：
    - 工具(Tools): 执行动作的函数，可以修改状态
    - 资源(Resources): 提供数据访问，通常是只读的
    
    资源特点：
    1. 使用 @mcp.resource() 装饰器
    2. 通过URI模式定义访问路径
    3. 通常用于提供静态或半静态数据
    4. 不需要异步（可以是同步函数）
    """
    
    # 模拟配置数据
    configs = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "mydb"
        },
        "api": {
            "base_url": "https://api.example.com",
            "version": "v1",
            "timeout": 30
        }
    }
    
    config_data = configs.get(config_name, {"error": f"配置 {config_name} 不存在"})
    
    return json.dumps({
        "config_name": config_name,
        "data": config_data
    })

# ============ 高级MCP工具示例 ============

@mcp.tool()
async def long_running_task(
    task_name: str,
    duration: int = 10,
    ctx: Context = None
) -> str:
    """
    长时间运行的任务 - 演示如何处理耗时操作
    
    这个例子展示了：
    1. 如何向客户端发送进度更新
    2. 如何处理长时间运行的任务
    3. 如何提供实时反馈
    """
    import asyncio
    
    if ctx:
        await ctx.session.send_log_message("info", f"开始执行任务: {task_name}")
    
    # 模拟长时间运行的任务
    for i in range(duration):
        await asyncio.sleep(1)  # 模拟工作
        
        progress = (i + 1) / duration * 100
        
        if ctx:
            await ctx.session.send_log_message(
                "info", 
                f"任务 {task_name} 进度: {progress:.1f}% ({i+1}/{duration})"
            )
    
    result = {
        "task_name": task_name,
        "status": "completed",
        "duration": duration,
        "message": f"任务 {task_name} 已完成"
    }
    
    if ctx:
        await ctx.session.send_log_message("info", f"任务 {task_name} 执行完成")
    
    return json.dumps(result)

@mcp.tool()
async def file_operations(
    operation: str,
    file_path: str,
    content: str = None,
    ctx: Context = None
) -> str:
    """
    文件操作工具 - 演示如何在MCP中处理文件系统操作
    
    安全考虑：
    1. 验证文件路径，防止路径遍历攻击
    2. 限制操作范围
    3. 适当的错误处理
    """
    import os
    import json
    from pathlib import Path
    
    if ctx:
        await ctx.session.send_log_message("info", f"执行文件操作: {operation} on {file_path}")
    
    try:
        # 安全检查：限制操作范围
        safe_path = Path(file_path).resolve()
        allowed_dir = Path("./data").resolve()
        
        if not str(safe_path).startswith(str(allowed_dir)):
            return json.dumps({"error": "不允许访问此路径"})
        
        if operation == "read":
            if safe_path.exists():
                with open(safe_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                result = {"success": True, "content": content}
            else:
                result = {"error": "文件不存在"}
                
        elif operation == "write":
            if content is None:
                result = {"error": "写入操作需要提供内容"}
            else:
                safe_path.parent.mkdir(parents=True, exist_ok=True)
                with open(safe_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                result = {"success": True, "message": "文件写入成功"}
                
        elif operation == "exists":
            result = {"exists": safe_path.exists()}
            
        else:
            result = {"error": f"不支持的操作: {operation}"}
    
    except Exception as e:
        result = {"error": str(e)}
    
    if ctx:
        status = "成功" if result.get("success") else "失败"
        await ctx.session.send_log_message("info", f"文件操作{status}")
    
    return json.dumps(result)

# ============ HTTP服务器模式 ============

def create_http_server():
    """
    创建HTTP模式的MCP服务器
    
    HTTP模式的优势：
    1. 支持多客户端连接
    2. 更好的可扩展性
    3. 支持负载均衡
    4. 适合生产环境部署
    """
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from mcp.server.sse import SseServerTransport
    
    # 创建SSE传输层
    sse = SseServerTransport("/messages/")
    
    async def handle_sse(request):
        """处理SSE连接"""
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            # 运行MCP服务器
            await mcp._mcp_server.run(
                read_stream,
                write_stream,
                mcp._mcp_server.create_initialization_options(),
            )
    
    async def handle_info(request):
        """服务器信息端点"""
        return JSONResponse({
            "server_name": "my-mcp-server",
            "version": "1.0.0",
            "description": "MCP学习示例服务器",
            "tools": ["simple_calculator", "external_api_call", "long_running_task", "file_operations"],
            "resources": ["config"]
        })
    
    # 创建Starlette应用
    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/info", endpoint=handle_info),
        ],
    )
    
    return app

# ============ 运行服务器 ============

async def run_stdio_server():
    """
    运行stdio模式的MCP服务器
    
    stdio模式的特点：
    1. 通过标准输入输出通信
    2. 适合作为子进程运行
    3. 简单直接的通信方式
    4. 适合开发和测试
    """
    from mcp import stdio_server
    
    print("启动MCP服务器 (stdio模式)...")
    
    try:
        async with stdio_server() as streams:
            await mcp._mcp_server.run(
                streams[0],  # 输入流
                streams[1],  # 输出流
                mcp._mcp_server.create_initialization_options()
            )
    except KeyboardInterrupt:
        print("服务器已停止")

def run_http_server():
    """运行HTTP模式的MCP服务器"""
    import uvicorn
    
    print("启动MCP服务器 (HTTP模式)...")
    app = create_http_server()
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ============ MCP最佳实践 ============

"""
MCP开发最佳实践：

1. 工具设计：
   - 保持工具功能单一且专注
   - 提供清晰的参数类型注解
   - 编写详细的文档字符串
   - 返回结构化的JSON数据

2. 错误处理：
   - 捕获和处理所有可能的异常
   - 提供有意义的错误消息
   - 使用统一的错误格式

3. 安全考虑：
   - 验证和清理输入参数
   - 限制文件系统访问范围
   - 使用适当的身份验证
   - 避免执行任意代码

4. 性能优化：
   - 使用异步操作
   - 实现适当的超时机制
   - 考虑资源使用限制
   - 提供进度反馈

5. 客户端通信：
   - 使用Context发送实时更新
   - 提供详细的日志信息
   - 支持取消长时间运行的操作

6. 部署和监控：
   - 实现健康检查端点
   - 添加度量和监控
   - 使用结构化日志
   - 考虑负载均衡和高可用性

7. 测试：
   - 编写单元测试
   - 测试错误场景
   - 验证与不同客户端的兼容性
   - 进行性能测试
"""

# ============ 主程序入口 ============

if __name__ == "__main__":
    import argparse
    import asyncio
    import json
    
    parser = argparse.ArgumentParser(description='MCP学习示例服务器')
    parser.add_argument('--mode', choices=['stdio', 'http'], default='stdio', help='运行模式')
    
    args = parser.parse_args()
    
    if args.mode == 'stdio':
        asyncio.run(run_stdio_server())
    else:
        run_http_server()

"""
MCP学习总结：

核心概念：
- MCP是连接AI与外部服务的标准协议
- 工具(Tools)执行动作，资源(Resources)提供数据
- 支持stdio和HTTP两种通信方式
- 异步操作是必需的

关键组件：
- FastMCP: 简化的服务器框架
- Context: 客户端通信接口
- 装饰器: 简化工具和资源注册
- 传输层: 处理底层通信

开发流程：
1. 创建MCP服务器实例
2. 定义工具和资源
3. 设置传输层
4. 运行服务器

这个学习指南展示了MCP的完整实现，从基础概念到高级特性，
为开发者提供了全面的MCP开发知识。
""" 