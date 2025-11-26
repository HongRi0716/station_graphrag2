"""
测试 MCP 工具注册和调用
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aperag.agent.agent_config import AgentConfig
from aperag.agent import agent_session_manager
from aperag.db.ops import async_db_ops


async def test_mcp_tools():
    """测试 MCP 工具是否正确注册"""
    user_id = "user5220eb7ee134ad0d"
    
    print("=" * 80)
    print("测试 MCP 工具注册")
    print("=" * 80)
    
    try:
        # 1. 获取模型配置
        print("\n【1】获取模型配置...")
        provider_name = "siliconflow"
        model_name = "Qwen/Qwen2.5-7B-Instruct"
        
        provider_info = await async_db_ops.query_llm_provider_by_name(provider_name)
        if not provider_info:
            print(f"❌ Provider '{provider_name}' 未找到")
            return
        
        api_key = await async_db_ops.query_provider_api_key(
            provider_name,
            user_id=user_id,
            need_public=True
        )
        if not api_key:
            print(f"❌ 没有找到 API key")
            return
        
        print(f"✅ Provider: {provider_name}")
        print(f"✅ Model: {model_name}")
        print(f"✅ Base URL: {provider_info.base_url}")
        
        # 2. 获取 aperag API key
        print("\n【2】获取 aperag API key...")
        aperag_api_keys = await async_db_ops.query_api_keys(user_id, is_system=True)
        aperag_api_key = None
        for item in aperag_api_keys:
            aperag_api_key = item.key
            break
        
        if not aperag_api_key:
            print("❌ 没有找到 aperag API key")
            return
        
        print(f"✅ Aperag API key: {aperag_api_key[:20]}...")
        
        # 3. 创建 AgentConfig
        print("\n【3】创建 Agent 会话...")
        config = AgentConfig(
            user_id=user_id,
            chat_id="test-mcp-tools",
            provider_name=provider_name,
            api_key=api_key,
            base_url=provider_info.base_url,
            default_model=model_name,
            language="zh-CN",
            instruction="你是一个测试助手",
            server_names=["aperag"],
            aperag_api_key=aperag_api_key,
            aperag_mcp_url=os.getenv("APERAG_MCP_URL", "http://localhost:8000/mcp/"),
            temperature=0.7,
            max_tokens=60000,
        )
        
        session = await agent_session_manager.get_or_create_session(config)
        print(f"✅ 会话创建成功")
        
        # 4. 检查可用工具
        print("\n【4】检查可用工具...")
        if session.agent:
            tools_result = await session.agent.list_tools()
            
            # 处理不同的返回类型
            if hasattr(tools_result, 'tools'):
                tools_list = tools_result.tools
            elif isinstance(tools_result, (list, tuple)):
                tools_list = tools_result
            else:
                tools_list = []
            
            if not tools_list:
                print("❌ 没有找到任何工具！")
                print("   这可能是 MCP 服务器连接问题")
                return
            
            print(f"✅ 找到 {len(tools_list)} 个工具:")
            for tool in tools_list:
                tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                tool_desc = tool.description if hasattr(tool, 'description') else "无描述"
                print(f"   - {tool_name}: {tool_desc}")
            
            # 检查是否有 search_collection 工具
            tool_names = [t.name if hasattr(t, 'name') else str(t) for t in tools_list]
            if 'search_collection' in tool_names:
                print(f"\n✅ search_collection 工具已注册")
            else:
                print(f"\n❌ search_collection 工具未找到！")
                print(f"   可用工具: {', '.join(tool_names)}")
        else:
            print("❌ session.agent 为 None")
        
        # 5. 测试简单的工具调用
        print("\n【5】测试工具调用...")
        llm = await session.get_llm(model_name)
        
        # 构建一个明确要求使用工具的提示词
        test_prompt = """请使用 search_collection 工具搜索知识库。

搜索参数:
- collection_ids: ["cold307b13f7b870c13", "colc8b5993e9352a49e"]
- query: "运维班组"
- top_k: 5

请立即调用工具并返回结果。"""
        
        from mcp_agent.workflows.llm.augmented_llm import RequestParams
        
        request_params = RequestParams(
            maxTokens=4096,
            model=model_name,
            use_history=False,
            max_iterations=5,
            parallel_tool_calls=True,
            temperature=0.3,
            user=user_id,
        )
        
        print(f"   发送提示词: {test_prompt[:100]}...")
        response = await llm.generate_str(test_prompt, request_params)
        
        print(f"\n   响应: {response[:500]}...")
        
        # 检查历史记录中的工具调用
        if hasattr(llm, 'history') and llm.history:
            print(f"\n   历史记录长度: {len(llm.history)}")
            tool_calls_found = 0
            for i, msg in enumerate(llm.history):
                if isinstance(msg, dict):
                    if msg.get("role") == "assistant" and msg.get("tool_calls"):
                        tool_calls_found += len(msg.get("tool_calls", []))
                        print(f"   消息 {i}: 找到 {len(msg.get('tool_calls', []))} 个工具调用")
                        for tc in msg.get("tool_calls", []):
                            print(f"      - {tc.get('function', {}).get('name', 'unknown')}")
            
            if tool_calls_found > 0:
                print(f"\n✅ 成功！LLM 调用了 {tool_calls_found} 个工具")
            else:
                print(f"\n❌ LLM 没有调用任何工具")
                print(f"   这可能是因为:")
                print(f"   1. LLM 模型不支持工具调用")
                print(f"   2. 提示词不够明确")
                print(f"   3. 工具定义有问题")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
