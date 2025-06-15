# 山东耕地流出分析 MCP 服务器 - 快速设置指南

## 📋 服务器概述

**服务器名称**: `shandong-cultivated-analysis-enhanced`  
**功能**: 山东耕地流出分析，支持自动Token管理和DAG批处理工作流  
**工具数量**: 8个核心工具  

## 🚀 支持的客户端

### 1. Claude Desktop

**配置文件位置**:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**配置内容**:
```json
{
  "mcpServers": {
    "shandong-analysis": {
      "command": "python3",
      "args": [
        "/Users/sxc/shandong-mcp-server/shandong_mcp_server_enhanced.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/sxc/shandong-mcp-server"
      }
    }
  }
}
```

### 2. Cursor

**配置文件位置**:
- macOS: `~/.cursor/mcp_config.json`
- Windows: `%USERPROFILE%\.cursor\mcp_config.json`

**配置内容**:
```json
{
  "mcpServers": {
    "shandong-cultivated-analysis-enhanced": {
      "command": "python3",
      "args": [
        "/Users/sxc/shandong-mcp-server/shandong_mcp_server_enhanced.py",
        "--mode", "stdio"
      ],
      "env": {
        "PYTHONPATH": "/Users/sxc/shandong-mcp-server"
      }
    }
  }
}
```

### 3. 其他MCP客户端

使用标准的MCP配置格式，参考 `mcp_config.json` 文件。

## 🔧 快速设置步骤

### 步骤1: 安装依赖
```bash
pip install fastmcp starlette uvicorn httpx
```

### 步骤2: 复制配置文件

#### 对于Claude Desktop:
```bash
# 复制配置文件到Claude Desktop配置目录
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

#### 对于Cursor:
```bash
# 创建配置目录并复制配置文件
mkdir -p ~/.cursor
cp mcp_config.json ~/.cursor/mcp_config.json
```

### 步骤3: 修改路径

将配置文件中的路径 `/Users/sxc/shandong-mcp-server/` 修改为你的实际路径。

### 步骤4: 重启客户端

重启Claude Desktop或Cursor，服务器会自动加载。

## 🛠️ 可用工具

1. **refresh_token** - 手动刷新认证Token
2. **coverage_aspect_analysis** - 坡向分析
3. **shandong_farmland_outflow** - 山东耕地流出分析
4. **run_big_query** - 查询山东省耕地矢量
5. **execute_code_to_dag** - 代码转DAG任务
6. **submit_batch_task** - 提交批处理任务
7. **query_task_status** - 查询任务状态
8. **execute_dag_workflow** - 执行完整DAG工作流

## 🔄 自动Token管理

- 检测到token过期(40003)时自动刷新
- 支持手动刷新token
- 使用内网认证: `edu_admin/123456`

## 🌐 HTTP模式 (可选)

如果需要HTTP模式，可以启动HTTP服务器:

```bash
python3 shandong_mcp_server_enhanced.py --mode http --host 0.0.0.0 --port 8000
```

访问: `http://localhost:8000/info` 查看服务器信息

## 📝 日志文件

- 服务器日志: `logs/shandong_mcp.log`
- API调用日志: `logs/api_calls.log`

## 🆘 故障排除

1. **找不到python3**: 确保Python 3已安装且在PATH中
2. **模块导入错误**: 检查依赖是否正确安装
3. **权限错误**: 确保脚本有执行权限
4. **网络错误**: 确保可以访问内网API地址

## 📞 支持

如需帮助，请检查日志文件或联系开发者。 