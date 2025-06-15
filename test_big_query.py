#!/usr/bin/env python3
"""
测试大数据查询工具
"""

import asyncio
from shandong_mcp_server_enhanced import run_big_query

async def test_big_query():
    """测试大数据查询工具"""
    print("🔍 测试大数据查询工具...")
    
    # 基于您提供的API调用信息构建测试查询
    test_query = "SELECT * FROM shp_guotubiangeng WHERE DLMC IN ('耕地', '水稻地', '水田')"
    
    print(f"📝 测试查询: {test_query}")
    print()
    
    try:
        print("🚀 开始执行查询...")
        result_json = await run_big_query(
            query=test_query,
            geometry_column="geom"
        )
        
        print("✅ 查询执行完成")
        print(f"📊 结果: {result_json[:500]}...")  # 只显示前500个字符
        
    except Exception as e:
        print(f"❌ 查询执行失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_big_query()) 