#!/bin/bash

REMOTE_HOST="172.20.70.142"
REMOTE_USER="root"
REMOTE_DIR="/opt/shandong-mcp-server"

echo "📤 上传文件到远程服务器..."

# 使用scp上传文件
scp shandong_mcp_deploy.tar.gz $REMOTE_USER@$REMOTE_HOST:/tmp/

# 远程执行安装命令
ssh $REMOTE_USER@$REMOTE_HOST << 'REMOTE_SCRIPT'
    echo "🔧 在远程服务器上安装MCP服务器..."
    
    # 创建目录
    mkdir -p /opt/shandong-mcp-server
    cd /opt/shandong-mcp-server
    
    # 解压文件
    tar -xzf /tmp/shandong_mcp_deploy.tar.gz
    
    # 安装Python依赖
    pip3 install fastmcp starlette uvicorn httpx pydantic
    
    # 创建日志目录
    mkdir -p logs
    
    # 创建systemd服务文件
    cat > /etc/systemd/system/shandong-mcp.service << 'SERVICE_FILE'
[Unit]
Description=Shandong MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/shandong-mcp-server
ExecStart=/usr/bin/python3 shandong_mcp_server_enhanced.py --mode http --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_FILE
    
    # 启用并启动服务
    systemctl daemon-reload
    systemctl enable shandong-mcp.service
    systemctl start shandong-mcp.service
    
    echo "✅ MCP服务器安装完成"
    echo "🌐 服务地址: http://172.20.70.142:8000"
    echo "📋 服务状态:"
    systemctl status shandong-mcp.service --no-pager
    
    # 清理临时文件
    rm -f /tmp/shandong_mcp_deploy.tar.gz
    
REMOTE_SCRIPT

echo "🎉 远程部署完成！"
echo "📋 服务信息:"
echo "   HTTP端点: http://172.20.70.142:8000"
echo "   健康检查: http://172.20.70.142:8000/health"
echo "   服务信息: http://172.20.70.142:8000/info"
echo "   SSE连接: http://172.20.70.142:8000/sse"

