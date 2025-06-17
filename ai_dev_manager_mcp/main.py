#!/usr/bin/env python3
"""
AI开发经理MCP服务器 - 主文件
使用fastmcp框架实现的智能开发经理，帮助AI管理项目开发流程
"""

import argparse
import sys
from typing import List
from fastmcp import FastMCP

from .models import (
    ProjectContext, IterationSummary, RequirementInput, TaskInput,
    TaskStatus, ReportMode, Phase
)
from .services import DevManagerService


def create_mcp_server(project_root: str = None) -> FastMCP:
    """创建配置好的MCP服务器实例"""
    # 创建FastMCP服务器实例
    mcp = FastMCP(
        name="AI开发经理 (AI Development Manager)",
        instructions="""
        这是一个智能开发经理MCP服务，可以帮助AI有条不紊地完成软件开发生命周期。
        
        主要功能：
        - 项目状态管理和上下文感知
        - 迭代式开发流程管理 
        - 需求分解和任务管理
        - 开发进度跟踪和报告生成
        - 智能引导和最佳实践推荐
        
        使用前请先调用 get_project_context 了解当前项目状态。
        """
    )

    # 初始化服务实例
    service = DevManagerService(project_root)

    # =============================================================================
    # 类别一：上下文与引导工具 (Context & Guidance)
    # =============================================================================

    @mcp.tool
    def get_project_context() -> ProjectContext:
        """
        获取当前项目的核心上下文信息。
        
        这是最重要的定位工具，用于解决AI可能混淆"工具安装目录"与"项目工作目录"的问题。
        在开始任何任务之前，AI应首先调用此工具以确保对当前操作环境有正确认知。
        
        Returns:
            ProjectContext: 包含项目根目录、计划目录和当前活动迭代的上下文信息
        """
        return service.get_project_context()

    @mcp.tool
    def get_guidance(phase: str) -> str:
        """
        根据指定的开发阶段，为AI提供下一步行动的结构化引导提示。
        
        当AI不确定下一步该做什么时，可以调用此工具获取明确的指示。
        
        Args:
            phase: 当前所处的阶段，可选值：'planning', 'decomposition', 'task_generation', 'reporting'
            
        Returns:
            str: 详细的指导性文本，告诉AI在该阶段的角色、目标和推荐使用的工具
        """
        try:
            phase_enum = Phase(phase)
            return service.get_guidance(phase_enum)
        except ValueError:
            return f"无效的阶段参数: {phase}. 有效值: planning, decomposition, task_generation, reporting"

    # =============================================================================
    # 类别二：迭代管理工具 (Iteration Management)
    # =============================================================================

    @mcp.tool
    def start_new_iteration(version: str, prd: str) -> str:
        """
        开启一个全新的开发迭代。这是所有规划工作的入口。
        
        该工具会创建对应的版本目录和初始文件，正式启动开发周期。
        AI在理解用户新需求并确定版本号后，调用此工具正式启动开发周期。
        
        Args:
            version: 必须符合语义化版本规范（如 "1.2.0"）的新版本号
            prd: 本次迭代的原始需求文档（PRD）或高阶目标描述
            
        Returns:
            str: 确认迭代已成功创建的文本消息
        """
        try:
            return service.start_new_iteration(version, prd)
        except Exception as e:
            return f"创建迭代失败: {str(e)}"

    @mcp.tool
    def list_iterations() -> List[IterationSummary]:
        """
        列出当前项目中所有已存在（包括已完成）的迭代版本及其状态。
        
        AI在规划新迭代时，调用此工具以了解项目的历史版本和演进情况，从而做出更合理的版本号决策。
        
        Returns:
            List[IterationSummary]: 包含所有迭代信息的列表，每个元素包括版本号、状态、任务统计等
        """
        try:
            return service.list_iterations()
        except Exception as e:
            return [{"error": f"获取迭代列表失败: {str(e)}"}]

    @mcp.tool
    def complete_iteration(version: str) -> str:
        """
        将一个进行中的迭代标记为"已完成"状态，并进行归档。
        
        当一个版本的所有任务和报告都完成后，调用此工具来正式关闭该迭代周期。
        
        Args:
            version: 要标记为完成的版本号
            
        Returns:
            str: 确认迭代状态已更新的文本消息
        """
        try:
            return service.complete_iteration(version)
        except Exception as e:
            return f"完成迭代失败: {str(e)}"

    # =============================================================================
    # 类别三：规划与拆解工具 (Planning & Decomposition)
    # =============================================================================

    @mcp.tool
    def decompose_goal_into_requirements(goal_id: str, requirements: List[RequirementInput]) -> str:
        """
        将高阶的、模糊的开发目标（来自PRD）拆解为一组清晰、独立、可实现的功能需求点。
        
        AI在理解了PRD之后，进行"分解思考"，然后调用此工具，将其思考结果（即拆分后的需求列表）持久化到当前迭代计划中。
        
        Args:
            goal_id: 要拆解的目标ID（如果目标不存在会自动创建）
            requirements: 需求对象列表，每个对象包含 title 和 description
            
        Returns:
            str: 确认已成功添加N个需求点的文本消息
        """
        try:
            return service.decompose_goal_into_requirements(goal_id, requirements)
        except Exception as e:
            return f"拆解目标失败: {str(e)}"

    @mcp.tool
    def generate_tasks_for_requirement(requirement_id: str, tasks: List[TaskInput]) -> str:
        """
        针对某一个具体的功能需求，生成更细粒度的、可执行的开发任务清单。
        
        AI在完成需求拆分后，对每一个需求点进行"实现思考"，然后调用此工具，将具体的开发步骤持久化。
        
        Args:
            requirement_id: 要生成任务的需求ID
            tasks: 任务对象列表，每个对象包含 title, description, complexity
            
        Returns:
            str: 确认已成功为指定需求添加N个任务的文本消息
        """
        try:
            return service.generate_tasks_for_requirement(requirement_id, tasks)
        except Exception as e:
            return f"生成任务失败: {str(e)}"

    # =============================================================================
    # 类别四：执行与报告工具 (Execution & Reporting)
    # =============================================================================

    @mcp.tool
    def update_task_status(task_id: str, status: str) -> dict:
        """
        更新单个开发任务的完成状态。
        
        在开发过程中，每当一个原子任务被完成时，由AI或用户调用，以实时更新项目进度。
        
        Args:
            task_id: 要更新的任务ID
            status: 新的状态，可选值：'todo', 'done'
            
        Returns:
            dict: 包含更新后任务信息的结构化对象
        """
        try:
            status_enum = TaskStatus(status)
            return service.update_task_status(task_id, status_enum)
        except ValueError:
            return {"error": f"无效的状态值: {status}. 有效值: todo, done"}
        except Exception as e:
            return {"error": f"更新任务状态失败: {str(e)}"}

    @mcp.tool
    def update_development_report(content: str, mode: str = "append") -> str:
        """
        创建或更新当前迭代的开发报告（Changelog / Release Notes）。
        
        在一组相关任务完成后，AI会被引导调用此工具，对已完成的工作进行总结，并将其记录到对人类友好的开发报告中。
        
        Args:
            content: 要写入报告的Markdown格式内容
            mode: 写入模式，可选值：'append' (追加), 'overwrite' (覆写)，默认为'append'
            
        Returns:
            str: 确认报告已更新的文本消息
        """
        try:
            mode_enum = ReportMode(mode)
            return service.update_development_report(content, mode_enum)
        except ValueError:
            return f"无效的模式参数: {mode}. 有效值: append, overwrite"
        except Exception as e:
            return f"更新开发报告失败: {str(e)}"

    # =============================================================================
    # 类别五：查询与视图工具 (Query & View)
    # =============================================================================

    @mcp.tool
    def view_current_iteration_plan() -> str:
        """
        以结构化的、人类可读的格式，完整展示当前活动迭代的所有信息。
        
        AI或用户在任何时候需要全面了解当前迭代的进展和计划全貌时调用。
        
        Returns:
            str: 格式化后的Markdown文本，清晰地展示当前迭代的目标、所有需求及其下的任务和各自的状态
        """
        try:
            return service.view_current_iteration_plan()
        except Exception as e:
            return f"查看迭代计划失败: {str(e)}"

    @mcp.tool
    def view_development_report() -> str:
        """
        获取并返回当前活动迭代的开发报告的完整内容。
        
        需要查看、审阅或发布当前版本更新日志时调用。
        
        Returns:
            str: 报告的Markdown原文
        """
        try:
            return service.view_development_report()
        except Exception as e:
            return f"查看开发报告失败: {str(e)}"

    return mcp


def main():
    """MCP服务器入口点"""
    parser = argparse.ArgumentParser(
        description="AI开发经理MCP服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  ai-dev-manager-mcp                           # 在当前目录启动
  ai-dev-manager-mcp -p /path/to/project       # 在指定目录启动
  uvx ai-dev-manager-mcp -p ~/my-project       # 使用uvx在指定目录启动
        """
    )
    parser.add_argument(
        '-p', '--project-root',
        help='项目根目录路径，默认为当前目录',
        default=None
    )
    
    args = parser.parse_args()
    
    # 创建MCP服务器实例
    mcp = create_mcp_server(args.project_root)
    
    # 运行MCP服务器，默认使用stdio传输
    mcp.run()


if __name__ == "__main__":
    main() 