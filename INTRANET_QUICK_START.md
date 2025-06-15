# 内网MCP服务器快速部署验证清单

## 📦 打包文件信息
- **文件名**: `shandong_mcp_intranet_20250614_121033.zip`
- **大小**: 39KB
- **包含**: 18个文件 (含核心服务器、依赖、文档、测试文件)

## 🚀 3分钟快速部署

### 1. 解压文件
```bash
unzip shandong_mcp_intranet_20250614_121033.zip
cd shandong_mcp_intranet_20250614_121033
```

### 2. 安装依赖
```bash
pip install -r requirements_enhanced.txt
```

### 3. 测试启动 (快速验证)
```bash
# 启动增强版服务器 (HTTP模式，便于测试)
python start_server.py --version enhanced --mode http --port 8000
```

### 4. 验证服务
打开浏览器访问：
- `http://localhost:8000/health` - 应该返回健康状态
- `http://localhost:8000/info` - 应该返回服务器信息

## 🧪 功能测试

### 测试1: 坡向分析API
```bash
# 在新终端中运行
python simple_test\(1\).py
```

### 测试2: MCP服务器基础功能
```bash
python test_mcp_server.py
```

## ⚙️ 内网配置修改

在投入使用前，需要修改以下配置：

### 文件: `shandong_mcp_server.py` 和 `shandong_mcp_server_enhanced.py`
```python
# 第13-14行左右，修改内网API地址
INTRANET_API_BASE_URL = "http://YOUR_INTERNAL_OGE_IP:PORT/gateway/computation-api/process"

# 第15行左右，更新认证Token
INTRANET_AUTH_TOKEN = "Bearer YOUR_VALID_INTERNAL_TOKEN"
```

## 🎯 核心功能验证

### 坡向分析功能
大模型可以调用的工具：
- **工具名**: `coverage_aspect_analysis`
- **OGE算法**: `Coverage.aspect`
- **参数**: bbox (边界框), radius (半径)

### 示例调用
```json
{
  "name": "coverage_aspect_analysis",
  "arguments": {
    "bbox": [110.062408, 19.317623, 110.413971, 19.500253],
    "radius": 1
  }
}
```

## 📊 预期结果

### 成功指标
1. ✅ 服务器正常启动，无错误日志
2. ✅ HTTP健康检查返回200状态
3. ✅ 坡向分析测试通过
4. ✅ MCP协议正常响应

### 关键文件
- `shandong_mcp_server_enhanced.py` - 推荐使用的增强版
- `start_server.py` - 统一启动脚本
- `DEPLOY_README.md` - 详细部署说明

## 🔧 故障排除

### 常见问题
1. **依赖安装失败**: 检查Python版本 (建议3.8+)
2. **API调用失败**: 检查内网地址和Token
3. **端口冲突**: 修改启动端口 `--port 8001`

### 日志查看
```bash
# 查看应用日志
tail -f logs/shandong_mcp.log

# 查看API调用日志  
tail -f logs/api_calls.log
```

## 🎊 部署成功确认

当你看到以下输出，说明部署成功：
```
shandong_mcp - 2025-06-14 12:10:33 - INFO - 启动山东耕地流出分析MCP服务器 (HTTP模式) - 0.0.0.0:8000
```

并且访问 `http://localhost:8000/health` 返回：
```json
{
  "status": "healthy",
  "server": "shandong-cultivated-analysis-enhanced"
}
```

## 📞 支持联系

如有问题，请提供：
1. 错误日志截图
2. 服务器启动输出
3. 内网环境信息 (Python版本、OS等)

---

**🎯 这个MCP服务器将赋予大模型调用OGE执行坡向分析的能力！** 