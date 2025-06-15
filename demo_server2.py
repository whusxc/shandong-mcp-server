# -*- coding: utf-8 -*-
# File: demo_server2.py.py
# Date: 2025/5/19
# Description:
import logging
from pathlib import Path
import argparse
import os
from mcp.server.fastmcp import FastMCP, Context
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
import json
import requests
from conf.env_conf import gp_service, api_url
from utils.common import get_uuid

# 定义服务器名称
MCP_SERVER_NAME = "mcp_server-demo-sse"


# 初始化 FastMCP 实例
mcp = FastMCP(MCP_SERVER_NAME)


from enum import IntEnum
from typing import Optional, TypeVar, Generic, Dict, Union, List, Any
from pydantic import BaseModel

T = TypeVar("T")
resource_path = os.path.join(os.path.dirname(__file__), "resource")

class RetCode(IntEnum):
    SUCCESS = 0
    FAILED = 1

class Result(BaseModel):
    success: bool = False
    code: Optional[int] = None
    msg: Optional[str] = None
    data: Optional[T] = None
    type: Optional[str] = "ask_map"
    map_type: Optional[str] = None

    @classmethod
    def succ(cls, data: T = None, msg="成功", map_type= None):
        return Result(success=True, code=RetCode.SUCCESS, msg=msg, data=data, map_type=map_type)

    @classmethod
    def failed(cls, code: int = RetCode.FAILED, msg=None):
        return Result(success=False, code=code, msg=msg, data=None)



def call_api(
        url: str,
        method: str = 'GET',
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json: Optional[Union[Dict, List]] = None,
        files: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None,
        verify_ssl: bool = True
):
    """
    通用API请求函数

    :param url: 请求地址
    :param method: HTTP方法 (GET, POST, PUT, DELETE等)
    :param params: URL参数 (GET参数)
    :param data: 表单数据 (POST表单数据)
    :param json: JSON数据 (POST JSON数据)
    :param headers: 请求头
    :param timeout: 超时时间（秒）
    :param verify_ssl: 是否验证SSL证书
    :return: 包含响应或错误的字典
    """
    # 合并默认请求头和自定义请求头
    import time
    default_headers = {}
    final_headers = {**default_headers, **(headers or {})}

    start_time = time.perf_counter()
    response = requests.request(
        method=method.upper(),
        url=url,
        params=params,
        data=data,
        json=json,
        files=files,
        headers=final_headers,
        timeout=timeout,
        verify=verify_ssl
    )
    execution_time =( time.perf_counter() - start_time)

    return response, f'{execution_time:.4f}'


def create_file_with_dir(file_path):
    p = Path(file_path)
    # 创建文件夹，exist_ok=True表示如果已存在则不抛出异常
    p.parent.mkdir(parents=True, exist_ok=True)
    # 创建文件，exist_ok=True表示如果已存在则不抛出异常
    p.touch(exist_ok=True)

def setup_logger(name=None, file=None, model='a', level=logging.INFO) -> logging.Logger:
    """获取工作区的Logger，会删除原来的工作区日志文件"""
    logger = logging.getLogger(name)
    logger.propagate = False  # 阻止日志传递给父 Logger（如根 Logger）

    logger.setLevel(level)
    # 获取原来的FileHandler，关闭Handlers并删除文件
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(fmt='%(name)s - %(asctime)s - %(message)s', datefmt='%Y-%m-%d %A %H:%M:%S')

    create_file_with_dir(file)

    file_handler = logging.FileHandler(filename=file, mode=model, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)
    logger.addHandler(stream_handler)

    return logger

call_api_logger = setup_logger(name="demo_server", file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", f'call_api.log'))
@mcp.prompt()
async def code_review_prompt(message: str, ctx: Context) -> str:
    prompt = "特定SOP操作指引"
    return f"{prompt}\n\n{message}"


@mcp.resource(uri="db://get_map_data/{name}", description="访问某个图层的资源")
def get_data(name: str) -> Result:
    """
    Parameters:
    - name: 资源的标识名称
    Returns:
    """
    try:
        with open(f"{resource_path}/{name}.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
        if name not in data:
            return Result.failed(msg="未查询到该图层资源")
        return Result.succ(data=data[name])
    except Exception as e:
        return Result.failed(msg="读取资源失败" + str(e))
    except json.JSONDecodeError as e:
        return Result.failed(msg="Json格式有问题" + str(e))


@mcp.tool()
async def get_all_layers(ctx: Context):
    """
    获取所有图层的信息/名称。
    ## 使用场景示例
    - 用户查询："地震对自然环境可能有哪些影响？"（只需要调用该工具）

    Parameters: None
    """

    try:
        await ctx.session.send_log_message("info", "开始进行图层信息获取")

        jsons = {"ExecuteTask": {"service": "GPSERVICE","version": "1.0.0","modelType": "ModelService","isSynchronization": True,
        "param": {
            "modelName": "layerMapping",
            "modelParam": []}}}
        response, call_time = call_api(url=gp_service, method="POST", json=jsons)
        call_api_logger.info(f"get_all_layers工具 调用layerMapping api 用时:{call_time}s")
        await ctx.session.send_log_message("info", "图层信息获取成功")
        result = json.loads(response.text)

        return Result.succ(data=json.loads(result["content"])["data"], map_type="layers").model_dump_json()
    except Exception as e:
        error_result = Result.failed(msg=f"查询图层信息失败: {str(e)}")
        return error_result.model_dump_json()


def get_ename(cnames: list):
    """
    查询，获取中文图层名对应的英文图层名称
    根据中文图层名称来查询，获取。
    Parameters:
    - cname: 中文图层的名称
    """



    enames = []
    for cname in cnames:
        jsons = {"ExecuteTask": {"service": "GPSERVICE", "version": "1.0.0", "modelType": "ModelService",
                                 "isSynchronization": True,
                                 "param": {
                                     "modelName": "queryMapping",
                                     "modelParam": [{"name": "cname", "value": cname}]}}}
        response, call_time = call_api(url=gp_service, method="POST", json=jsons)
        call_api_logger.info(f"调用queryMapping api 用时:{call_time}s")
        result = json.loads(response.text)
        enames.append(json.loads(result["content"])["data"][0]["ename"])
    return enames


@mcp.tool()
async def vec_layer_query(cnames: list, ctx: Context):
    """
    查询，获取中文图层名对应的矢量图层
    根据中文图层名称来查询，获取。
    Parameters:
    - cname: 中文图层的名称的列表
    """
    try:
        enames = get_ename(cnames)

        info = "，".join(cnames)
        data = {}
        for i, ename in enumerate(enames):
            jsons = {"ExecuteTask": {"service": "GPSERVICE", "version": "1.0.0", "modelType": "ModelService",
                                 "isSynchronization": True,
                                 "param": {
                                     "modelName": "queryGeoJson",
                                     "modelParam": [{"name":"layerName", "value":ename}]}}}
            response, call_time = call_api(url=gp_service, method="POST", json=jsons)
            call_api_logger.info(f"vec_layer_query工具 调用queryGeoJson api 用时:{call_time}s")
            result = json.loads(response.text)
            with open(f"{resource_path}/{ename}.json", "w") as f:
                f.write(json.dumps({ename: json.loads(result["content"])["data"]}, ensure_ascii=False, indent=2))
            data[f"{cnames[i]}"] = f"db://get_map_data/{ename}"
        await ctx.session.send_log_message("info", f"成功获取{info}图层数据")


        return Result.succ(data=data, msg=f"矢量图数据已成功获取", map_type="geojson").model_dump_json()
    except json.JSONDecodeError as e:
        name = "，".join(cnames)
        return Result.failed(msg=f"{name}数据在地理底图中未找到，请重新输入").model_dump_json()
    except Exception as e:
        return Result.failed(msg=f"查询图层矢量图工具调用失败: {str(e)}").model_dump_json()





@mcp.tool()
async def conflict_detection(cname1: str, cname2: str, ctx: Context):
    """
    叠加分析两个图层是否有冲突
    输入为两个图层中文名称

    Parameters:
    - cname1: 图层1的中文名
    - cname1: 图层2的中文名
    """
    try:
        # 分别获取cname1 和 cname2 的矢量图
        result = await vec_layer_query([cname1, cname2], ctx)
        uris = json.loads(result)["data"]
        if not uris:
            await ctx.session.send_log_message("info", f"地理底图中没有您想分析的数据图层，无法进行分析")
            return Result.failed(msg="地理底图中没有您想分析的数据图层，无法进行分析").model_dump_json()
        else:
            # 获取英文名
            enames = [v.split('/')[-1] for k, v in uris.items()]

        # 进行冲突分析
        await ctx.session.send_log_message("info", f"调用叠加分析模型，将{cname1},{cname2}图层数据输入，开始执行叠加分析模型")
        jsons = {"ExecuteTask": {"service": "GPSERVICE", "version": "1.0.0", "modelType": "ModelService",
                                 "isSynchronization": True,
                                 "param": {
                                     "modelName": "analysis",
                                     "modelParam": [{ "name": "layerName1", "value": enames[0], "paramType": None, "description": None },
                                                    { "name": "layerName2", "value": enames[1], "paramType": None, "description": None }]}}}
        response, call_time = call_api(url=gp_service, method="POST", json=jsons)
        call_api_logger.info(f"conflict_detection工具 调用analysis api 用时:{call_time}s")
        result = json.loads(response.text)

        # 写入resource
        with open(f"{resource_path}/{enames[0]}-{enames[1]}-conflict.json", "w") as f:
            f.write(json.dumps({f"{enames[0]}-{enames[1]}-conflict": json.loads(result["content"])["data"]}, ensure_ascii=False, indent=2))
        uris["conflict"] = f"db://get_map_data/{enames[0]}-{enames[1]}-conflict"

        await ctx.session.send_log_message("info", f"输出分析结果，生成分析结果图层")
        return Result.succ(data=uris, msg=f"冲突分析结果已完成", map_type="geojson").model_dump_json()
    except Exception as e:
        return Result.failed(msg=f"冲突分析工具调用失败: {str(e)}").model_dump_json()



#@mcp.tool()
async def division_positioning(question: str, ctx: Context):
    """
    对地点进行定位
    Parameters:
    - question: 完整的行政区划
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key="sk", base_url="http://192.168.42.63:4203/v1")
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": "请根据用户输入的行政区划输出最小一级的行政区划"
                                                   "注意：1.只需要输出最小一级的行政区划，不需要有多余的解释"
                                                    "2.根据用户的输入，直接取最小一级区划名称，用户输入中没有的行政区划不要凭空捏造"
                                                    "例如：用户输入：定位到北京市 输出：北京市"},
                      {"role": "user", "content": question}
                      ],
            temperature= 0.1,
            max_tokens= 512,
            stream=False,
            model="qwen3",
            extra_body={"chat_template_kwargs": {"enable_thinking": False}}
        )
        return Result.succ(data=response.choices[0].message.content, map_type="operation").model_dump_json()
    except Exception as e:
        return Result.failed(msg=f"获取最小一级的行政区划工具调用失败: {str(e)}").model_dump_json()



@mcp.tool()
async  def operate_layer(layer_name: str, action: str, ctx: Context):
    """
    关闭/打开/切换/定位图层
    Parameters:
    - question: 需要执行操作的图层名
    - action: 取值有：open，close，change，location
    """
    try:
        return Result.succ(data=layer_name, map_type=action).model_dump_json()
    except Exception as e:
        return Result.failed(msg=f"操作图层工具调用失败: {str(e)}").model_dump_json()




@mcp.tool()
async def point_buffer(coordinates: list, radius: int, ctx: Context):
    """
    根据经纬度坐标和半径进行缓冲分析

    Parameters:
    - coordinates: 经纬度坐标
    - radius：缓冲半径，单位为米
    """
    try:
        await ctx.session.send_log_message("info", f"调用单个要素缓冲服务")
        jsons = {"ExecuteTask": {"service": "GPSERVICE", "version": "1.0.0", "modelType": "ModelService",
                                 "isSynchronization": True,
                                 "param": {
                                     "modelName": "geojsonBuffer",
                                     "modelParam": [{ "name": "geojson", "value": {"type":"Feature", "geometry": {"type": 'Point', "coordinates": coordinates}}, "paramType": None, "description": None },
                                                    { "name": "radius", "value": radius, "paramType": None, "description": None }]}}}
        response, call_time = call_api(url=gp_service, method="POST", json=jsons)
        call_api_logger.info(f"single_element_buffer工具 调用geojsonBuffer api 用时:{call_time}s")
        result = json.loads(response.text)

        uri = f"point_buffer_{get_uuid()}"
        with open(f"{resource_path}/{uri}.json", "w") as f:
            f.write(json.dumps({f"{uri}": json.loads(result["content"])["data"]}, ensure_ascii=False, indent=2))
        await ctx.session.send_log_message("info", f"成功生成缓冲面")

        return Result.succ(data={"uri": f"db://get_map_data/{uri}"}, msg=f"单个要素缓冲已保存到resource", map_type="bufferPolygon").model_dump_json()
    except Exception as e:
        return Result.failed(msg=f"单个要素缓冲工具调用失败: {str(e)}").model_dump_json()


@mcp.tool()
async def line_or_polygon_buffer(uri: str, radius: int, ctx: Context):
    """
    根据矢量面的uri和半径进行缓冲分析

    Parameters:
    - uri: 矢量面的唯一资源标识
    - radius：缓冲半径，单位为米
    """
    try:
        # 根据uri获取geojson文件
        filename = uri.split("/")[-1]
        with open(f"{resource_path}/{filename}.json", 'r', encoding="utf-8") as f:
            geojson = json.load(f)
            geojson = json.loads(geojson[f'{filename}'][0]['textorfile'])
            [f.pop('properties') for f in geojson["features"]]

        await ctx.session.send_log_message("info", f"调用单个要素缓冲服务")
        jsons = {"ExecuteTask": {"service": "GPSERVICE", "version": "1.0.0", "modelType": "ModelService",
                                 "isSynchronization": True,
                                 "param": {
                                     "modelName": "geojsonBuffer",
                                     "modelParam": [{ "name": "geojson", "value": geojson},
                                                    { "name": "radius", "value": radius}]}}}
        response, call_time = call_api(url=gp_service, method="POST", json=jsons)
        call_api_logger.info(f"single_element_buffer工具 调用geojsonBuffer api 用时:{call_time}s")
        result = json.loads(response.text)

        uri = f"line_or_polygon_buffer_{get_uuid()}"
        with open(f"{resource_path}/{uri}.json", "w") as f:
            f.write(json.dumps({f"{uri}": json.loads(result["content"])["data"]}, ensure_ascii=False, indent=2))
        await ctx.session.send_log_message("info", f"成功生成缓冲面")

        return Result.succ(data={"uri": f"db://get_map_data/{uri}"}, msg=f"单个要素缓冲已保存到resource", map_type="bufferPolygon").model_dump_json()
    except Exception as e:
        return Result.failed(msg=f"单个要素缓冲工具调用失败: {str(e)}").model_dump_json()



@mcp.tool()
async def layer_buffer(name1: str, name2: str, radius: int, ctx: Context):
    """
    给定两个中文实体名（图层名）以及半径，先使用一个实体（图层名）和半径进行缓冲然后和另外一个实体（图层）叠加分析
    Parameters:
    - name1: 中文实体名1（图层名）
    - name2:中文实体名2（图层名）
    - radius：半径，单位：米
    """
    try:
        # 分别获取name1 和 name2 的矢量图
        result = await vec_layer_query([name1, name2], ctx)
        uris = json.loads(result)["data"]
        if not uris:
            await ctx.session.send_log_message("info", f"地理底图中没有您想分析的数据图层，无法进行分析")
            return Result.failed(msg="地理底图中没有您想分析的数据图层，无法进行分析").model_dump_json()

        enames = get_ename([name1, name2])

        await ctx.session.send_log_message("info", f"调用缓冲分析模型，将{name1},{name2}图层数据输入，开始执行缓冲分析模型")
        jsons = {"ExecuteTask": {"service": "GPSERVICE", "version": "1.0.0", "modelType": "ModelService",
                                 "isSynchronization": True,
                                 "param": {
                                     "modelName": "layerBufferAnalysis",
                                     "modelParam": [{ "name": "layerName1", "value": enames[0]},
                                                    { "name": "layerName2", "value": enames[1]},
                                                    { "name": "radius", "value": radius} ]}}}
        response, call_time = call_api(url=gp_service, method="POST", json=jsons)
        call_api_logger.info(f"BufferAnalysis工具 调用layerBufferAnalysis api 用时:{call_time}s")
        result = json.loads(response.text)

        with open(f"{resource_path}/{enames[0]}-{enames[1]}-layer_buffer.json", "w") as f:
            f.write(json.dumps({f"{enames[0]}-{enames[1]}-layer_buffer": json.loads(result["content"])["data"]}, ensure_ascii=False, indent=2))
        uris["conflict"] = f"db://get_map_data/{enames[0]}-{enames[1]}-layer_buffer"
        await ctx.session.send_log_message("info", f"输出分析结果，生成分析结果图层")

        return Result.succ(data=uris, msg=f"图层缓冲结果已保存", map_type="geojson").model_dump_json()
    except Exception as e:
        return Result.failed(msg=f"图层缓冲服务工具调用失败: {str(e)}").model_dump_json()


@mcp.tool()
async def geojson_layer_overlay(uri: str, names: list, ctx: Context):
    """
    geojson和图层进行叠加分析

    Parameters:
    - uri: geojson文件的唯一标识
    - names：图层的中文名列表
    """
    try:
        # 根据uri获取geojson文件
        filename = uri.split("/")[-1]
        with open(f"{resource_path}/{filename}.json", 'r', encoding="utf-8") as f:
            geojson = json.load(f)
            geojson = json.loads(geojson[f'{filename}'][0]['textorfile'])
            [f.pop('properties') for f in geojson["features"]]

        # 获取对应的英文名
        enames = get_ename(cnames=names)

        uris = {}
        for i, ename in enumerate(enames):
            await ctx.session.send_log_message("info", f"调用叠加分析服务, 将矢量面和{names[i]}图层数据输入，开始执行叠加分析模型")
            jsons = {"ExecuteTask": {"service": "GPSERVICE", "version": "1.0.0", "modelType": "ModelService",
                                     "isSynchronization": True,
                                     "param": {
                                         "modelName": "geoJsonLayerOverlay",
                                         "modelParam": [{ "name": "geojson", "value": {"type": "FeatureCollection", "features": geojson["features"]}},
                                                        { "name": "layerName", "value": ename}]}}}
            response, call_time = call_api(url=gp_service, method="POST", json=jsons)
            call_api_logger.info(f"superimposed_analysis工具 调用geojsonBuffer api 用时:{call_time}s")
            result = json.loads(response.text)

            with open(f"{resource_path}/geojson_{ename}_overlay.json", "w") as f:
                f.write(json.dumps({f"geojson_{ename}_overlay": json.loads(result["content"])["data"]}, ensure_ascii=False, indent=2))
            await ctx.session.send_log_message("info", f"输出分析结果，生成分析结果图层")
            uris[f"{names[i]}"] = f"db://get_map_data/geojson_{ename}_overlay"

        return Result.succ(data=uris, msg=f"叠加分析结果已完成", map_type="overlayList").model_dump_json()
    except Exception as e:
        return Result.failed(msg=f"叠加分析工具调用失败: {str(e)}").model_dump_json()


@mcp.tool()
async def buffer(name: str, radius: int, ctx: Context):
    """
    给定一个实体名(图层)和半径进行缓冲分析

    Parameters:
    - name：图层的中文名
    - radius: 缓冲半径，单位：米
    """
    try:
        # 获取矢量图
        result = await vec_layer_query([name], ctx)
        uris = json.loads(result)["data"]
        if not uris:
            await ctx.session.send_log_message("info", f"地理底图中没有您想分析的数据图层，无法进行分析")
            return Result.failed(msg="地理底图中没有您想分析的数据图层，无法进行分析").model_dump_json()
        else:
            # 获取英文名
            ename = [v.split('/')[-1] for k, v in uris.items()]


        await ctx.session.send_log_message("info", f"调用缓冲分析服务, 将{name}图层数据输入，开始执行缓冲分析模型")
        jsons = {"ExecuteTask": {"service": "GPSERVICE", "version": "1.0.0", "modelType": "ModelService",
                                     "isSynchronization": True,
                                     "param": {
                                         "modelName": "layerBuffer",
                                         "modelParam": [{"name":"layerName", "value":ename[0]},
                                                        {"name":"radius", "value":radius}]}}}
        response, call_time = call_api(url=gp_service, method="POST", json=jsons)
        call_api_logger.info(f"superimposed_analysis工具 调用geojsonBuffer api 用时:{call_time}s")
        result = json.loads(response.text)

        with open(f"{resource_path}/{ename[0]}_buffer.json", "w") as f:
            f.write(json.dumps({f"{ename[0]}_buffer": json.loads(result["content"])["data"]}, ensure_ascii=False, indent=2))
        await ctx.session.send_log_message("info", f"输出分析结果，生成分析结果图层")
        uris["layerbuffer"] = f"db://get_map_data/{ename[0]}_buffer"

        return Result.succ(data=uris, msg=f"缓冲分析结果已完成", map_type="bufferPolygon").model_dump_json()
    except Exception as e:
        return Result.failed(msg=f"叠加分析工具调用失败: {str(e)}").model_dump_json()


#@mcp.tool()
async def geojson_buffer_layer(uri: str, names: list, radius: int, ctx: Context):
    """
    给定一个geojson的uri和中文实体名列表（图层名列表）以及半径，先使用geojson数据和半径进行缓冲然后和中文名实体列表（中文图层列表）叠加分析
    Parameters:
    - uri: geojson的唯一资源标识符
    - names:图层的中文名列表（中文图层名列表）
    - radius：半径，单位：米
    """
    try:
        # 根据uri获取geojson文件
        filename = uri.split("/")[-1]
        with open(f"{resource_path}/{filename}.json", 'r', encoding="utf-8") as f:
            geojson = json.load(f)
            geojson = json.loads(geojson[f'{filename}'][0]['textorfile'])
            [f.pop('properties') for f in geojson["features"]]

        # 获取对应的英文名
        enames = get_ename(cnames=names)

        uris = {}
        for i, ename in enumerate(enames):
            await ctx.session.send_log_message("info",
                                               f"调用缓冲叠加分析服务, 将缓冲面和{names[i]}图层数据输入，开始执行叠加分析模型")
            jsons = {"ExecuteTask": {"service": "GPSERVICE", "version": "1.0.0", "modelType": "ModelService",
                                     "isSynchronization": True,
                                     "param": {
                                         "modelName": "bufferAnalysis",
                                         "modelParam": [{"name": "geojson", "value": {"type": "FeatureCollection",
                                                                                      "features": geojson["features"]}},
                                                        {"name": "radius", "value": radius},
                                                        {"name": "layerName", "value": ename}]}}}
            response, call_time = call_api(url=gp_service, method="POST", json=jsons)
            call_api_logger.info(f"geojson_buffer_layer 调用bufferAnalysis api 用时:{call_time}s")
            result = json.loads(response.text)

            with open(f"{resource_path}/geojson_{ename}_bufferoverlay.json", "w") as f:
                f.write(
                    json.dumps({f"geojson_{ename}_bufferoverlay": json.loads(result["content"])["data"]}, ensure_ascii=False,
                               indent=2))
            await ctx.session.send_log_message("info", f"输出分析结果，生成分析结果图层")
            uris[f"{names[i]}"] = f"db://get_map_data/geojson_{ename}_bufferoverlay"

        return Result.succ(data=uris, msg=f"缓冲叠加分析结果已完成", map_type="overlayList").model_dump_json()
    except Exception as e:
        return Result.failed(msg=f"缓冲叠加分析工具调用失败: {str(e)}").model_dump_json()


# 创建 Starlette 应用
def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """创建一个支持 SSE 的 Starlette 应用，用于运行 MCP 服务器。"""
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
    async def handle_healthy(request: Request):
        return JSONResponse({"status": "healthy"})


    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/ping", endpoint=handle_healthy),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


# 主程序入口
if __name__ == "__main__":
    mcp_server = mcp._mcp_server

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='运行基于 SSE 的 MCP 取模服务器')
    parser.add_argument('--host', default='0.0.0.0', help='绑定的主机地址')
    parser.add_argument('--port', type=int, default=18084, help='监听端口')
    args = parser.parse_args()

    # 创建并运行 Starlette 应用
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host=args.host, port=args.port)