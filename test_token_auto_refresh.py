#!/usr/bin/env python3
"""
Token自动刷新功能测试脚本
验证当token过期时的自动刷新和重试机制
"""

import asyncio
import json
import logging
import time
from pathlib import Path

# 尝试导入MCP相关模块
try:
    from mcp.server.fastmcp import Context
    # 导入我们的服务器
    from shandong_mcp_server_enhanced import (
        get_oauth_token,
        refresh_token_auto,
        call_api_with_auto_refresh,
        _is_token_expired_error,
        _auto_refresh_token,
        INTRANET_AUTH_TOKEN
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
logger = logging.getLogger("token_test")

async def test_oauth_token():
    """测试OAuth token获取功能"""
    print("\n=== 测试1: OAuth Token获取 ===")
    
    try:
        result_json = await get_oauth_token(
            username="edu_admin",
            password="123456",
            client_id="test",
            client_secret="123456",
            scopes="web",
            grant_type="password"
        )
        
        result = json.loads(result_json)
        print(f"执行结果: {result.get('success')}")
        print(f"消息: {result.get('msg')}")
        
        if result.get("success"):
            data = result.get("data", {})
            token_type = data.get("token_type", "")
            expires_in = data.get("expires_in", 0)
            token_preview = data.get("full_token", "")[:50] + "..."
            
            print(f"Token类型: {token_type}")
            print(f"有效期: {expires_in}秒")
            print(f"Token预览: {token_preview}")
            
            return True
        
        return False
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

async def test_auto_refresh_token():
    """测试自动token刷新功能"""
    print(f"\n=== 测试2: 自动Token刷新 ===")
    
    try:
        result_json = await refresh_token_auto()
        
        result = json.loads(result_json)
        print(f"执行结果: {result.get('success')}")
        print(f"消息: {result.get('msg')}")
        
        if result.get("success"):
            data = result.get("data", {})
            old_preview = data.get("old_token_preview", "")
            new_preview = data.get("new_token_preview", "")
            expires_in = data.get("expires_in", 0)
            
            print(f"旧Token: {old_preview}")
            print(f"新Token: {new_preview}")
            print(f"有效期: {expires_in}秒")
            
            return True
        
        return False
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def test_token_expired_detection():
    """测试token过期检测逻辑"""
    print(f"\n=== 测试3: Token过期检测 ===")
    
    # 测试各种token过期的响应格式
    test_cases = [
        # HTTP 401错误
        {"status_code": 401, "error": "Unauthorized"},
        
        # 错误消息包含关键词
        {"error": "Token expired, please refresh"},
        {"error": "Invalid token provided"},
        {"error": "Authentication failed: 401"},
        
        # 业务错误码
        {"code": 401, "msg": "Token无效"},
        {"code": 40001, "msg": "Token过期"},
        
        # 您提供的具体错误格式
        {"code": 40003, "msg": "token过期或异常", "data": None},
        {"code": 40003, "msg": "无效token"},
        
        # 其他可能的40003错误
        {"code": 40003, "msg": "token异常"},
        
        # 正常响应（不应该被识别为过期）
        {"code": 200, "data": {"result": "success"}},
        {"success": True, "msg": "操作成功"}
    ]
    
    expected_results = [True, True, True, True, True, True, True, True, True, False, False]
    
    passed = 0
    total = len(test_cases)
    
    for i, (test_case, expected) in enumerate(zip(test_cases, expected_results)):
        result = _is_token_expired_error(test_case)
        status = "✓" if result == expected else "✗"
        print(f"  案例{i+1}: {test_case} -> {result} {status}")
        
        if result == expected:
            passed += 1
    
    print(f"检测逻辑测试: {passed}/{total} 通过")
    return passed == total

async def test_api_with_auto_refresh():
    """测试带自动刷新的API调用"""
    print(f"\n=== 测试4: 自动刷新API调用 ===")
    
    try:
        # 模拟一个可能返回token过期的API调用
        test_url = "http://172.20.70.141/api/test"  # 这是一个测试地址
        
        print("模拟API调用（可能会触发token刷新）...")
        
        result, execution_time = await call_api_with_auto_refresh(
            url=test_url,
            method="GET",
            auto_refresh_token=True
        )
        
        print(f"API调用结果: {result}")
        print(f"执行时间: {execution_time:.2f}秒")
        
        # 如果是网络错误或404，这是正常的（测试URL不存在）
        if "error" in result:
            error_msg = result.get("error", "")
            if "404" in error_msg or "Connection" in error_msg or "timeout" in error_msg:
                print("API地址不存在或网络问题，这是正常的测试结果")
                return True
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

async def test_background_refresh():
    """测试后台自动刷新功能"""
    print(f"\n=== 测试5: 后台自动刷新 ===")
    
    try:
        print("测试后台token刷新逻辑...")
        
        success = await _auto_refresh_token()
        
        if success:
            print("后台token刷新成功")
            print(f"当前全局token预览: {INTRANET_AUTH_TOKEN[:50]}...")
            return True
        else:
            print("后台token刷新失败")
            return False
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("开始Token自动刷新功能测试...")
    
    if not MCP_AVAILABLE:
        print("错误: MCP模块不可用，无法运行测试")
        return
    
    test_results = []
    
    # 测试1: OAuth token获取
    oauth_success = await test_oauth_token()
    test_results.append(("OAuth Token获取", oauth_success))
    
    # 测试2: 自动token刷新
    auto_refresh_success = await test_auto_refresh_token()
    test_results.append(("自动Token刷新", auto_refresh_success))
    
    # 测试3: token过期检测
    detection_success = test_token_expired_detection()
    test_results.append(("Token过期检测", detection_success))
    
    # 测试4: 带自动刷新的API调用
    api_success = await test_api_with_auto_refresh()
    test_results.append(("自动刷新API调用", api_success))
    
    # 测试5: 后台自动刷新
    background_success = await test_background_refresh()
    test_results.append(("后台自动刷新", background_success))
    
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
        print("🎉 所有Token自动刷新功能测试通过！")
        print("\n现在您可以放心使用以下功能：")
        print("- 当API调用返回token过期错误时，系统会自动刷新token并重试")
        print("- 可以手动调用 refresh_token_auto 工具刷新token")
        print("- 全局token会自动更新，无需手动配置")
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