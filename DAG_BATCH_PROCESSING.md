# DAG批处理功能使用指南

## 概述

本文档介绍在MCP服务器增强版中新增的DAG批处理功能。该功能提供了完整的OGE代码批处理工作流，包括代码转换、任务提交和状态查询。

## 功能特性

### 新增工具

1. **execute_code_to_dag** - 将OGE代码转换为DAG任务
2. **submit_batch_task** - 提交批处理任务运行
3. **query_task_status** - 查询任务执行状态
4. **execute_dag_workflow** - 执行完整的DAG工作流

### API端点配置

- **DAG API基础URL**: `http://172.20.70.141/api/oge-dag-22`
- **代码转DAG**: `POST /executeCode`
- **提交任务**: `POST /addTaskRecord`
- **状态查询**: `GET /getState`

## 工具详细说明

### 1. execute_code_to_dag

将OGE代码解析转换为DAG任务。

**参数:**
- `code` (必需): 要执行的OGE代码
- `user_id` (可选): 用户UUID，默认使用预设值
- `sample_name` (可选): 示例代码名称
- `auth_token` (可选): 认证Token

**返回:**
```json
{
  "success": true,
  "msg": "代码转DAG任务成功，生成了1个DAG任务",
  "data": {
    "dags": {...},
    "dag_ids": ["f950cff2-07c8-461a-9c24-9162d59e2ef6_1745742165497_0"],
    "space_params": {...},
    "log": "",
    "user_id": "f950cff2-07c8-461a-9c24-9162d59e2ef6",
    "sample_name": "test.py"
  }
}
```

### 2. submit_batch_task

提交批处理任务到执行队列。

**参数:**
- `dag_id` (必需): DAG任务ID
- `task_name` (可选): 任务名称，默认自动生成
- `filename` (可选): 输出文件名，默认自动生成
- `crs` (可选): 坐标参考系统，默认"EPSG:4326"
- `scale` (可选): 比例尺，默认"1000"
- `format` (可选): 输出格式，默认"tif"
- `username` (可选): 用户名
- `script` (可选): 脚本代码
- `auth_token` (可选): 认证Token

**返回:**
```json
{
  "success": true,
  "msg": "提交批处理任务成功，任务状态: starting",
  "data": {
    "batch_session_id": "27",
    "task_id": "5c1aeed0-31bf-4ab0-9fbe-7c1ef8054c62",
    "dag_id": "f950cff2-07c8-461a-9c24-9162d59e2ef6_1745742165497_0",
    "state": "starting",
    ...
  }
}
```

### 3. query_task_status

查询任务的执行状态。

**参数:**
- `dag_id` (必需): DAG任务ID
- `auth_token` (可选): 认证Token

**返回:**
```json
{
  "success": true,
  "msg": "查询任务状态成功，当前状态: running",
  "data": {
    "dag_id": "f950cff2-07c8-461a-9c24-9162d59e2ef6_1745742165497_0",
    "status": "running",
    "is_completed": false,
    "is_running": true,
    "is_failed": false
  }
}
```

**状态说明:**
- `success`: 任务完成
- `running`: 正在运行
- `starting`: 启动中
- `failed`: 执行失败

### 4. execute_dag_workflow

执行完整的DAG批处理工作流，包含所有步骤。

**参数:**
- `code` (必需): OGE代码
- `user_id`, `sample_name`, `task_name`, `filename`, `crs`, `scale`, `format`, `username`: 同上
- `auth_token` (可选): 认证Token
- `auto_submit` (可选): 是否自动提交任务，默认true
- `wait_for_completion` (可选): 是否等待任务完成，默认false
- `check_interval` (可选): 状态检查间隔(秒)，默认10
- `max_wait_time` (可选): 最大等待时间(秒)，默认300

**返回:**
```json
{
  "success": true,
  "msg": "DAG批处理工作流成功，状态: submitted",
  "data": {
    "steps": [
      {
        "step": 1,
        "name": "代码转DAG",
        "success": true,
        "result": {...}
      },
      {
        "step": 2,
        "name": "提交批处理任务",
        "success": true,
        "result": {...}
      }
    ],
    "final_status": "submitted",
    "dag_ids": ["..."],
    "task_info": {...}
  }
}
```

## 使用示例

### 示例1: 基本使用

```python
# 1. 代码转DAG
dag_result = await execute_code_to_dag(
    code="""
    import oge
    oge.initialize()
    service = oge.Service()
    dem = service.getCoverage(coverageID="ASTGTM_N28E056", productID="ASTER_GDEM_DEM30")
    aspect = service.getProcess("Coverage.aspect").execute(dem, 1)
    aspect.export("aspect")
    """
)

# 2. 提交任务
dag_id = json.loads(dag_result)["data"]["dag_ids"][0]
submit_result = await submit_batch_task(
    dag_id=dag_id,
    task_name="my_aspect_analysis"
)

# 3. 状态查询
status_result = await query_task_status(dag_id=dag_id)
```

### 示例2: 完整工作流

```python
# 一次调用完成所有步骤
workflow_result = await execute_dag_workflow(
    code=oge_code,
    sample_name="DEM坡向分析.py",
    task_name="aspect_batch_task",
    auto_submit=True,
    wait_for_completion=True,
    max_wait_time=600
)
```

## 测试脚本

使用 `test_dag_workflow.py` 脚本测试所有DAG功能：

```bash
python test_dag_workflow.py
```

测试脚本将依次验证：
1. 代码转DAG功能
2. 批处理任务提交
3. 任务状态查询
4. 完整工作流

## 注意事项

1. **认证**: 所有API调用都需要有效的Bearer Token
2. **网络**: 确保可以访问内网API地址 `http://172.20.70.141`
3. **超时**: API调用设置了120秒超时，复杂任务可能需要更长时间
4. **状态监控**: 建议定期查询任务状态，避免长时间等待
5. **错误处理**: 注意检查每个步骤的返回结果，及时处理错误

## 常见问题

### Q: 代码转DAG失败怎么办？
A: 检查OGE代码语法是否正确，确认网络连接和认证Token是否有效。

### Q: 任务提交后一直是starting状态？
A: 这是正常现象，任务需要排队等待资源分配，请耐心等待。

### Q: 如何获取任务结果？
A: 当任务状态变为"success"时，结果文件会保存在指定的输出目录中。

### Q: 可以同时提交多个任务吗？
A: 可以，但建议控制并发数量，避免系统负载过高。

## 更新日志

### v2.1.0
- 新增DAG批处理功能
- 支持代码转DAG、任务提交、状态查询
- 提供完整工作流工具
- 增加详细的日志和错误处理 