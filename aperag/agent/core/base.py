from abc import ABC, abstractmethod
from datetime import datetime
import logging
import os
from typing import Any, Dict, List, Optional

from mcp_agent.workflows.llm.augmented_llm import RequestParams

from aperag.agent.core.models import (
    AgentMessage,
    AgentRole,
    AgentState,
    AgentThinkingStep,
    ToolCallInfo,
)
from aperag.agent.agent_config import AgentConfig
import aperag.agent.agent_session_manager as agent_session_manager
from aperag.db.ops import async_db_ops
from aperag.service.prompt_template_service import build_agent_query_prompt, get_agent_system_prompt

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    所有智能体（专家/值长）的基类
    
    功能:
    - 标准的思维链记录和状态管理
    - MCP工具调用能力（RAG检索、网络搜索等）
    - 参考文档学习和模板提取
    - 模板渲染和使用
    """

    def __init__(
        self,
        role: AgentRole,
        name: str,
        description: str,
        tools: Optional[List[Any]] = None,
        user_id: str = None,
        chat_id: str = None,
    ):
        self.role = role
        self.name = name
        self.description = description
        self.tools = tools or []
        self.user_id = user_id
        self.chat_id = chat_id
        
        # MCP会话（延迟初始化）
        self._mcp_session = None
        self._llm = None
        
        # 参考文档缓存
        self._reference_docs = []
        self._extracted_template = None

    async def run(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能体执行的主入口。
        使用 Template Method 模式，封装了通用的日志和思维链记录逻辑。
        """
        try:
            # 1. 记录开始思考
            self._log_thought(state, "thought",
                              f"{self.name} 开始接收任务", input_data)

            # 2. 执行具体的业务逻辑 (由子类实现)
            result = await self._execute(state, input_data)

            # 3. 记录执行完成
            self._log_thought(state, "final_answer",
                              f"{self.name} 任务完成", result)

            return result

        except Exception as e:
            logger.error(f"Agent {self.name} failed: {str(e)}", exc_info=True)
            self._log_thought(state, "correction", f"发生错误: {str(e)}")
            raise e

    @abstractmethod
    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心执行逻辑，必须由子类实现。
        例如：图纸侦探在此处调用 VLM，安监卫士在此处查询规则库。
        """
        ...

    def _log_thought(
        self,
        state: AgentState,
        step_type: str,
        description: str,
        detail: Optional[Dict[str, Any]] = None,
        citations: Optional[List[str]] = None,
    ):
        """
        辅助方法：向共享状态中添加思考步骤，用于前端展示"气泡"
        """
        step = AgentThinkingStep(
            role=self.role,
            step_type=step_type,
            description=description,
            detail=detail,
            citations=citations or [],
        )
        state.add_thought(step)
        # 也可以在此处通过 WebSocket 实时推送到前端

    def _log_tool_use(self, state: AgentState, tool_info: ToolCallInfo):
        """
        记录工具调用
        """
        self._log_thought(
            state,
            "action",
            f"调用工具: {tool_info.tool_name}",
            detail=tool_info.model_dump(),
        )

    async def reflect(self, state: AgentState, result: Any) -> bool:
        """
        (可选) 反思机制：检查结果是否符合预期，是否需要重试
        """
        return True
    
    # ========== MCP工具调用功能 ==========
    
    async def _ensure_mcp_session(
        self,
        state: AgentState,
        model_provider: str = "siliconflow",
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        language: str = "zh-CN"
    ):
        """
        确保MCP会话已初始化
        
        Args:
            state: 智能体状态
            model_provider: 模型提供商
            model_name: 模型名称
            language: 语言
        """
        if self._mcp_session and self._llm:
            return
        
        try:
            # 获取智能体的系统提示词
            from aperag.agent import agent_registry
            system_prompt = agent_registry.get_system_prompt(self.role, language)
            if not system_prompt:
                system_prompt = get_agent_system_prompt(language)
            
            # 查询provider信息
            provider_info = await async_db_ops.query_llm_provider_by_name(model_provider)
            if not provider_info:
                raise Exception(f"Provider '{model_provider}' not found")
            
            # 查询API key
            api_key = await async_db_ops.query_provider_api_key(
                model_provider, 
                user_id=self.user_id, 
                need_public=True
            )
            if not api_key:
                raise Exception(f"No API key for provider '{model_provider}'")
            
            # 获取或创建aperag API key
            aperag_api_keys = await async_db_ops.query_api_keys(self.user_id, is_system=True)
            aperag_api_key = None
            for item in aperag_api_keys:
                aperag_api_key = item.key
                break
            
            if not aperag_api_key:
                api_key_result = await async_db_ops.create_api_key(
                    user=self.user_id, 
                    description="aperag", 
                    is_system=True
                )
                aperag_api_key = api_key_result.key
            
            # 创建AgentConfig
            config = AgentConfig(
                user_id=self.user_id,
                chat_id=self.chat_id or f"agent-{self.role.value}",
                provider_name=model_provider,
                api_key=api_key,
                base_url=provider_info.base_url,
                default_model=model_name,
                language=language,
                instruction=system_prompt,
                server_names=["aperag"],
                aperag_api_key=aperag_api_key,
                aperag_mcp_url=os.getenv("APERAG_MCP_URL", "http://localhost:8000/mcp/"),
                temperature=0.7,
                max_tokens=60000,
            )
            
            # 获取或创建会话
            self._mcp_session = await agent_session_manager.get_or_create_session(config)
            self._llm = await self._mcp_session.get_llm(model_name)
            
            self._log_thought(
                state,
                "action",
                f"初始化MCP会话成功: {model_provider}/{model_name}"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP session: {e}")
            self._log_thought(
                state,
                "correction",
                f"MCP会话初始化失败: {str(e)}"
            )
            raise
    
    async def _search_knowledge(
        self,
        state: AgentState,
        query: str,
        collection_ids: Optional[List[str]] = None,
        top_k: int = 5,
        model_provider: str = "siliconflow",
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        language: str = "zh-CN"
    ) -> List[Dict[str, Any]]:
        """
        从知识库检索文档（使用MCP工具）
        
        Args:
            state: 智能体状态
            query: 查询文本
            collection_ids: 知识库ID列表（如果为None，使用智能体默认知识库）
            top_k: 返回结果数量
            model_provider: 模型提供商
            model_name: 模型名称
            language: 语言
            
        Returns:
            检索结果列表
        """
        # 确保MCP会话已初始化
        await self._ensure_mcp_session(state, model_provider, model_name, language)
        
        # 如果没有指定知识库，使用智能体的默认知识库
        if not collection_ids:
            from aperag.agent import agent_registry
            collection_ids = agent_registry.get_default_collections(self.role)
        
        if not collection_ids:
            self._log_thought(
                state,
                "observation",
                "未指定知识库，跳过检索"
            )
            return []
        
        # 记录检索操作
        self._log_thought(
            state,
            "action",
            f"正在检索知识库: {', '.join(collection_ids)}",
            detail={"query": query, "collections": collection_ids, "top_k": top_k}
        )
        
        try:
            # 构建检索提示词
            search_prompt = f"""
请从以下知识库中检索与查询相关的文档：
知识库: {', '.join(collection_ids)}
查询: {query}

使用 search_collection 工具进行检索。
"""
            
            # 使用LLM调用MCP工具
            request_params = RequestParams(
                maxTokens=4096,
                model=model_name,
                use_history=False,
                max_iterations=5,
                parallel_tool_calls=True,
                temperature=0.3,
                user=self.user_id,
            )
            
            response = await self._llm.generate_str(search_prompt, request_params)
            
            # 从历史记录中提取工具调用结果
            from aperag.agent import extract_tool_call_references
            tool_references = extract_tool_call_references(self._llm.history)
            
            # 记录检索结果
            self._log_thought(
                state,
                "observation",
                f"检索完成，找到 {len(tool_references)} 个工具调用",
                detail={"tool_calls": len(tool_references)}
            )
            
            return tool_references
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            self._log_thought(
                state,
                "correction",
                f"知识库检索失败: {str(e)}"
            )
            return []
    
    async def _web_search(
        self,
        state: AgentState,
        query: str,
        num_results: int = 5,
        model_provider: str = "siliconflow",
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        language: str = "zh-CN"
    ) -> List[Dict[str, Any]]:
        """
        网络搜索（使用MCP工具）
        
        Args:
            state: 智能体状态
            query: 搜索查询
            num_results: 结果数量
            model_provider: 模型提供商
            model_name: 模型名称
            language: 语言
            
        Returns:
            搜索结果列表
        """
        # 确保MCP会话已初始化
        await self._ensure_mcp_session(state, model_provider, model_name, language)
        
        # 记录搜索操作
        self._log_thought(
            state,
            "action",
            f"正在进行网络搜索: {query}",
            detail={"query": query, "num_results": num_results}
        )
        
        try:
            # 构建搜索提示词
            search_prompt = f"""
请使用网络搜索查找以下信息：
查询: {query}

使用 web_search 工具进行搜索，获取最新信息。
"""
            
            # 使用LLM调用MCP工具
            request_params = RequestParams(
                maxTokens=4096,
                model=model_name,
                use_history=False,
                max_iterations=5,
                parallel_tool_calls=True,
                temperature=0.3,
                user=self.user_id,
            )
            
            response = await self._llm.generate_str(search_prompt, request_params)
            
            # 从历史记录中提取工具调用结果
            from aperag.agent import extract_tool_call_references
            tool_references = extract_tool_call_references(self._llm.history)
            
            # 记录搜索结果
            self._log_thought(
                state,
                "observation",
                f"网络搜索完成，找到 {len(tool_references)} 个结果",
                detail={"results": len(tool_references)}
            )
            
            return tool_references
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            self._log_thought(
                state,
                "correction",
                f"网络搜索失败: {str(e)}"
            )
            return []
    
    async def _generate_with_llm(
        self,
        state: AgentState,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_provider: str = "siliconflow",
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        language: str = "zh-CN",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        使用LLM生成文本
        
        Args:
            state: 智能体状态
            prompt: 用户提示词
            system_prompt: 系统提示词（如果为None，使用智能体默认提示词）
            model_provider: 模型提供商
            model_name: 模型名称
            language: 语言
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            生成的文本
        """
        # 确保MCP会话已初始化
        await self._ensure_mcp_session(state, model_provider, model_name, language)
        
        # 记录生成操作
        self._log_thought(
            state,
            "action",
            "正在使用LLM生成内容",
            detail={"prompt_length": len(prompt), "temperature": temperature}
        )
        
        try:
            # 使用LLM生成
            request_params = RequestParams(
                maxTokens=max_tokens,
                model=model_name,
                use_history=True,
                max_iterations=10,
                parallel_tool_calls=True,
                temperature=temperature,
                user=self.user_id,
            )
            
            response = await self._llm.generate_str(prompt, request_params)
            
            # 记录生成结果
            self._log_thought(
                state,
                "observation",
                f"生成完成，长度: {len(response)} 字符"
            )
            
            return response if response else ""
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            self._log_thought(
                state,
                "correction",
                f"LLM生成失败: {str(e)}"
            )
            return ""
    
    # ========== 参考文档功能 ==========
    
    async def add_reference_document(
        self,
        state: AgentState,
        document_content: str,
        document_name: str = "参考文档"
    ):
        """
        添加参考文档
        
        Args:
            state: 智能体状态
            document_content: 文档内容
            document_name: 文档名称
        """
        self._reference_docs.append({
            "name": document_name,
            "content": document_content
        })
        
        self._log_thought(
            state,
            "action",
            f"添加参考文档: {document_name}",
            detail={"length": len(document_content)}
        )
    
    async def extract_template_from_reference(
        self,
        state: AgentState,
        model_provider: str = "siliconflow",
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        language: str = "zh-CN"
    ) -> Optional[str]:
        """
        从参考文档中提取模板
        
        Args:
            state: 智能体状态
            model_provider: 模型提供商
            model_name: 模型名称
            language: 语言
            
        Returns:
            提取的模板（Jinja2格式）
        """
        if not self._reference_docs:
            self._log_thought(
                state,
                "observation",
                "没有参考文档，无法提取模板"
            )
            return None
        
        # 确保MCP会话已初始化
        await self._ensure_mcp_session(state, model_provider, model_name, language)
        
        self._log_thought(
            state,
            "action",
            f"正在从 {len(self._reference_docs)} 个参考文档中提取模板"
        )
        
        try:
            # 构建提取提示词
            docs_content = "\n\n---\n\n".join([
                f"## {doc['name']}\n\n{doc['content']}"
                for doc in self._reference_docs
            ])
            
            extract_prompt = f"""
请分析以下参考文档，提取出通用的Jinja2模板格式。

参考文档：
{docs_content}

要求：
1. 识别文档中的固定结构和可变内容
2. 将可变内容替换为Jinja2变量，如 {{{{ variable_name }}}}
3. 保留文档的整体结构和格式
4. 使用Jinja2的条件和循环语法处理可选和重复内容
5. 输出完整的Jinja2模板

请直接输出模板内容，不要添加额外说明。
"""
            
            # 使用LLM提取模板
            template_content = await self._generate_with_llm(
                state,
                prompt=extract_prompt,
                model_provider=model_provider,
                model_name=model_name,
                language=language,
                temperature=0.3
            )
            
            if template_content:
                self._extracted_template = template_content
                
                self._log_thought(
                    state,
                    "observation",
                    f"成功提取模板，长度: {len(template_content)} 字符"
                )
                
                return template_content
            else:
                return None
                
        except Exception as e:
            logger.error(f"Template extraction failed: {e}")
            self._log_thought(
                state,
                "correction",
                f"模板提取失败: {str(e)}"
            )
            return None
    
    async def save_extracted_template(
        self,
        state: AgentState,
        template_path: str
    ) -> bool:
        """
        保存提取的模板到文件
        
        Args:
            state: 智能体状态
            template_path: 模板文件路径
            
        Returns:
            是否保存成功
        """
        if not self._extracted_template:
            self._log_thought(
                state,
                "observation",
                "没有提取的模板，无法保存"
            )
            return False
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(template_path), exist_ok=True)
            
            # 保存模板
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(self._extracted_template)
            
            self._log_thought(
                state,
                "action",
                f"模板已保存到: {template_path}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            self._log_thought(
                state,
                "correction",
                f"模板保存失败: {str(e)}"
            )
            return False
    
    async def render_with_template(
        self,
        state: AgentState,
        template_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        使用模板渲染内容
        
        Args:
            state: 智能体状态
            template_name: 模板名称（如果为None，使用提取的模板）
            context: 模板上下文数据
            
        Returns:
            渲染后的内容
        """
        from aperag.service.template_service import template_service
        
        if context is None:
            context = {}
        
        try:
            if template_name:
                # 使用指定的模板文件
                self._log_thought(
                    state,
                    "action",
                    f"使用模板渲染: {template_name}"
                )
                
                rendered = template_service.render_template(template_name, context)
            elif self._extracted_template:
                # 使用提取的模板
                self._log_thought(
                    state,
                    "action",
                    "使用提取的模板渲染"
                )
                
                rendered = template_service.render_from_string(
                    self._extracted_template,
                    context
                )
            else:
                self._log_thought(
                    state,
                    "observation",
                    "没有可用的模板"
                )
                return ""
            
            self._log_thought(
                state,
                "observation",
                f"模板渲染完成，长度: {len(rendered)} 字符"
            )
            
            return rendered
            
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            self._log_thought(
                state,
                "correction",
                f"模板渲染失败: {str(e)}"
            )
            return ""
