# 山东MCP服务器部署指南 - 172.20.70.142

## 🎯 部署目标
将山东耕地流出分析MCP服务器部署到内网应用服务器：**172.20.70.142**

## 📋 前置条件

### 1. 本地准备
- [x] 确保本地有SSH客户端
- [x] 确保可以SSH连接到目标服务器
- [x] 确保有部署脚本执行权限

### 2. 服务器要求
- **服务器IP**: 172.20.70.142
- **操作系统**: Linux (CentOS/RHEL/Ubuntu)
- **Python版本**: 3.8+
- **网络**: 能访问内网API和DAG服务
- **权限**: root权限或sudo权限

### 3. 网络配置
- **HTTP端口**: 8000 (MCP服务端口)
- **API访问**: 需要能访问内网API服务
- **防火墙**: 需要开放8000端口

## 🚀 快速部署

### 方法一：一键自动部署 (推荐)

```bash
# 1. 给部署脚本执行权限
chmod +x deploy_to_142.sh

# 2. 执行自动部署
./deploy_to_142.sh
```

### 方法二：手动部署步骤

#### 步骤1: 准备服务器环境
```bash
# SSH连接到服务器
ssh root@172.20.70.142

# 更新系统包
yum update -y  # CentOS/RHEL
# 或者
apt update && apt upgrade -y  # Ubuntu/Debian

# 安装必要软件
yum install -y python3 python3-pip git  # CentOS/RHEL
# 或者
apt install -y python3 python3-pip git  # Ubuntu/Debian

# 创建部署目录
mkdir -p /opt/shandong_mcp
mkdir -p /var/log/shandong_mcp
```

#### 步骤2: 上传文件
```bash
# 在本地执行，上传主程序
scp shandong_mcp_server_enhanced.py root@172.20.70.142:/opt/shandong_mcp/

# 上传依赖文件
scp requirements_enhanced.txt root@172.20.70.142:/opt/shandong_mcp/
```

#### 步骤3: 安装Python依赖
```bash
# SSH到服务器
ssh root@172.20.70.142

cd /opt/shandong_mcp

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements_enhanced.txt
```

#### 步骤4: 创建系统服务
```bash
# 创建systemd服务文件
cat > /etc/systemd/system/shandong-mcp.service << 'EOF'
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
EOF

# 重载systemd配置
systemctl daemon-reload
```

#### 步骤5: 配置防火墙
```bash
# 如果使用firewalld
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --reload

# 如果使用ufw
ufw allow 8000/tcp
```

#### 步骤6: 启动服务
```bash
# 启用并启动服务
systemctl enable shandong-mcp
systemctl start shandong-mcp

# 检查服务状态
systemctl status shandong-mcp
```

## 🔍 验证部署

### 1. 检查服务状态
```bash
# 检查系统服务状态
systemctl status shandong-mcp

# 检查服务日志
journalctl -u shandong-mcp -f
```

### 2. 测试HTTP端点
```bash
# 健康检查
curl http://172.20.70.142:8000/health

# 服务信息
curl http://172.20.70.142:8000/info
```

### 3. 预期响应
健康检查应该返回：
```json
{
  "status": "healthy",
  "server": "shandong-cultivated-analysis-enhanced",
  "endpoints": {
    "sse": "/sse",
    "health": "/health",
    "messages": "/messages/"
  }
}
```

## 🔧 服务管理

### 常用命令
```bash
# 启动服务
systemctl start shandong-mcp

# 停止服务
systemctl stop shandong-mcp

# 重启服务
systemctl restart shandong-mcp

# 查看状态
systemctl status shandong-mcp

# 查看实时日志
journalctl -u shandong-mcp -f

# 查看最近日志
journalctl -u shandong-mcp -n 100
```

### 配置文件位置
- **主程序**: `/opt/shandong_mcp/shandong_mcp_server_enhanced.py`
- **依赖文件**: `/opt/shandong_mcp/requirements_enhanced.txt`
- **系统服务**: `/etc/systemd/system/shandong-mcp.service`
- **应用日志**: `/var/log/shandong_mcp/`
- **系统日志**: `journalctl -u shandong-mcp`

## 🌐 访问端点

部署成功后，MCP服务器将在以下端点提供服务：

| 端点 | URL | 说明 |
|------|-----|------|
| 健康检查 | `http://172.20.70.142:8000/health` | 服务状态检查 |
| 服务信息 | `http://172.20.70.142:8000/info` | 服务详细信息 |
| SSE连接 | `http://172.20.70.142:8000/sse` | 服务器发送事件 |
| 消息处理 | `http://172.20.70.142:8000/messages/` | MCP消息处理 |

## 🔑 Token管理

### 当前Token配置
Token位置：`shandong_mcp_server_enhanced.py` 第43行
```python
INTRANET_AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 更新Token
当Token过期时：
1. 编辑服务器上的主程序文件
2. 更新Token值
3. 重启服务: `systemctl restart shandong-mcp`

## 🚨 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 检查详细错误信息
journalctl -u shandong-mcp -n 50

# 常见原因：
# - Python依赖未安装
# - 端口被占用
# - 权限问题
```

#### 2. 端口访问失败
```bash
# 检查端口是否监听
netstat -tlnp | grep 8000

# 检查防火墙规则
firewall-cmd --list-ports  # firewalld
ufw status  # ufw
```

#### 3. API调用失败
- 检查内网连接
- 验证Token是否有效
- 确认API地址正确

### 日志查看
```bash
# 实时查看应用日志
journalctl -u shandong-mcp -f

# 查看错误日志
journalctl -u shandong-mcp -p err

# 查看特定时间段日志
journalctl -u shandong-mcp --since "1 hour ago"
```

## 📞 技术支持

### 部署支持
- 检查网络连接
- 验证SSH权限
- 确认服务器资源

### 运行支持
- 监控服务状态
- 定期检查日志
- 及时更新Token

## 🔄 更新和维护

### 更新服务
```bash
# 1. 停止服务
systemctl stop shandong-mcp

# 2. 备份当前版本
cp /opt/shandong_mcp/shandong_mcp_server_enhanced.py /opt/shandong_mcp/shandong_mcp_server_enhanced.py.backup

# 3. 上传新版本
scp shandong_mcp_server_enhanced.py root@172.20.70.142:/opt/shandong_mcp/

# 4. 重启服务
systemctl start shandong-mcp
```

### 定期维护
- 定期检查服务状态
- 清理过期日志
- 更新依赖包
- 备份配置文件

---

## ✅ 部署检查清单

- [ ] 服务器SSH连接正常
- [ ] Python 3.8+ 已安装
- [ ] 依赖包安装成功
- [ ] 系统服务创建完成
- [ ] 防火墙规则配置正确
- [ ] 服务启动成功
- [ ] HTTP端点响应正常
- [ ] 日志输出正常
- [ ] Token配置正确

完成以上检查后，MCP服务器应该可以正常运行在172.20.70.142:8000上。 