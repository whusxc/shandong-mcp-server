# Token自动刷新机制修复说明

## 🔍 问题描述

之前版本存在一个关键问题：当MCP工具函数执行过程中token过期时，虽然系统会自动刷新token，但工具函数依然无法获得最新的token，导致调用持续失败。

## 🐛 问题根因

### 原来的实现方式
```python
# 在工具函数中
headers = {
    "Content-Type": "application/json",
    "Authorization": INTRANET_AUTH_TOKEN  # ❌ 这里在函数开始时就固定了
}

api_result, execution_time = await call_api_with_timing(
    url=INTRANET_API_BASE_URL,
    json_data=api_payload,
    headers=headers  # ❌ 传递的是固定的headers
)
```

### 问题流程
1. 工具函数开始执行，构建headers（使用当前token）
2. API调用返回40003错误（token过期）
3. `call_api_with_timing`内部刷新了全局token
4. 但headers中的token仍是旧的，重试时依然失败

## ✅ 修复方案

### 1. 新增`use_intranet_token`参数
```python
async def call_api_with_timing(
    url: str,
    method: str = 'POST',
    json_data: dict = None,
    headers: dict = None,
    timeout: int = 120,
    auto_retry_on_token_expire: bool = True,
    use_intranet_token: bool = False  # ✅ 新增参数
) -> tuple[dict, float]:
```

### 2. 动态构建headers
```python
# 如果指定使用内网token，则动态更新headers
if use_intranet_token:
    if headers is None:
        headers = {"Content-Type": "application/json"}
    headers["Authorization"] = INTRANET_AUTH_TOKEN  # ✅ 动态获取最新token
    logger.info(f"使用内网token: {INTRANET_AUTH_TOKEN[:50]}...")
```

### 3. 重试时重新构建headers
```python
if success:
    logger.info("Token刷新成功，重新调用API...")
    
    # 重新调用API（递归，但禁用自动重试避免无限循环）
    return await call_api_with_timing(
        url=url,
        method=method,
        json_data=json_data,
        headers=None,  # ✅ 重置headers，让函数重新构建
        timeout=timeout,
        auto_retry_on_token_expire=False,
        use_intranet_token=use_intranet_token  # ✅ 保持标志
    )
```

### 4. 更新所有工具函数
```python
# 之前
api_result, execution_time = await call_api_with_timing(
    url=INTRANET_API_BASE_URL,
    json_data=api_payload,
    headers=headers
)

# 现在 ✅
api_result, execution_time = await call_api_with_timing(
    url=INTRANET_API_BASE_URL,
    json_data=api_payload,
    use_intranet_token=True  # ✅ 使用新参数
)
```

## 🛠️ 修复的工具函数

1. ✅ `coverage_aspect_analysis` - 坡向分析
2. ✅ `run_big_query` - 大数据查询
3. ✅ `execute_code_to_dag` - 代码转DAG
4. ✅ `submit_batch_task` - 提交批处理任务
5. ✅ `query_task_status` - 查询任务状态

## 🔄 新的执行流程

1. 工具函数调用`call_api_with_timing`，设置`use_intranet_token=True`
2. `call_api_with_timing`动态构建headers，使用最新的全局token
3. 如果API返回40003错误：
   - 自动刷新全局token
   - 重新调用自身，`headers=None`让函数重新构建
   - 新构建的headers包含最新token
4. 重试成功

## 🧪 测试验证

创建了`test_token_refresh.py`测试脚本：

```bash
python3 test_token_refresh.py
```

测试内容：
- ✅ 手动token刷新功能
- ✅ 正常API调用
- ✅ 模拟token过期自动刷新

## 📋 兼容性说明

### 向后兼容
- 原有的`headers`参数仍然支持
- 自定义token（如DAG API的auth_token参数）不受影响
- 只有明确设置`use_intranet_token=True`的调用才会启用自动刷新

### 参数优先级
1. 如果传递了自定义`auth_token` → 使用自定义token
2. 如果设置了`use_intranet_token=True` → 使用全局内网token（支持自动刷新）
3. 如果只传递了`headers` → 按原方式处理（不支持自动刷新）

## 🎯 预期效果

修复后，当工具函数遇到token过期时：
- ❌ 之前：调用失败，需要手动刷新token后重试
- ✅ 现在：自动刷新token并重试，用户无感知

## 🚀 部署建议

1. 更新MCP服务器代码
2. 运行测试脚本验证功能
3. 重新部署到172.20.70.142服务器
4. 内网用户可以正常使用，无需手动处理token过期问题

## 📝 使用示例

```python
# 在MCP客户端中调用任何工具
# 如果token过期，系统会自动处理：

# 用户调用
run_big_query()

# 系统日志会显示：
# "检测到token过期(40003)，尝试自动刷新..."
# "Token刷新成功，重新调用API..."
# "API调用成功 - 耗时: 2.34s"
```

这样就彻底解决了token过期导致工具调用失败的问题！🎉 