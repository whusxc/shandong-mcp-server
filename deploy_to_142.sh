#!/bin/bash

# 山东MCP服务器部署脚本 - 目标服务器: 172.20.70.142
# 作者: MCP部署助手
# 日期: $(date +%Y-%m-%d)

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
TARGET_SERVER="172.20.70.142"
REMOTE_USER="root"
SSH_KEY_PATH="~/.ssh/id_rsa"  # 根据实际情况修改
REMOTE_DIR="/opt/shandong_mcp"
SERVICE_NAME="shandong-mcp"
HTTP_PORT=8000

echo -e "${BLUE}=== 山东MCP服务器部署脚本 ===${NC}"
echo -e "${BLUE}目标服务器: ${TARGET_SERVER}${NC}"
echo ""

# 检查本地文件
check_local_files() {
    echo -e "${YELLOW}[1/8] 检查本地文件...${NC}"
    
    required_files=(
        "shandong_mcp_server_enhanced.py"
        "requirements_enhanced.txt"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            echo -e "${RED}错误: 缺少必要文件 $file${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ $file${NC}"
    done
    
    echo -e "${GREEN}本地文件检查完成${NC}"
    echo ""
}

# 检查SSH连接
check_ssh_connection() {
    echo -e "${YELLOW}[2/8] 检查SSH连接...${NC}"
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes ${REMOTE_USER}@${TARGET_SERVER} "echo 'SSH连接成功'" 2>/dev/null; then
        echo -e "${GREEN}✓ SSH连接正常${NC}"
    else
        echo -e "${RED}错误: 无法连接到服务器 ${TARGET_SERVER}${NC}"
        echo -e "${YELLOW}请检查:${NC}"
        echo "1. 服务器IP是否正确"
        echo "2. SSH密钥是否配置正确"
        echo "3. 服务器是否开启了SSH服务"
        exit 1
    fi
    echo ""
}

# 准备远程环境
prepare_remote_environment() {
    echo -e "${YELLOW}[3/8] 准备远程环境...${NC}"
    
    ssh ${REMOTE_USER}@${TARGET_SERVER} << 'EOF'
        # 更新系统包
        if command -v yum >/dev/null 2>&1; then
            yum update -y
            yum install -y python3 python3-pip git
        elif command -v apt >/dev/null 2>&1; then
            apt update
            apt install -y python3 python3-pip git
        else
            echo "不支持的包管理器"
            exit 1
        fi
        
        # 检查Python版本
        python3 --version
        pip3 --version
        
        # 创建部署目录
        mkdir -p /opt/shandong_mcp
        mkdir -p /var/log/shandong_mcp
        
        echo "远程环境准备完成"
EOF
    
    echo -e "${GREEN}✓ 远程环境准备完成${NC}"
    echo ""
}

# 上传文件
upload_files() {
    echo -e "${YELLOW}[4/8] 上传文件到服务器...${NC}"
    
    # 上传主程序文件
    scp shandong_mcp_server_enhanced.py ${REMOTE_USER}@${TARGET_SERVER}:${REMOTE_DIR}/
    echo -e "${GREEN}✓ 主程序文件上传完成${NC}"
    
    # 上传依赖文件
    scp requirements_enhanced.txt ${REMOTE_USER}@${TARGET_SERVER}:${REMOTE_DIR}/
    echo -e "${GREEN}✓ 依赖文件上传完成${NC}"
    
    # 创建配置文件
    cat > temp_config.py << 'EOF'
#!/usr/bin/env python3
"""
MCP服务器配置文件
"""

# 服务器配置
MCP_SERVER_NAME = "shandong-cultivated-analysis-enhanced"
HOST = "0.0.0.0"
PORT = 8000

# API配置 
INTRANET_API_BASE_URL = "http://172.20.70.142:16555/gateway/computation-api/process"
DAG_API_BASE_URL = "http://172.20.70.141/api/oge-dag-22"

# 日志配置
LOG_LEVEL = "INFO"
LOG_DIR = "/var/log/shandong_mcp"

# 认证配置（需要手动更新）
INTRANET_AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjMyNCwidXNlcl9uYW1lIjoiZWR1X2FkbWluIiwic2NvcGUiOlsid2ViIl0sImV4cCI6MTc0OTkwNjkwMiwidXVpZCI6ImY5NTBjZmYyLTA3YzgtNDYxYS05YzI0LTkxNjJkNTllMmVmNiIsImF1dGhvcml0aWVzIjpbIkFETUlOSVNUUkFUT1JTIl0sImp0aSI6IkxQbjJQTThlRlpBRDhUNFBxN2U3SWlRdmRGQSIsImNsaWVudF9pZCI6InRlc3QiLCJ1c2VybmFtZSI6ImVkdV9hZG1pbiJ9.jFepdzkcDDlcH0v3Z_Ge35vbiTB3RVt8OQsHJ0o6qEU"

EOF
    
    scp temp_config.py ${REMOTE_USER}@${TARGET_SERVER}:${REMOTE_DIR}/config.py
    rm temp_config.py
    echo -e "${GREEN}✓ 配置文件上传完成${NC}"
    echo ""
}

# 安装依赖
install_dependencies() {
    echo -e "${YELLOW}[5/8] 安装Python依赖...${NC}"
    
    ssh ${REMOTE_USER}@${TARGET_SERVER} << 'EOF'
        cd /opt/shandong_mcp
        
        # 创建虚拟环境
        python3 -m venv venv
        source venv/bin/activate
        
        # 升级pip
        pip install --upgrade pip
        
        # 安装依赖
        pip install -r requirements_enhanced.txt
        
        echo "依赖安装完成"
EOF
    
    echo -e "${GREEN}✓ Python依赖安装完成${NC}"
    echo ""
}

# 创建系统服务
create_systemd_service() {
    echo -e "${YELLOW}[6/8] 创建系统服务...${NC}"
    
    ssh ${REMOTE_USER}@${TARGET_SERVER} << 'EOF'
        cat > /etc/systemd/system/shandong-mcp.service << 'SYSTEMD_EOF'
[Unit]
Description=Shandong MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/shandong_mcp
Environment=PATH=/opt/shandong_mcp/venv/bin
ExecStart=/opt/shandong_mcp/venv/bin/python shandong_mcp_server_enhanced.py --mode http --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=shandong-mcp

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

        # 重载systemd配置
        systemctl daemon-reload
        
        echo "系统服务创建完成"
EOF
    
    echo -e "${GREEN}✓ 系统服务创建完成${NC}"
    echo ""
}

# 配置防火墙
configure_firewall() {
    echo -e "${YELLOW}[7/8] 配置防火墙...${NC}"
    
    ssh ${REMOTE_USER}@${TARGET_SERVER} << 'EOF'
        # 检查防火墙状态
        if systemctl is-active --quiet firewalld; then
            echo "配置firewalld..."
            firewall-cmd --permanent --add-port=8000/tcp
            firewall-cmd --reload
            echo "firewalld配置完成"
        elif systemctl is-active --quiet ufw; then
            echo "配置ufw..."
            ufw allow 8000/tcp
            echo "ufw配置完成"
        else
            echo "未检测到防火墙服务或防火墙已关闭"
        fi
EOF
    
    echo -e "${GREEN}✓ 防火墙配置完成${NC}"
    echo ""
}

# 启动服务
start_service() {
    echo -e "${YELLOW}[8/8] 启动MCP服务...${NC}"
    
    ssh ${REMOTE_USER}@${TARGET_SERVER} << 'EOF'
        # 启动服务
        systemctl enable shandong-mcp
        systemctl start shandong-mcp
        
        # 等待服务启动
        sleep 3
        
        # 检查服务状态
        systemctl status shandong-mcp --no-pager
        
        echo ""
        echo "服务启动完成"
EOF
    
    echo -e "${GREEN}✓ MCP服务启动完成${NC}"
    echo ""
}

# 验证部署
verify_deployment() {
    echo -e "${YELLOW}验证部署结果...${NC}"
    
    # 检查HTTP端点
    if curl -s --max-time 10 http://${TARGET_SERVER}:${HTTP_PORT}/health > /dev/null; then
        echo -e "${GREEN}✓ HTTP服务正常${NC}"
    else
        echo -e "${RED}✗ HTTP服务异常${NC}"
    fi
    
    # 显示服务信息
    echo -e "${BLUE}=== 部署完成信息 ===${NC}"
    echo "服务器地址: ${TARGET_SERVER}"
    echo "HTTP端口: ${HTTP_PORT}"
    echo "健康检查: http://${TARGET_SERVER}:${HTTP_PORT}/health"
    echo "服务信息: http://${TARGET_SERVER}:${HTTP_PORT}/info"
    echo "SSE端点: http://${TARGET_SERVER}:${HTTP_PORT}/sse"
    echo ""
    echo -e "${GREEN}=== 部署成功完成 ===${NC}"
    echo ""
    echo -e "${YELLOW}管理命令:${NC}"
    echo "启动服务: systemctl start shandong-mcp"
    echo "停止服务: systemctl stop shandong-mcp"
    echo "重启服务: systemctl restart shandong-mcp"
    echo "查看状态: systemctl status shandong-mcp"
    echo "查看日志: journalctl -u shandong-mcp -f"
}

# 主函数
main() {
    echo -e "${BLUE}开始部署流程...${NC}"
    echo ""
    
    check_local_files
    check_ssh_connection
    prepare_remote_environment
    upload_files
    install_dependencies
    create_systemd_service
    configure_firewall
    start_service
    verify_deployment
}

# 执行主函数
main 