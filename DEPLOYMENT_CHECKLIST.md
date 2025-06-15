# 🚀 MCP服务器部署检查清单

## ✅ 部署前检查

### 环境要求
- [ ] Python 3.8+ 已安装
- [ ] 可以访问内网OGE服务器
- [ ] 有足够的磁盘空间（至少50MB）

### 文件完整性
- [ ] `shandong_mcp_server.py` - 主服务器文件 (28KB)
- [ ] `deepseek_mcp_config_simple_test.json` - 配置文件
- [ ] `requirements.txt` - 依赖列表
- [ ] `README.md` - 部署指南
- [ ] `test_mcp_server.py` - 测试脚本
- [ ] `deploy_test.py` - 部署验证脚本

## 🔧 部署步骤

### 1. 环境设置
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置修改
```bash
# 运行部署验证（会自动更新配置）
python deploy_test.py
```

### 3. 测试验证
```bash
# 运行完整测试
python test_mcp_server.py
```

## 📊 功能验证

### MCP工具清单（13个）
- [ ] `execute_full_workflow` - 完整工作流
- [ ] `run_big_query` - SQL查询
- [ ] `get_feature_collection` - 获取要素集合
- [ ] `reproject_features` - 坐标投影
- [ ] `spatial_intersection` - 空间相交
- [ ] `spatial_erase` - 空间擦除
- [ ] `buffer_analysis` - 缓冲区分析
- [ ] `spatial_join` - 空间连接
- [ ] `calculate_area` - 面积计算
- [ ] `filter_by_metadata` - 属性过滤
- [ ] `field_subtract` - 字段减法
- [ ] `merge_feature_collections` - 合并要素
- [ ] `visualize_features` - 要素可视化

### 测试结果期望
- [ ] 所有依赖包安装成功
- [ ] MCP服务器可以启动
- [ ] 配置文件格式正确
- [ ] 13个工具全部可用

## 🌐 内网部署配置

### OGE服务器配置
在 `shandong_mcp_server.py` 第27行修改：
```python
OGE_API_BASE_URL = "http://你的内网OGE服务器IP:端口/gateway/computation-api/process"
```

### 网络检查
- [ ] 可以ping通OGE服务器
- [ ] 防火墙允许相关端口
- [ ] DNS解析正常（如使用域名）

## 🔗 AI客户端集成

### 配置文件路径
将以下配置添加到你的AI客户端：
```json
{
  "mcpServers": {
    "shandong-analysis": {
      "command": "/path/to/your/venv/bin/python",
      "args": ["/path/to/your/deployment/shandong_mcp_server.py"],
      "cwd": "/path/to/your/deployment"
    }
  }
}
```

### 测试连接
- [ ] AI客户端可以连接到MCP服务器
- [ ] 可以列出所有13个工具
- [ ] 可以成功调用简单工具（如`get_feature_collection`）

## 🐛 故障排除

### 常见问题
1. **导入错误**
   - 检查虚拟环境是否激活
   - 重新安装依赖：`pip install -r requirements.txt`

2. **路径错误**
   - 运行 `python deploy_test.py` 自动修复路径
   - 手动检查配置文件中的路径

3. **网络连接**
   - 检查OGE服务器地址是否正确
   - 测试网络连通性：`ping OGE服务器IP`

4. **权限问题**
   - 确保文件有执行权限：`chmod +x shandong_mcp_server.py`
   - 检查目录写权限

### 日志查看
MCP服务器启动时会显示详细日志，包括：
- 工具注册信息
- API调用状态
- 错误详情

## 📞 支持文档

- `README.md` - 详细部署指南
- `SHANDONG_MCP_USAGE_GUIDE.md` - 使用说明
- `OGE_API_FORMAT_FIXES.md` - API格式说明

## ✅ 部署完成确认

- [ ] 所有测试通过
- [ ] AI客户端成功连接
- [ ] 可以调用MCP工具
- [ ] OGE服务器连接正常
- [ ] 日志输出正常

---

**版本**: v1.1 (API格式修复版)  
**最后更新**: 2024年  
**支持的工作流**: 山东耕地流出分析（18步完整流程） 