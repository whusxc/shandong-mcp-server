# 山东耕地流出分析MCP服务器 - 增强版使用指南

## 🚀 主要改进

### 1. **双模式支持**
- **stdio模式**：传统的MCP协议支持，适用于Claude Desktop等客户端
- **HTTP模式**：基于SSE的HTTP接口，适用于Web应用集成

### 2. **FastMCP框架**
- 更简洁的API定义
- 自动参数验证
- 内置Context支持
- 更好的错误处理

### 3. **结构化日志**
- 分离的应用日志和API调用日志
- 文件日志 + 控制台日志
- 性能监控和调用时间记录

### 4. **统一响应格式**
```python
{
    "success": true,
    "code": 0,
    "msg": "操作成功",
    "data": {...},
    "operation": "坡向分析",
    "execution_time": 2.34,
    "api_endpoint": "intranet"
}
```

### 5. **HTTP端点**
- `/health` - 健康检查
- `/info` - 服务器信息
- `/sse` - SSE连接端点
- `/messages/` - 消息处理

## 📦 安装依赖

```bash
pip install -r requirements_enhanced.txt
```

## 🔧 使用方式

### 1. stdio模式 (默认)
```bash
# 启动服务器
python shandong_mcp_server_enhanced.py

# 或者明确指定stdio模式
python shandong_mcp_server_enhanced.py --mode stdio
```

### 2. HTTP模式
```bash
# 启动HTTP服务器
python shandong_mcp_server_enhanced.py --mode http --host 0.0.0.0 --port 8000
```

启动后可以访问：
- `http://localhost:8000/health` - 健康检查
- `http://localhost:8000/info` - 服务器信息
- `http://localhost:8000/sse` - SSE连接

## 🛠️ 工具列表

### 1. 完整工作流分析
```json
{
    "name": "execute_full_workflow",
    "parameters": {
        "enable_visualization": true,
        "intermediate_results": false
    }
}
```

### 2. 坡向分析
```json
{
    "name": "coverage_aspect_analysis",
    "parameters": {
        "bbox": [110.062408, 19.317623, 110.413971, 19.500253],
        "radius": 1
    }
}
```

### 3. 空间相交分析
```json
{
    "name": "spatial_intersection",
    "parameters": {
        "features_a": "collection_id_1",
        "features_b": "collection_id_2"
    }
}
```

## 📊 性能监控

增强版提供了完整的性能监控：

### 日志文件
- `logs/shandong_mcp.log` - 应用日志
- `logs/api_calls.log` - API调用日志

### 监控指标
- API调用耗时
- 操作执行时间
- 错误率统计
- 内存使用情况

## 🔌 集成示例

### 1. 在Claude Desktop中使用
```json
{
    "mcp": {
        "servers": {
            "shandong-analysis": {
                "command": "python",
                "args": ["path/to/shandong_mcp_server_enhanced.py"],
                "env": {}
            }
        }
    }
}
```

### 2. 通过HTTP接口使用
```javascript
// 连接SSE
const eventSource = new EventSource('http://localhost:8000/sse');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};

// 发送请求
fetch('http://localhost:8000/messages/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "coverage_aspect_analysis",
            "arguments": {
                "bbox": [110.062408, 19.317623, 110.413971, 19.500253]
            }
        }
    })
});
```

## 🎯 最佳实践

1. **选择合适的模式**
   - 本地开发：stdio模式
   - Web集成：HTTP模式

2. **监控日志**
   - 定期检查日志文件
   - 关注API调用性能

3. **错误处理**
   - 检查响应的success字段
   - 处理超时和网络错误

4. **性能优化**
   - 监控execution_time
   - 优化频繁调用的API

## 🔧 配置选项

### 环境变量
```bash
# API端点配置
export OGE_API_BASE_URL="http://172.30.22.116:16555/gateway/computation-api/process"
export INTRANET_API_BASE_URL="http://172.20.70.142:16555/gateway/computation-api/process"

# 日志级别
export LOG_LEVEL="INFO"
```

### 配置文件
可以创建`config.json`文件进行配置：
```json
{
    "server": {
        "name": "shandong-analysis",
        "version": "2.0.0"
    },
    "apis": {
        "oge_url": "http://172.30.22.116:16555/gateway/computation-api/process",
        "intranet_url": "http://172.20.70.142:16555/gateway/computation-api/process"
    },
    "logging": {
        "level": "INFO",
        "file": "logs/shandong_mcp.log"
    }
}
```

## 📈 性能对比

| 特性 | 原版 | 增强版 |
|------|------|--------|
| 传输方式 | stdio | stdio + HTTP |
| 响应格式 | 不统一 | 统一Result格式 |
| 日志系统 | 基础 | 结构化日志 |
| 性能监控 | 无 | 完整监控 |
| 错误处理 | 基础 | 增强错误处理 |
| 开发体验 | 一般 | 优秀 |

## 🛡️ 安全性

1. **认证**：支持Bearer Token认证
2. **CORS**：可配置跨域访问
3. **限流**：可添加请求限流
4. **日志**：完整的访问日志

## 📞 支持

如有问题，请查看：
1. 日志文件：`logs/shandong_mcp.log`
2. 健康检查：`http://localhost:8000/health`
3. 服务器信息：`http://localhost:8000/info` 