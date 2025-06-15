#!/usr/bin/env python3
"""
简单的API连接测试
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, Optional

# API配置
BASE_URL = "http://172.20.70.142:16555"
PROCESS_API = f"{BASE_URL}/gateway/computation-api/process"
STATUS_API = f"{BASE_URL}/gateway/asset/algorithm-processing-result/detail"
EXECUTECODE_API = f"{BASE_URL}/gateway/oge-dag-22/executeCode"
EXECUTEDAG_API = f"{BASE_URL}/gateway/oge-dag-22/executeDag"


# Token
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjMyNCwidXNlcl9uYW1lIjoiZWR1X2FkbWluIiwic2NvcGUiOlsid2ViIl0sImV4cCI6MTc0OTkwNjkwMiwidXVpZCI6ImY5NTBjZmYyLTA3YzgtNDYxYS05YzI0LTkxNjJkNTllMmVmNiIsImF1dGhvcml0aWVzIjpbIkFETUlOSVNUUkFUT1JTIl0sImp0aSI6IkxQbjJQTThlRlpBRDhUNFBxN2U3SWlRdmRGQSIsImNsaWVudF9pZCI6InRlc3QiLCJ1c2VybmFtZSI6ImVkdV9hZG1pbiJ9.jFepdzkcDDlcH0v3Z_Ge35vbiTB3RVt8OQsHJ0o6qEU"
TIMEOUT = 120

async def call_api(
        algorithm_name: str,
        algorithm_args: Dict[str, Any],
        timeout: int = TIMEOUT
    ) -> Dict[str, Any]:
        """
        直接调用OGE API
        
        Args:
            algorithm_name: 算法名称
            algorithm_args: 算法参数
            timeout: 超时时间
            
        Returns:
            API响应结果
        """
        # 按照OGE API格式构建请求体
        payload = {
            "name": algorithm_name,
            "args": algorithm_args,
            "dockerImageSource":"DOCKER_HUB"
        }
        
        print(f"🚀 调用算法: {algorithm_name}")
        print(f"📝 请求参数: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        print(f"🌐 API地址: {BASE_URL}")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    PROCESS_API,
                    json=payload,
                    headers={"Content-Type": "application/json","Authorization":AUTH_TOKEN}
                )
                
                execution_time = time.time() - start_time
                
                print(f"⏱️  执行时间: {execution_time:.2f}秒")
                print(f"📊 HTTP状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 调用成功!")
                    print(f"📄 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "data": result,
                        "execution_time": execution_time,
                        "algorithm": algorithm_name
                    }
                else:
                    print(f"❌ 调用失败!")
                    print(f"📄 错误内容: {response.text}")
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.text,
                        "execution_time": execution_time,
                        "algorithm": algorithm_name
                    }
                    
        except httpx.TimeoutException:
            print(f"⏰ 请求超时 (>{timeout}秒)")
            return {
                "success": False,
                "error": "请求超时",
                "timeout": timeout,
                "algorithm": algorithm_name
            }
            
        except httpx.NetworkError as e:
            print(f"🌐 网络错误: {str(e)}")
            return {
                "success": False,
                "error": f"网络错误: {str(e)}",
                "algorithm": algorithm_name
            }
            
        except Exception as e:
            print(f"💥 未知错误: {str(e)}")
            return {
                "success": False,
                "error": f"未知错误: {str(e)}",
                "algorithm": algorithm_name
            }


async def test_coverage_aspect():
        """测试坡向分析 - 基于您提供的示例"""
        print("=" * 60)
        print("🧪 测试1: Coverage.aspect (坡向分析)")
        print("=" * 60)
        
        result = await call_api(
            algorithm_name="Coverage.aspect",
            algorithm_args={
                "coverage": {
                    "type": "Coverage",
                    "pretreatment": True,
                    "preParams": {
                        "bbox": [
                            110.062408,
                            19.317623,
                            110.413971,
                            19.500253
                        ]
                    },
                    "value": [
                        "Platform:Product:ASTER_GDEM_DEM30"
                    ]
                },
                "radius": 1
            },
        )
        return result

async def test_connection():
    """测试基础连接"""
    print("🔍 测试基础连接...")
    
    async with httpx.AsyncClient(timeout=300) as client:
        try:
            response = await client.get(BASE_URL)
            print(f"✅ 连接成功! 状态码: {response.status_code}")
            print(f"📥 响应内容: {response.text[:200]}...")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {type(e).__name__}: {str(e)}")
            return False

async def test_auth():
    """测试认证"""
    print("\n🔐 测试认证...")
    
    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # 测试状态查询API
            response = await client.get(
                STATUS_API,
                headers=headers,
                params={"processId": "test123"}
            )
            print(f"📥 认证测试状态码: {response.status_code}")
            print(f"📥 响应内容: {response.text}")
            
            if response.status_code == 401:
                print("❌ 认证失败!")
                return False
            elif response.status_code == 404:
                print("✅ 认证成功! (404是因为processId不存在)")
                return True
            else:
                print(f"✅ 认证可能成功 (状态码: {response.status_code})")
                return True
                
        except Exception as e:
            print(f"❌ 认证测试失败: {type(e).__name__}: {str(e)}")
            return False

async def test_simple_api():
    """测试简单API调用"""
    print("\n🧪 测试简单API调用...")
    
    tests = [
            ("坡向分析", test_coverage_aspect)
        ]
    results = []
    for test_name, test_func in tests:
            print(f"\n🔄 执行测试: {test_name}")
            try:
                result = await test_func()
                results.append({
                    "test_name": test_name,
                    "result": result
                })
                
                if result.get("success"):
                    print(f"✅ {test_name} - 成功")
                else:
                    print(f"❌ {test_name} - 失败")
                    
            except Exception as e:
                print(e)
                print(f"💥 {test_name} - 异常: {str(e)}")
                results.append({
                    "test_name": test_name,
                    "result": {"success": False, "error": str(e)}
                })
            
            print("-" * 40)
            await asyncio.sleep(1)  # 避免请求过于频繁

async def main():
    print("🚀 简单API测试")
    print("=" * 40)
    
    # 步骤1: 测试连接
    if not await test_connection():
        print("❌ 基础连接失败，停止测试")
        return
    
    # 步骤2: 测试认证
    if not await test_auth():
        print("❌ 认证失败，停止测试")
        return
    
    # 步骤3: 测试API
    await test_simple_api()

if __name__ == "__main__":
    asyncio.run(main()) 