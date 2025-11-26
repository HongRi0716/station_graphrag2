"""
智能体系统集成测试
测试 The Supervisor 和 The Archivist 的完整功能
"""

import pytest
import asyncio
from aperag.agent import agent_registry
from aperag.agent.core.models import AgentRole, AgentState


class TestSupervisorAgent:
    """The Supervisor 集成测试"""
    
    @pytest.mark.asyncio
    async def test_task_analysis(self):
        """测试任务分析功能"""
        supervisor = agent_registry.get_agent(AgentRole.SUPERVISOR)
        
        state = AgentState(session_id="test-analysis")

        # 测试应急响应任务
        analysis = await supervisor._analyze_task(state, "#1主变跳闸")
        assert analysis["task_type"] == "emergency_response"
        assert analysis["priority"] == "urgent"
        assert analysis["requires_collaboration"] == True
        
        # 测试操作规划任务
        analysis = await supervisor._analyze_task(state, "生成#1主变转冷备用操作票")
        assert analysis["task_type"] == "operation_planning"
        assert analysis["priority"] == "high"
        
        # 测试查询任务
        analysis = await supervisor._analyze_task(state, "查询主变操作规程")
        assert analysis["task_type"] == "information_retrieval"
        assert analysis["requires_collaboration"] == False
    
    @pytest.mark.asyncio
    async def test_single_task_dispatch(self):
        """测试单任务分发"""
        supervisor = agent_registry.get_agent(AgentRole.SUPERVISOR)
        supervisor.user_id = None  # 不设置user_id，测试回退
        
        state = AgentState(session_id="test-supervisor")
        result = await supervisor.run(state, {
            "task": "查询主变操作规程"
        })
        
        assert "answer" in result
        assert result["answer"] is not None
    
    @pytest.mark.asyncio
    async def test_collaboration_dispatch(self):
        """测试协作任务分发"""
        supervisor = agent_registry.get_agent(AgentRole.SUPERVISOR)
        supervisor.user_id = "test-user"
        supervisor.chat_id = "test-chat"
        
        state = AgentState(session_id="test-supervisor-collab")
        result = await supervisor.run(state, {
            "task": "#1主变跳闸，请组织应急处置"
        })
        
        assert "answer" in result
        # 检查是否有协作结果或回退结果
        assert "collaboration_result" in result or "delegated_to" in result or "task_analysis" in result
    
    @pytest.mark.asyncio
    async def test_station_status(self):
        """测试态势感知"""
        supervisor = agent_registry.get_agent(AgentRole.SUPERVISOR)
        supervisor.user_id = "test-user"
        
        state = AgentState(session_id="test-status")
        status = await supervisor.get_station_status(state)
        
        assert "timestamp" in status
        assert "overall_status" in status
        assert "equipment_count" in status
        assert "alarm_count" in status


class TestArchivistAgent:
    """The Archivist 集成测试"""
    
    @pytest.mark.asyncio
    async def test_knowledge_search(self):
        """测试知识库检索"""
        archivist = agent_registry.get_agent(AgentRole.ARCHIVIST)
        archivist.user_id = None  # 测试Mock回退
        
        state = AgentState(session_id="test-archivist")
        result = await archivist.run(state, {
            "query": "查询主变操作规程",
            "search_type": "hybrid"
        })
        
        assert "answer" in result
        assert "documents" in result
        assert result["count"] > 0
    
    @pytest.mark.asyncio
    async def test_graph_traversal(self):
        """测试图谱遍历"""
        archivist = agent_registry.get_agent(AgentRole.ARCHIVIST)
        archivist.user_id = None  # 测试回退
        
        state = AgentState(session_id="test-graph")
        result = await archivist.run(state, {
            "query": "#1主变与哪些设备有连接关系"
        })
        
        assert "answer" in result
    
    @pytest.mark.asyncio
    async def test_historical_search(self):
        """测试历史查询"""
        archivist = agent_registry.get_agent(AgentRole.ARCHIVIST)
        archivist.user_id = None  # 测试Mock回退
        
        state = AgentState(session_id="test-history")
        result = await archivist.run(state, {
            "query": "查询2024年的主变检修记录"
        })
        
        assert "answer" in result
        assert "documents" in result
    
    @pytest.mark.asyncio
    async def test_fallback_response(self):
        """测试回退响应"""
        archivist = agent_registry.get_agent(AgentRole.ARCHIVIST)
        
        # 测试Mock数据
        result = archivist._fallback_response("查询主变")
        
        assert "answer" in result
        assert "documents" in result
        assert len(result["documents"]) > 0
        assert "note" in result


class TestIntegration:
    """完整流程集成测试"""
    
    @pytest.mark.asyncio
    async def test_supervisor_archivist_integration(self):
        """测试 Supervisor 和 Archivist 的集成"""
        supervisor = agent_registry.get_agent(AgentRole.SUPERVISOR)
        supervisor.user_id = "test-user"
        
        state = AgentState(session_id="test-integration")
        
        # Supervisor 接收查询任务，应该分发给 Archivist
        result = await supervisor.run(state, {
            "task": "查询主变操作规程"
        })
        
        assert "answer" in result
        # 检查是否分发给了 Archivist
        if "delegated_to" in result:
            assert "Archivist" in result["delegated_to"]
    
    @pytest.mark.asyncio
    async def test_emergency_response_workflow(self):
        """测试应急响应完整流程"""
        supervisor = agent_registry.get_agent(AgentRole.SUPERVISOR)
        supervisor.user_id = "test-user"
        supervisor.chat_id = "test-emergency"
        
        state = AgentState(session_id="test-emergency-workflow")
        
        # 模拟应急响应场景
        result = await supervisor.run(state, {
            "task": "#1主变跳闸，请组织应急处置"
        })
        
        assert "answer" in result
        assert len(state.thinking_stream) > 0
        
        # 检查思维链
        thought_types = [step.step_type for step in state.thinking_stream]
        assert "thought" in thought_types
        assert "action" in thought_types


class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_supervisor_response_time(self):
        """测试 Supervisor 响应时间"""
        import time
        
        supervisor = agent_registry.get_agent(AgentRole.SUPERVISOR)
        supervisor.user_id = None  # 使用回退，测试最快响应
        
        state = AgentState(session_id="test-perf-supervisor")
        
        start_time = time.time()
        result = await supervisor.run(state, {
            "task": "查询主变操作规程"
        })
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"Supervisor response time: {response_time:.2f}s")
        
        # 回退响应应该很快
        assert response_time < 2.0
    
    @pytest.mark.asyncio
    async def test_archivist_response_time(self):
        """测试 Archivist 响应时间"""
        import time
        
        archivist = agent_registry.get_agent(AgentRole.ARCHIVIST)
        archivist.user_id = None  # 使用Mock回退
        
        state = AgentState(session_id="test-perf-archivist")
        
        start_time = time.time()
        result = await archivist.run(state, {
            "query": "查询主变操作规程"
        })
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"Archivist response time: {response_time:.2f}s")
        
        # Mock响应应该很快
        assert response_time < 1.0
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求"""
        import time
        
        supervisor = agent_registry.get_agent(AgentRole.SUPERVISOR)
        
        async def single_request(i):
            supervisor_copy = agent_registry.get_agent(AgentRole.SUPERVISOR)
            supervisor_copy.user_id = None
            state = AgentState(session_id=f"test-concurrent-{i}")
            return await supervisor_copy.run(state, {
                "task": "查询主变操作规程"
            })
        
        # 并发10个请求
        start_time = time.time()
        results = await asyncio.gather(*[single_request(i) for i in range(10)])
        end_time = time.time()
        
        total_time = end_time - start_time
        print(f"10 concurrent requests completed in: {total_time:.2f}s")
        
        # 所有请求都应该成功
        assert len(results) == 10
        assert all("answer" in r for r in results)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
