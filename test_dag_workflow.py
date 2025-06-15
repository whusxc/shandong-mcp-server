#!/usr/bin/env python3
"""
DAG批处理工作流测试脚本
测试新增的DAG批处理功能
"""

import asyncio
import json
import logging
from pathlib import Path

# 尝试导入MCP相关模块
try:
    from mcp.server.fastmcp import Context
    # 导入我们的服务器
    from shandong_mcp_server_enhanced import (
        execute_code_to_dag,
        submit_batch_task,
        query_task_status,
        execute_dag_workflow,
        DEFAULT_USER_ID,
        DEFAULT_USERNAME
    )
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"MCP模块导入失败: {e}")
    MCP_AVAILABLE = False

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dag_test")

# 测试用的OGE代码
TEST_OGE_CODE = """import oge

oge.initialize()
service = oge.Service()

dem = service.getCoverage(coverageID="ASTGTM_N28E056", productID="ASTER_GDEM_DEM30")
aspect = service.getProcess("Coverage.aspect").execute(dem, 1)

vis_params = {"min": -1, "max": 1, "palette": ["#808080", "#949494", "#a9a9a9", "#bdbebd", "#d3d3d3","#e9e9e9"]}
aspect.styles(vis_params).export("aspect")
oge.mapclient.centerMap(56.25, 28.40, 11)"""

async def test_code_to_dag():
    """测试代码转DAG功能"""
    print("\n=== 测试1: 代码转DAG ===")
    
    try:
        result_json = await execute_code_to_dag(
            code=TEST_OGE_CODE,
            user_id=DEFAULT_USER_ID,
            sample_name="DEM数据坡向计算批处理测试.py"
        )
        
        result = json.loads(result_json)
        print(f"执行结果: {result.get('success')}")
        print(f"消息: {result.get('msg')}")
        
        if result.get("success"):
            data = result.get("data", {})
            dag_ids = data.get("dag_ids", [])
            print(f"生成的DAG数量: {len(dag_ids)}")
            print(f"DAG IDs: {dag_ids}")
            
            if dag_ids:
                return dag_ids[0]  # 返回第一个DAG ID用于后续测试
        
        return None
        
    except Exception as e:
        print(f"测试失败: {e}")
        return None

async def test_submit_task(dag_id: str):
    """测试提交批处理任务"""
    print(f"\n=== 测试2: 提交批处理任务 (DAG: {dag_id}) ===")
    
    try:
        result_json = await submit_batch_task(
            dag_id=dag_id,
            task_name="test_dag_task",
            filename="test_aspect_output",
            script=TEST_OGE_CODE
        )
        
        result = json.loads(result_json)
        print(f"执行结果: {result.get('success')}")
        print(f"消息: {result.get('msg')}")
        
        if result.get("success"):
            data = result.get("data", {})
            print(f"任务ID: {data.get('task_id')}")
            print(f"任务状态: {data.get('state')}")
            print(f"批处理会话ID: {data.get('batch_session_id')}")
            return True
        
        return False
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

async def test_query_status(dag_id: str):
    """测试查询任务状态"""
    print(f"\n=== 测试3: 查询任务状态 (DAG: {dag_id}) ===")
    
    try:
        result_json = await query_task_status(dag_id=dag_id)
        
        result = json.loads(result_json)
        print(f"执行结果: {result.get('success')}")
        print(f"消息: {result.get('msg')}")
        
        if result.get("success"):
            data = result.get("data", {})
            print(f"任务状态: {data.get('status')}")
            print(f"是否完成: {data.get('is_completed')}")
            print(f"是否运行中: {data.get('is_running')}")
            print(f"是否失败: {data.get('is_failed')}")
            return True
        
        return False
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

async def test_complete_workflow():
    """测试完整的DAG工作流"""
    print(f"\n=== 测试4: 完整DAG工作流 ===")
    
    try:
        result_json = await execute_dag_workflow(
            code=TEST_OGE_CODE,
            sample_name="完整工作流测试.py",
            task_name="workflow_test_task",
            filename="workflow_test_output",
            auto_submit=True,
            wait_for_completion=False  # 不等待完成，避免测试时间过长
        )
        
        result = json.loads(result_json)
        print(f"执行结果: {result.get('success')}")
        print(f"消息: {result.get('msg')}")
        
        if result.get("success"):
            data = result.get("data", {})
            print(f"最终状态: {data.get('final_status')}")
            print(f"DAG IDs: {data.get('dag_ids')}")
            
            steps = data.get("steps", [])
            print(f"执行步骤数: {len(steps)}")
            for step in steps:
                print(f"  步骤{step.get('step')}: {step.get('name')} - {'成功' if step.get('success') else '失败'}")
            
            return True
        
        return False
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("开始DAG批处理功能测试...")
    
    if not MCP_AVAILABLE:
        print("错误: MCP模块不可用，无法运行测试")
        return
    
    test_results = []
    
    # 测试1: 代码转DAG
    dag_id = await test_code_to_dag()
    test_results.append(("代码转DAG", dag_id is not None))
    
    if dag_id:
        # 测试2: 提交任务
        submit_success = await test_submit_task(dag_id)
        test_results.append(("提交批处理任务", submit_success))
        
        # 测试3: 查询状态
        status_success = await test_query_status(dag_id)
        test_results.append(("查询任务状态", status_success))
    else:
        test_results.append(("提交批处理任务", False))
        test_results.append(("查询任务状态", False))
    
    # 测试4: 完整工作流
    workflow_success = await test_complete_workflow()
    test_results.append(("完整DAG工作流", workflow_success))
    
    # 输出测试总结
    print(f"\n=== 测试总结 ===")
    success_count = 0
    total_count = len(test_results)
    
    for test_name, success in test_results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n总体结果: {success_count}/{total_count} 项测试通过")
    
    if success_count == total_count:
        print("🎉 所有DAG批处理功能测试通过！")
    else:
        print("⚠️  部分测试失败，请检查网络连接和API配置")

def main():
    """主函数"""
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试执行出错: {e}")

if __name__ == "__main__":
    main() 