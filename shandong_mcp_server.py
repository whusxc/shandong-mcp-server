#!/usr/bin/env python3
"""
山东耕地流出分析 MCP服务器
基于shandong.txt中的工作流，将每个算法步骤封装为MCP工具
支持完整工作流执行和单步执行两种模式
"""

import asyncio
import json
import logging
import httpx
from typing import Any, Dict, List, Optional

# MCP SDK 导入
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    from mcp import stdio_server
except ImportError as e:
    print(f"Error importing MCP SDK: {e}")
    print("Please install: pip install mcp")
    exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OGE API配置
OGE_API_BASE_URL = "http://172.30.22.116:16555/gateway/computation-api/process"

# 内网API配置 (新增)
INTRANET_API_BASE_URL = "http://172.20.70.142:16555/gateway/computation-api/process"
INTRANET_AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjMyNCwidXNlcl9uYW1lIjoiZWR1X2FkbWluIiwic2NvcGUiOlsid2ViIl0sImV4cCI6MTc0OTkwNjkwMiwidXVpZCI6ImY5NTBjZmYyLTA3YzgtNDYxYS05YzI0LTkxNjJkNTllMmVmNiIsImF1dGhvcml0aWVzIjpbIkFETUlOSVNUUkFUT1JTIl0sImp0aSI6IkxQbjJQTThlRlpBRDhUNFBxN2U3SWlRdmRGQSIsImNsaWVudF9pZCI6InRlc3QiLCJ1c2VybmFtZSI6ImVkdV9hZG1pbiJ9.jFepdzkcDDlcH0v3Z_Ge35vbiTB3RVt8OQsHJ0o6qEU"

# 创建MCP服务器
server = Server("shandong-cultivated-analysis")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """列出所有耕地分析工具"""
    return [
        # 完整工作流工具
        Tool(
            name="execute_full_workflow",
            description="执行完整的山东耕地流出分析工作流（按照shandong.txt的完整流程）",
            inputSchema={
                "type": "object",
                "properties": {
                    "enable_visualization": {
                        "type": "boolean", 
                        "description": "是否生成最终可视化地图",
                        "default": True
                    },
                    "intermediate_results": {
                        "type": "boolean",
                        "description": "是否返回中间步骤结果",
                        "default": False
                    }
                }
            }
        ),
        
        # 数据获取工具
        Tool(
            name="run_big_query",
            description="执行SQL查询获取要素集合",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql_query": {"type": "string", "description": "SQL查询语句"},
                    "geometry_field": {"type": "string", "description": "几何字段名", "default": "geom"}
                },
                "required": ["sql_query"]
            }
        ),
        Tool(
            name="get_feature_collection",
            description="获取指定的要素集合",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection_name": {"type": "string", "description": "要素集合名称"}
                },
                "required": ["collection_name"]
            }
        ),
        Tool(
            name="reproject_features",
            description="要素集合坐标投影转换",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_collection": {"type": "string", "description": "输入要素集合ID"},
                    "target_crs": {"type": "string", "description": "目标坐标系", "default": "EPSG:4527"}
                },
                "required": ["feature_collection", "target_crs"]
            }
        ),
        
        # 空间分析工具
        Tool(
            name="spatial_intersection",
            description="两个要素集合的空间相交分析",
            inputSchema={
                "type": "object",
                "properties": {
                    "features_a": {"type": "string", "description": "要素集合A的ID"},
                    "features_b": {"type": "string", "description": "要素集合B的ID"}
                },
                "required": ["features_a", "features_b"]
            }
        ),
        Tool(
            name="spatial_erase",
            description="空间擦除分析（从A中去除B的重叠部分）",
            inputSchema={
                "type": "object",
                "properties": {
                    "features_a": {"type": "string", "description": "被擦除的要素集合ID"},
                    "features_b": {"type": "string", "description": "擦除用的要素集合ID"}
                },
                "required": ["features_a", "features_b"]
            }
        ),
        Tool(
            name="buffer_analysis",
            description="缓冲区分析",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_collection": {"type": "string", "description": "输入要素集合ID"},
                    "distance": {"type": "number", "description": "缓冲距离（米）"}
                },
                "required": ["feature_collection", "distance"]
            }
        ),
        Tool(
            name="spatial_join",
            description="空间连接分析",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_features": {"type": "string", "description": "目标要素集合ID"},
                    "join_features": {"type": "string", "description": "连接要素集合ID"},
                    "target_geom_field": {"type": "string", "description": "目标几何字段", "default": "geom"},
                    "join_geom_field": {"type": "string", "description": "连接几何字段", "default": "geom"},
                    "retain_geometry": {"type": "boolean", "description": "是否保留几何", "default": True},
                    "spatial_relation": {"type": "string", "description": "空间关系", "default": "Intersects"},
                    "properties": {"type": "array", "items": {"type": "string"}, "description": "要连接的属性字段"},
                    "reducer": {"type": "array", "items": {"type": "string"}, "description": "聚合方式"}
                },
                "required": ["target_features", "join_features", "properties", "reducer"]
            }
        ),
        
        # 属性计算工具
        Tool(
            name="calculate_area",
            description="计算要素集合中每个要素的面积",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_collection": {"type": "string", "description": "输入要素集合ID"}
                },
                "required": ["feature_collection"]
            }
        ),
        Tool(
            name="filter_by_metadata",
            description="基于属性字段过滤要素",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_collection": {"type": "string", "description": "输入要素集合ID"},
                    "property_name": {"type": "string", "description": "过滤字段名"},
                    "operator": {"type": "string", "description": "比较操作符", "enum": ["greater_than", "less_than", "equals", "not_equals"]},
                    "value": {"type": ["string", "number"], "description": "比较值"}
                },
                "required": ["feature_collection", "property_name", "operator", "value"]
            }
        ),
        Tool(
            name="field_subtract",
            description="字段减法运算（创建新字段 = field_a - field_b）",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_collection": {"type": "string", "description": "输入要素集合ID"},
                    "field_a": {"type": "string", "description": "被减数字段"},
                    "field_b": {"type": "string", "description": "减数字段"},
                    "result_field": {"type": "string", "description": "结果字段名"}
                },
                "required": ["feature_collection", "field_a", "field_b", "result_field"]
            }
        ),
        
        # 数据合并工具
        Tool(
            name="merge_feature_collections",
            description="合并多个要素集合",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_collections": {"type": "array", "items": {"type": "string"}, "description": "要合并的要素集合ID列表"}
                },
                "required": ["feature_collections"]
            }
        ),
        
        # 可视化工具
        Tool(
            name="visualize_features",
            description="创建要素集合的可视化地图",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_collection": {"type": "string", "description": "要素集合ID"},
                    "style_colors": {"type": "array", "items": {"type": "string"}, "description": "样式颜色列表"},
                    "map_name": {"type": "string", "description": "地图名称"}
                },
                "required": ["feature_collection", "style_colors", "map_name"]
            }
        ),
        
        # 内网专用算法工具
        Tool(
            name="coverage_aspect_analysis",
            description="坡向分析 - 基于DEM数据计算坡向信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "coverage_type": {
                        "type": "string", 
                        "description": "覆盖类型", 
                        "default": "Coverage"
                    },
                    "pretreatment": {
                        "type": "boolean", 
                        "description": "是否进行预处理", 
                        "default": True
                    },
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "边界框坐标 [minLon, minLat, maxLon, maxLat]",
                        "minItems": 4,
                        "maxItems": 4
                    },
                    "product_value": {
                        "type": "string",
                        "description": "产品数据源",
                        "default": "Platform:Product:ASTER_GDEM_DEM30"
                    },
                    "radius": {
                        "type": "number",
                        "description": "计算半径",
                        "default": 1
                    }
                },
                "required": ["bbox"]
            }
        ),
        
        # 认证工具
        Tool(
            name="get_oauth_token",
            description="获取OAuth认证Token",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "用户名"},
                    "password": {"type": "string", "description": "密码"},
                    "client_id": {"type": "string", "description": "客户端ID", "default": "test"},
                    "client_secret": {"type": "string", "description": "客户端密钥", "default": "123456"},
                    "scopes": {"type": "string", "description": "权限范围", "default": "web"},
                    "grant_type": {"type": "string", "description": "授权类型", "default": "password"},
                    "base_url": {"type": "string", "description": "基础URL (可选)"},
                    "existing_token": {"type": "string", "description": "现有token (可选)"}
                },
                "required": ["username", "password"]
            }
        ),
        Tool(
            name="refresh_intranet_token",
            description="刷新内网认证Token并可选择性更新全局Token",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "用户名"},
                    "password": {"type": "string", "description": "密码"},
                    "update_global_token": {"type": "boolean", "description": "是否更新全局使用的token", "default": True}
                },
                "required": ["username", "password"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """处理工具调用"""
    
    tool_mapping = {
        "execute_full_workflow": execute_full_workflow,
        "run_big_query": call_run_big_query,
        "get_feature_collection": call_get_feature_collection,
        "reproject_features": call_reproject_features,
        "spatial_intersection": call_spatial_intersection,
        "spatial_erase": call_spatial_erase,
        "buffer_analysis": call_buffer_analysis,
        "spatial_join": call_spatial_join,
        "calculate_area": call_calculate_area,
        "filter_by_metadata": call_filter_by_metadata,
        "field_subtract": call_field_subtract,
        "merge_feature_collections": call_merge_feature_collections,
        "visualize_features": call_visualize_features,
        "coverage_aspect_analysis": call_coverage_aspect_analysis,
        "get_oauth_token": call_get_oauth_token,
        "refresh_intranet_token": call_refresh_intranet_token
    }
    
    if name in tool_mapping:
        return await tool_mapping[name](arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

# 完整工作流实现
async def execute_full_workflow(arguments: dict) -> List[TextContent]:
    """执行完整的山东耕地流出分析工作流"""
    enable_visualization = arguments.get("enable_visualization", True)
    show_intermediate = arguments.get("intermediate_results", False)
    
    logger.info("开始执行完整的山东耕地流出分析工作流...")
    
    workflow_results = {
        "workflow_name": "山东耕地流出分析",
        "status": "running",
        "steps_completed": 0,
        "total_steps": 16,
        "results": {},
        "intermediate_data": {} if show_intermediate else None,
        "final_result": None,
        "errors": []
    }
    
    try:
        # 步骤1: 获取耕地数据
        logger.info("步骤1: 获取耕地数据...")
        cultivated_sql = "SELECT * FROM guotubiangeng WHERE DLMC IN ('旱地', '水浇地', '水田')"
        cultivated_result = await execute_step("run_big_query", {
            "sql_query": cultivated_sql,
            "geometry_field": "geom"
        })
        workflow_results["steps_completed"] += 1
        if show_intermediate:
            workflow_results["intermediate_data"]["step1_cultivated"] = cultivated_result
        
        # 步骤2: 获取坡度数据
        logger.info("步骤2: 获取坡度数据...")
        slope_result = await execute_step("get_feature_collection", {
            "collection_name": "podu"
        })
        workflow_results["steps_completed"] += 1
        if show_intermediate:
            workflow_results["intermediate_data"]["step2_slope"] = slope_result
        
        # 步骤3: 过滤大于15度坡地
        logger.info("步骤3: 过滤大于15度坡地...")
        slope_filtered_result = await execute_step("filter_by_metadata", {
            "feature_collection": "slope_collection_id",  # 这里需要从步骤2的结果中获取实际ID
            "property_name": "pdjb",
            "operator": "greater_than",
            "value": 4
        })
        workflow_results["steps_completed"] += 1
        
        # 步骤4-6: 坐标投影转换
        logger.info("步骤4-6: 坐标投影转换...")
        collections_to_reproject = ["slope_morethan15", "urban", "nature", "ecology"]
        for collection in collections_to_reproject:
            await execute_step("reproject_features", {
                "feature_collection": f"{collection}_id",
                "target_crs": "EPSG:4527"
            })
            workflow_results["steps_completed"] += 1
        
        # 步骤7: 获取边界数据
        logger.info("步骤7: 获取边界数据...")
        boundary_collections = ["chengzhenkaifa", "ziranbaohu", "shengtaibaohu"]
        boundary_results = {}
        for collection in boundary_collections:
            result = await execute_step("get_feature_collection", {
                "collection_name": collection
            })
            boundary_results[collection] = result
        workflow_results["steps_completed"] += 1
        
        # 步骤8-11: 逐层空间分析
        logger.info("步骤8-11: 逐层空间分析...")
        spatial_analysis_steps = [
            ("urban_intersection", "spatial_intersection", "cultivated", "urban"),
            ("urban_erase", "spatial_erase", "cultivated", "urban"),
            ("nature_intersection", "spatial_intersection", "urban_erase", "nature"),
            ("nature_erase", "spatial_erase", "urban_erase", "nature"),
            ("ecology_intersection", "spatial_intersection", "nature_erase", "ecology"),
            ("ecology_erase", "spatial_erase", "nature_erase", "ecology"),
            ("slope_intersection", "spatial_intersection", "ecology_erase", "slope_morethan15"),
            ("slope_erase", "spatial_erase", "ecology_erase", "slope_morethan15")
        ]
        
        spatial_results = {}
        for result_name, operation, input_a, input_b in spatial_analysis_steps:
            if operation == "spatial_intersection":
                result = await execute_step("spatial_intersection", {
                    "features_a": f"{input_a}_id",
                    "features_b": f"{input_b}_id"
                })
            else:  # spatial_erase
                result = await execute_step("spatial_erase", {
                    "features_a": f"{input_a}_id",
                    "features_b": f"{input_b}_id"
                })
            spatial_results[result_name] = result
            workflow_results["steps_completed"] += 1
        
        # 步骤12-16: 细碎化耕地处理
        logger.info("步骤12-16: 细碎化耕地处理...")
        
        # 面积计算
        area_result = await execute_step("calculate_area", {
            "feature_collection": "slope_erase_id"
        })
        
        # 小于5亩过滤
        small_fields_result = await execute_step("filter_by_metadata", {
            "feature_collection": "cultivated1_area_id",
            "property_name": "area",
            "operator": "less_than",
            "value": 3333.3333
        })
        
        # 缓冲区分析
        buffer_result = await execute_step("buffer_analysis", {
            "feature_collection": "cultivated1_lessthan5_id",
            "distance": 10
        })
        
        # 空间连接
        join_result = await execute_step("spatial_join", {
            "target_features": "cultivated1_buffer_id",
            "join_features": "cultivated1_area_id",
            "target_geom_field": "buffer",
            "join_geom_field": "geom",
            "retain_geometry": True,
            "spatial_relation": "Intersects",
            "properties": ["area"],
            "reducer": ["sum"]
        })
        
        # 字段减法
        subtract_result = await execute_step("field_subtract", {
            "feature_collection": "cultivated1_join_id",
            "field_a": "area_sum",
            "field_b": "area",
            "result_field": "area_peri"
        })
        
        # 最终过滤
        deprecated1_result = await execute_step("filter_by_metadata", {
            "feature_collection": "cultivated1_subtract_id",
            "property_name": "area_peri",
            "operator": "less_than",
            "value": 6666.6667
        })
        
        workflow_results["steps_completed"] += 5
        
        # 步骤17: 合并所有流出耕地
        logger.info("步骤17: 合并所有流出耕地...")
        final_merge_result = await execute_step("merge_feature_collections", {
            "feature_collections": [
                "urban_intersection_id",
                "nature_intersection_id",
                "ecology_intersection_id",
                "slope_intersection_id",
                "deprecated1_id"
            ]
        })
        workflow_results["steps_completed"] += 1
        
        # 步骤18: 可视化（可选）
        if enable_visualization:
            logger.info("步骤18: 创建可视化地图...")
            viz_result = await execute_step("visualize_features", {
                "feature_collection": "deprecated_id",
                "style_colors": ["#808080"],
                "map_name": "deprecated"
            })
            workflow_results["results"]["visualization"] = viz_result
            workflow_results["steps_completed"] += 1
        
        # 完成工作流
        workflow_results["status"] = "completed"
        workflow_results["final_result"] = final_merge_result
        workflow_results["message"] = "山东耕地流出分析工作流执行完成"
        
        logger.info("完整工作流执行完成!")
        
    except Exception as e:
        logger.error(f"工作流执行失败: {str(e)}")
        workflow_results["status"] = "failed"
        workflow_results["errors"].append(str(e))
        workflow_results["message"] = f"工作流执行失败: {str(e)}"
    
    return [TextContent(
        type="text",
        text=json.dumps(workflow_results, ensure_ascii=False, indent=2)
    )]

async def execute_step(tool_name: str, arguments: dict) -> dict:
    """执行单个工作流步骤"""
    try:
        # 按照OGE API文档格式构建请求体
        api_payload = {
            "name": get_algorithm_name_for_tool(tool_name),
            "args": arguments,
            "dockerImageSource": "DOCKER_HUB"
        }
        
        # 调用OGE API（简化版，实际需要根据工具类型调用对应函数）
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OGE_API_BASE_URL,
                json=api_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "tool": tool_name,
                    "result": response.json()
                }
            else:
                return {
                    "status": "error", 
                    "tool": tool_name,
                    "error": response.text
                }
                
    except Exception as e:
        return {
            "status": "error",
            "tool": tool_name, 
            "error": str(e)
        }

def get_algorithm_name_for_tool(tool_name: str) -> str:
    """根据工具名获取对应的算法名"""
    mapping = {
        "run_big_query": "FeatureCollection.runBigQuery",
        "get_feature_collection": "FeatureCollection.get",
        "reproject_features": "FeatureCollection.reproject",
        "spatial_intersection": "FeatureCollection.intersection",
        "spatial_erase": "FeatureCollection.erase",
        "buffer_analysis": "FeatureCollection.buffer",
        "spatial_join": "FeatureCollection.spatialJoinOneToOne",
        "calculate_area": "FeatureCollection.area",
        "filter_by_metadata": "FeatureCollection.filterMetadata",
        "field_subtract": "FeatureCollection.subtract",
        "merge_feature_collections": "FeatureCollection.mergeAll",
        "visualize_features": "FeatureCollection.getMap"
    }
    return mapping.get(tool_name, "unknown")

# 工具实现函数
async def call_run_big_query(arguments: dict) -> List[TextContent]:
    """执行SQL查询"""
    sql_query = arguments.get("sql_query", "")
    geometry_field = arguments.get("geometry_field", "geom")
    
    algorithm_args = {
        "sql": sql_query,
        "geometry_field": geometry_field
    }
    
    return await call_oge_api("FeatureCollection.runBigQuery", algorithm_args, "SQL查询")

async def call_get_feature_collection(arguments: dict) -> List[TextContent]:
    """获取要素集合"""
    collection_name = arguments.get("collection_name", "")
    
    algorithm_args = {
        "collection_name": collection_name
    }
    
    return await call_oge_api("FeatureCollection.get", algorithm_args, f"获取要素集合: {collection_name}")

async def call_reproject_features(arguments: dict) -> List[TextContent]:
    """坐标投影转换"""
    feature_collection = arguments.get("feature_collection", "")
    target_crs = arguments.get("target_crs", "EPSG:4527")
    
    algorithm_args = {
        "feature_collection": feature_collection,
        "crs": target_crs
    }
    
    return await call_oge_api("FeatureCollection.reproject", algorithm_args, f"坐标投影转换到 {target_crs}")

async def call_spatial_intersection(arguments: dict) -> List[TextContent]:
    """空间相交分析"""
    features_a = arguments.get("features_a", "")
    features_b = arguments.get("features_b", "")
    
    algorithm_args = {
        "feature_collection_a": features_a,
        "feature_collection_b": features_b
    }
    
    return await call_oge_api("FeatureCollection.intersection", algorithm_args, "空间相交分析")

async def call_spatial_erase(arguments: dict) -> List[TextContent]:
    """空间擦除分析"""
    features_a = arguments.get("features_a", "")
    features_b = arguments.get("features_b", "")
    
    algorithm_args = {
        "feature_collection": features_a,
        "erase_collection": features_b
    }
    
    return await call_oge_api("FeatureCollection.erase", algorithm_args, "空间擦除分析")

async def call_buffer_analysis(arguments: dict) -> List[TextContent]:
    """缓冲区分析"""
    feature_collection = arguments.get("feature_collection", "")
    distance = arguments.get("distance", 10)
    
    algorithm_args = {
        "feature_collection": feature_collection,
        "distance": distance
    }
    
    return await call_oge_api("FeatureCollection.buffer", algorithm_args, f"缓冲区分析 (距离: {distance}m)")

async def call_spatial_join(arguments: dict) -> List[TextContent]:
    """空间连接分析"""
    target_features = arguments.get("target_features", "")
    join_features = arguments.get("join_features", "")
    target_geom_field = arguments.get("target_geom_field", "geom")
    join_geom_field = arguments.get("join_geom_field", "geom")
    retain_geometry = arguments.get("retain_geometry", True)
    spatial_relation = arguments.get("spatial_relation", "Intersects")
    properties = arguments.get("properties", [])
    reducer = arguments.get("reducer", [])
    
    algorithm_args = {
        "target": target_features,
        "join": join_features,
        "target_geometry_field": target_geom_field,
        "join_geometry_field": join_geom_field,
        "retain_geometry": retain_geometry,
        "spatial_relation": spatial_relation,
        "properties": properties,
        "reducer": reducer
    }
    
    return await call_oge_api("FeatureCollection.spatialJoinOneToOne", algorithm_args, "空间连接分析")

async def call_calculate_area(arguments: dict) -> List[TextContent]:
    """计算面积"""
    feature_collection = arguments.get("feature_collection", "")
    
    algorithm_args = {
        "feature_collection": feature_collection
    }
    
    return await call_oge_api("FeatureCollection.area", algorithm_args, "面积计算")

async def call_filter_by_metadata(arguments: dict) -> List[TextContent]:
    """属性过滤"""
    feature_collection = arguments.get("feature_collection", "")
    property_name = arguments.get("property_name", "")
    operator = arguments.get("operator", "equals")
    value = arguments.get("value", "")
    
    algorithm_args = {
        "feature_collection": feature_collection,
        "property": property_name,
        "operator": operator,
        "value": value
    }
    
    return await call_oge_api("FeatureCollection.filterMetadata", algorithm_args, f"属性过滤: {property_name} {operator} {value}")

async def call_field_subtract(arguments: dict) -> List[TextContent]:
    """字段减法运算"""
    feature_collection = arguments.get("feature_collection", "")
    field_a = arguments.get("field_a", "")
    field_b = arguments.get("field_b", "")
    result_field = arguments.get("result_field", "")
    
    algorithm_args = {
        "feature_collection": feature_collection,
        "field_a": field_a,
        "field_b": field_b,
        "result_field": result_field
    }
    
    return await call_oge_api("FeatureCollection.subtract", algorithm_args, f"字段减法: {result_field} = {field_a} - {field_b}")

async def call_merge_feature_collections(arguments: dict) -> List[TextContent]:
    """合并要素集合"""
    feature_collections = arguments.get("feature_collections", [])
    
    algorithm_args = {
        "feature_collections": feature_collections
    }
    
    return await call_oge_api("FeatureCollection.mergeAll", algorithm_args, f"合并 {len(feature_collections)} 个要素集合")

async def call_visualize_features(arguments: dict) -> List[TextContent]:
    """可视化要素"""
    feature_collection = arguments.get("feature_collection", "")
    style_colors = arguments.get("style_colors", ["#808080"])
    map_name = arguments.get("map_name", "map")
    
    algorithm_args = {
        "feature_collection": feature_collection,
        "vis_params": style_colors,
        "map_name": map_name
    }
    
    return await call_oge_api("FeatureCollection.getMap", algorithm_args, f"创建地图: {map_name}")

async def call_coverage_aspect_analysis(arguments: dict) -> List[TextContent]:
    """坡向分析 - 使用内网API"""
    coverage_type = arguments.get("coverage_type", "Coverage")
    pretreatment = arguments.get("pretreatment", True)
    bbox = arguments.get("bbox", [])
    product_value = arguments.get("product_value", "Platform:Product:ASTER_GDEM_DEM30")
    radius = arguments.get("radius", 1)
    
    algorithm_args = {
        "coverage": {
            "type": coverage_type,
            "pretreatment": pretreatment,
            "preParams": {
                "bbox": bbox
            },
            "value": [product_value]
        },
        "radius": radius
    }
    
    return await call_intranet_api("Coverage.aspect", algorithm_args, "坡向分析")

async def call_oge_api(algorithm_name: str, algorithm_args: dict, operation_desc: str) -> List[TextContent]:
    """统一的OGE API调用函数 - 使用正确的API格式"""
    logger.info(f"执行操作: {operation_desc}")
    
    # 按照OGE API文档格式构建请求体
    api_payload = {
        "name": algorithm_name,
        "args": algorithm_args,
        "dockerImageSource": "DOCKER_HUB"
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OGE_API_BASE_URL,
                json=api_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                result = {
                    "operation": operation_desc,
                    "status": "success",
                    "api_response": result_data,
                    "algorithm": algorithm_name,
                    "parameters": algorithm_args,
                    "message": f"{operation_desc} 执行成功"
                }
                
            else:
                result = {
                    "operation": operation_desc,
                    "status": "error",
                    "error_code": response.status_code,
                    "error_message": response.text,
                    "algorithm": algorithm_name,
                    "parameters": algorithm_args
                }
                
    except Exception as e:
        logger.error(f"API调用失败: {str(e)}")
        result = {
            "operation": operation_desc,
            "status": "error",
            "error_message": str(e),
            "algorithm": algorithm_name,
            "parameters": algorithm_args
        }
    
    return [TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]

async def call_intranet_api(algorithm_name: str, algorithm_args: dict, operation_desc: str) -> List[TextContent]:
    """内网API调用函数 - 支持认证"""
    logger.info(f"执行内网操作: {operation_desc}")
    
    # 按照内网API格式构建请求体
    api_payload = {
        "name": algorithm_name,
        "args": algorithm_args,
        "dockerImageSource": "DOCKER_HUB"
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                INTRANET_API_BASE_URL,
                json=api_payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": INTRANET_AUTH_TOKEN
                }
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                result = {
                    "operation": operation_desc,
                    "status": "success",
                    "api_response": result_data,
                    "algorithm": algorithm_name,
                    "parameters": algorithm_args,
                    "message": f"{operation_desc} 执行成功",
                    "api_endpoint": "intranet"
                }
                
            else:
                result = {
                    "operation": operation_desc,
                    "status": "error",
                    "error_code": response.status_code,
                    "error_message": response.text,
                    "algorithm": algorithm_name,
                    "parameters": algorithm_args,
                    "api_endpoint": "intranet"
                }
                
    except Exception as e:
        logger.error(f"内网API调用失败: {str(e)}")
        result = {
            "operation": operation_desc,
            "status": "error",
            "error_message": str(e),
            "algorithm": algorithm_name,
            "parameters": algorithm_args,
            "api_endpoint": "intranet"
        }
    
    return [TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]

async def call_get_oauth_token(arguments: dict) -> List[TextContent]:
    """获取OAuth认证Token"""
    username = arguments.get("username", "")
    password = arguments.get("password", "")
    client_id = arguments.get("client_id", "test")
    client_secret = arguments.get("client_secret", "123456")
    scopes = arguments.get("scopes", "web")
    grant_type = arguments.get("grant_type", "password")
    base_url = arguments.get("base_url")
    existing_token = arguments.get("existing_token")
    
    operation_desc = "获取OAuth Token"
    logger.info(f"执行操作: {operation_desc} - 用户: {username}")
    
    try:
        # 确定API地址
        if base_url is None:
            base_url = INTRANET_API_BASE_URL.replace('/gateway/computation-api/process', '')
        
        token_url = f"{base_url}/gateway/oauth/token"
        
        # 构建查询参数
        params = {
            "scopes": scopes,
            "client_secret": client_secret,
            "client_id": client_id,
            "username": username,
            "password": password,
            "grant_type": grant_type
        }
        
        # 构建请求头
        headers = {"Content-Type": "application/json"}
        
        if existing_token:
            if not existing_token.startswith("Bearer "):
                existing_token = f"Bearer {existing_token}"
            headers["Authorization"] = existing_token
        elif INTRANET_AUTH_TOKEN:
            headers["Authorization"] = INTRANET_AUTH_TOKEN
        
        # 构建请求体
        request_body = {
            "username": username,
            "password": password
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                token_url,
                params=params,
                json=request_body,
                headers=headers
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                access_token = token_data.get('access_token', '')
                token_type = token_data.get('token_type', 'Bearer')
                expires_in = token_data.get('expires_in', 0)
                
                result = {
                    "operation": operation_desc,
                    "status": "success",
                    "data": {
                        "access_token": access_token,
                        "token_type": token_type,
                        "expires_in": expires_in,
                        "full_token": f"{token_type} {access_token}" if access_token else "",
                        "raw_response": token_data
                    },
                    "message": f"{operation_desc} 执行成功",
                    "api_endpoint": "oauth"
                }
                
            else:
                result = {
                    "operation": operation_desc,
                    "status": "error",
                    "error_code": response.status_code,
                    "error_message": response.text,
                    "api_endpoint": "oauth"
                }
                
    except Exception as e:
        logger.error(f"OAuth API调用失败: {str(e)}")
        result = {
            "operation": operation_desc,
            "status": "error",
            "error_message": str(e),
            "api_endpoint": "oauth"
        }
    
    return [TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]

async def call_refresh_intranet_token(arguments: dict) -> List[TextContent]:
    """刷新内网认证Token"""
    username = arguments.get("username", "")
    password = arguments.get("password", "")
    update_global_token = arguments.get("update_global_token", True)
    
    operation_desc = "刷新内网Token"
    logger.info(f"执行操作: {operation_desc}")
    
    try:
        # 调用获取token函数
        token_arguments = {
            "username": username,
            "password": password
        }
        
        token_results = await call_get_oauth_token(token_arguments)
        token_result = json.loads(token_results[0].text)
        
        if token_result.get("status") == "success":
            token_data = token_result.get("data", {})
            full_token = token_data.get("full_token", "")
            
            if update_global_token and full_token:
                # 更新全局token
                global INTRANET_AUTH_TOKEN
                INTRANET_AUTH_TOKEN = full_token
                logger.info("全局Token已更新")
                
                result = {
                    "operation": operation_desc,
                    "status": "success",
                    "data": {
                        "token_info": token_data,
                        "global_updated": True,
                        "message": "Token已刷新并更新到全局配置"
                    },
                    "message": f"{operation_desc} 执行成功并已更新全局配置"
                }
            else:
                result = {
                    "operation": operation_desc,
                    "status": "success",
                    "data": {
                        "token_info": token_data,
                        "global_updated": False,
                        "message": "Token已刷新但未更新全局配置"
                    },
                    "message": f"{operation_desc} 执行成功"
                }
        else:
            result = {
                "operation": operation_desc,
                "status": "error",
                "error_message": token_result.get("error_message", "未知错误")
            }
            
    except Exception as e:
        logger.error(f"{operation_desc}执行失败: {str(e)}")
        result = {
            "operation": operation_desc,
            "status": "error",
            "error_message": str(e)
        }
    
    return [TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]

async def main():
    """主函数"""
    logger.info("启动山东耕地流出分析MCP服务器...")
    
    try:
        async with stdio_server() as streams:
            await server.run(
                streams[0], streams[1], 
                server.create_initialization_options()
            )
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器运行出错: {e}")
    finally:
        logger.info("MCP服务器已关闭")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务器已停止") 