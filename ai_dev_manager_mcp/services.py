"""
核心服务类 - AI开发经理MCP服务
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import semantic_version

from .models import (
    ProjectContext, Iteration, Goal, Requirement, Task, IterationSummary,
    IterationStatus, TaskStatus, RequirementInput, TaskInput, ReportMode, Phase
)


class DevManagerService:
    """开发经理核心服务类"""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        初始化服务
        
        Args:
            project_root: 项目根目录路径，如果为None则使用当前工作目录
        """
        self.project_root = Path(project_root or os.getcwd()).resolve()
        self.plan_directory = self.project_root / ".cursor" / "devplan"
        self._ensure_plan_directory()
    
    def _ensure_plan_directory(self) -> None:
        """确保计划目录存在"""
        self.plan_directory.mkdir(parents=True, exist_ok=True)
    
    def _get_active_iteration_file(self) -> Path:
        """获取活动迭代文件路径"""
        return self.plan_directory / "active_iteration.json"
    
    def _get_iterations_index_file(self) -> Path:
        """获取迭代索引文件路径"""
        return self.plan_directory / "iterations_index.json"
    
    def _get_iteration_directory(self, version: str) -> Path:
        """获取特定版本的迭代目录路径"""
        return self.plan_directory / f"v{version}"
    
    def _validate_version(self, version: str) -> None:
        """验证版本号格式"""
        try:
            semantic_version.Version(version)
        except ValueError as e:
            raise ValueError(f"无效的版本号格式: {version}. 请使用语义化版本号格式 (如 1.0.0)")
    
    def _load_json_file(self, file_path: Path, default_value: Any = None) -> Any:
        """安全加载JSON文件"""
        if not file_path.exists():
            return default_value
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise RuntimeError(f"无法读取文件 {file_path}: {e}")
    
    def _save_json_file(self, file_path: Path, data: Any) -> None:
        """安全保存JSON文件（原子操作）"""
        temp_path = file_path.with_suffix('.tmp')
        try:
            # 先写入临时文件
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            # 原子性移动到目标文件
            shutil.move(str(temp_path), str(file_path))
        except Exception as e:
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()
            raise RuntimeError(f"无法保存文件 {file_path}: {e}")
    
    def get_project_context(self) -> ProjectContext:
        """获取项目上下文信息"""
        active_iteration = self._load_json_file(self._get_active_iteration_file())
        
        return ProjectContext(
            project_root=str(self.project_root),
            plan_directory=str(self.plan_directory),
            active_iteration=active_iteration.get("version") if active_iteration else None
        )
    
    def start_new_iteration(self, version: str, prd: str) -> str:
        """开始新的迭代"""
        self._validate_version(version)
        
        # 检查版本是否已存在
        iteration_dir = self._get_iteration_directory(version)
        if iteration_dir.exists():
            raise ValueError(f"版本 {version} 已存在，请使用不同的版本号")
        
        # 创建迭代目录
        iteration_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建初始迭代数据
        iteration = Iteration(version=version, prd=prd)
        self._save_iteration(iteration)
        
        # 更新活动迭代
        self._save_json_file(self._get_active_iteration_file(), {"version": version})
        
        # 更新迭代索引
        self._update_iterations_index(version, IterationStatus.PLANNING)
        
        return f"已成功创建新迭代 v{version}"
    
    def _save_iteration(self, iteration: Iteration) -> None:
        """保存迭代数据到文件"""
        iteration_dir = self._get_iteration_directory(iteration.version)
        
        # 保存迭代元数据
        iteration_file = iteration_dir / "iteration.json"
        self._save_json_file(iteration_file, iteration.model_dump())
        
        # 初始化空的报告文件
        report_file = iteration_dir / "report.md"
        if not report_file.exists():
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"# 开发报告 - v{iteration.version}\n\n")
                f.write(f"## 版本概述\n\n{iteration.prd}\n\n")
                f.write("## 开发日志\n\n")
    
    def _load_iteration(self, version: str) -> Optional[Iteration]:
        """加载迭代数据"""
        iteration_file = self._get_iteration_directory(version) / "iteration.json"
        data = self._load_json_file(iteration_file)
        return Iteration(**data) if data else None
    
    def _update_iterations_index(self, version: str, status: IterationStatus) -> None:
        """更新迭代索引"""
        index_file = self._get_iterations_index_file()
        index_data = self._load_json_file(index_file, {})
        
        index_data[version] = {
            "status": status.value,
            "updated_at": datetime.now().isoformat()
        }
        
        self._save_json_file(index_file, index_data)
    
    def list_iterations(self) -> List[IterationSummary]:
        """列出所有迭代"""
        summaries = []
        
        # 遍历所有版本目录
        for version_dir in self.plan_directory.glob("v*"):
            if not version_dir.is_dir():
                continue
                
            version = version_dir.name[1:]  # 移除 'v' 前缀
            iteration = self._load_iteration(version)
            
            if iteration:
                # 统计任务信息
                total_tasks = 0
                completed_tasks = 0
                total_requirements = 0
                
                for goal in iteration.goals:
                    total_requirements += len(goal.requirements)
                    for req in goal.requirements:
                        total_tasks += len(req.tasks)
                        completed_tasks += sum(1 for task in req.tasks if task.status == TaskStatus.DONE)
                
                summary = IterationSummary(
                    version=iteration.version,
                    status=iteration.status,
                    created_at=iteration.created_at,
                    completed_at=iteration.completed_at,
                    goals_count=len(iteration.goals),
                    requirements_count=total_requirements,
                    tasks_count=total_tasks,
                    completed_tasks_count=completed_tasks
                )
                summaries.append(summary)
        
        # 按版本号排序
        summaries.sort(key=lambda x: semantic_version.Version(x.version), reverse=True)
        return summaries
    
    def complete_iteration(self, version: str) -> str:
        """完成迭代"""
        iteration = self._load_iteration(version)
        if not iteration:
            raise ValueError(f"迭代 {version} 不存在")
        
        if iteration.status == IterationStatus.COMPLETED:
            return f"迭代 v{version} 已经是完成状态"
        
        # 更新状态
        iteration.status = IterationStatus.COMPLETED
        iteration.completed_at = datetime.now()
        
        # 保存更新
        self._save_iteration(iteration)
        self._update_iterations_index(version, IterationStatus.COMPLETED)
        
        # 如果这是活动迭代，清除活动状态
        active_iter = self._load_json_file(self._get_active_iteration_file())
        if active_iter and active_iter.get("version") == version:
            self._save_json_file(self._get_active_iteration_file(), {})
        
        return f"已成功完成迭代 v{version}"
    
    def decompose_goal_into_requirements(self, goal_id: str, requirements: List[RequirementInput]) -> str:
        """将目标拆解为需求"""
        context = self.get_project_context()
        if not context.active_iteration:
            raise ValueError("当前没有活动的迭代，请先开始一个新迭代")
        
        iteration = self._load_iteration(context.active_iteration)
        if not iteration:
            raise ValueError(f"无法加载活动迭代 {context.active_iteration}")
        
        # 查找目标
        goal = None
        for g in iteration.goals:
            if g.id == goal_id:
                goal = g
                break
        
        if not goal:
            # 如果目标不存在，创建一个默认目标
            goal = Goal(
                id=goal_id,
                title="主要开发目标",
                description=iteration.prd
            )
            iteration.goals.append(goal)
        
        # 添加需求
        for req_input in requirements:
            requirement = Requirement(
                title=req_input.title,
                description=req_input.description
            )
            goal.requirements.append(requirement)
        
        # 保存更新
        self._save_iteration(iteration)
        
        return f"已成功为目标添加 {len(requirements)} 个需求"
    
    def generate_tasks_for_requirement(self, requirement_id: str, tasks: List[TaskInput]) -> str:
        """为需求生成任务"""
        context = self.get_project_context()
        if not context.active_iteration:
            raise ValueError("当前没有活动的迭代，请先开始一个新迭代")
        
        iteration = self._load_iteration(context.active_iteration)
        if not iteration:
            raise ValueError(f"无法加载活动迭代 {context.active_iteration}")
        
        # 查找需求
        requirement = None
        for goal in iteration.goals:
            for req in goal.requirements:
                if req.id == requirement_id:
                    requirement = req
                    break
            if requirement:
                break
        
        if not requirement:
            raise ValueError(f"需求 {requirement_id} 不存在")
        
        # 添加任务
        for task_input in tasks:
            task = Task(
                title=task_input.title,
                description=task_input.description,
                complexity=task_input.complexity
            )
            requirement.tasks.append(task)
        
        # 更新迭代状态为进行中
        if iteration.status == IterationStatus.PLANNING:
            iteration.status = IterationStatus.IN_PROGRESS
        
        # 保存更新
        self._save_iteration(iteration)
        self._update_iterations_index(iteration.version, iteration.status)
        
        return f"已成功为需求 '{requirement.title}' 添加 {len(tasks)} 个任务"
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> Dict[str, Any]:
        """更新任务状态"""
        context = self.get_project_context()
        if not context.active_iteration:
            raise ValueError("当前没有活动的迭代")
        
        iteration = self._load_iteration(context.active_iteration)
        if not iteration:
            raise ValueError(f"无法加载活动迭代 {context.active_iteration}")
        
        # 查找任务
        task = None
        for goal in iteration.goals:
            for req in goal.requirements:
                for t in req.tasks:
                    if t.id == task_id:
                        task = t
                        break
                if task:
                    break
            if task:
                break
        
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")
        
        # 更新状态
        old_status = task.status
        task.status = status
        
        if status == TaskStatus.DONE and old_status != TaskStatus.DONE:
            task.completed_at = datetime.now()
        elif status == TaskStatus.TODO:
            task.completed_at = None
        
        # 保存更新
        self._save_iteration(iteration)
        
        return {
            "task_id": task.id,
            "title": task.title,
            "old_status": old_status.value,
            "new_status": status.value,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
    
    def update_development_report(self, content: str, mode: ReportMode = ReportMode.APPEND) -> str:
        """更新开发报告"""
        context = self.get_project_context()
        if not context.active_iteration:
            raise ValueError("当前没有活动的迭代")
        
        report_file = self._get_iteration_directory(context.active_iteration) / "report.md"
        
        if mode == ReportMode.OVERWRITE:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(content)
        else:  # APPEND
            with open(report_file, 'a', encoding='utf-8') as f:
                f.write(f"\n\n---\n*更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                f.write(content)
        
        return f"已成功更新开发报告 ({'覆写' if mode == ReportMode.OVERWRITE else '追加'}模式)"
    
    def view_current_iteration_plan(self) -> str:
        """查看当前迭代计划"""
        context = self.get_project_context()
        if not context.active_iteration:
            return "当前没有活动的迭代。请先使用 start_new_iteration 开始一个新迭代。"
        
        iteration = self._load_iteration(context.active_iteration)
        if not iteration:
            return f"无法加载活动迭代 {context.active_iteration}"
        
        # 构建Markdown格式的计划视图
        plan_md = f"# 迭代计划 - v{iteration.version}\n\n"
        plan_md += f"**状态**: {iteration.status.value}\n"
        plan_md += f"**创建时间**: {iteration.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        if iteration.completed_at:
            plan_md += f"**完成时间**: {iteration.completed_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        plan_md += f"\n## 产品需求文档\n\n{iteration.prd}\n\n"
        
        if not iteration.goals:
            plan_md += "## 目标和需求\n\n*尚未定义目标和需求*\n"
        else:
            plan_md += "## 目标和需求\n\n"
            for goal in iteration.goals:
                plan_md += f"### 🎯 {goal.title}\n\n{goal.description}\n\n"
                
                if not goal.requirements:
                    plan_md += "*尚未拆解需求*\n\n"
                else:
                    for req in goal.requirements:
                        plan_md += f"#### 📋 {req.title}\n\n{req.description}\n\n"
                        
                        if not req.tasks:
                            plan_md += "*尚未生成任务*\n\n"
                        else:
                            plan_md += "**任务列表**:\n\n"
                            for task in req.tasks:
                                status_icon = "✅" if task.status == TaskStatus.DONE else "⏳"
                                complexity_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}[task.complexity.value]
                                plan_md += f"- {status_icon} {complexity_icon} **{task.title}**: {task.description}\n"
                            plan_md += "\n"
        
        # 添加统计信息
        total_tasks = sum(len(req.tasks) for goal in iteration.goals for req in goal.requirements)
        completed_tasks = sum(1 for goal in iteration.goals for req in goal.requirements for task in req.tasks if task.status == TaskStatus.DONE)
        
        plan_md += "## 📊 进度统计\n\n"
        plan_md += f"- **总目标数**: {len(iteration.goals)}\n"
        plan_md += f"- **总需求数**: {sum(len(goal.requirements) for goal in iteration.goals)}\n"
        plan_md += f"- **总任务数**: {total_tasks}\n"
        plan_md += f"- **已完成任务**: {completed_tasks}\n"
        if total_tasks > 0:
            progress = (completed_tasks / total_tasks) * 100
            plan_md += f"- **完成进度**: {progress:.1f}%\n"
        
        return plan_md
    
    def view_development_report(self) -> str:
        """查看开发报告"""
        context = self.get_project_context()
        if not context.active_iteration:
            return "当前没有活动的迭代。请先使用 start_new_iteration 开始一个新迭代。"
        
        report_file = self._get_iteration_directory(context.active_iteration) / "report.md"
        
        if not report_file.exists():
            return f"迭代 v{context.active_iteration} 的开发报告不存在"
        
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                return f.read()
        except OSError as e:
            return f"无法读取开发报告: {e}"
    
    def get_guidance(self, phase: Phase) -> str:
        """获取阶段引导信息"""
        guidance_map = {
            Phase.PLANNING: """
# 🏛️ 阶段一：规划与奠基 (Planning & Foundation)

**当前角色**: **战略架构师 (Strategic Architect)**

**当前阶段**: 您接收到了一个新的业务目标或产品需求文档(PRD)。您的任务是将其从一个模糊的想法，转化为一个已定义、已启动、版本化的开发迭代。

**核心任务**:
1.  **理解商业意图**: 深入分析PRD，明确本次迭代要解决的核心问题和商业价值。
2.  **定义范围与版本**: 确定此迭代的边界。为它赋予一个清晰的语义化版本号（如 1.2.0）。
3.  **正式启动迭代**: 创建迭代的"容器"，为后续所有规划和开发工作奠定基础。

**推荐工具**:
- `get_project_context`: 检查当前项目状态，确保没有正在进行的迭代。
- `list_iterations`: 查看历史迭代，以决定合适的版本号。
- `start_new_iteration`: 使用确定的版本号和PRD描述，正式开启新的迭代。

**下一步**: 迭代成功创建后，您将进入"蓝图设计"阶段，将宏观目标拆解为具体的系统功能模块。
    """,

    Phase.DECOMPOSITION: """
# 🏛️ 阶段二：蓝图设计与需求分解 (Blueprint & Decomposition)

**当前角色**: **系统设计师 (System Designer)**

**当前阶段**: 开发迭代已启动。现在您需要将宏大的版本目标，拆解成高内聚、低耦合的功能模块或服务（即"需求"）。这是设计的核心阶段。

**核心任务**:
1.  **架构性拆分**: 将PRD描述的整体功能，分解为逻辑上独立的功能单元。思考："这个系统应该由哪几个主要部分组成？"
2.  **明确模块职责**: 为每个功能单元（Requirement）编写清晰的描述，定义它的输入、输出和核心职责。
3.  **验证设计**: 确保这些模块组合起来能够完整地实现版本目标，并且模块之间接口清晰。

**推荐工具**:
- `view_current_iteration_plan`: 查看当前迭代的PRD和目标，作为拆解的依据。
- `decompose_goal_into_requirements`: 将您设计好的功能模块列表，持久化到迭代计划中。

**下一步**: 完成高层蓝图设计后，您将进入"任务生成"阶段，为每一个功能模块规划具体的实现路径和工程任务。
    """,

    Phase.TASK_GENERATION: """
# 🏛️ 阶段三：任务规划与实现设计 (Task Planning & Implementation Design)

**当前角色**: **总工程师 (Chief Engineer)**

**当前阶段**: 系统的高层蓝图（需求）已经确定。您的任务是为每一个独立的需求模块，设计出具体的、可执行的工程任务清单。您需要通过序列化提问，深入思考实现细节。

**核心思维流程**:
1.  **理解需求**: 彻底分析单个需求的目标和边界。
2.  **提出战略性问题**: 针对架构、技术选型、集成、安全、性能、数据等方面提出具体问题。
3.  **分析响应并制定计划**: 基于问题的答案，创建详细、可操作的实施步骤，并评估其复杂度。
4.  **迭代优化**: 持续提问和优化，直到实现路径完全清晰。

**主要任务**:
1.  **任务分解**: 将每个需求拆解为可执行的开发任务。
2.  **复杂度评估**: 为每个任务标记复杂度。
3.  **执行顺序**: 考虑任务间的依赖关系，合理安排顺序。

**推荐工具**:
- `generate_tasks_for_requirement`: 将您为某个需求设计好的详细任务列表，提交并保存到迭代计划中。
- `view_current_iteration_plan`: 查看完整的开发计划，了解任务在整个项目中的位置。

**下一步**: 所有任务规划完毕后，进入开发执行阶段。在完成每个任务后，及时更新其状态。
    """,

    Phase.REPORTING: """
# 🏛️ 阶段四：总结与交付 (Review & Delivery)

**当前角色**: **发布经理 (Release Manager)**

**当前阶段**: 本次迭代的核心开发任务已完成。您的职责是总结工作成果，生成对内对外的交付物（如开发报告、更新日志），并正式关闭本次迭代。

**核心任务**:
1.  **工作成果总结**: 汇总所有已完成的功能和任务，形成一份清晰的交付清单。
2.  **编写开发报告**: 记录开发过程中的关键决策、遇到的问题、解决方案以及任何需要注意的事项。这份报告对团队知识传承至关重要。
3.  **完成并归档**: 将迭代标记为"已完成"，使其成为项目历史上一个不可变的里程碑。

**推荐工具**:
- `update_development_report`: 撰写或追加开发报告/版本说明。
- `view_development_report`: 查看和审阅报告的当前内容。
- `complete_iteration`: 在所有工作和文档都完成后，调用此工具正式结束当前迭代周期。

**下一步**: 完成迭代后，您可以选择开启一个新的迭代，或根据需要进行其他项目维护工作。
            """
        }
        
        return guidance_map.get(phase, "未知阶段，请检查phase参数是否正确") 