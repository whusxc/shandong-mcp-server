# Token刷新使用指南

## 修正内容

✅ **已修正token获取接口地址**
- 原地址：`http://172.20.70.142:16555/gateway/oauth/token`
- 新地址：`http://172.20.70.141/api/oauth/token`

✅ **已修正token获取时的Authorization header问题**
- 问题：获取token时错误地包含了Authorization header
- 修正：获取token时不再包含任何Authorization header
- 影响：现在可以正确获取新token了

## 使用方式

### 1. 自动token刷新（推荐）
当API调用遇到token过期错误时，系统会自动刷新token并重试：

```python
# 系统会自动检测token过期并处理
result = await coverage_aspect_analysis(bbox=[116.0, 39.0, 117.0, 40.0])
```

### 2. 手动刷新token
如需手动刷新token，可使用以下工具：

#### 方式A：自动刷新（使用预设凭证）
```python
await refresh_token_auto()
```

#### 方式B：指定凭证刷新
```python
await refresh_intranet_token(
    username="edu_admin",
    password="123456",
    update_global_token=True
)
```

#### 方式C：直接获取token
```python
await get_oauth_token(
    username="edu_admin", 
    password="123456"
)
```

## 当前状态

- ✅ Token获取接口地址已修正
- ✅ 自动刷新逻辑已实现
- ✅ 支持手动刷新
- ✅ 错误检测和重试机制

## 内网部署建议

1. **将代码部署到内网环境**
2. **运行MCP服务器**：
   ```bash
   python shandong_mcp_server_enhanced.py --mode stdio
   ```
3. **测试token刷新**：
   ```bash
   python debug_token_issue.py
   ```

## 注意事项

- 当前token过期时间：2025-06-14 21:15:02（已过期）
- 新token会在成功获取后自动更新到全局配置
- 所有API调用都具备自动token刷新能力
- 本地电脑无法连接内网是正常现象，不影响内网环境使用 