# 山东MCP服务器 - 增强版

基于FastMCP框架的山东省耕地流出监测与分析系统。

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Linux服务器 (推荐CentOS/Ubuntu)

### 本地安装
```bash
# 安装依赖
pip install -r requirements_enhanced.txt

# 启动HTTP服务器
python shandong_mcp_server_enhanced.py --mode http --host 0.0.0.0 --port 8000

# 或启动stdio模式
python shandong_mcp_server_enhanced.py --mode stdio
```

### 一键部署到172.20.70.142
```bash
# 测试SSH连接
./test_ssh_connection.sh

# 自动部署
./deploy_to_142.sh
```

## 🔧 主要功能

- **坡向分析**: 基于DEM数据的地形坡向计算
- **大数据查询**: 高性能的地理数据库查询
- **DAG批处理**: 完整的批处理工作流系统
- **双模式支持**: HTTP和stdio两种模式

## 🌐 访问地址

部署后可通过以下地址访问：

- **健康检查**: `http://172.20.70.142:8000/health`
- **服务信息**: `http://172.20.70.142:8000/info`
- **MCP连接**: `http://172.20.70.142:8000/sse`

## 🛠️ 服务管理

```bash
# 启动服务
systemctl start shandong-mcp

# 停止服务
systemctl stop shandong-mcp

# 查看状态
systemctl status shandong-mcp

# 查看日志
journalctl -u shandong-mcp -f
```

## 📝 配置说明

Token位置：`shandong_mcp_server_enhanced.py` 第43行

当Token过期时：
1. 编辑服务器上的主程序文件
2. 更新Token值
3. 重启服务: `systemctl restart shandong-mcp`

## �� 许可证

MIT License 