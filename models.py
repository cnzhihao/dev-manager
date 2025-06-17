"""
数据模型定义 - AI开发经理MCP服务
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    """任务状态枚举"""
    TODO = "todo"
    DONE = "done"


class IterationStatus(str, Enum):
    """迭代状态枚举"""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskComplexity(str, Enum):
    """任务复杂度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReportMode(str, Enum):
    """报告更新模式枚举"""
    APPEND = "append"
    OVERWRITE = "overwrite"


class Phase(str, Enum):
    """开发阶段枚举"""
    PLANNING = "planning"
    DECOMPOSITION = "decomposition"
    TASK_GENERATION = "task_generation"
    REPORTING = "reporting"


class ProjectContext(BaseModel):
    """项目上下文信息"""
    project_root: str = Field(..., description="项目根目录的绝对路径")
    plan_directory: str = Field(..., description="计划存储目录的绝对路径")
    active_iteration: Optional[str] = Field(None, description="当前活动的迭代版本号")


class Task(BaseModel):
    """开发任务"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="任务唯一标识")
    title: str = Field(..., description="任务标题")
    description: str = Field(..., description="任务详细描述")
    complexity: TaskComplexity = Field(..., description="任务复杂度")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="任务状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class Requirement(BaseModel):
    """功能需求"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="需求唯一标识")
    title: str = Field(..., description="需求标题")
    description: str = Field(..., description="需求详细描述")
    tasks: List[Task] = Field(default_factory=list, description="相关任务列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class Goal(BaseModel):
    """项目目标"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="目标唯一标识")
    title: str = Field(..., description="目标标题")
    description: str = Field(..., description="目标详细描述")
    requirements: List[Requirement] = Field(default_factory=list, description="相关需求列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class Iteration(BaseModel):
    """开发迭代"""
    version: str = Field(..., description="语义化版本号")
    prd: str = Field(..., description="产品需求文档或目标描述")
    status: IterationStatus = Field(default=IterationStatus.PLANNING, description="迭代状态")
    goals: List[Goal] = Field(default_factory=list, description="迭代目标列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class IterationSummary(BaseModel):
    """迭代摘要信息（用于列表显示）"""
    version: str = Field(..., description="版本号")
    status: IterationStatus = Field(..., description="迭代状态")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    goals_count: int = Field(default=0, description="目标数量")
    requirements_count: int = Field(default=0, description="需求数量")
    tasks_count: int = Field(default=0, description="任务数量")
    completed_tasks_count: int = Field(default=0, description="已完成任务数量")


class RequirementInput(BaseModel):
    """需求输入模型（用于API接口）"""
    title: str = Field(..., description="需求标题")
    description: str = Field(..., description="需求详细描述")


class TaskInput(BaseModel):
    """任务输入模型（用于API接口）"""
    title: str = Field(..., description="任务标题")
    description: str = Field(..., description="任务详细描述")
    complexity: TaskComplexity = Field(..., description="任务复杂度") 