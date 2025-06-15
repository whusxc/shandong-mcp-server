# 山东耕地流出分析 MCP服务器使用指南

## 🎯 概述

本MCP服务器基于 `shandong.txt` 工作流设计，提供**两种执行模式**：

1. **🔄 完整工作流模式** - 一键执行整个分析流程
2. **🔧 单步执行模式** - 单独调用任意分析步骤

## 📦 可用工具列表

### 🚀 完整工作流工具

#### `execute_full_workflow`
执行完整的山东耕地流出分析工作流（按照shandong.txt的18个步骤）

**参数**：
- `enable_visualization` (boolean): 是否生成最终可视化地图 (默认: true)
- `intermediate_results` (boolean): 是否返回中间步骤结果 (默认: false)

**示例调用**：
```
使用 execute_full_workflow 工具：
- enable_visualization: true
- intermediate_results: false
```

---

### 🛠️ 单步执行工具

#### 1. 数据获取工具

##### `run_big_query`
执行SQL查询获取要素集合
- `sql_query` (string): SQL查询语句
- `geometry_field` (string): 几何字段名 (默认: "geom")

##### `get_feature_collection`
获取指定的要素集合
- `collection_name` (string): 要素集合名称

##### `reproject_features`
要素集合坐标投影转换
- `feature_collection` (string): 输入要素集合ID
- `target_crs` (string): 目标坐标系 (默认: "EPSG:4527")

#### 2. 空间分析工具

##### `spatial_intersection`
两个要素集合的空间相交分析
- `features_a` (string): 要素集合A的ID
- `features_b` (string): 要素集合B的ID

##### `spatial_erase`
空间擦除分析（从A中去除B的重叠部分）
- `features_a` (string): 被擦除的要素集合ID
- `features_b` (string): 擦除用的要素集合ID

##### `buffer_analysis`
缓冲区分析
- `feature_collection` (string): 输入要素集合ID
- `distance` (number): 缓冲距离（米）

##### `spatial_join`
空间连接分析
- `target_features` (string): 目标要素集合ID
- `join_features` (string): 连接要素集合ID
- `properties` (array): 要连接的属性字段
- `reducer` (array): 聚合方式

#### 3. 属性计算工具

##### `calculate_area`
计算要素集合中每个要素的面积
- `feature_collection` (string): 输入要素集合ID

##### `filter_by_metadata`
基于属性字段过滤要素
- `feature_collection` (string): 输入要素集合ID
- `property_name` (string): 过滤字段名
- `operator` (string): 比较操作符 (greater_than/less_than/equals/not_equals)
- `value` (string/number): 比较值

##### `field_subtract`
字段减法运算（创建新字段 = field_a - field_b）
- `feature_collection` (string): 输入要素集合ID
- `field_a` (string): 被减数字段
- `field_b` (string): 减数字段
- `result_field` (string): 结果字段名

#### 4. 数据合并工具

##### `merge_feature_collections`
合并多个要素集合
- `feature_collections` (array): 要合并的要素集合ID列表

#### 5. 可视化工具

##### `visualize_features`
创建要素集合的可视化地图
- `feature_collection` (string): 要素集合ID
- `style_colors` (array): 样式颜色列表
- `map_name` (string): 地图名称

## 📋 完整工作流步骤详解

完整工作流 `execute_full_workflow` 按以下顺序执行：

1. **📊 获取耕地数据**: SQL查询旱地、水浇地、水田
2. **⛰️  获取坡度数据**: 获取podu坡度数据集
3. **🔍 过滤大坡度**: 筛选>15度坡地(pdjb>4)
4. **🗺️  坐标投影**: 转换到EPSG:4527坐标系
5. **🏙️  获取限制区域**: 城镇开发边界、自然保护地、生态红线
6. **🔄 空间相交分析**: 耕地与各限制区域相交
7. **✂️  空间擦除分析**: 从耕地中擦除限制区域
8. **🔬 细碎化处理**: 识别小于5亩的细碎耕地
9. **📦 合并结果**: 合并所有需流出的耕地
10. **🎨 可视化**: 生成最终地图(可选)

## 🚀 使用场景

### 场景1: 完整分析
智能体需要执行完整的耕地流出分析：
```
请使用 execute_full_workflow 工具执行完整的山东耕地流出分析
```

### 场景2: 单步调试
智能体需要单独测试某个分析步骤：
```
请使用 spatial_intersection 工具分析耕地与城镇开发边界的相交区域
```

### 场景3: 自定义流程
智能体根据具体需求调整分析流程：
```
1. 先获取耕地数据
2. 根据结果决定是否需要坐标转换
3. 选择性地应用某些限制条件
```

## ⚙️ 配置要求

### MCP配置文件
```json
{
  "mcpServers": {
    "shandong-cultivated": {
      "command": "/path/to/python",
      "args": ["/path/to/shandong_mcp_server.py"],
      "cwd": "/path/to/project",
      "env": {}
    }
  }
}
```

### 系统要求
- Python 3.8+
- httpx 库用于API调用
- mcp 库用于MCP协议
- 网络访问OGE API服务器

## 🔧 故障排除

### 常见问题

1. **API连接超时**
   - 检查OGE服务器状态
   - 调整httpx timeout设置

2. **数据ID不匹配**
   - 单步执行时需要使用正确的要素集合ID
   - 完整工作流会自动处理ID传递

3. **投影转换失败**
   - 确认源数据的坐标系
   - 检查目标CRS格式

## 📈 性能优化

- **完整工作流**: 适合生产环境一次性分析
- **单步执行**: 适合开发测试和错误排查
- **中间结果**: 开启时会占用更多内存但便于调试

## 🎯 最佳实践

1. **开发阶段**: 使用单步工具逐步验证
2. **测试阶段**: 启用intermediate_results查看中间结果
3. **生产阶段**: 使用完整工作流提高效率
4. **错误处理**: 检查每步的status字段判断执行结果 