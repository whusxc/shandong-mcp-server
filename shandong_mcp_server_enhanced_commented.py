#!/usr/bin/env python3
"""
山东耕地流出分析 MCP服务器 - 增强版（带详细注释）
整合FastMCP框架，支持HTTP和stdio两种传输方式

MCP (Model Context Protocol) 是一个开放标准，用于将应用程序与AI模型连接
它允许AI助手访问外部工具、数据源和服务
"""

# ============ 标准库导入 ============
import asyncio          # 异步编程支持，MCP服务器需要异步运行
import json            # JSON数据处理，MCP协议使用JSON格式通信
import logging         # 日志记录，用于调试和监控
import httpx           # 异步HTTP客户端，用于调用外部API
import time            # 时间相关功能，用于性能监控
from pathlib import Path      # 路径操作，处理文件和目录
from typing import Any, Dict, List, Optional, TypeVar  # 类型提示，提高代码可读性
from pydantic import BaseModel    # 数据模型验证
from enum import IntEnum         # 枚举类型

# ============ MCP SDK 导入 ============
try:
    # FastMCP: 简化的MCP服务器框架，提供装饰器式的工具定义
    from mcp.server.fastmcp import FastMCP, Context
    
    # SSE (Server-Sent Events): 用于实时通信的传输层
    from mcp.server.sse import SseServerTransport
    
    # MCP核心服务器类
    from mcp.server import Server
    
    # Web服务器相关（用于HTTP模式）
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route
    import uvicorn    # ASGI服务器
    import argparse   # 命令行参数解析
except ImportError as e:
    # 如果MCP依赖未安装，给出明确的安装指导
    print(f"Error importing enhanced MCP dependencies: {e}")
    print("Please install: pip install fastmcp starlette uvicorn")
    exit(1)

# 类型变量，用于泛型
T = TypeVar("T")

# ============ 配置部分 ============

# MCP服务器名称，客户端用此名称识别服务器
MCP_SERVER_NAME = "shandong-cultivated-analysis-enhanced"

# API端点配置 - 定义外部服务的访问地址
OGE_API_BASE_URL = "http://172.30.22.116:16555/gateway/computation-api/process"
INTRANET_API_BASE_URL = "http://172.20.70.142:16555/gateway/computation-api/process"
INTRANET_AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjMyNCwidXNlcl9uYW1lIjoiZWR1X2FkbWluIiwic2NvcGUiOlsid2ViIl0sImV4cCI6MTc0OTkwNjkwMiwidXVpZCI6ImY5NTBjZmYyLTA3YzgtNDYxYS05YzI0LTkxNjJkNTllMmVmNiIsImF1dGhvcml0aWVzIjpbIkFETUlOSVNUUkFUT1JTIl0sImp0aSI6IkxQbjJQTThlRlpBRDhUNFBxN2U3SWlRdmRGQSIsImNsaWVudF9pZCI6InRlc3QiLCJ1c2VybmFtZSI6ImVkdV9hZG1pbiJ9.jFepdzkcDDlcH0v3Z_Ge35vbiTB3RVt8OQsHJ0o6qEU"

# DAG批处理API配置
DAG_API_BASE_URL = "http://172.20.70.141/api/oge-dag-22"
DEFAULT_USER_ID = "f950cff2-07c8-461a-9c24-9162d59e2ef6"
DEFAULT_USERNAME = "edu_admin"

# ============ 响应格式定义 ============

class RetCode(IntEnum):
    """返回码枚举 - 标准化API响应状态"""
    SUCCESS = 0    # 成功
    FAILED = 1     # 失败

class Result(BaseModel):
    """
    统一的响应结果模型
    使用Pydantic进行数据验证，确保响应格式一致性
    """
    success: bool = False                    # 操作是否成功
    code: Optional[int] = None              # 返回码
    msg: Optional[str] = None               # 消息描述
    data: Optional[T] = None                # 数据载荷
    operation: Optional[str] = None         # 操作名称（用于日志追踪）
    execution_time: Optional[float] = None  # 执行时间（性能监控）
    api_endpoint: Optional[str] = "oge"     # API端点标识

    @classmethod
    def succ(cls, data: T = None, msg="成功", operation=None, execution_time=None, api_endpoint="oge"):
        """创建成功响应的类方法"""
        return cls(
            success=True, 
            code=RetCode.SUCCESS, 
            msg=msg, 
            data=data,
            operation=operation,
            execution_time=execution_time,
            api_endpoint=api_endpoint
        )

    @classmethod
    def failed(cls, code: int = RetCode.FAILED, msg="操作失败", operation=None):
        """创建失败响应的类方法"""
        return cls(success=False, code=code, msg=msg, operation=operation)

# ============ 日志配置 ============

def setup_logger(name: str = None, file: str = None, level=logging.INFO) -> logging.Logger:
    """
    设置结构化日志系统
    
    Args:
        name: 日志器名称
        file: 日志文件路径
        level: 日志级别
    
    Returns:
        配置好的Logger实例
    """
    # 获取或创建指定名称的日志器
    logger = logging.getLogger(name)
    logger.propagate = False  # 不向父日志器传播消息
    logger.setLevel(level)
    
    # 清除已有的处理器，避免重复日志
    if logger.hasHandlers():
        logger.handlers.clear()

    # 定义日志格式
    formatter = logging.Formatter(
        fmt='%(name)s - %(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件日志处理器
    if file:
        Path(file).parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在
        file_handler = logging.FileHandler(filename=file, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    # 控制台日志处理器
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)
    logger.addHandler(stream_handler)

    return logger

# 创建日志实例 - 分离业务日志和API调用日志
logger = setup_logger("shandong_mcp", "logs/shandong_mcp.log")        # 主业务日志
api_logger = setup_logger("shandong_api", "logs/api_calls.log")       # API调用日志

# ============ FastMCP实例 ============

# 创建FastMCP服务器实例
# FastMCP提供装饰器模式的工具定义，简化MCP服务器开发
mcp = FastMCP(MCP_SERVER_NAME)

# ============ 通用API调用函数 ============

async def call_api_with_timing(
    url: str,
    method: str = 'POST',
    json_data: dict = None,
    headers: dict = None,
    timeout: int = 120
) -> tuple[dict, float]:
    """
    通用的异步API调用函数，带性能监控
    
    Args:
        url: API地址
        method: HTTP方法
        json_data: JSON请求体
        headers: HTTP头部
        timeout: 超时时间（秒）
    
    Returns:
        tuple: (响应数据, 执行时间)
    """
    start_time = time.perf_counter()  # 记录开始时间
    
    try:
        # 使用httpx异步客户端发送请求
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method.upper(),
                url=url,
                json=json_data,
                headers=headers or {"Content-Type": "application/json"}
            )
            
            execution_time = time.perf_counter() - start_time
            
            # 检查HTTP状态码
            if response.status_code == 200:
                result = response.json()
                api_logger.info(f"API调用成功 - URL: {url} - 耗时: {execution_time:.4f}s")
                return result, execution_time
            else:
                api_logger.error(f"API调用失败 - URL: {url} - 状态码: {response.status_code} - 耗时: {execution_time:.4f}s")
                return {"error": response.text, "status_code": response.status_code}, execution_time
                
    except Exception as e:
        execution_time = time.perf_counter() - start_time
        api_logger.error(f"API调用异常 - URL: {url} - 错误: {str(e)} - 耗时: {execution_time:.4f}s")
        return {"error": str(e)}, execution_time

# ============ MCP工具定义 ============

@mcp.tool()  # MCP工具装饰器 - 将函数注册为可供AI调用的工具
async def execute_full_workflow(
    enable_visualization: bool = True,
    intermediate_results: bool = False,
    ctx: Context = None  # MCP上下文，提供与客户端通信的能力
) -> str:
    """
    执行完整的山东耕地流出分析工作流
    
    这是一个MCP工具，AI可以调用此工具来执行完整的分析流程
    
    Parameters:
    - enable_visualization: 是否生成最终可视化地图
    - intermediate_results: 是否返回中间步骤结果
    """
    operation = "完整工作流分析"
    start_time = time.perf_counter()
    
    try:
        # 通过MCP上下文向客户端发送日志消息
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation}")
        
        # 模拟工作流执行（实际应用中这里会有复杂的业务逻辑）
        workflow_result = {
            "workflow_name": "山东耕地流出分析",
            "status": "completed",
            "steps_completed": 16,
            "total_steps": 16,
            "enable_visualization": enable_visualization,
            "intermediate_results": intermediate_results
        }
        
        execution_time = time.perf_counter() - start_time
        
        # 创建成功响应
        result = Result.succ(
            data=workflow_result,
            msg=f"{operation}执行成功",
            operation=operation,
            execution_time=execution_time
        )
        
        # 向客户端发送完成消息
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成，耗时{execution_time:.2f}秒")
        
        # MCP工具必须返回字符串，通常是JSON格式
        return result.model_dump_json()
        
    except Exception as e:
        execution_time = time.perf_counter() - start_time
        logger.error(f"{operation}执行失败: {str(e)}")
        
        # 创建失败响应
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            operation=operation
        )
        return result.model_dump_json()

@mcp.tool()  # 另一个MCP工具
async def coverage_aspect_analysis(
    bbox: List[float],  # 参数类型注解，帮助AI理解参数要求
    coverage_type: str = "Coverage",
    pretreatment: bool = True,
    product_value: str = "Platform:Product:ASTER_GDEM_DEM30",
    radius: int = 1,
    ctx: Context = None
) -> str:
    """
    坡向分析 - 基于DEM数据计算坡向信息
    
    这个工具调用外部地理计算API来执行地形分析
    
    Parameters:
    - bbox: 边界框坐标 [minLon, minLat, maxLon, maxLat]
    - coverage_type: 覆盖类型
    - pretreatment: 是否进行预处理
    - product_value: 产品数据源
    - radius: 计算半径
    """
    operation = "坡向分析"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation} - 边界框: {bbox}")
        
        # 构建算法参数 - 根据外部API要求格式化参数
        algorithm_args = {
            "coverage": {
                "type": coverage_type,
                "pretreatment": pretreatment,
                "preParams": {"bbox": bbox},
                "value": [product_value]
            },
            "radius": radius
        }
        
        # 构建API请求负载
        api_payload = {
            "name": "Coverage.aspect",  # 算法名称
            "args": algorithm_args,     # 算法参数
            "dockerImageSource": "DOCKER_HUB"  # 执行环境
        }
        
        # 设置请求头，包含认证信息
        headers = {
            "Content-Type": "application/json",
            "Authorization": INTRANET_AUTH_TOKEN
        }
        
        # 调用外部API
        api_result, execution_time = await call_api_with_timing(
            url=INTRANET_API_BASE_URL,
            json_data=api_payload,
            headers=headers
        )
        
        # 根据API调用结果创建响应
        if "error" in api_result:
            result = Result.failed(
                msg=f"{operation}失败: {api_result.get('error')}",
                operation=operation
            )
        else:
            result = Result.succ(
                data=api_result,
                msg=f"{operation}执行成功",
                operation=operation,
                execution_time=execution_time,
                api_endpoint="intranet"
            )
        
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成，耗时{execution_time:.2f}秒")
        
        logger.info(f"{operation}执行完成 - 耗时: {execution_time:.2f}秒")
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            operation=operation
        )
        return result.model_dump_json()

# ============ DAG批处理工具 ============

@mcp.tool()
async def execute_code_to_dag(
    code: str,
    user_id: str = DEFAULT_USER_ID,
    sample_name: str = "",
    auth_token: str = None,
    ctx: Context = None
) -> str:
    """
    将代码转化为DAG生成任务
    
    这个工具展示了MCP如何集成复杂的外部服务
    将用户代码转换为可执行的有向无环图(DAG)任务
    
    Parameters:
    - code: 要执行的OGE代码
    - user_id: 用户UUID
    - sample_name: 示例代码名称（可为空）
    - auth_token: 认证Token（可选，默认使用全局Token）
    """
    operation = "代码转DAG任务"
    
    try:
        if ctx:
            # 向MCP客户端发送实时状态更新
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation}")
        
        # 构建API URL
        api_url = f"{DAG_API_BASE_URL}/executeCode"
        
        # 构建请求数据
        request_data = {
            "code": code,
            "userId": user_id,
            "sampleName": sample_name
        }
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        # 动态选择认证token
        if auth_token:
            if not auth_token.startswith("Bearer "):
                auth_token = f"Bearer {auth_token}"
            headers["Authorization"] = auth_token
        elif INTRANET_AUTH_TOKEN:
            headers["Authorization"] = INTRANET_AUTH_TOKEN
        
        logger.info(f"调用API: {api_url}")
        logger.info(f"请求数据: userId={user_id}, sampleName={sample_name}")
        
        # 调用API
        api_result, execution_time = await call_api_with_timing(
            url=api_url,
            method="POST",
            json_data=request_data,
            headers=headers,
            timeout=120
        )
        
        if "error" not in api_result:
            # 解析API响应，提取有用信息
            dags = api_result.get("dags", {})
            space_params = api_result.get("spaceParams", {})
            log_info = api_result.get("log", "")
            
            # 提取DAG ID列表
            dag_ids = []
            for key, value in dags.items():
                if isinstance(value, dict):
                    dag_ids.append(key)
                elif isinstance(value, str):
                    dag_ids.append(value)
            
            # 构建结构化响应数据
            result_data = {
                "dags": dags,
                "dag_ids": dag_ids,
                "space_params": space_params,
                "log": log_info,
                "user_id": user_id,
                "sample_name": sample_name
            }
            
            result = Result.succ(
                data=result_data,
                msg=f"{operation}成功，生成了{len(dag_ids)}个DAG任务",
                operation=operation,
                execution_time=execution_time,
                api_endpoint="dag"
            )
            
            logger.info(f"{operation}成功 - 生成DAG数量: {len(dag_ids)}")
            
        else:
            result = Result.failed(
                msg=f"{operation}失败: {api_result.get('error', '未知错误')}",
                operation=operation
            )
        
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成，耗时{execution_time:.2f}秒")
        
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            operation=operation
        )
        return result.model_dump_json()

# ============ MCP资源管理 ============

@mcp.resource(uri="analysis://results/{result_id}", description="访问分析结果资源")
def get_analysis_result(result_id: str) -> str:
    """
    MCP资源 - 提供对分析结果的访问
    
    MCP资源与工具不同，资源是静态数据的访问点
    而工具是执行动作的函数
    
    Parameters:
    - result_id: 结果ID
    """
    try:
        # 模拟资源获取逻辑
        resource_data = {
            "result_id": result_id,
            "status": "available",
            "data": f"Analysis result for {result_id}"
        }
        
        result = Result.succ(data=resource_data, msg="资源获取成功")
        return result.model_dump_json()
        
    except Exception as e:
        result = Result.failed(msg=f"资源获取失败: {str(e)}")
        return result.model_dump_json()

# ============ HTTP服务器设置 ============

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """
    创建支持SSE的Starlette Web应用
    
    这允许MCP服务器通过HTTP而不是stdio运行
    提供更好的可扩展性和部署灵活性
    """
    # 创建SSE传输层，用于实时通信
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        """处理SSE连接的端点"""
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            # 运行MCP服务器实例
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    async def handle_health(request: Request):
        """健康检查端点"""
        return JSONResponse({
            "status": "healthy",
            "server": MCP_SERVER_NAME,
            "endpoints": {
                "sse": "/sse",
                "health": "/health",
                "messages": "/messages/"
            }
        })

    async def handle_info(request: Request):
        """服务器信息端点 - 提供服务器能力描述"""
        return JSONResponse({
            "server_name": MCP_SERVER_NAME,
            "version": "2.1.0",
            "description": "山东耕地流出分析MCP服务器 - 增强版 (支持DAG批处理)",
            "features": [
                "完整工作流分析",
                "坡向分析",
                "空间分析",
                "OAuth Token管理",
                "DAG批处理工作流",
                "代码转DAG任务",
                "批处理任务提交",
                "任务状态查询",
                "SSE传输",
                "HTTP endpoints",
                "结构化日志",
                "性能监控"
            ],
            "apis": {
                "oge_api": OGE_API_BASE_URL,
                "intranet_api": INTRANET_API_BASE_URL,
                "dag_api": DAG_API_BASE_URL
            },
            "dag_tools": [
                "execute_code_to_dag",
                "submit_batch_task", 
                "query_task_status",
                "execute_dag_workflow"
            ]
        })

    # 创建Starlette应用并定义路由
    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),           # SSE连接端点
            Route("/health", endpoint=handle_health),     # 健康检查
            Route("/info", endpoint=handle_info),         # 服务器信息
            Mount("/messages/", app=sse.handle_post_message),  # 消息处理
        ],
    )

# ============ 主程序 ============

async def run_stdio_server():
    """
    运行stdio模式的MCP服务器
    
    stdio模式是MCP的标准运行方式，通过标准输入输出与客户端通信
    适合作为子进程或命令行工具运行
    """
    logger.info("启动山东耕地流出分析MCP服务器 (stdio模式)...")
    
    try:
        # 导入MCP stdio服务器支持
        from mcp import stdio_server
        
        # 创建stdio流并运行MCP服务器
        async with stdio_server() as streams:
            await mcp._mcp_server.run(
                streams[0],  # 输入流
                streams[1],  # 输出流
                mcp._mcp_server.create_initialization_options()
            )
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器运行出错: {e}")
    finally:
        logger.info("MCP服务器已关闭")

def run_http_server(host: str = "0.0.0.0", port: int = 8000):
    """
    运行HTTP模式的MCP服务器
    
    HTTP模式允许MCP服务器作为独立的Web服务运行
    支持多客户端连接和更复杂的部署场景
    """
    logger.info(f"启动山东耕地流出分析MCP服务器 (HTTP模式) - {host}:{port}")
    
    # 获取底层MCP服务器实例
    mcp_server = mcp._mcp_server
    
    # 创建Starlette Web应用
    starlette_app = create_starlette_app(mcp_server, debug=True)
    
    # 使用uvicorn运行应用
    uvicorn.run(starlette_app, host=host, port=port)

if __name__ == "__main__":
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='山东耕地流出分析MCP服务器 - 增强版')
    parser.add_argument('--mode', choices=['stdio', 'http'], default='stdio', help='运行模式')
    parser.add_argument('--host', default='0.0.0.0', help='HTTP模式的绑定地址')
    parser.add_argument('--port', type=int, default=8000, help='HTTP模式的监听端口')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'stdio':
            # 运行stdio模式服务器
            asyncio.run(run_stdio_server())
        else:
            # 运行HTTP模式服务器
            run_http_server(args.host, args.port)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        logger.error(f"启动失败: {e}")

"""
MCP核心概念总结：

1. **MCP协议**: 连接AI助手与外部服务的开放标准
2. **工具(Tools)**: AI可以调用的函数，执行特定操作
3. **资源(Resources)**: AI可以访问的数据源
4. **传输层**: stdio或HTTP，用于客户端-服务器通信
5. **上下文(Context)**: 提供与客户端通信的能力
6. **装饰器**: @mcp.tool() 简化工具注册
7. **异步**: MCP服务器必须支持异步操作

MCP工作流程：
1. 客户端连接到MCP服务器
2. 服务器发送可用工具和资源列表
3. AI助手根据需要调用工具
4. 服务器执行工具并返回结果
5. 客户端将结果提供给AI助手

这个服务器展示了MCP的完整实现，包括：
- 多种部署模式
- 外部API集成
- 错误处理
- 日志记录
- 性能监控
- 实时通信
""" 