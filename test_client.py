#!/usr/bin/env python3
"""
AI开发经理MCP服务测试客户端
"""

import asyncio
from fastmcp import Client


async def test_dev_manager_service():
    """测试开发经理服务的基本功能"""
    
    print("🚀 开始测试AI开发经理MCP服务...")
    
    # 直接连接到服务器实例
    from main import mcp
    
    async with Client(mcp) as client:
        print("\n✅ 成功连接到MCP服务器")
        
        # 1. 测试获取项目上下文
        print("\n📍 测试1: 获取项目上下文")
        context = await client.call_tool("get_project_context")
        print(f"项目上下文: {context[0].text}")
        
        # 2. 测试获取引导信息
        print("\n🧭 测试2: 获取规划阶段引导")
        guidance = await client.call_tool("get_guidance", {"phase": "planning"})
        print(f"引导信息:\n{guidance[0].text}")
        
        # 3. 测试开始新迭代
        print("\n🎯 测试3: 开始新迭代")
        iteration_result = await client.call_tool(
            "start_new_iteration", 
            {
                "version": "1.0.0",
                "prd": """
                # AI开发经理MCP服务 v1.0.0
                
                ## 项目目标
                开发一个基于FastMCP的AI开发经理服务，帮助AI管理软件开发生命周期。
                
                ## 核心功能
                1. 项目状态管理和上下文感知
                2. 迭代式开发流程管理
                3. 需求分解和任务管理
                4. 开发进度跟踪和报告生成
                5. 智能引导和最佳实践推荐
                
                ## 技术要求
                - 使用Python + FastMCP框架
                - 数据存储在.cursor/devplan目录
                - 支持语义化版本管理
                - 提供11个核心MCP工具
                """
            }
        )
        print(f"创建迭代结果: {iteration_result[0].text}")
        
        # 4. 测试查看当前迭代计划
        print("\n📋 测试4: 查看当前迭代计划")
        plan = await client.call_tool("view_current_iteration_plan")
        print(f"当前迭代计划:\n{plan[0].text}")
        
        # 5. 测试拆解目标为需求
        print("\n🔄 测试5: 拆解目标为需求")
        requirements = [
            {
                "title": "核心MCP服务框架",
                "description": "实现基于FastMCP的服务器框架，包含11个核心工具的注册和实现"
            },
            {
                "title": "数据模型和存储",
                "description": "设计并实现项目、迭代、需求、任务的数据模型，以及文件系统存储逻辑"
            },
            {
                "title": "引导系统",
                "description": "实现智能引导系统，为AI在不同开发阶段提供针对性指导"
            }
        ]
        
        decompose_result = await client.call_tool(
            "decompose_goal_into_requirements",
            {
                "goal_id": "main_goal", 
                "requirements": requirements
            }
        )
        print(f"拆解结果: {decompose_result[0].text}")
        
        # 6. 测试查看更新后的计划
        print("\n📊 测试6: 查看更新后的迭代计划")
        updated_plan = await client.call_tool("view_current_iteration_plan")
        print(f"更新后的计划:\n{updated_plan[0].text}")
        
        # 7. 测试列出迭代
        print("\n📚 测试7: 列出所有迭代")
        iterations = await client.call_tool("list_iterations")
        print(f"迭代列表: {iterations[0].text}")
        
        # 8. 测试获取工具列表
        print("\n🛠️ 测试8: 获取可用工具列表")
        tools = await client.list_tools()
        print(f"\n可用工具 ({len(tools)}个):")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        print("\n🎉 所有测试完成！AI开发经理MCP服务运行正常。")


if __name__ == "__main__":
    asyncio.run(test_dev_manager_service()) 