# 山东耕地流出分析 MCP 服务器

基于Model Context Protocol (MCP)的山东省耕地流出分析服务器，提供地理信息分析和处理功能。

## 🚀 功能特性

- 🗺️ **地理信息分析**：坡向分析、耕地流出分析
- 📊 **大数据查询**：PostGIS数据库查询
- 🔄 **自动Token管理**：智能认证和自动刷新
- 🚀 **DAG批处理工作流**：任务调度和管理
- 📡 **远程HTTP服务**：内网部署，多客户端访问

## 🛠️ 核心工具

1. **refresh_token** - 刷新认证Token
2. **coverage_aspect_analysis** - 坡向分析
3. **shandong_farmland_outflow** - 山东耕地流出分析
4. **run_big_query** - 查询山东省耕地矢量
5. **execute_code_to_dag** - 代码转DAG任务
6. **submit_batch_task** - 提交批处理任务
7. **query_task_status** - 查询任务状态
8. **execute_dag_workflow** - 执行完整DAG工作流

## 📱 客户端配置

### Claude Desktop

配置文件位置：`~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "shandong-remote": {
      "type": "sse",
      "url": "http://172.20.70.142:8000/sse"
    }
  }
}
```

### 使用方法

配置完成后，在Claude Desktop中直接对话：
- "请帮我查询山东省的耕地数据"
- "请对这个区域进行坡向分析"
- "请刷新一下认证token"

## 🌐 服务器部署

服务器运行于内网：`http://172.20.70.142:8000`

- 健康检查：`/health`
- 服务信息：`/info`
- SSE连接：`/sse`

## �� 许可证

MIT License 