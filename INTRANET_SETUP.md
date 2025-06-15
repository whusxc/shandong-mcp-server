# 山东耕地流出分析 MCP 服务器 - 内网部署指南

## 🌐 部署架构

```
内网用户电脑 ←→ 172.20.70.142:8000 (MCP服务器) ←→ 172.20.70.141/142等内网API
```

## 🚀 服务器端部署 (172.20.70.142)

### 方法1: 自动部署脚本
```bash
# 在本地执行
./deploy_remote.sh
./upload_to_remote.sh
```

### 方法2: 手动部署
```bash
# 1. 上传文件到服务器
scp shandong_mcp_deploy.tar.gz root@172.20.70.142:/tmp/

# 2. 登录服务器
ssh root@172.20.70.142

# 3. 在服务器上执行
mkdir -p /opt/shandong-mcp-server
cd /opt/shandong-mcp-server
tar -xzf /tmp/shandong_mcp_deploy.tar.gz

# 4. 安装依赖
pip3 install -r requirements.txt

# 5. 启动服务 (后台运行)
nohup python3 shandong_mcp_server_enhanced.py --mode http --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &

# 6. 检查服务状态
curl http://localhost:8000/health
```

### 方法3: 系统服务 (推荐)
```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/shandong-mcp.service << EOF
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
StandardOutput=append:/opt/shandong-mcp-server/logs/server.log
StandardError=append:/opt/shandong-mcp-server/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable shandong-mcp.service
sudo systemctl start shandong-mcp.service

# 查看服务状态
sudo systemctl status shandong-mcp.service
```

## 💻 客户端配置 (内网用户)

### Claude Desktop 配置
**文件位置**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "shandong-remote": {
      "command": "python3",
      "args": ["-c", "import requests; import json; import sys; data=json.load(sys.stdin); resp=requests.post('http://172.20.70.142:8000/messages/', json=data); print(resp.text)"],
      "description": "山东耕地流出分析MCP服务器 - 远程连接"
    }
  }
}
```

### Cursor 配置
**文件位置**: `~/.cursor/mcp_config.json`

```json
{
  "mcpServers": {
    "shandong-remote": {
      "transport": "http",
      "url": "http://172.20.70.142:8000/sse",
      "description": "山东耕地流出分析MCP服务器 - HTTP传输"
    }
  }
}
```

## 🔧 服务管理命令

### 启动/停止服务
```bash
# 系统服务方式
sudo systemctl start shandong-mcp.service    # 启动
sudo systemctl stop shandong-mcp.service     # 停止
sudo systemctl restart shandong-mcp.service  # 重启
sudo systemctl status shandong-mcp.service   # 状态

# 手动方式
# 查找进程
ps aux | grep shandong_mcp_server_enhanced.py
# 杀死进程
kill <PID>
# 重新启动
nohup python3 shandong_mcp_server_enhanced.py --mode http --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &
```

### 查看日志
```bash
# 系统日志
sudo journalctl -u shandong-mcp.service -f

# 应用日志
tail -f /opt/shandong-mcp-server/logs/server.log
tail -f /opt/shandong-mcp-server/logs/shandong_mcp.log
tail -f /opt/shandong-mcp-server/logs/api_calls.log
```

## 🌐 服务端点

| 端点 | 用途 | 示例 |
|------|------|------|
| `/health` | 健康检查 | `curl http://172.20.70.142:8000/health` |
| `/info` | 服务信息 | `curl http://172.20.70.142:8000/info` |
| `/sse` | SSE连接 | MCP客户端使用 |
| `/messages/` | 消息处理 | MCP协议端点 |

## 🛠️ 可用工具

1. **refresh_token** - 自动刷新认证Token
2. **coverage_aspect_analysis** - 坡向分析  
3. **shandong_farmland_outflow** - 山东耕地流出分析
4. **run_big_query** - 查询山东省耕地矢量
5. **execute_code_to_dag** - 代码转DAG任务
6. **submit_batch_task** - 提交批处理任务
7. **query_task_status** - 查询任务状态
8. **execute_dag_workflow** - 执行完整DAG工作流

## 🔄 自动Token管理

服务器会自动处理token过期问题：
- 使用内网认证: `edu_admin/123456`
- 检测到40003错误时自动刷新
- 支持手动刷新token

## 🆘 故障排除

### 1. 服务无法访问
```bash
# 检查端口是否监听
netstat -tlnp | grep 8000
# 检查防火墙
firewall-cmd --list-ports
# 开放端口 (如需要)
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --reload
```

### 2. Token认证失败
```bash
# 测试token获取
curl -X POST "http://172.20.70.141/api/oauth/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "edu_admin", "password": "123456"}' \
  -G -d "scopes=web" -d "client_secret=123456" -d "client_id=test" -d "grant_type=password" -d "username=edu_admin" -d "password=123456"
```

### 3. 查看详细错误
```bash
# 查看实时日志
tail -f /opt/shandong-mcp-server/logs/shandong_mcp.log
tail -f /opt/shandong-mcp-server/logs/api_calls.log
```

## 📞 使用示例

### 测试服务器连通性
```bash
# 从内网任意机器测试
curl http://172.20.70.142:8000/health
curl http://172.20.70.142:8000/info
```

### MCP客户端测试
在配置好的Claude Desktop或Cursor中：
1. 重启客户端
2. 查看是否出现"shandong-remote"服务器
3. 尝试调用工具: `refresh_token`
4. 进行地理分析: `run_big_query`

## ⚡ 性能优化

- 服务器配置: 4核8G内存推荐
- 并发连接: 默认支持100个并发
- 日志轮转: 建议配置logrotate
- 监控告警: 可集成Prometheus/Grafana 