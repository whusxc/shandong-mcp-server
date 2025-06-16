#!/usr/bin/env python3
"""
山东耕地流出分析 MCP服务器 - 增强版
整合FastMCP框架，支持HTTP和stdio两种传输方式
"""

import asyncio
import json
import logging
import httpx
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar
from pydantic import BaseModel
from enum import IntEnum

# MCP SDK 导入
try:
    from mcp.server.fastmcp import FastMCP, Context
    from mcp.server.sse import SseServerTransport
    from mcp.server import Server
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route
    import uvicorn
    import argparse
except ImportError as e:
    print(f"Error importing enhanced MCP dependencies: {e}")
    print("Please install: pip install fastmcp starlette uvicorn")
    exit(1)

T = TypeVar("T")

# ============ 配置部分 ============

# 服务器配置
MCP_SERVER_NAME = "shandong-cultivated-analysis-enhanced"

# API配置
OGE_API_BASE_URL = "http://172.30.22.116:16555/gateway/computation-api/process"
INTRANET_API_BASE_URL = "http://172.20.70.142:16555/gateway/computation-api/process"
INTRANET_AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjMyNCwidXNlcl9uYW1lIjoiZWR1X2FkbWluIiwic2NvcGUiOlsid2ViIl0sImV4cCI6MTc1MDAwMzQ1NiwidXVpZCI6ImY5NTBjZmYyLTA3YzgtNDYxYS05YzI0LTkxNjJkNTllMmVmNiIsImF1dGhvcml0aWVzIjpbIkFETUlOSVNUUkFUT1JTIl0sImp0aSI6IkhrbG9YdDhiMTFmMDJXTFRON3pXc0FkVlk3TSIsImNsaWVudF9pZCI6InRlc3QiLCJ1c2VybmFtZSI6ImVkdV9hZG1pbiJ9.RAaOX2Bzqn0ys8ZpzlsYaVY6RQuYMNwzYXWcJ_9KD8U"

# DAG批处理API配置
DAG_API_BASE_URL = "http://172.20.70.141/api/oge-dag-22"
DEFAULT_USER_ID = "f950cff2-07c8-461a-9c24-9162d59e2ef6"
DEFAULT_USERNAME = "edu_admin"

# ============ 响应格式定义 ============

class RetCode(IntEnum):
    SUCCESS = 0
    FAILED = 1

class Result(BaseModel):
    success: bool = False
    code: Optional[int] = None
    msg: Optional[str] = None
    data: Optional[T] = None
    operation: Optional[str] = None
    execution_time: Optional[float] = None
    api_endpoint: Optional[str] = "oge"

    @classmethod
    def succ(cls, data: T = None, msg="成功", operation=None, execution_time=None, api_endpoint="oge"):
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
        return cls(success=False, code=code, msg=msg, operation=operation)

# ============ 日志配置 ============

def setup_logger(name: str = None, file: str = None, level=logging.INFO) -> logging.Logger:
    """设置结构化日志"""
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(level)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt='%(name)s - %(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件日志
    if file:
        Path(file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(filename=file, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    # 控制台日志
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)
    logger.addHandler(stream_handler)

    return logger

# 创建日志实例
logger = setup_logger("shandong_mcp", "logs/shandong_mcp.log")
api_logger = setup_logger("shandong_api", "logs/api_calls.log")

# ============ FastMCP实例 ============

mcp = FastMCP(MCP_SERVER_NAME)

# ============ Token管理 ============

async def refresh_intranet_token() -> tuple[bool, str]:
    """自动刷新内网token"""
    global INTRANET_AUTH_TOKEN
    
    try:
        logger.info("开始刷新内网token...")
        
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
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params, json=body, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and 'token' in data['data']:
                    token = data['data']['token']
                    token_head = data['data'].get('tokenHead', 'Bearer').rstrip()  # 去掉尾部空格
                    full_token = f"{token_head} {token}"
                    
                    # 更新全局token
                    INTRANET_AUTH_TOKEN = full_token
                    
                    logger.info(f"Token刷新成功: {full_token[:50]}...")
                    logger.info(f"Token格式检查 - head: '{token_head}', length: {len(full_token)}")
                    return True, full_token
                else:
                    logger.error(f"Token响应格式异常: {data}")
                    return False, f"Token响应格式异常: {data}"
            else:
                error_msg = f"Token获取失败 - 状态码: {response.status_code} - 响应: {response.text}"
                logger.error(error_msg)
                return False, error_msg
                
    except Exception as e:
        error_msg = f"Token刷新异常: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

# ============ 通用API调用函数 ============

async def call_api_with_timing(
    url: str,
    method: str = 'POST',
    json_data: dict = None,
    headers: dict = None,
    timeout: int = 120,
    auto_retry_on_token_expire: bool = True,
    use_intranet_token: bool = False
) -> tuple[dict, float]:
    """通用API调用，带性能监控和自动token刷新"""
    global INTRANET_AUTH_TOKEN
    start_time = time.perf_counter()
    
    # 如果指定使用内网token，则动态更新headers
    if use_intranet_token:
        if headers is None:
            headers = {"Content-Type": "application/json"}
        headers["Authorization"] = INTRANET_AUTH_TOKEN
        logger.info(f"使用内网token: {INTRANET_AUTH_TOKEN[:50]}...")
        logger.info(f"实际发送headers: {dict((k, v[:50] + '...' if k == 'Authorization' and len(v) > 50 else v) for k, v in headers.items())}")
    
    # 检查是否需要自动重试
    should_auto_retry = (
        use_intranet_token and 
        auto_retry_on_token_expire
    )
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 处理GET请求的参数
            if method.upper() == "GET" and headers and "params" in headers:
                params = headers.pop("params")
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    headers=headers or {"Content-Type": "application/json"}
                )
            else:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    json=json_data,
                    headers=headers or {"Content-Type": "application/json"}
                )
            
            execution_time = time.perf_counter() - start_time
            
            if response.status_code == 200:
                # 安全处理JSON解析
                response_text = response.text.strip()
                try:
                    result = response.json()
                except Exception as json_error:
                    # 如果JSON解析失败，返回原始文本作为结果
                    logger.info(f"响应不是JSON格式，作为纯文本处理: {response_text[:100]}...")
                    # 对于DAG状态查询，直接返回文本状态
                    if "/getState" in url:
                        result = response_text if response_text else "unknown"
                    else:
                        result = {
                            "raw_text": response_text,
                            "json_parse_error": str(json_error),
                            "content_type": response.headers.get("content-type", "unknown")
                        }
                
                # 检查是否为token过期错误
                if (should_auto_retry and 
                    isinstance(result, dict) and 
                    result.get("code") == 40003):
                    
                    logger.warning("检测到token过期(40003)，尝试自动刷新...")
                    
                    # 刷新token
                    success, new_token = await refresh_intranet_token()
                    
                    if success:
                        logger.info("Token刷新成功，重新调用API...")
                        
                        # 确保使用新token重新构建headers
                        new_headers = None
                        if use_intranet_token:
                            new_headers = {
                                "Content-Type": "application/json",
                                "Authorization": new_token
                            }
                        
                        # 重新调用API（递归，但禁用自动重试避免无限循环）
                        return await call_api_with_timing(
                            url=url,
                            method=method,
                            json_data=json_data,
                            headers=new_headers,
                            timeout=timeout,
                            auto_retry_on_token_expire=False,  # 禁用重试避免循环
                            use_intranet_token=False  # 已经手动设置headers了，不需要再次设置
                        )
                    else:
                        logger.error(f"Token刷新失败: {new_token}")
                        api_logger.error(f"API调用失败(token刷新失败) - URL: {url}")
                        return {"error": f"Token过期且刷新失败: {new_token}", "code": 40003}, execution_time
                
                api_logger.info(f"API调用成功 - URL: {url} - 耗时: {execution_time:.4f}s")
                return result, execution_time
            elif response.status_code == 401 and should_auto_retry:
                # 处理HTTP 401状态码（认证失败）
                logger.warning("检测到401状态码，尝试自动刷新token...")
                
                # 刷新token
                success, new_token = await refresh_intranet_token()
                
                if success:
                    logger.info("Token刷新成功，重新调用API...")
                    
                    # 确保使用新token重新构建headers
                    new_headers = None
                    if use_intranet_token:
                        new_headers = {
                            "Content-Type": "application/json",
                            "Authorization": new_token
                        }
                    
                    # 重新调用API（递归，但禁用自动重试避免无限循环）
                    return await call_api_with_timing(
                        url=url,
                        method=method,
                        json_data=json_data,
                        headers=new_headers,
                        timeout=timeout,
                        auto_retry_on_token_expire=False,  # 禁用重试避免循环
                        use_intranet_token=False  # 已经手动设置headers了，不需要再次设置
                    )
                else:
                    logger.error(f"Token刷新失败: {new_token}")
                    api_logger.error(f"API调用失败(token刷新失败) - URL: {url}")
                    return {"error": f"401认证失败且token刷新失败: {new_token}", "status_code": 401}, execution_time
            else:
                error_detail = f"API调用失败 - URL: {url} - 状态码: {response.status_code} - 耗时: {execution_time:.4f}s"
                if response.status_code == 401:
                    current_token_preview = INTRANET_AUTH_TOKEN[:30] + "..." if INTRANET_AUTH_TOKEN else "None"
                    error_detail += f" - 当前token预览: {current_token_preview}"
                api_logger.error(error_detail)
                return {"error": response.text, "status_code": response.status_code}, execution_time
                
    except Exception as e:
        execution_time = time.perf_counter() - start_time
        api_logger.error(f"API调用异常 - URL: {url} - 错误: {str(e)} - 耗时: {execution_time:.4f}s")
        return {"error": str(e)}, execution_time

# ============ 工具定义 ============

@mcp.tool()
async def refresh_token(ctx: Context = None) -> str:
    """
    手动刷新内网认证Token
    
    当遇到token过期错误(40003)时，可以使用此工具手动刷新token
    """
    operation = "刷新Token"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"手动执行{operation}")
        
        success, token_or_error = await refresh_intranet_token()
        
        if success:
            result = Result.succ(
                data={
                    "new_token": token_or_error[:50] + "...",  # 只显示前50个字符
                    "token_length": len(token_or_error),
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                msg=f"{operation}成功",
                operation=operation,
                api_endpoint="auth"
            )
            
            if ctx:
                await ctx.session.send_log_message("info", f"{operation}成功，新token已更新")
        else:
            result = Result.failed(
                msg=f"{operation}失败: {token_or_error}",
                operation=operation
            )
            
            if ctx:
                await ctx.session.send_log_message("error", f"{operation}失败: {token_or_error}")
        
        logger.info(f"{operation}执行完成 - 成功: {success}")
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            operation=operation
        )
        return result.model_dump_json()

@mcp.tool()
async def check_token_status(ctx: Context = None) -> str:
    """
    检查当前内网认证Token状态
    
    用于调试token问题，显示当前token的信息
    """
    global INTRANET_AUTH_TOKEN
    operation = "检查Token状态"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation}")
        
        if INTRANET_AUTH_TOKEN:
            # 尝试解析JWT token的有效期（如果是JWT格式）
            token_info = {
                "has_token": True,
                "token_preview": INTRANET_AUTH_TOKEN[:50] + "...",
                "token_length": len(INTRANET_AUTH_TOKEN),
                "starts_with_bearer": INTRANET_AUTH_TOKEN.startswith("Bearer "),
                "has_double_space": "Bearer  " in INTRANET_AUTH_TOKEN,  # 检测双空格问题
                "current_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "bearer_prefix_length": len(INTRANET_AUTH_TOKEN.split(' ')[0]) if ' ' in INTRANET_AUTH_TOKEN else 0
            }
            
            # 如果是JWT token，尝试解析过期时间
            if "Bearer " in INTRANET_AUTH_TOKEN:
                jwt_part = INTRANET_AUTH_TOKEN.replace("Bearer ", "")
                try:
                    import base64
                    import json
                    # 简单解析JWT payload（不验证签名）
                    parts = jwt_part.split('.')
                    if len(parts) >= 2:
                        # 添加padding如果需要
                        payload = parts[1]
                        payload += '=' * (4 - len(payload) % 4)
                        decoded = base64.b64decode(payload)
                        payload_data = json.loads(decoded)
                        
                        if 'exp' in payload_data:
                            exp_time = payload_data['exp']
                            exp_readable = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(exp_time))
                            token_info["expires_at"] = exp_readable
                            token_info["expires_timestamp"] = exp_time
                            token_info["is_expired"] = time.time() > exp_time
                        
                        if 'user_name' in payload_data:
                            token_info["username"] = payload_data['user_name']
                            
                except Exception as e:
                    token_info["parse_error"] = str(e)
            
            result = Result.succ(
                data=token_info,
                msg=f"{operation}成功",
                operation=operation,
                api_endpoint="debug"
            )
        else:
            result = Result.failed(
                msg=f"{operation}: 当前没有token",
                operation=operation
            )
        
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成")
        
        logger.info(f"{operation}执行完成")
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            operation=operation
        )
        return result.model_dump_json()

@mcp.tool()
async def coverage_aspect_analysis(
    bbox: List[float],
    coverage_type: str = "Coverage",
    pretreatment: bool = True,
    product_value: str = "Platform:Product:ASTER_GDEM_DEM30",
    radius: int = 1,
    ctx: Context = None
) -> str:
    """
    坡向分析 - 基于DEM数据计算坡向信息
    
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
        
        # 构建算法参数
        algorithm_args = {
            "coverage": {
                "type": coverage_type,
                "pretreatment": pretreatment,
                "preParams": {"bbox": bbox},
                "value": [product_value]
            },
            "radius": radius
        }
        
        # 调用内网API
        api_payload = {
            "name": "Coverage.aspect",
            "args": algorithm_args,
            "dockerImageSource": "DOCKER_HUB"
        }
        
        api_result, execution_time = await call_api_with_timing(
            url=INTRANET_API_BASE_URL,
            json_data=api_payload,
            use_intranet_token=True
        )
        
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

# spatial_intersection 工具已删除

# coverage_slope_analysis 工具已删除

# terrain_analysis_suite 工具已删除

# get_oauth_token 和 refresh_intranet_token 工具已删除

@mcp.tool()
async def shandong_farmland_outflow(
    region_id: str = "ASTGTM_N28E056",
    product_id: str = "ASTER_GDEM_DEM30", 
    center_lon: float = 56.25,
    center_lat: float = 28.40,
    zoom_level: int = 11,
    wait_for_completion: bool = False,  # 默认立即返回，避免超时
    ctx: Context = None
) -> str:
    """
    山东耕地流出分析 - 基于DEM数据进行坡向分析和可视化
    
    执行完整的耕地流出分析工作流，包括数据获取、坡向计算、可视化和导出
    
    工作流程：
    1. 提交任务（立即返回DAG ID）
    2. 使用返回的DAG ID调用 query_task_status 查询进度
    3. 重复查询直到任务完成
    
    Parameters:
    - region_id: DEM数据区域ID (默认: ASTGTM_N28E056)
    - product_id: 产品数据源ID (默认: ASTER_GDEM_DEM30)
    - center_lon: 地图中心经度 (默认: 56.25)
    - center_lat: 地图中心纬度 (默认: 28.40)
    - zoom_level: 地图缩放级别 (默认: 11)
    - wait_for_completion: 是否等待任务完成 (默认: False，立即返回避免超时)
    
    返回信息包含：
    - 任务状态和DAG ID
    - 下一步操作指引
    - 查询状态的具体参数
    """
    operation = "山东耕地流出分析"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation} - 区域: {region_id}, 产品: {product_id}")
        
        # 构建OGE代码
        oge_code = f"""import oge

oge.initialize()
service = oge.Service()

dem = service.getCoverage(coverageID="{region_id}", productID="{product_id}")
aspect = service.getProcess("Coverage.aspect").execute(dem, 1)

vis_params = {{"min": -1, "max": 1, "palette": ["#808080", "#949494", "#a9a9a9", "#bdbebd", "#d3d3d3","#e9e9e9"]}}
aspect.styles(vis_params).export("aspect")
oge.mapclient.centerMap({center_lon}, {center_lat}, {zoom_level})"""
        
        logger.info(f"生成的OGE代码长度: {len(oge_code)} 字符")
        
        # 调用execute_dag_workflow执行完整工作流
        workflow_result = await execute_dag_workflow(
            code=oge_code,
            task_name="shandong_farmland_outflow_analysis",
            filename="shandong_aspect_analysis",
            auto_submit=True,
            wait_for_completion=wait_for_completion,
            check_interval=10,          # 每10秒轮询一次
            max_wait_time=1800,         # 30分钟超时
            ctx=ctx
        )
        
        # 解析workflow结果
        import json
        workflow_data = json.loads(workflow_result)
        
        if workflow_data.get("success"):
            # 提取关键信息
            workflow_details = workflow_data.get("data", {})
            final_status = workflow_details.get("final_status", "unknown")
            
            result_data = {
                "region_id": region_id,
                "product_id": product_id,
                "analysis_type": "aspect_analysis",
                "map_center": {"lon": center_lon, "lat": center_lat, "zoom": zoom_level},
                "workflow_status": final_status,
                "execution_steps": workflow_details.get("steps", []),
                "execution_times": workflow_details.get("execution_times", {}),
                "dag_info": {
                    "dag_ids": workflow_details.get("dag_ids", []),
                    "primary_dag_id": workflow_details.get("dag_ids", ["unknown"])[0],
                    "task_name": "shandong_farmland_outflow_analysis"
                },
                "next_action": {
                    "tool_name": "query_task_status",
                    "parameters": {
                        "dag_id": workflow_details.get("dag_ids", ["unknown"])[0]
                    },
                    "description": "查询任务执行状态"
                } if final_status == "submitted" else None
            }
            
            if final_status == "completed":
                msg = f"{operation}执行成功 - DEM坡向分析已完成并可视化"
            elif final_status == "submitted":
                primary_dag_id = workflow_details.get("dag_ids", ["unknown"])[0]
                msg = f"{operation}任务已提交 - DAG ID: {primary_dag_id}\n" + \
                      f"💡 请使用以下命令查询进度：\n" + \
                      f"query_task_status(dag_id=\"{primary_dag_id}\")"
            else:
                msg = f"{operation}执行完成 - 状态: {final_status}"
            
            result = Result.succ(
                data=result_data,
                msg=msg,
                operation=operation,
                api_endpoint="dag_workflow"
            )
        else:
            # 工作流执行失败
            error_msg = workflow_data.get("msg", "工作流执行失败")
            result = Result.failed(
                msg=f"{operation}失败: {error_msg}",
                operation=operation
            )
            result.data = workflow_data.get("data")
        
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成")
        
        logger.info(f"{operation}执行完成 - 最终状态: {final_status}")
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            operation=operation
        )
        return result.model_dump_json()


@mcp.tool()
async def run_big_query(
    # query: str,
    # geometry_column: str = "geom",
    ctx: Context = None
) -> str:
    """
    查询山东省耕地矢量,只会返回数据的标识，通过标识后续可以访问结果数据
    
    Parameters:
        无参数
    """
    operation = "大数据查询"
    query = "SELECT * FROM shp_guotubiangeng WHERE DLMC IN ('旱地', '水浇地', '水田')"
    geometry_column = "geom"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation} - 查询: {query[:100]}...")
        
        # 构建算法参数
        algorithm_args = {
            "query": query,
            "geometryColumn": geometry_column
        }
        
        # 调用内网API
        api_payload = {
            "name": "FeatureCollection.runBigQuery",
            "args": algorithm_args,
            "dockerImageSource": "DOCKER_HUB"
        }
        
        api_result, execution_time = await call_api_with_timing(
            url=INTRANET_API_BASE_URL,
            json_data=api_payload,
            use_intranet_token=True
        )
        
        if "error" in api_result:
            error_detail = api_result.get('error', '未知错误')
            status_code = api_result.get('status_code', '未知状态码')
            result = Result.failed(
                msg=f"{operation}失败: {error_detail} (状态码: {status_code})",
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
    
    Parameters:
    - code: 要执行的OGE代码
    - user_id: 用户UUID
    - sample_name: 示例代码名称（可为空）
    - auth_token: 认证Token（可选，默认使用全局Token）
    """
    operation = "代码转DAG任务"
    
    try:
        if ctx:
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
        
        # 准备认证
        use_custom_token = bool(auth_token)
        final_headers = None
        
        if use_custom_token:
            if not auth_token.startswith("Bearer "):
                auth_token = f"Bearer {auth_token}"
            final_headers = {
                "Content-Type": "application/json",
                "Authorization": auth_token
            }
        
        logger.info(f"调用API: {api_url}")
        logger.info(f"请求数据: userId={user_id}, sampleName={sample_name}")
        
        # 调用API
        api_result, execution_time = await call_api_with_timing(
            url=api_url,
            method="POST",
            json_data=request_data,
            headers=final_headers,
            timeout=300,     # 5分钟超时，DAG创建可能需要更长时间
            use_intranet_token=not use_custom_token
        )
        
        if "error" not in api_result:
            # 提取DAG信息
            dags = api_result.get("dags", {})
            space_params = api_result.get("spaceParams", {})
            log_info = api_result.get("log", "")
            
            # 提取DAG ID
            dag_ids = []
            for key, value in dags.items():
                if isinstance(value, dict):
                    dag_ids.append(key)
                elif isinstance(value, str):
                    dag_ids.append(value)
            
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

@mcp.tool()
async def submit_batch_task(
    dag_id: str,
    task_name: str = None,
    filename: str = None,
    crs: str = "EPSG:4326",
    scale: str = "1000",
    format: str = "tif",
    username: str = DEFAULT_USERNAME,
    script: str = "",
    auth_token: str = None,
    ctx: Context = None
) -> str:
    """
    提交批处理任务运行
    
    Parameters:
    - dag_id: DAG任务ID
    - task_name: 任务名称（可选，默认自动生成）
    - filename: 文件名（可选，默认自动生成）
    - crs: 坐标参考系统
    - scale: 比例尺
    - format: 输出格式
    - username: 用户名
    - script: 脚本代码
    - auth_token: 认证Token（可选，默认使用全局Token）
    """
    operation = "提交批处理任务"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation} - DAG ID: {dag_id}")
        
        # 构建API URL
        api_url = f"{DAG_API_BASE_URL}/addTaskRecord"
        
        # 生成默认任务名和文件名（如果未提供）
        if not task_name:
            timestamp = time.strftime("%Y_%m_%d_%H_%M_%S")
            task_name = f"task_{timestamp}"
            
        if not filename:
            timestamp = time.strftime("%Y_%m_%d_%H_%M_%S")
            filename = f"file_{timestamp}"
        
        # 构建请求数据
        request_data = {
            "taskName": task_name,
            "crs": crs,
            "scale": scale,
            "filename": filename,
            "format": format,
            "id": dag_id,
            "userName": username,
            "script": script
        }
        
        # 准备认证
        use_custom_token = bool(auth_token)
        final_headers = None
        
        if use_custom_token:
            if not auth_token.startswith("Bearer "):
                auth_token = f"Bearer {auth_token}"
            final_headers = {
                "Content-Type": "application/json",
                "Authorization": auth_token
            }
        
        logger.info(f"调用API: {api_url}")
        logger.info(f"请求数据: taskName={task_name}, dagId={dag_id}")
        
        # 调用API
        api_result, execution_time = await call_api_with_timing(
            url=api_url,
            method="POST",
            json_data=request_data,
            headers=final_headers,
            timeout=300,     # 5分钟超时，任务提交可能需要更长时间
            use_intranet_token=not use_custom_token
        )
        
        if "error" not in api_result:
            # 检查API响应格式
            if api_result.get("code") == 200:
                task_data = api_result.get("data", {})
                
                result_data = {
                    "batch_session_id": task_data.get("batchSessionId"),
                    "task_id": task_data.get("id"),
                    "dag_id": task_data.get("dagId"),
                    "task_name": task_data.get("taskName"),
                    "state": task_data.get("state"),
                    "filename": task_data.get("filename"),
                    "format": task_data.get("format"),
                    "scale": task_data.get("scale"),
                    "crs": task_data.get("crs"),
                    "user_id": task_data.get("userId"),
                    "username": task_data.get("userName"),
                    "folder": task_data.get("folder"),
                    "api_response": api_result
                }
                
                result = Result.succ(
                    data=result_data,
                    msg=f"{operation}成功，任务状态: {task_data.get('state', 'unknown')}",
                    operation=operation,
                    execution_time=execution_time,
                    api_endpoint="dag"
                )
                
                logger.info(f"{operation}成功 - 任务ID: {task_data.get('id')}, 状态: {task_data.get('state')}")
                
            else:
                result = Result.failed(
                    msg=f"{operation}失败: {api_result.get('msg', '未知错误')}",
                    operation=operation
                )
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

@mcp.tool()
async def query_task_status(
    dag_id: str,
    auth_token: str = None,
    ctx: Context = None
) -> str:
    """
    查询批处理任务执行状态
    
    Parameters:
    - dag_id: DAG任务ID
    - auth_token: 认证Token（可选，默认使用全局Token）
    """
    operation = "查询任务状态"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation} - DAG ID: {dag_id}")
        
        # 构建API URL
        api_url = f"{DAG_API_BASE_URL}/getState"
        
        # 准备认证
        use_custom_token = bool(auth_token)
        final_headers = None
        
        if use_custom_token:
            if not auth_token.startswith("Bearer "):
                auth_token = f"Bearer {auth_token}"
            final_headers = {
                "Content-Type": "application/json",
                "Authorization": auth_token
            }
        
        # 构建查询参数
        params = {"dagId": dag_id}
        
        logger.info(f"调用API: {api_url}?dagId={dag_id}")
        
        # 调用API - 需要特殊处理GET请求
        if use_custom_token:
            # 使用自定义token
            start_time = time.perf_counter()
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    api_url,
                    params=params,
                    headers=final_headers
                )
                
                execution_time = time.perf_counter() - start_time
                
                if response.status_code == 200:
                    # API返回的可能是简单的字符串状态
                    response_text = response.text.strip()
                    
                    if not response_text:
                        # 空响应，可能表示任务不存在或查询出错
                        status_data = "unknown"
                    else:
                        try:
                            status_data = response.json()
                        except:
                            # 如果不是JSON，则是纯文本状态
                            status_data = response_text
                    
                    # 确保status_data是字符串形式
                    if isinstance(status_data, dict):
                        status_str = status_data.get("status", str(status_data))
                    else:
                        status_str = str(status_data)
                    
                    result_data = {
                        "dag_id": dag_id,
                        "status": status_str,
                        "is_completed": status_str in ["success", "completed"],
                        "is_running": status_str in ["running", "starting"],
                        "is_failed": status_str in ["failed", "error"],
                        "raw_response": status_data,
                        "response_length": len(response_text)
                    }
                    
                    result = Result.succ(
                        data=result_data,
                        msg=f"{operation}成功，当前状态: {status_data}",
                        operation=operation,
                        execution_time=execution_time,
                        api_endpoint="dag"
                    )
                    
                    logger.info(f"{operation}成功 - DAG ID: {dag_id}, 状态: {status_data}")
                    
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    result = Result.failed(
                        msg=f"{operation}失败: {error_msg}",
                        operation=operation
                    )
                    logger.error(f"{operation}失败 - {error_msg}")
        else:
            # 使用内网token - 转换为POST请求以支持token刷新
            get_params = {"dagId": dag_id}
            
            api_result, execution_time = await call_api_with_timing(
                url=api_url,
                method="GET",
                headers={"params": get_params},  # 传递GET参数
                timeout=30,
                use_intranet_token=True
            )
            
            if "error" not in api_result:
                status_data = api_result
                if isinstance(status_data, dict):
                    status_data = status_data.get("status", "unknown")
                
                result_data = {
                    "dag_id": dag_id,
                    "status": status_data,
                    "is_completed": status_data in ["success", "completed"],
                    "is_running": status_data in ["running", "starting"],
                    "is_failed": status_data in ["failed", "error"],
                    "raw_response": status_data
                }
                
                result = Result.succ(
                    data=result_data,
                    msg=f"{operation}成功，当前状态: {status_data}",
                    operation=operation,
                    execution_time=execution_time,
                    api_endpoint="dag"
                )
                
                logger.info(f"{operation}成功 - DAG ID: {dag_id}, 状态: {status_data}")
                
            else:
                result = Result.failed(
                    msg=f"{operation}失败: {api_result.get('error')}",
                    operation=operation
                )
                logger.error(f"{operation}失败 - {api_result.get('error')}")
        
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

@mcp.tool()
async def execute_dag_workflow(
    code: str,
    user_id: str = DEFAULT_USER_ID,
    sample_name: str = "",
    task_name: str = None,
    filename: str = None,
    crs: str = "EPSG:4326",
    scale: str = "1000",
    format: str = "tif",
    username: str = DEFAULT_USERNAME,
    auth_token: str = None,
    auto_submit: bool = True,
    wait_for_completion: bool = False,
    check_interval: int = 15,     # 默认15秒检查一次
    max_wait_time: int = 1800,    # 默认30分钟超时
    ctx: Context = None
) -> str:
    """
    执行完整的DAG批处理工作流：代码转DAG -> 提交任务 -> (可选)等待完成
    
    Parameters:
    - code: OGE代码
    - user_id: 用户UUID
    - sample_name: 示例代码名称
    - task_name: 任务名称（可选）
    - filename: 文件名（可选）
    - crs: 坐标参考系统
    - scale: 比例尺
    - format: 输出格式
    - username: 用户名
    - auth_token: 认证Token（可选）
    - auto_submit: 是否自动提交任务
    - wait_for_completion: 是否等待任务完成
    - check_interval: 状态检查间隔（秒）
    - max_wait_time: 最大等待时间（秒）
    """
    operation = "DAG批处理工作流"
    workflow_start_time = time.perf_counter()
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation}")
        
        workflow_results = {
            "steps": [],
            "final_status": "unknown",
            "dag_ids": [],
            "task_info": None,
            "execution_times": {}
        }
        
        # 步骤1: 代码转DAG
        if ctx:
            await ctx.session.send_log_message("info", "步骤1: 代码转换为DAG...")
        
        dag_result_json = await execute_code_to_dag(
            code=code,
            user_id=user_id,
            sample_name=sample_name,
            auth_token=auth_token,
            ctx=ctx
        )
        
        dag_result = json.loads(dag_result_json)
        workflow_results["steps"].append({
            "step": 1,
            "name": "代码转DAG",
            "success": dag_result.get("success", False),
            "result": dag_result
        })
        
        if not dag_result.get("success"):
            workflow_results["final_status"] = "failed_at_dag_creation"
            result = Result.failed(
                msg=f"{operation}失败：代码转DAG步骤失败",
                operation=operation
            )
            result.data = workflow_results
            return result.model_dump_json()
        
        # 获取DAG信息
        dag_data = dag_result.get("data", {})
        dag_ids = dag_data.get("dag_ids", [])
        workflow_results["dag_ids"] = dag_ids
        
        if not dag_ids:
            workflow_results["final_status"] = "no_dag_generated"
            result = Result.failed(
                msg=f"{operation}失败：未生成DAG任务",
                operation=operation
            )
            result.data = workflow_results
            return result.model_dump_json()
        
        # 使用第一个DAG ID
        primary_dag_id = dag_ids[0]
        logger.info(f"使用DAG ID: {primary_dag_id}")
        
        if auto_submit:
            # 步骤2: 提交批处理任务
            if ctx:
                await ctx.session.send_log_message("info", f"步骤2: 提交批处理任务 (DAG: {primary_dag_id})...")
            
            submit_result_json = await submit_batch_task(
                dag_id=primary_dag_id,
                task_name=task_name,
                filename=filename,
                crs=crs,
                scale=scale,
                format=format,
                username=username,
                script=code,
                auth_token=auth_token,
                ctx=ctx
            )
            
            submit_result = json.loads(submit_result_json)
            workflow_results["steps"].append({
                "step": 2,
                "name": "提交批处理任务",
                "success": submit_result.get("success", False),
                "result": submit_result
            })
            
            if not submit_result.get("success"):
                workflow_results["final_status"] = "failed_at_task_submission"
                result = Result.failed(
                    msg=f"{operation}失败：任务提交步骤失败",
                    operation=operation
                )
                result.data = workflow_results
                return result.model_dump_json()
            
            # 获取任务信息
            task_data = submit_result.get("data", {})
            workflow_results["task_info"] = task_data
            
            if wait_for_completion:
                # 步骤3: 等待任务完成
                if ctx:
                    await ctx.session.send_log_message("info", f"步骤3: 等待任务完成...")
                
                waited_time = 0
                final_status = "unknown"
                
                while waited_time < max_wait_time:
                    status_result_json = await query_task_status(
                        dag_id=primary_dag_id,
                        auth_token=auth_token,
                        ctx=None  # 避免过多日志
                    )
                    
                    status_result = json.loads(status_result_json)
                    
                    if status_result.get("success"):
                        status_data = status_result.get("data", {})
                        current_status = status_data.get("status", "unknown")
                        
                        if status_data.get("is_completed"):
                            final_status = "completed"
                            workflow_results["final_status"] = "completed"
                            logger.info(f"任务已完成: {current_status}")
                            break
                        elif status_data.get("is_failed"):
                            final_status = "failed"
                            workflow_results["final_status"] = "failed"
                            logger.info(f"任务失败: {current_status}")
                            break
                        else:
                            # 任务仍在运行
                            if ctx:
                                await ctx.session.send_log_message("info", f"任务状态: {current_status}, 已等待 {waited_time}s")
                    
                    await asyncio.sleep(check_interval)
                    waited_time += check_interval
                
                if waited_time >= max_wait_time:
                    workflow_results["final_status"] = "timeout"
                    final_status = "timeout"
                
                workflow_results["steps"].append({
                    "step": 3,
                    "name": "等待任务完成",
                    "success": final_status == "completed",
                    "final_status": final_status,
                    "waited_time": waited_time
                })
            else:
                workflow_results["final_status"] = "submitted"
        else:
            workflow_results["final_status"] = "dag_created"
        
        total_execution_time = time.perf_counter() - workflow_start_time
        workflow_results["execution_times"]["total"] = total_execution_time
        
        # 构建最终结果
        if workflow_results["final_status"] in ["completed", "submitted", "dag_created"]:
            result = Result.succ(
                data=workflow_results,
                msg=f"{operation}成功，状态: {workflow_results['final_status']}",
                operation=operation,
                execution_time=total_execution_time,
                api_endpoint="dag"
            )
        else:
            result = Result.failed(
                msg=f"{operation}完成但状态异常: {workflow_results['final_status']}",
                operation=operation
            )
            result.data = workflow_results
        
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成，总耗时{total_execution_time:.2f}秒")
        
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            operation=operation
        )
        result.data = workflow_results
        return result.model_dump_json()

# ============ 资源管理已删除 ============

# ============ HTTP服务器设置 ============

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """创建支持SSE的Starlette应用"""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    async def handle_health(request: Request):
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
        return JSONResponse({
            "server_name": MCP_SERVER_NAME,
            "version": "2.4.0",
            "description": "山东耕地流出分析MCP服务器 - 增强版 (9个核心工具 + 自动Token管理)",
            "features": [
                "自动Token刷新",
                "手动Token刷新",
                "坡向分析", 
                "山东耕地流出分析",
                "大数据查询",
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
                "intranet_api": INTRANET_API_BASE_URL,
                "dag_api": DAG_API_BASE_URL
            },
            "available_tools": [
                "refresh_token",
                "check_token_status",
                "coverage_aspect_analysis", 
                "shandong_farmland_outflow",
                "run_big_query",
                "execute_code_to_dag",
                "submit_batch_task", 
                "query_task_status",
                "execute_dag_workflow"
            ],
            "token_management": {
                "type": "automatic",
                "description": "自动检测token过期(40003)并刷新，也支持手动刷新",
                "auto_refresh": "检测到40003错误时自动刷新",
                "manual_refresh": "可使用refresh_token工具手动刷新", 
                "credentials": "edu_admin/123456",
                "format": "Bearer <jwt_token>"
            }
        })

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/health", endpoint=handle_health),
            Route("/info", endpoint=handle_info),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

# ============ 主程序 ============

async def run_stdio_server():
    """运行stdio模式的服务器"""
    logger.info("启动山东耕地流出分析MCP服务器 (stdio模式)...")
    
    try:
        from mcp import stdio_server
        
        async with stdio_server() as streams:
            await mcp._mcp_server.run(
                streams[0], streams[1], 
                mcp._mcp_server.create_initialization_options()
            )
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器运行出错: {e}")
    finally:
        logger.info("MCP服务器已关闭")

def run_http_server(host: str = "0.0.0.0", port: int = 8000):
    """运行HTTP模式的服务器"""
    logger.info(f"启动山东耕地流出分析MCP服务器 (HTTP模式) - {host}:{port}")
    
    mcp_server = mcp._mcp_server
    starlette_app = create_starlette_app(mcp_server, debug=True)
    
    uvicorn.run(starlette_app, host=host, port=port)

# 在文件末尾添加测试工具

@mcp.tool()
async def test_dag_status_api(
    dag_id: str,
    ctx: Context = None
) -> str:
    """
    测试DAG状态查询API - 直接调用不经过封装
    
    用于诊断query_task_status的问题
    """
    operation = "测试DAG状态API"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation} - DAG ID: {dag_id}")
        
        # 构建API URL
        api_url = f"{DAG_API_BASE_URL}/getState"
        params = {"dagId": dag_id}
        
        logger.info(f"测试API调用: {api_url}?dagId={dag_id}")
        
        start_time = time.perf_counter()
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                api_url,
                params=params,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": INTRANET_AUTH_TOKEN
                }
            )
            
            execution_time = time.perf_counter() - start_time
            
            # 详细记录响应信息
            response_info = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_length": len(response.content),
                "text_preview": response.text[:200] if response.text else "Empty",
                "is_json": False,
                "execution_time": execution_time
            }
            
            # 尝试解析JSON
            json_data = None
            try:
                json_data = response.json()
                response_info["is_json"] = True
                response_info["json_data"] = json_data
            except Exception as e:
                response_info["json_error"] = str(e)
            
            result = Result.succ(
                data=response_info,
                msg=f"{operation}完成 - 状态码: {response.status_code}",
                operation=operation,
                execution_time=execution_time,
                api_endpoint="dag_test"
            )
            
            logger.info(f"{operation}完成 - 状态码: {response.status_code}, 内容长度: {len(response.content)}")
            
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成")
        
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            operation=operation
        )
        return result.model_dump_json()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='山东耕地流出分析MCP服务器 - 增强版')
    parser.add_argument('--mode', choices=['stdio', 'http'], default='stdio', help='运行模式')
    parser.add_argument('--host', default='0.0.0.0', help='HTTP模式的绑定地址')
    parser.add_argument('--port', type=int, default=8000, help='HTTP模式的监听端口')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'stdio':
            asyncio.run(run_stdio_server())
        else:
            run_http_server(args.host, args.port)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        logger.error(f"启动失败: {e}") 