#!/bin/bash

# SSH连接测试脚本 - 172.20.70.142
# 使用前请确保已配置SSH密钥或密码认证

TARGET_SERVER="172.20.70.142"
REMOTE_USER="root"

echo "=== SSH连接测试 ==="
echo "目标服务器: ${TARGET_SERVER}"
echo "用户: ${REMOTE_USER}"
echo ""

echo "正在测试SSH连接..."
if ssh -o ConnectTimeout=10 -o BatchMode=yes ${REMOTE_USER}@${TARGET_SERVER} "echo 'SSH连接成功!'" 2>/dev/null; then
    echo "✓ SSH连接正常"
    echo ""
    
    echo "获取服务器信息..."
    ssh ${REMOTE_USER}@${TARGET_SERVER} << 'EOF'
        echo "=== 服务器信息 ==="
        echo "主机名: $(hostname)"
        echo "操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
        echo "Python版本: $(python3 --version 2>/dev/null || echo '未安装Python3')"
        echo "可用内存: $(free -h | grep Mem | awk '{print $2}')"
        echo "磁盘空间: $(df -h / | tail -1 | awk '{print $4}')"
        echo "网络连接: $(curl -s --max-time 5 http://172.20.70.142:16555 && echo '内网API可访问' || echo '内网API不可访问')"
        echo ""
        echo "=== 端口检查 ==="
        netstat -tlnp | grep :8000 && echo "端口8000已被占用" || echo "端口8000可用"
EOF
    
else
    echo "✗ SSH连接失败"
    echo ""
    echo "请检查："
    echo "1. 服务器IP是否正确: ${TARGET_SERVER}"
    echo "2. 是否可以ping通服务器: ping ${TARGET_SERVER}"
    echo "3. SSH密钥是否配置正确"
    echo "4. 服务器SSH服务是否开启"
    echo "5. 防火墙是否允许SSH连接"
    echo ""
    echo "手动测试连接: ssh ${REMOTE_USER}@${TARGET_SERVER}"
fi 