# OAuth Token 集成功能说明

## 📋 功能概述

在山东耕地流出分析MCP服务器中新增了OAuth认证Token获取和管理功能，支持动态获取和刷新认证token，确保内网API调用的安全性和连续性。

## 🔧 新增MCP工具

### 1. get_oauth_token - 获取OAuth认证Token

**功能描述**: 通过用户名密码获取OAuth认证Token

**参数说明**:
- `username` (必需): 用户名
- `password` (必需): 密码  
- `client_id` (可选): 客户端ID，默认"test"
- `client_secret` (可选): 客户端密钥，默认"123456"
- `scopes` (可选): 权限范围，默认"web"
- `grant_type` (可选): 授权类型，默认"password"
- `base_url` (可选): 基础URL，默认使用内网地址
- `existing_token` (可选): 现有token用于认证

**返回信息**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "full_token": "Bearer eyJhbGciOiJIUzI1NiIs...",
    "raw_response": {...}
  },
  "msg": "获取OAuth Token 成功获取",
  "operation": "获取OAuth Token",
  "execution_time": 0.85
}
```

### 2. refresh_intranet_token - 刷新内网Token

**功能描述**: 刷新内网认证Token并可选择性更新全局Token配置

**参数说明**:
- `username` (必需): 用户名
- `password` (必需): 密码
- `update_global_token` (可选): 是否更新全局token，默认true

**返回信息**:
```json
{
  "success": true,
  "data": {
    "token_info": {...},
    "global_updated": true,
    "message": "Token已刷新并更新到全局配置"
  },
  "msg": "刷新内网Token 成功并已更新全局配置",
  "operation": "刷新内网Token"
}
```

## 🌐 API接口详情

### OAuth Token获取接口

**接口地址**: `http://172.20.70.142:16555/gateway/oauth/token`

**请求方法**: POST

**请求参数**:

查询参数 (Query Parameters):
- `scopes`: 权限范围 (例: "web")
- `client_secret`: 客户端密钥 (例: "123456")
- `client_id`: 客户端ID (例: "test")
- `username`: 用户名 (例: "edu_admin")
- `password`: 密码 (例: "123456")
- `grant_type`: 授权类型 (例: "password")

请求头 (Headers):
- `Content-Type`: application/json
- `Authorization`: Bearer {existing_token} (可选)

请求体 (Body):
```json
{
  "username": "edu_admin",
  "password": "123456"
}
```

## 🎯 使用场景

### 1. 动态Token获取
```python
# 通过MCP工具获取新token
result = await get_oauth_token(
    username="edu_admin",
    password="123456"
)
```

### 2. Token刷新与更新
```python
# 刷新token并更新全局配置
result = await refresh_intranet_token(
    username="edu_admin", 
    password="123456",
    update_global_token=True
)
```

### 3. 配合坡向分析使用
```python
# 1. 先刷新token
await refresh_intranet_token(username="edu_admin", password="123456")

# 2. 进行坡向分析
result = await coverage_aspect_analysis(
    bbox=[116.0, 36.0, 117.0, 37.0]
)
```

## 🔒 安全特性

1. **双重认证**: 支持现有token认证和用户名密码认证
2. **安全传输**: 使用HTTPS加密传输(内网环境)
3. **Token管理**: 自动提取和格式化token信息
4. **错误处理**: 完善的异常处理和错误提示
5. **日志记录**: 详细的操作日志和执行时间记录

## 📊 集成效果

### 原版服务器 (shandong_mcp_server.py)
- ✅ 添加 `get_oauth_token` 工具
- ✅ 添加 `refresh_intranet_token` 工具
- ✅ 支持标准MCP协议
- ✅ 与现有业务流程集成

### 增强版服务器 (shandong_mcp_server_enhanced.py)
- ✅ 基于FastMCP框架的OAuth集成
- ✅ 统一Result响应格式
- ✅ 完善的日志记录系统
- ✅ 性能计时和错误处理
- ✅ 支持HTTP模式实时监控

## 🚀 部署说明

### 1. 依赖要求
无需额外依赖，使用现有的httpx和asyncio库即可。

### 2. 配置要求
确保内网API地址正确配置:
```python
INTRANET_API_BASE_URL = "http://172.20.70.142:16555/gateway/computation-api/process"
```

### 3. 使用流程
1. 启动MCP服务器
2. 大模型调用 `get_oauth_token` 获取token
3. 调用 `refresh_intranet_token` 更新全局token
4. 正常使用其他分析工具

## 🧪 测试验证

已创建 `test_oauth_token.py` 测试脚本:
- ✅ 直接API调用测试
- ✅ MCP工具集成示例
- ✅ 错误处理验证
- ✅ 性能测试

## 💡 使用建议

1. **定期刷新**: 建议在执行长时间分析前先刷新token
2. **错误处理**: 监控token过期错误，自动重新获取
3. **日志监控**: 关注OAuth认证相关日志信息
4. **安全管理**: 妥善保管用户名密码等认证信息

## 🔗 相关文件

- `shandong_mcp_server.py` - 原版服务器OAuth集成
- `shandong_mcp_server_enhanced.py` - 增强版服务器OAuth集成
- `test_oauth_token.py` - OAuth功能测试脚本
- `OAUTH_TOKEN_INTEGRATION.md` - 本文档

通过这个OAuth token集成，大模型现在可以动态管理认证token，确保内网API调用的安全性和可靠性！🎉 