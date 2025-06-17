# AI开发经理 MCP服务

一个基于FastMCP框架的智能开发经理服务，帮助AI有条不紊地完成从需求分析、迭代规划、任务拆解到生成开发报告的完整软件开发生命周期。

## 🎯 项目概述

本MCP服务扮演AI的"开发经理"角色，提供：

- **项目状态机**: 作为项目元数据的唯一、可靠的数据源
- **AI引导者**: 为AI提供结构清晰的工具集和上下文感知的引导提示

### 核心特性

- ✅ **自动感知工作目录**: 基于当前工作目录进行项目管理
- ✅ **版本化迭代管理**: 支持语义化版本号和完整的迭代生命周期
- ✅ **结构化数据存储**: 所有数据存储在`.cursor/devplan/`目录
- ✅ **智能引导系统**: 根据开发阶段提供针对性指导
- ✅ **原子性操作**: 确保数据一致性和操作安全性

## 📦 安装与依赖

### 依赖要求

```bash
pip install -r requirements.txt
```

主要依赖：
- `fastmcp>=0.15.0` - MCP框架
- `pydantic>=2.0.0` - 数据验证
- `semantic-version>=2.10.0` - 版本号处理

### 项目结构

```
dev-manager/
├── main.py              # 主服务器文件
├── models.py            # 数据模型定义
├── services.py          # 核心服务逻辑
├── requirements.txt     # 项目依赖
└── README.md           # 项目说明
```

## 🚀 快速开始

### 1. 运行服务器

```bash
python main.py
```

### 2. 集成到Claude Desktop

在Claude Desktop配置文件中添加：

```json
{
  "mcpServers": {
    "dev-manager": {
      "command": "python",
      "args": ["/path/to/dev-manager/main.py"],
      "cwd": "/your/project/directory"
    }
  }
}
```

### 3. 基本使用流程

1. **获取项目上下文**
   ```
   调用: get_project_context()
   了解当前项目状态和工作目录
   ```

2. **开始新迭代**
   ```
   调用: start_new_iteration("1.0.0", "项目需求描述")
   创建新的开发版本
   ```

3. **拆解需求**
   ```
   调用: decompose_goal_into_requirements(goal_id, requirements_list)
   将高层目标分解为具体需求
   ```

4. **生成任务**
   ```
   调用: generate_tasks_for_requirement(requirement_id, tasks_list)
   为每个需求创建可执行的任务
   ```

5. **跟踪进度**
   ```
   调用: update_task_status(task_id, "done")
   实时更新任务完成状态
   ```

## 🛠️ 工具说明

### 类别一：上下文与引导工具

#### `get_project_context()`
- **功能**: 获取项目根目录、计划目录和当前活动迭代
- **用途**: AI的第一个调用，确保正确理解工作环境
- **返回**: ProjectContext对象

#### `get_guidance(phase)`
- **功能**: 根据开发阶段提供引导建议
- **参数**: `phase` - planning/decomposition/task_generation/reporting
- **用途**: 当AI不确定下一步时获取指导

### 类别二：迭代管理工具

#### `start_new_iteration(version, prd)`
- **功能**: 创建新的开发迭代
- **参数**: 
  - `version` - 语义化版本号(如"1.0.0")
  - `prd` - 产品需求文档
- **创建**: 版本目录、初始文件、活动状态

#### `list_iterations()`
- **功能**: 列出所有历史迭代
- **返回**: 包含版本、状态、统计信息的摘要列表
- **用途**: 了解项目演进历史

#### `complete_iteration(version)`
- **功能**: 完成并归档指定迭代
- **效果**: 更新状态、设置完成时间、清除活动状态

### 类别三：规划与拆解工具

#### `decompose_goal_into_requirements(goal_id, requirements)`
- **功能**: 将目标拆解为功能需求
- **参数**:
  - `goal_id` - 目标标识符
  - `requirements` - RequirementInput对象列表
- **用途**: 需求分析阶段的核心工具

#### `generate_tasks_for_requirement(requirement_id, tasks)`
- **功能**: 为需求生成具体任务
- **参数**:
  - `requirement_id` - 需求标识符  
  - `tasks` - TaskInput对象列表
- **特性**: 自动评估复杂度、支持依赖关系

### 类别四：执行与报告工具

#### `update_task_status(task_id, status)`
- **功能**: 更新任务完成状态
- **参数**: 
  - `task_id` - 任务标识符
  - `status` - todo/done
- **效果**: 实时进度跟踪、自动时间戳

#### `update_development_report(content, mode)`
- **功能**: 更新开发报告
- **参数**:
  - `content` - Markdown格式内容
  - `mode` - append/overwrite
- **用途**: 生成版本更新日志

### 类别五：查询与视图工具

#### `view_current_iteration_plan()`
- **功能**: 查看当前迭代的完整计划
- **返回**: 格式化的Markdown文档
- **内容**: 目标、需求、任务、进度统计

#### `view_development_report()`
- **功能**: 查看当前迭代的开发报告
- **返回**: 完整的Markdown报告内容
- **用途**: 审阅、发布版本说明

## 📁 数据存储结构

```
.cursor/devplan/
├── active_iteration.json      # 当前活动迭代
├── iterations_index.json      # 迭代索引
├── v1.0.0/                    # 版本目录
│   ├── iteration.json          # 迭代数据
│   └── report.md              # 开发报告
└── v1.1.0/
    ├── iteration.json
    └── report.md
```

## 🔧 配置选项

### 环境变量
- 无需特殊环境变量配置
- 自动使用当前工作目录作为项目根目录

### 自定义配置
可以通过修改`DevManagerService`构造函数参数来自定义项目根目录：

```python
service = DevManagerService(project_root="/custom/path")
```

## 📋 最佳实践

### 1. 版本号管理
- 使用语义化版本号（如1.0.0, 1.1.0, 2.0.0）
- 主版本号：重大功能或架构变更
- 次版本号：新功能添加
- 修订版本号：错误修复

### 2. 需求拆解原则
- 每个需求应该独立可实现
- 需求描述清晰具体，避免模糊表述
- 合理设置优先级，核心功能优先

### 3. 任务设计
- 每个任务应在1-4小时内完成
- 包含明确的验收标准
- 合理评估复杂度（low/medium/high）

### 4. 开发流程
1. **规划阶段**: 理解需求，创建迭代
2. **拆解阶段**: 分解目标为需求
3. **任务生成**: 为需求创建具体任务  
4. **执行阶段**: 完成任务，更新状态
5. **报告阶段**: 总结成果，完成迭代

## 🐛 故障排除

### 常见问题

**Q: 版本号格式错误**
A: 请使用语义化版本号格式，如"1.0.0"

**Q: 找不到活动迭代**  
A: 请先调用`start_new_iteration`创建迭代

**Q: 任务ID不存在**
A: 请确认任务ID正确，或先查看`view_current_iteration_plan`

### 数据恢复
如果数据损坏，可以从`.cursor/devplan/`目录的JSON文件手动恢复。

## 🤝 开发贡献

这是一个专门为AI开发经理场景设计的MCP服务。欢迎提交Issue和Pull Request。

### 开发环境搭建

```bash
git clone <repository>
cd dev-manager
pip install -r requirements.txt
python main.py
```

## 📄 许可证

本项目采用MIT许可证。详见LICENSE文件。

---

**自我挑战**: 

这个AI开发经理MCP服务的设计有什么潜在的改进空间？

1. **数据持久化**: 当前使用JSON文件存储，对于大型项目可能需要考虑数据库支持
2. **并发控制**: 多人协作时可能需要更强的锁机制
3. **模板系统**: 可以为不同类型的项目提供预定义的需求和任务模板
4. **集成能力**: 可以考虑与Git、CI/CD系统的集成
5. **可视化**: 可以增加进度图表、甘特图等可视化功能
6. **AI学习**: 可以基于历史数据为AI提供更智能的建议

这些改进点可以根据实际使用反馈逐步实现，确保服务始终满足实际开发需求！ 