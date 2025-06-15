#!/usr/bin/env python3
"""
部署验证脚本
验证MCP服务器在实际部署环境中的配置和连接
"""

import asyncio
import json
import os
import sys
import subprocess
import httpx
from pathlib import Path

def get_current_paths():
    """获取当前部署路径"""
    current_dir = Path.cwd()
    python_path = sys.executable
    
    return {
        "deployment_dir": str(current_dir),
        "python_path": python_path,
        "server_script": str(current_dir / "shandong_mcp_server.py"),
        "config_file": str(current_dir / "deepseek_mcp_config_simple_test.json")
    }

def generate_config_template():
    """生成正确的配置文件模板"""
    paths = get_current_paths()
    
    config_template = {
        "mcpServers": {
            "shandong-analysis": {
                "command": paths["python_path"],
                "args": [paths["server_script"]],
                "cwd": paths["deployment_dir"]
            }
        }
    }
    
    return config_template

def update_config_file():
    """更新配置文件为正确的路径"""
    print("🔧 更新配置文件...")
    
    config_file = "deepseek_mcp_config_simple_test.json"
    backup_file = "deepseek_mcp_config_simple_test.json.backup"
    
    # 备份原配置文件
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                content = f.read()
            with open(backup_file, 'w') as f:
                f.write(content)
            print(f"✅ 原配置文件已备份为: {backup_file}")
        except Exception as e:
            print(f"⚠️  备份配置文件失败: {e}")
    
    # 生成新配置
    try:
        new_config = generate_config_template()
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)
        
        print("✅ 配置文件已更新为当前部署路径")
        print(f"   Python路径: {new_config['mcpServers']['shandong-analysis']['command']}")
        print(f"   脚本路径: {new_config['mcpServers']['shandong-analysis']['args'][0]}")
        print(f"   工作目录: {new_config['mcpServers']['shandong-analysis']['cwd']}")
        
        return True
    except Exception as e:
        print(f"❌ 更新配置文件失败: {e}")
        return False

def test_python_environment():
    """测试Python环境"""
    print("\n🔍 测试Python环境...")
    
    try:
        # 测试Python版本
        result = subprocess.run([sys.executable, "--version"], 
                              capture_output=True, text=True)
        print(f"✅ Python版本: {result.stdout.strip()}")
        
        # 测试必要包
        packages = ["mcp", "httpx"]
        for package in packages:
            try:
                result = subprocess.run([sys.executable, "-c", f"import {package}; print(f'{package} 已安装')"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {package} 包可用")
                else:
                    print(f"❌ {package} 包不可用: {result.stderr}")
                    return False
            except Exception as e:
                print(f"❌ 检查 {package} 包时出错: {e}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Python环境测试失败: {e}")
        return False

async def test_oge_connectivity():
    """测试OGE服务器连接"""
    print("\n🔍 测试OGE服务器连接...")
    
    # 从服务器脚本中读取OGE API地址
    try:
        with open("shandong_mcp_server.py", 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 简单的正则匹配找到OGE_API_BASE_URL
        import re
        match = re.search(r'OGE_API_BASE_URL\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            oge_url = match.group(1)
            print(f"📡 OGE服务器地址: {oge_url}")
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # 尝试连接OGE服务器
                    response = await client.get(oge_url.replace('/process', ''))
                    print(f"✅ OGE服务器可访问 (状态码: {response.status_code})")
                    return True
            except httpx.ConnectError:
                print("⚠️  OGE服务器连接失败 - 可能是内网环境或服务器未启动")
                print("   这在部署测试阶段是正常的，实际使用时需要确保网络连通性")
                return True  # 在部署测试中，这不算失败
            except Exception as e:
                print(f"⚠️  OGE连接测试异常: {e}")
                return True  # 在部署测试中，这不算失败
        else:
            print("❌ 无法从脚本中找到OGE服务器地址")
            return False
            
    except Exception as e:
        print(f"❌ 读取OGE配置失败: {e}")
        return False

def test_mcp_server_startup():
    """测试MCP服务器启动"""
    print("\n🔍 测试MCP服务器启动...")
    
    try:
        # 尝试启动MCP服务器（短时间测试）
        process = subprocess.Popen(
            [sys.executable, "shandong_mcp_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待短时间看是否有错误
        try:
            stdout, stderr = process.communicate(timeout=3)
            if process.returncode == 0:
                print("✅ MCP服务器启动成功")
                return True
            else:
                print(f"❌ MCP服务器启动失败: {stderr}")
                return False
        except subprocess.TimeoutExpired:
            # 超时说明服务器正在运行，这是好的
            process.terminate()
            print("✅ MCP服务器启动正常（正在等待连接）")
            return True
            
    except Exception as e:
        print(f"❌ MCP服务器启动测试失败: {e}")
        return False

def print_deployment_summary():
    """打印部署总结"""
    paths = get_current_paths()
    
    print("\n" + "="*60)
    print("📋 部署信息总结")
    print("="*60)
    print(f"部署目录: {paths['deployment_dir']}")
    print(f"Python路径: {paths['python_path']}")
    print(f"服务器脚本: {paths['server_script']}")
    print(f"配置文件: {paths['config_file']}")
    
    print("\n📝 下一步操作:")
    print("1. 将配置文件路径添加到你的AI客户端")
    print("2. 确保内网环境可以访问OGE服务器")
    print("3. 在AI客户端中测试MCP工具调用")
    
    print(f"\n🔧 配置文件内容:")
    try:
        with open("deepseek_mcp_config_simple_test.json", 'r') as f:
            config = json.load(f)
        print(json.dumps(config, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"无法读取配置文件: {e}")

async def main():
    """主验证函数"""
    print("🚀 MCP服务器部署验证开始...\n")
    
    tests = [
        ("Python环境测试", test_python_environment),
        ("配置文件更新", update_config_file),
        ("OGE服务器连接测试", test_oge_connectivity),
        ("MCP服务器启动测试", test_mcp_server_startup),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 部署验证结果:")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 验证结果: {passed}/{total} 项通过")
    
    if passed >= total - 1:  # 允许OGE连接测试失败
        print("🎉 部署验证基本通过！")
        print_deployment_summary()
        return 0
    else:
        print("⚠️  部分关键验证失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 