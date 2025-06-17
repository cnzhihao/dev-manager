"""
AI开发经理MCP服务包
智能开发流程管理工具
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .main import create_mcp_server
from .services import DevManagerService
from .models import (
    ProjectContext, IterationSummary, RequirementInput, TaskInput,
    TaskStatus, ReportMode, Phase
)

__all__ = [
    "create_mcp_server",
    "DevManagerService", 
    "ProjectContext",
    "IterationSummary",
    "RequirementInput", 
    "TaskInput",
    "TaskStatus",
    "ReportMode",
    "Phase",
] 