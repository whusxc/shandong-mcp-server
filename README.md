# 山东耕地流出分析 MCP服务器 - 增强版

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-0.1.0+-green.svg)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于MCP (Model Context Protocol) 框架的山东省耕地流出监测与分析系统 - 增强版。

## 🌟 项目概述

本项目是一个基于FastMCP框架开发的高性能服务器，专门用于山东省耕地流出监测分析。系统集成了多种地理信息处理算法，支持HTTP和stdio两种传输方式，提供完整的地理数据分析和批处理能力。

## 🚀 主要特性

### 📊 核心分析功能
- **坡向分析** (coverage_aspect_analysis): 基于DEM数据的地形坡向计算
- **大数据查询** (run_big_query): 高性能的地理数据库查询

### 🔄 DAG批处理系统
- **代码转DAG** (execute_code_to_dag): 将OGE代码转换为DAG任务
- **任务提交** (submit_batch_task): 批处理任务的提交和管理
- **状态监控** (query_task_status): 实时任务状态查询
- **完整工作流** (execute_dag_workflow): 一键式批处理流程

### 🌐 双模式支持
- **HTTP模式**: RESTful API + SSE (Server-Sent Events)
- **stdio模式**: 标准输入输出，适合MCP客户端集成

### 🎯 部署友好
- **一键部署脚本**: 自动化部署到内网服务器 (172.20.70.142)
- **系统服务**: systemd服务管理
- **健康监控**: 完整的健康检查和日志系统

## 📋 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │  FastMCP Server │    │   OGE APIs      │
│                 │───▶│                 │───▶│                 │
│ • HTTP Client   │    │ • HTTP/SSE      │    │ • Computation   │
│ • IDE Plugin    │    │ • stdio         │    │ • DAG Batch     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心组件
- **FastMCP框架**: 高性能MCP实现
- **异步处理**: 基于asyncio的并发处理
- **智能路由**: 多API端点负载均衡
- **结构化日志**: 完整的操作审计

## 🛠️ 快速开始

### 环境要求
- Python 3.8+
- Linux服务器 (推荐CentOS/Ubuntu)
- 网络访问权限 (内网API)

### 1. 本地安装
```bash
# 克隆项目
git clone <your-repo-url>
cd shandong-mcp-server

# 安装依赖
pip install -r requirements_enhanced.txt

# 启动HTTP服务器
python shandong_mcp_server_enhanced.py --mode http --host 0.0.0.0 --port 8000

# 或启动stdio模式
python shandong_mcp_server_enhanced.py --mode stdio
```

### 2. 一键部署到172.20.70.142
```bash
# 测试SSH连接
./test_ssh_connection.sh

# 自动部署
./deploy_to_142.sh
```

## 🌐 API端点

部署成功后，服务器提供以下端点：

| 端点 | URL | 说明 |
|------|-----|------|
| 健康检查 | `http://172.20.70.142:8000/health` | 服务状态检查 |
| 服务信息 | `http://172.20.70.142:8000/info` | 详细服务信息 |
| SSE连接 | `http://172.20.70.142:8000/sse` | MCP客户端连接 |
| 消息处理 | `http://172.20.70.142:8000/messages/` | MCP消息处理 |

## 🔧 可用工具

### 1. 地理分析工具
```python
# 坡向分析
coverage_aspect_analysis(
    bbox=[116.0, 36.0, 118.0, 38.0],
    product_value="Platform:Product:ASTER_GDEM_DEM30"
)

# 大数据查询
run_big_query(
    query="SELECT * FROM cultivated_land WHERE area > 1000",
    geometry_column="geom"
)
```

### 2. 批处理工具
```python
# 完整DAG工作流
execute_dag_workflow(
    code="var image = Dataset('landsat8').filterBounds(roi);",
    auto_submit=True,
    wait_for_completion=True
)
```

## 📁 项目结构

```
shandong-mcp-server/
├── shandong_mcp_server_enhanced.py    # 主服务器文件
├── requirements_enhanced.txt          # Python依赖
├── deploy_to_142.sh                   # 自动部署脚本
├── test_ssh_connection.sh             # SSH连接测试
├── DEPLOY_TO_142_GUIDE.md            # 部署指南
├── docs/                             # 文档目录
│   ├── MCP_COMPREHENSIVE_GUIDE.md    # MCP详细指南
│   ├── DAG_BATCH_PROCESSING.md       # 批处理指南
│   ├── TOKEN_AUTO_REFRESH_GUIDE.md   # Token管理指南
│   └── ENHANCED_USAGE.md             # 使用说明
├── tests/                            # 测试文件
│   ├── test_mcp_tools.py            # 工具测试
│   ├── test_dag_workflow.py         # 工作流测试
│   └── test_token_*.py              # Token测试
└── deployment/                       # 部署相关
    ├── DEPLOYMENT_CHECKLIST.md      # 部署检查清单
    └── INTRANET_QUICK_START.md      # 内网快速开始
```

## 🔑 配置管理

### API配置
```python
INTRANET_API_BASE_URL = "http://172.20.70.142:16555/gateway/computation-api/process"
DAG_API_BASE_URL = "http://172.20.70.141/api/oge-dag-22"
```

### Token管理
```python
INTRANET_AUTH_TOKEN = "Bearer your_token_here"
```

当Token过期时，更新代码中的Token值并重启服务：
```bash
systemctl restart shandong-mcp
```

## 🚀 部署说明

### 生产环境部署
1. **服务器**: 172.20.70.142 (应用服务器)
2. **端口**: 8000 (HTTP服务)
3. **服务管理**: systemd
4. **日志**: journalctl -u shandong-mcp -f

### 服务管理命令
```bash
# 启动服务
systemctl start shandong-mcp

# 停止服务
systemctl stop shandong-mcp

# 重启服务
systemctl restart shandong-mcp

# 查看状态
systemctl status shandong-mcp

# 查看日志
journalctl -u shandong-mcp -f
```

## 📊 监控和维护

### 健康检查
```bash
curl http://172.20.70.142:8000/health
```

### 日志监控
```bash
# 实时日志
journalctl -u shandong-mcp -f

# 错误日志
journalctl -u shandong-mcp -p err

# 最近日志
journalctl -u shandong-mcp -n 100
```

## 🐛 故障排除

### 常见问题
1. **服务启动失败**: 检查Python依赖和权限
2. **API调用失败**: 验证Token和网络连接
3. **端口冲突**: 检查端口8000是否被占用

### 调试步骤
```bash
# 检查服务状态
systemctl status shandong-mcp

# 查看详细错误
journalctl -u shandong-mcp -n 50

# 测试API连接
curl -X POST http://172.20.70.142:16555/gateway/computation-api/process
```

## 📚 文档和指南

- [MCP详细指南](MCP_COMPREHENSIVE_GUIDE.md)
- [DAG批处理指南](DAG_BATCH_PROCESSING.md)
- [部署指南](DEPLOY_TO_142_GUIDE.md)
- [使用说明](ENHANCED_USAGE.md)
- [Token管理](TOKEN_AUTO_REFRESH_GUIDE.md)

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 技术支持

- **问题反馈**: 请在GitHub Issues中提交
- **功能建议**: 欢迎在Discussions中讨论
- **紧急支持**: 请联系项目维护者

---

## 🏷️ 版本信息

- **当前版本**: v2.4.0 Enhanced
- **最后更新**: 2024-06-14
- **兼容性**: Python 3.8+, FastMCP 0.1.0+

## 📈 更新日志

### v2.4.0 Enhanced (2024-06-14)
- ✅ 新增DAG批处理工作流
- ✅ 优化Token管理机制
- ✅ 增强HTTP/SSE支持
- ✅ 完善部署自动化
- ✅ 改进错误处理和日志

### v2.3.0 (2024-06-13)
- ✅ 集成FastMCP框架
- ✅ 支持HTTP和stdio双模式
- ✅ 新增坡向分析功能
- ✅ 优化API调用性能 