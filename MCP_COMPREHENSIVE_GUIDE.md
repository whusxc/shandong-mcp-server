# MCP (Model Context Protocol) 全面学习指南

## 📖 目录
1. [MCP基础概念](#mcp基础概念)
2. [核心架构](#核心架构)
3. [代码详解](#代码详解)
4. [实战示例](#实战示例)
5. [最佳实践](#最佳实践)
6. [常见问题](#常见问题)

## 🏗️ MCP基础概念

### MCP是什么？
**Model Context Protocol (MCP)** 是一个开放标准协议，专门用于连接AI模型与外部工具、数据源和服务。它允许AI助手安全地访问和操作外部资源。

### 为什么需要MCP？
```
传统AI局限性:
┌─────────────────┐
│   AI模型        │  ❌ 只能处理训练数据
│                 │  ❌ 无法访问实时信息
│                 │  ❌ 不能执行外部操作
└─────────────────┘

MCP解决方案:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI模型        │◄──►│  MCP服务器      │◄──►│  外部服务       │
│                 │    │                 │    │                 │
│ • 推理能力      │    │ • 工具集合      │    │ • 数据库        │
│ • 语言理解      │    │ • 安全控制      │    │ • API服务       │
│ • 决策制定      │    │ • 实时通信      │    │ • 文件系统      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🏛️ 核心架构

### 架构组件

#### 1. **客户端 (Client)**
```python
# 客户端是AI应用，负责：
# - 连接到MCP服务器
# - 发送工具调用请求
# - 接收和处理响应
```

#### 2. **服务器 (Server)**
```python
# 服务器提供工具和资源，负责：
# - 注册可用的工具和资源
# - 处理客户端请求
# - 执行具体操作
# - 返回结果
```

#### 3. **传输层 (Transport)**
```python
# 两种传输方式：

# stdio: 标准输入输出
# - 适合子进程运行
# - 简单直接
# - 适用于开发测试

# HTTP/SSE: Web服务
# - 支持多客户端
# - 适合生产环境
# - 支持负载均衡
```

### 数据流图
```
客户端请求流程:
┌─────────┐  1.连接    ┌─────────┐  2.发现    ┌─────────┐
│AI客户端 │ ────────► │MCP服务器│ ────────► │工具列表 │
└─────────┘           └─────────┘           └─────────┘
     │                      │                      │
     │3.调用工具              │4.执行               │
     ▼                      ▼                      ▼
┌─────────┐  6.返回    ┌─────────┐  5.获取    ┌─────────┐
│处理结果 │ ◄──────── │处理请求 │ ◄──────── │外部资源 │
└─────────┘           └─────────┘           └─────────┘
```

## 💻 代码详解

### 1. 导入和基础设置

```python
#!/usr/bin/env python3
# Shebang行：指定Python解释器路径

from mcp.server.fastmcp import FastMCP, Context
# FastMCP: 简化的MCP服务器框架
# - 提供装饰器模式的工具定义
# - 自动处理MCP协议的底层细节
# - 支持异步操作

# Context: MCP上下文对象
# - 提供与客户端的通信接口
# - 包含会话状态信息
# - 支持实时消息推送
```

### 2. 创建服务器实例

```python
mcp = FastMCP("my-server-name")
# 创建MCP服务器实例
# 参数: 服务器名称（客户端用于识别）
```

### 3. 定义工具 (Tools)

```python
@mcp.tool()  # 🔧 工具装饰器
async def my_function(
    param1: str,           # 📝 参数类型注解（帮助AI理解）
    param2: int = 10,      # 📝 默认值
    ctx: Context = None    # 📝 MCP上下文（可选）
) -> str:                  # 📝 返回类型必须是字符串
    """
    工具描述文档
    
    这里的文档字符串会被MCP客户端看到，
    帮助AI理解工具的功能和用法。
    """
    
    # 💬 向客户端发送实时消息
    if ctx:
        await ctx.session.send_log_message("info", "开始执行...")
    
    # 🔄 执行业务逻辑
    result = perform_some_operation(param1, param2)
    
    # 📤 返回JSON格式结果
    return json.dumps({
        "success": True,
        "data": result,
        "message": "操作完成"
    })
```

#### 工具定义要点：
- **装饰器**: `@mcp.tool()` 注册函数为MCP工具
- **异步**: 必须使用 `async def`
- **返回类型**: 必须返回字符串（通常是JSON）
- **参数注解**: 帮助AI理解参数要求
- **文档字符串**: 为AI提供工具说明

### 4. 定义资源 (Resources)

```python
@mcp.resource(uri="data://config/{name}", description="配置数据访问")
def get_config(name: str) -> str:
    """
    🗂️ MCP资源：提供数据访问
    
    资源vs工具：
    - 工具: 执行动作，可能修改状态
    - 资源: 提供数据，通常只读
    """
    
    # 📊 获取数据
    config_data = load_config(name)
    
    # 📤 返回数据
    return json.dumps(config_data)
```

### 5. 实时通信

```python
async def long_task(ctx: Context = None):
    """演示实时通信功能"""
    
    for i in range(10):
        # 💼 执行工作
        await do_some_work()
        
        # 📢 发送进度更新
        if ctx:
            progress = (i + 1) * 10
            await ctx.session.send_log_message(
                "info", 
                f"进度: {progress}%"
            )
```

### 6. 服务器运行模式

#### stdio模式：
```python
async def run_stdio():
    """标准输入输出模式"""
    from mcp import stdio_server
    
    async with stdio_server() as streams:
        await mcp._mcp_server.run(
            streams[0],  # 输入流
            streams[1],  # 输出流
            mcp._mcp_server.create_initialization_options()
        )
```

#### HTTP模式：
```python
def run_http():
    """HTTP服务器模式"""
    from starlette.applications import Starlette
    import uvicorn
    
    app = create_starlette_app(mcp._mcp_server)
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 🛠️ 实战示例

### 示例1: 简单计算器

```python
@mcp.tool()
async def calculator(operation: str, a: float, b: float, ctx: Context = None) -> str:
    """
    计算器工具
    
    Parameters:
    - operation: 运算类型 (add, sub, mul, div)
    - a: 第一个数字
    - b: 第二个数字
    """
    
    # 📝 记录开始
    if ctx:
        await ctx.session.send_log_message("info", f"计算: {a} {operation} {b}")
    
    # 🧮 执行计算
    operations = {
        "add": lambda x, y: x + y,
        "sub": lambda x, y: x - y,
        "mul": lambda x, y: x * y,
        "div": lambda x, y: x / y if y != 0 else None
    }
    
    if operation not in operations:
        return json.dumps({"error": f"不支持的运算: {operation}"})
    
    result = operations[operation](a, b)
    
    if result is None:
        return json.dumps({"error": "除数不能为0"})
    
    # 📤 返回结果
    return json.dumps({
        "operation": operation,
        "operands": [a, b],
        "result": result
    })
```

### 示例2: 文件操作

```python
@mcp.tool()
async def file_manager(
    action: str, 
    path: str, 
    content: str = None, 
    ctx: Context = None
) -> str:
    """
    文件管理工具
    
    Parameters:
    - action: 操作类型 (read, write, delete, exists)
    - path: 文件路径
    - content: 文件内容（写入时需要）
    """
    import os
    from pathlib import Path
    
    # 🔒 安全检查
    safe_path = Path(path).resolve()
    allowed_dir = Path("./data").resolve()
    
    if not str(safe_path).startswith(str(allowed_dir)):
        return json.dumps({"error": "路径不在允许范围内"})
    
    # 📝 记录操作
    if ctx:
        await ctx.session.send_log_message("info", f"文件操作: {action} {path}")
    
    try:
        if action == "read":
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            result = {"success": True, "content": content}
            
        elif action == "write":
            if content is None:
                return json.dumps({"error": "写入操作需要提供内容"})
            
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            result = {"success": True, "message": "写入成功"}
            
        elif action == "delete":
            if safe_path.exists():
                safe_path.unlink()
                result = {"success": True, "message": "删除成功"}
            else:
                result = {"error": "文件不存在"}
                
        elif action == "exists":
            result = {"exists": safe_path.exists()}
            
        else:
            result = {"error": f"不支持的操作: {action}"}
    
    except Exception as e:
        result = {"error": str(e)}
    
    return json.dumps(result)
```

### 示例3: 外部API集成

```python
@mcp.tool()
async def api_client(
    url: str, 
    method: str = "GET", 
    data: dict = None,
    ctx: Context = None
) -> str:
    """
    外部API客户端
    
    Parameters:
    - url: API地址
    - method: HTTP方法
    - data: 请求数据
    """
    import httpx
    
    if ctx:
        await ctx.session.send_log_message("info", f"调用API: {method} {url}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=data)
            else:
                return json.dumps({"error": f"不支持的方法: {method}"})
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }
    
    except Exception as e:
        result = {"error": str(e), "success": False}
    
    if ctx:
        status = "成功" if result.get("success") else "失败"
        await ctx.session.send_log_message("info", f"API调用{status}")
    
    return json.dumps(result)
```

## ✅ 最佳实践

### 1. 工具设计原则

```python
# ✅ 好的设计
@mcp.tool()
async def send_email(to: str, subject: str, body: str) -> str:
    """发送邮件 - 功能单一，参数清晰"""
    pass

# ❌ 不好的设计
@mcp.tool()
async def do_everything(action: str, **kwargs) -> str:
    """万能工具 - 功能混乱，难以理解"""
    pass
```

### 2. 错误处理

```python
@mcp.tool()
async def robust_tool(param: str, ctx: Context = None) -> str:
    """展示良好的错误处理"""
    
    try:
        # ✅ 参数验证
        if not param or not param.strip():
            return json.dumps({"error": "参数不能为空"})
        
        # ✅ 业务逻辑
        result = process_data(param)
        
        # ✅ 成功响应
        return json.dumps({
            "success": True,
            "data": result,
            "message": "处理成功"
        })
    
    except ValueError as e:
        # ✅ 具体错误处理
        return json.dumps({"error": f"数据错误: {str(e)}"})
    
    except Exception as e:
        # ✅ 通用错误处理
        return json.dumps({"error": f"处理失败: {str(e)}"})
```

### 3. 安全考虑

```python
@mcp.tool()
async def secure_tool(file_path: str) -> str:
    """安全的文件操作"""
    from pathlib import Path
    
    # ✅ 路径验证
    safe_path = Path(file_path).resolve()
    allowed_base = Path("./safe_directory").resolve()
    
    if not str(safe_path).startswith(str(allowed_base)):
        return json.dumps({"error": "路径不在允许范围内"})
    
    # ✅ 权限检查
    if not os.access(safe_path.parent, os.W_OK):
        return json.dumps({"error": "没有写入权限"})
    
    # 继续处理...
```

### 4. 性能优化

```python
@mcp.tool()
async def optimized_tool(data_list: List[str], ctx: Context = None) -> str:
    """性能优化示例"""
    
    total = len(data_list)
    results = []
    
    # ✅ 批量处理
    for i, item in enumerate(data_list):
        result = await process_item(item)
        results.append(result)
        
        # ✅ 进度反馈
        if ctx and i % 10 == 0:
            progress = (i + 1) / total * 100
            await ctx.session.send_log_message("info", f"进度: {progress:.1f}%")
    
    return json.dumps({"results": results, "total": total})
```

## ❓ 常见问题

### Q: 为什么工具函数必须是异步的？
**A:** MCP设计为异步协议，支持：
- 非阻塞的并发操作
- 实时状态更新
- 长时间运行的任务
- 更好的性能和响应性

### Q: 工具的返回值为什么必须是字符串？
**A:** 这是MCP协议的要求：
- 确保跨语言兼容性
- 简化序列化/反序列化
- 通常返回JSON格式的字符串

### Q: 什么时候使用工具，什么时候使用资源？
**A:** 
- **工具 (Tools)**: 执行动作，可能修改状态
  - 发送邮件、创建文件、调用API
- **资源 (Resources)**: 提供数据访问，通常只读
  - 配置文件、日志文件、数据库查询结果

### Q: 如何处理敏感信息？
**A:** 
```python
# ✅ 安全处理敏感信息
@mcp.tool()
async def handle_sensitive_data(api_key: str) -> str:
    # 不要在日志中记录敏感信息
    # 使用安全的存储方式
    # 验证权限
    pass
```

### Q: 如何调试MCP服务器？
**A:**
```python
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)

# 在工具中添加调试信息
@mcp.tool()
async def debug_tool(param: str, ctx: Context = None) -> str:
    if ctx:
        await ctx.session.send_log_message("debug", f"参数: {param}")
    # ...
```

## 🎯 总结

MCP是一个强大的协议，让AI能够：
- 🔧 **调用外部工具** - 执行各种操作
- 📊 **访问实时数据** - 获取最新信息
- 🔄 **实时通信** - 提供进度反馈
- 🛡️ **安全控制** - 限制访问范围

通过理解MCP的核心概念和最佳实践，您可以构建强大的AI集成解决方案！

---

## 📚 进一步学习

- [MCP官方文档](https://modelcontextprotocol.io)
- [MCP GitHub仓库](https://github.com/modelcontextprotocol)
- [示例项目](https://github.com/modelcontextprotocol/servers) 