#!/usr/bin/env python3
"""
事故预想智能体测试脚本
测试事故预想智能体的各项功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from aperag.agent.core.models import AgentRole, AgentState
from aperag.agent.registry import agent_registry
from aperag.agent.specialists.accident_deduction_agent import AccidentDeductionAgent


async def test_accident_deduction_agent():
    """测试事故预想智能体"""
    
    print("=" * 80)
    print("事故预想智能体测试")
    print("=" * 80)
    
    # 1. 创建智能体实例
    print("\n1. 创建事故预想智能体实例...")
    agent = AccidentDeductionAgent(llm_service=None)
    print(f"   ✓ 智能体名称: {agent.name}")
    print(f"   ✓ 智能体角色: {agent.role}")
    print(f"   ✓ 智能体描述: {agent.description}")
    print(f"   ✓ 可用工具: {agent.tools}")
    
    # 2. 创建智能体状态
    print("\n2. 创建智能体状态...")
    state = AgentState(session_id="test-accident-deduction-001")
    print(f"   ✓ 会话ID: {state.session_id}")
    
    # 3. 测试事故预想生成
    print("\n3. 测试事故预想生成...")
    print("   查询: #1主变重瓦斯保护动作事故预想")
    
    input_data = {
        "task": "#1主变重瓦斯保护动作事故预想"
    }
    
    try:
        result = await agent.run(state, input_data)
        
        print("\n   ✓ 执行成功!")
        print(f"\n   思维链步骤数: {len(state.thinking_stream)}")
        
        # 显示思维链
        print("\n   思维链:")
        for i, step in enumerate(state.thinking_stream, 1):
            print(f"   [{i}] [{step.step_type}] {step.description}")
        
        # 显示结果
        print("\n   生成的事故预想报告:")
        print("   " + "-" * 76)
        answer = result.get("answer", "")
        for line in answer.split("\n")[:30]:  # 只显示前30行
            print(f"   {line}")
        if len(answer.split("\n")) > 30:
            print(f"   ... (还有 {len(answer.split('\n')) - 30} 行)")
        print("   " + "-" * 76)
        
        # 显示事故预想数据
        if "deduction" in result:
            deduction = result["deduction"]
            print(f"\n   事故预想数据:")
            print(f"   - 标题: {deduction.get('title', 'N/A')}")
            print(f"   - 设备: {deduction.get('equipment', 'N/A')}")
            print(f"   - 事故类型: {deduction.get('accident_type', 'N/A')}")
            
            if "possible_causes" in deduction:
                print(f"   - 可能原因数: {len(deduction['possible_causes'])}")
                for i, cause in enumerate(deduction['possible_causes'][:3], 1):
                    print(f"     {i}. {cause.get('cause', 'N/A')} (可能性: {cause.get('probability', 'N/A')})")
            
            if "immediate_actions" in deduction:
                print(f"   - 应急措施数: {len(deduction['immediate_actions'])}")
                for i, action in enumerate(deduction['immediate_actions'][:3], 1):
                    print(f"     {i}. {action.get('action', 'N/A')}")
        
    except Exception as e:
        print(f"\n   ✗ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 4. 测试应急预案生成
    print("\n4. 测试应急预案生成...")
    print("   查询: 生成变电站火灾应急预案")
    
    input_data = {
        "task": "生成变电站火灾应急预案"
    }
    
    try:
        result = await agent.run(state, input_data)
        
        print("\n   ✓ 执行成功!")
        print(f"\n   应急预案:")
        print("   " + "-" * 76)
        answer = result.get("answer", "")
        for line in answer.split("\n")[:20]:  # 只显示前20行
            print(f"   {line}")
        if len(answer.split("\n")) > 20:
            print(f"   ... (还有 {len(answer.split('\n')) - 20} 行)")
        print("   " + "-" * 76)
        
    except Exception as e:
        print(f"\n   ✗ 执行失败: {str(e)}")
    
    # 5. 测试应急演练设计
    print("\n5. 测试应急演练设计...")
    print("   查询: 设计主变跳闸应急演练方案")
    
    input_data = {
        "task": "设计主变跳闸应急演练方案"
    }
    
    try:
        result = await agent.run(state, input_data)
        
        print("\n   ✓ 执行成功!")
        print(f"\n   演练方案:")
        print("   " + "-" * 76)
        answer = result.get("answer", "")
        for line in answer.split("\n")[:20]:  # 只显示前20行
            print(f"   {line}")
        if len(answer.split("\n")) > 20:
            print(f"   ... (还有 {len(answer.split('\n')) - 20} 行)")
        print("   " + "-" * 76)
        
    except Exception as e:
        print(f"\n   ✗ 执行失败: {str(e)}")
    
    # 6. 测试注册状态
    print("\n6. 测试智能体注册状态...")
    
    # 初始化注册中心
    agent_registry.initialize_default_agents(llm_service=None)
    
    # 检查是否已注册
    registered_agent = agent_registry.get_agent(AgentRole.ACCIDENT_DEDUCTION)
    if registered_agent:
        print(f"   ✓ 智能体已注册")
        print(f"   - 名称: {registered_agent.name}")
        print(f"   - 角色: {registered_agent.role}")
        
        # 检查元数据
        metadata = agent_registry.get_metadata(AgentRole.ACCIDENT_DEDUCTION)
        if metadata:
            print(f"   ✓ 元数据已加载")
            print(f"   - 能力标签: {metadata.capabilities}")
            print(f"   - 优先级: {metadata.priority}")
            print(f"   - 必需工具: {metadata.required_tools}")
            print(f"   - 可选工具: {metadata.optional_tools}")
    else:
        print(f"   ✗ 智能体未注册")
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_accident_deduction_agent())
