# MCP工具清单 - 山东耕地流出分析服务器

## 📊 工具总览

当前MCP服务器共有 **12个工具**，分为5个功能类别：

---

## 🔧 当前工具列表

### 1. 🌟 核心分析工具

#### 1.1 `execute_full_workflow`
- **功能**: 执行完整的山东耕地流出分析工作流
- **参数**: 
  - `enable_visualization` (bool): 是否生成最终可视化地图
  - `intermediate_results` (bool): 是否返回中间步骤结果
- **用途**: 一键执行完整分析流程

### 2. 🗺️ 地形分析工具

#### 2.1 `coverage_aspect_analysis`
- **功能**: 坡向分析 - 基于DEM数据计算坡向信息
- **参数**:
  - `bbox` (List[float]): 边界框坐标 [minLon, minLat, maxLon, maxLat]
  - `coverage_type` (str): 覆盖类型，默认"Coverage"
  - `pretreatment` (bool): 是否进行预处理，默认true
  - `product_value` (str): 产品数据源，默认"Platform:Product:ASTER_GDEM_DEM30"
  - `radius` (int): 计算半径，默认1

#### 2.2 `coverage_slope_analysis`
- **功能**: 坡度分析 - 基于DEM数据计算坡度信息
- **参数**: 同`coverage_aspect_analysis`

#### 2.3 `terrain_analysis_suite`
- **功能**: 地形分析套件 - 支持多种地形分析（坡度、坡向等）
- **参数**:
  - `bbox` (List[float]): 边界框坐标
  - `analysis_types` (List[str]): 分析类型列表，默认["slope", "aspect"]
  - 其他参数同上

### 3. 🔍 空间分析工具

#### 3.1 `spatial_intersection`
- **功能**: 空间相交分析
- **参数**:
  - `features_a` (str): 要素集合A的ID
  - `features_b` (str): 要素集合B的ID

### 4. 🔐 认证管理工具

#### 4.1 `get_oauth_token`
- **功能**: 获取OAuth认证Token
- **参数**:
  - `username` (str): 用户名
  - `password` (str): 密码
  - `client_id` (str): 客户端ID，默认"test"
  - `client_secret` (str): 客户端密钥，默认"123456"
  - `scopes` (str): 权限范围，默认"web"
  - `grant_type` (str): 授权类型，默认"password"

#### 4.2 `refresh_intranet_token`
- **功能**: 刷新内网认证Token并可选择性更新全局Token
- **参数**:
  - `username` (str): 用户名
  - `password` (str): 密码
  - `update_global_token` (bool): 是否更新全局使用的token，默认true

#### 4.3 `refresh_token_auto`
- **功能**: 自动刷新token - 使用预设的认证信息(edu_admin/123456)
- **参数**: 无（使用预设凭证）

### 5. 🔄 DAG批处理工具

#### 5.1 `execute_code_to_dag`
- **功能**: 将代码转化为DAG生成任务
- **参数**:
  - `code` (str): 要执行的OGE代码
  - `user_id` (str): 用户UUID，默认预设值
  - `sample_name` (str): 示例代码名称（可为空）
  - `auth_token` (str): 认证Token（可选）

#### 5.2 `submit_batch_task`
- **功能**: 提交批处理任务运行
- **参数**:
  - `dag_id` (str): DAG任务ID
  - `task_name` (str): 任务名称（可选）
  - `filename` (str): 文件名（可选）
  - `crs` (str): 坐标参考系统，默认"EPSG:4326"
  - `scale` (str): 比例尺，默认"1000"
  - `format` (str): 输出格式，默认"tif"
  - `username` (str): 用户名，默认预设值
  - `script` (str): 脚本代码
  - `auth_token` (str): 认证Token（可选）

#### 5.3 `query_task_status`
- **功能**: 查询批处理任务执行状态
- **参数**:
  - `dag_id` (str): DAG任务ID
  - `auth_token` (str): 认证Token（可选）

#### 5.4 `execute_dag_workflow`
- **功能**: 执行完整的DAG批处理工作流：代码转DAG -> 提交任务 -> (可选)等待完成
- **参数**:
  - `code` (str): OGE代码
  - `user_id` (str): 用户UUID，默认预设值
  - `sample_name` (str): 示例代码名称
  - `task_name` (str): 任务名称（可选）
  - `filename` (str): 文件名（可选）
  - `crs` (str): 坐标参考系统，默认"EPSG:4326"
  - `scale` (str): 比例尺，默认"1000"
  - `format` (str): 输出格式，默认"tif"
  - `username` (str): 用户名，默认预设值
  - `auth_token` (str): 认证Token（可选）
  - `auto_submit` (bool): 是否自动提交任务，默认true
  - `wait_for_completion` (bool): 是否等待任务完成，默认false
  - `check_interval` (int): 状态检查间隔（秒），默认10
  - `max_wait_time` (int): 最大等待时间（秒），默认300

---

## 📝 增删改查操作

### ➕ 添加新工具

```python
@mcp.tool()
async def your_new_tool(
    param1: str,
    param2: int = 100,
    ctx: Context = None
) -> str:
    """
    您的新工具描述
    
    Parameters:
    - param1: 参数描述
    - param2: 可选参数，默认100
    """
    operation = "新工具操作"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        # 您的工具逻辑
        result_data = {"status": "success"}
        
        result = Result.succ(
            data=result_data,
            msg=f"{operation}执行成功",
            operation=operation
        )
        
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            operation=operation
        )
        return result.model_dump_json()
```

### ✏️ 修改现有工具

1. 在文件中找到对应的工具函数
2. 修改参数、逻辑或描述
3. 测试修改后的功能

### 🗑️ 删除工具

1. 注释或删除`@mcp.tool()`装饰器
2. 删除整个函数定义

### 🔍 查看工具详情

使用grep搜索工具名称：
```bash
grep -n "async def 工具名" shandong_mcp_server_enhanced.py
```

---

## 🚀 使用建议

### 常用工具组合：

1. **地形分析流程**:
   ```
   refresh_token_auto -> terrain_analysis_suite -> coverage_aspect_analysis
   ```

2. **批处理工作流**:
   ```
   refresh_token_auto -> execute_dag_workflow
   ```

3. **完整分析**:
   ```
   refresh_token_auto -> execute_full_workflow
   ```

### 工具依赖关系：
- 所有需要API调用的工具都依赖有效的token
- DAG工具之间有顺序依赖关系
- 地形分析工具可以独立使用或组合使用 