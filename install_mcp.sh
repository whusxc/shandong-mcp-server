#!/bin/bash

echo "🚀 山东耕地流出分析 MCP 服务器 - 自动安装脚本"
echo "=================================================="

# 获取当前目录
CURRENT_DIR=$(pwd)
echo "📁 当前目录: $CURRENT_DIR"

# 检查Python环境
echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi
echo "✅ Python3 已安装: $(python3 --version)"

# 安装依赖
echo "📦 安装Python依赖..."
pip3 install fastmcp starlette uvicorn httpx pydantic

# 检查主要客户端
echo "🔍 检查MCP客户端..."

# Claude Desktop 配置
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
if [ -d "$CLAUDE_CONFIG_DIR" ]; then
    echo "✅ 发现Claude Desktop"
    
    # 备份现有配置
    if [ -f "$CLAUDE_CONFIG_DIR/claude_desktop_config.json" ]; then
        cp "$CLAUDE_CONFIG_DIR/claude_desktop_config.json" "$CLAUDE_CONFIG_DIR/claude_desktop_config.json.backup"
        echo "📋 已备份现有Claude配置"
    fi
    
    # 更新配置文件中的路径
    sed "s|/Users/sxc/shandong-mcp-server|$CURRENT_DIR|g" claude_desktop_config.json > "$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
    echo "✅ Claude Desktop配置已更新"
else
    echo "⚠️  未找到Claude Desktop"
fi

# Cursor 配置
CURSOR_CONFIG_DIR="$HOME/.cursor"
echo "📁 设置Cursor配置..."
mkdir -p "$CURSOR_CONFIG_DIR"

# 更新配置文件中的路径
sed "s|/Users/sxc/shandong-mcp-server|$CURRENT_DIR|g" mcp_config.json > "$CURSOR_CONFIG_DIR/mcp_config.json"
echo "✅ Cursor配置已更新"

# VS Code 配置
if [ -d ".vscode" ]; then
    # 更新VS Code配置中的路径
    sed "s|/Users/sxc/shandong-mcp-server|$CURRENT_DIR|g" .vscode/settings.json > .vscode/settings_updated.json
    mv .vscode/settings_updated.json .vscode/settings.json
    echo "✅ VS Code配置已更新"
fi

# 创建日志目录
mkdir -p logs
echo "📝 日志目录已创建"

# 测试服务器
echo "🧪 测试MCP服务器..."
if python3 shandong_mcp_server_enhanced.py --mode http --host 127.0.0.1 --port 8000 &>/dev/null &
then
    SERVER_PID=$!
    sleep 3
    
    # 测试HTTP端点
    if curl -s http://127.0.0.1:8000/health > /dev/null; then
        echo "✅ MCP服务器测试成功"
        kill $SERVER_PID 2>/dev/null
    else
        echo "⚠️  MCP服务器测试失败，但这不影响stdio模式"
        kill $SERVER_PID 2>/dev/null
    fi
else
    echo "⚠️  无法启动测试服务器，但这不影响stdio模式"
fi

echo ""
echo "🎉 安装完成！"
echo "=================================================="
echo "📋 配置文件已更新:"
echo "   • Claude Desktop: $CLAUDE_CONFIG_DIR/claude_desktop_config.json"
echo "   • Cursor: $CURSOR_CONFIG_DIR/mcp_config.json"
echo "   • VS Code: .vscode/settings.json"
echo ""
echo "🔄 接下来的步骤:"
echo "   1. 重启Claude Desktop、Cursor或VS Code"
echo "   2. MCP服务器会自动加载"
echo "   3. 开始使用8个强大的地理分析工具！"
echo ""
echo "🛠️  可用工具:"
echo "   • refresh_token - 刷新认证Token"
echo "   • coverage_aspect_analysis - 坡向分析"
echo "   • shandong_farmland_outflow - 山东耕地流出分析"
echo "   • run_big_query - 查询山东省耕地矢量"
echo "   • execute_code_to_dag - 代码转DAG任务"
echo "   • submit_batch_task - 提交批处理任务"
echo "   • query_task_status - 查询任务状态"
echo "   • execute_dag_workflow - 执行完整DAG工作流"
echo ""
echo "📖 详细说明请查看: README_MCP_Setup.md"
echo "🆘 如遇问题，请检查logs目录下的日志文件" 