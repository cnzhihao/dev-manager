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

from models import (
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
# 🎯 规划阶段引导

**当前阶段**: 需求分析和目标设定

**主要任务**:
1. **理解需求**: 仔细分析用户提供的PRD或需求文档
2. **创建迭代**: 使用 `start_new_iteration` 工具开始新的开发周期
3. **设定目标**: 明确这个版本要实现的核心目标

**推荐工具**:
- `get_project_context` - 了解当前项目状态
- `start_new_iteration` - 开始新的迭代
- `list_iterations` - 查看历史版本

**下一步**: 进入拆解阶段，将目标分解为具体的功能需求
            """,
            
            Phase.DECOMPOSITION: """
# 🔄 拆解阶段引导

**当前阶段**: 目标拆解为功能需求

**主要任务**:
1. **分析目标**: 将高层次目标分解为独立的功能模块
2. **定义需求**: 为每个功能模块编写清晰的需求描述
3. **需求验证**: 确保需求可测试、可实现、相互独立

**推荐工具**:
- `decompose_goal_into_requirements` - 拆解目标为需求列表
- `view_current_iteration_plan` - 查看当前规划状态

**拆解原则**:
- 每个需求应该是独立可实现的
- 需求描述要清晰具体，避免模糊表述
- 优先级明确，核心功能优先

**下一步**: 进入任务生成阶段，为每个需求创建具体的开发任务
            """,
            
            Phase.TASK_GENERATION: """
# ⚡ 任务生成阶段引导

**当前阶段**: 需求分解为具体任务

**主要任务**:
1. **任务分解**: 将每个需求拆解为可执行的开发任务
2. **复杂度评估**: 为每个任务标记复杂度(low/medium/high)
3. **执行顺序**: 考虑任务间的依赖关系，合理安排顺序

**推荐工具**:
- `generate_tasks_for_requirement` - 为需求生成任务列表
- `view_current_iteration_plan` - 查看完整的开发计划

**任务拆解原则**:
- 每个任务应该在1-4小时内完成
- 任务描述要具体可操作
- 包含验收标准和实现细节
- 合理评估复杂度

**下一步**: 开始执行开发任务，并及时更新进度
            """,
            
            Phase.REPORTING: """
# 📝 报告阶段引导

**当前阶段**: 开发总结和报告生成

**主要任务**:
1. **进度总结**: 汇总完成的功能和任务
2. **问题记录**: 记录开发过程中遇到的问题和解决方案
3. **版本发布**: 准备版本发布说明和更新日志

**推荐工具**:
- `update_development_report` - 更新开发报告
- `view_development_report` - 查看当前报告
- `complete_iteration` - 完成当前迭代

**报告内容建议**:
- 功能完成情况
- 技术难点和解决方案
- 性能优化和改进
- 已知问题和后续计划
- 用户使用指南

**完成条件**: 所有任务完成后，使用 `complete_iteration` 正式结束迭代
            """
        }
        
        return guidance_map.get(phase, "未知阶段，请检查phase参数是否正确") 