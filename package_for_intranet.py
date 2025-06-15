#!/usr/bin/env python3
"""
MCP服务器内网部署打包脚本
"""

import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

def create_deployment_package():
    """创建内网部署包"""
    
    # 创建打包目录
    package_name = f"shandong_mcp_intranet_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    package_dir = Path(package_name)
    
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    package_dir.mkdir()
    print(f"📦 创建打包目录: {package_dir}")
    
    # 需要打包的文件列表
    files_to_package = {
        # 核心服务器文件
        "shandong_mcp_server.py": "原版MCP服务器",
        "shandong_mcp_server_enhanced.py": "增强版MCP服务器",
        
        # 依赖文件
        "requirements.txt": "基础依赖",
        "requirements_enhanced.txt": "增强版依赖",
        
        # 配置文件
        "deepseek_mcp_config_simple_test.json": "MCP客户端配置示例",
        
        # 测试文件
        "simple_test(1).py": "坡向分析测试脚本",
        "test_mcp_server.py": "MCP服务器测试脚本",
        
        # 文档文件
        "README.md": "项目说明",
        "ENHANCED_USAGE.md": "增强版使用指南",
        "SHANDONG_MCP_USAGE_GUIDE.md": "山东MCP使用指南",
        "DEPLOYMENT_CHECKLIST.md": "部署检查清单",
        "OGE_API_FORMAT_FIXES.md": "OGE API格式说明",
        
        # 业务文件
        "shandong.txt": "山东耕地分析工作流",
        "demo_server2.py": "参考MCP模板"
    }
    
    # 复制文件
    copied_files = []
    missing_files = []
    
    for filename, description in files_to_package.items():
        source_file = Path(filename)
        if source_file.exists():
            dest_file = package_dir / filename
            shutil.copy2(source_file, dest_file)
            copied_files.append(f"✅ {filename} - {description}")
        else:
            missing_files.append(f"❌ {filename} - {description} (文件不存在)")
    
    # 创建部署说明文件
    deploy_readme = package_dir / "DEPLOY_README.md"
    with open(deploy_readme, 'w', encoding='utf-8') as f:
        f.write(f"""# 山东耕地流出分析MCP服务器 - 内网部署包

## 📦 打包信息
- 打包时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 打包版本: 内网测试版
- 包含文件: {len(copied_files)} 个

## 🚀 快速部署

### 1. 环境准备
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\\Scripts\\activate  # Windows

# 安装依赖
pip install -r requirements_enhanced.txt
```

### 2. 启动服务器

#### 方式1: 原版服务器 (稳定版)
```bash
python shandong_mcp_server.py
```

#### 方式2: 增强版服务器 (推荐)
```bash
# stdio模式 (默认)
python shandong_mcp_server_enhanced.py

# HTTP模式 (便于调试)
python shandong_mcp_server_enhanced.py --mode http --port 8000
```

### 3. 测试验证

#### 测试坡向分析
```bash
python simple_test\\(1\\).py
```

#### 测试MCP服务器
```bash
python test_mcp_server.py
```

### 4. 配置说明

#### 内网API配置
在服务器文件中修改以下配置：
```python
# 内网API地址
INTRANET_API_BASE_URL = "http://172.20.70.142:16555/gateway/computation-api/process"

# 认证Token (需要更新为内网环境的有效Token)
INTRANET_AUTH_TOKEN = "Bearer YOUR_INTERNAL_TOKEN"
```

## 🛠️ 主要功能

### 1. 坡向分析
- 工具名: `coverage_aspect_analysis`
- OGE算法: `Coverage.aspect`
- 支持边界框和半径参数

### 2. 完整工作流
- 工具名: `execute_full_workflow`
- 包含16步耕地流出分析流程

### 3. 空间分析
- 空间相交、擦除、缓冲等多种分析

## 📊 监控和日志

增强版服务器提供完整的日志系统：
- `logs/shandong_mcp.log` - 应用日志
- `logs/api_calls.log` - API调用日志

## 🔧 健康检查

HTTP模式下可以访问：
- `http://localhost:8000/health` - 健康检查
- `http://localhost:8000/info` - 服务器信息

## 📞 支持

如有问题，请检查：
1. 日志文件
2. 网络连接
3. API认证
4. 依赖安装

## 📋 文件清单

""")
        
        for file_info in copied_files:
            f.write(f"{file_info}\n")
        
        if missing_files:
            f.write("\n## ⚠️  缺失文件\n\n")
            for file_info in missing_files:
                f.write(f"{file_info}\n")
    
    # 创建启动脚本
    start_script = package_dir / "start_server.py"
    with open(start_script, 'w', encoding='utf-8') as f:
        f.write("""#!/usr/bin/env python3
'''
MCP服务器启动脚本
'''

import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description='启动山东耕地分析MCP服务器')
    parser.add_argument('--version', choices=['original', 'enhanced'], default='enhanced', 
                       help='选择服务器版本 (original=原版, enhanced=增强版)')
    parser.add_argument('--mode', choices=['stdio', 'http'], default='stdio',
                       help='运行模式 (仅增强版支持)')
    parser.add_argument('--port', type=int, default=8000,
                       help='HTTP端口 (仅HTTP模式)')
    
    args = parser.parse_args()
    
    if args.version == 'original':
        print("🚀 启动原版MCP服务器...")
        subprocess.run([sys.executable, "shandong_mcp_server.py"])
    else:
        print("🚀 启动增强版MCP服务器...")
        cmd = [sys.executable, "shandong_mcp_server_enhanced.py"]
        
        if args.mode == 'http':
            cmd.extend(['--mode', 'http', '--port', str(args.port)])
            print(f"HTTP模式: http://localhost:{args.port}")
        
        subprocess.run(cmd)

if __name__ == "__main__":
    main()
""")
    
    # 创建压缩包
    zip_filename = f"{package_name}.zip"
    
    print(f"\n📝 创建压缩包: {zip_filename}")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(package_dir.parent)
                zipf.write(file_path, arc_path)
    
    # 显示打包结果
    print("\n" + "="*60)
    print("📦 打包完成!")
    print("="*60)
    print(f"📁 目录: {package_dir}")
    print(f"📦 压缩包: {zip_filename}")
    print(f"📊 文件数量: {len(copied_files)}")
    
    if missing_files:
        print(f"⚠️  缺失文件: {len(missing_files)}")
    
    print("\n📋 打包内容:")
    for file_info in copied_files:
        print(f"  {file_info}")
    
    if missing_files:
        print("\n⚠️  缺失文件:")
        for file_info in missing_files:
            print(f"  {file_info}")
    
    print(f"\n🚀 部署建议:")
    print(f"1. 将 {zip_filename} 上传到内网服务器")
    print(f"2. 解压: unzip {zip_filename}")
    print(f"3. 阅读: DEPLOY_README.md")
    print(f"4. 安装依赖: pip install -r requirements_enhanced.txt")
    print(f"5. 启动服务: python start_server.py")
    
    return zip_filename

if __name__ == "__main__":
    create_deployment_package() 