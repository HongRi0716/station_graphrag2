import logging
from typing import Any, Dict, List

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class OperationTicketAgent(BaseAgent):
    """
    操作票智能编制与审核专家 (Operation Ticket Agent)
    职责：自动生成操作票、审核操作票合规性、优化操作步骤顺序。
    特点：精通倒闸操作流程和安全规程，确保操作票的正确性和安全性。
    """

    def __init__(self, llm_service: Any = None):
        super().__init__(
            role=AgentRole.OPERATION_TICKET,
            name="操作票专家 (Operation Ticket Agent)",
            description="智能生成和审核操作票，确保倒闸操作的安全性和规范性。",
            tools=["operation_template", "safety_checker", "sequence_optimizer"],
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行操作票编制或审核任务
        """
        query = input_data.get("task", "")

        self._log_thought(state, "thought", f"收到操作票任务: {query}")

        # 判断任务类型
        if "生成" in query or "编制" in query or "开票" in query:
            return await self._generate_operation_ticket(state, query)
        elif "审核" in query or "检查" in query or "校验" in query:
            return await self._review_operation_ticket(state, query)
        elif "优化" in query or "调整" in query:
            return await self._optimize_operation_steps(state, query)
        else:
            return await self._general_guidance(state, query)

    async def _generate_operation_ticket(self, state: AgentState, query: str) -> Dict[str, Any]:
        """生成操作票 (Mock)"""
        self._log_thought(state, "plan", "开始智能生成操作票...")

        # 解析操作任务
        operation_type = self._parse_operation_type(query)

        self._log_thought(
            state,
            "action",
            f"识别操作类型: {operation_type}",
            detail={"query": query, "type": operation_type}
        )

        # Mock: 查询设备拓扑和状态
        self._log_thought(
            state,
            "action",
            "正在查询设备拓扑关系和当前运行状态...",
            detail={"data_source": "知识图谱 + SCADA实时数据"}
        )

        # 生成操作步骤
        ticket = self._create_ticket_template(operation_type)

        self._log_thought(
            state,
            "observation",
            f"已生成 {len(ticket['steps'])} 步操作",
            detail=ticket
        )

        # 安全校验
        safety_check = self._perform_safety_check(ticket)
        self._log_thought(
            state,
            "thought",
            "执行安全性校验...",
            detail=safety_check
        )

        # 格式化输出
        report = self._format_operation_ticket(ticket, safety_check)

        return {
            "answer": report,
            "ticket": ticket,
            "safety_check": safety_check
        }

    def _parse_operation_type(self, query: str) -> str:
        """解析操作类型"""
        if "冷备用" in query or "停运" in query:
            return "设备转冷备用"
        elif "热备用" in query:
            return "设备转热备用"
        elif "投运" in query or "送电" in query:
            return "设备投运送电"
        elif "母线倒闸" in query or "母线切换" in query:
            return "母线倒闸操作"
        else:
            return "通用操作"

    def _create_ticket_template(self, operation_type: str) -> Dict[str, Any]:
        """创建操作票模板 (Mock)"""

        if operation_type == "设备转冷备用":
            return {
                "ticket_no": "OT-2024-1124-001",
                "title": "#1主变转冷备用",
                "equipment": "#1主变压器",
                "voltage_level": "110kV/10kV",
                "operation_date": "2024-11-24",
                "operator": "待指定",
                "supervisor": "待指定",
                "steps": [
                    {
                        "seq": 1,
                        "action": "核对运行方式",
                        "detail": "确认#1主变当前运行，110kV侧101开关、10kV侧1011开关在合位",
                        "safety_note": "禁止在负荷状态下操作"
                    },
                    {
                        "seq": 2,
                        "action": "联系调度",
                        "detail": "向地区调度申请#1主变转冷备用操作令",
                        "safety_note": "必须取得调度许可"
                    },
                    {
                        "seq": 3,
                        "action": "负荷转移",
                        "detail": "通知用户，将10kV I段负荷转移至10kV II段",
                        "safety_note": "确认负荷转移完成"
                    },
                    {
                        "seq": 4,
                        "action": "投入保护停用压板",
                        "detail": "在主变保护屏投入'差动保护停用'压板",
                        "safety_note": "防止保护误动"
                    },
                    {
                        "seq": 5,
                        "action": "断开10kV侧开关",
                        "detail": "断开1011开关(#1主变10kV侧开关)",
                        "safety_note": "确认开关分位指示灯亮"
                    },
                    {
                        "seq": 6,
                        "action": "断开110kV侧开关",
                        "detail": "断开101开关(#1主变110kV侧开关)",
                        "safety_note": "确认开关分位指示灯亮"
                    },
                    {
                        "seq": 7,
                        "action": "验电",
                        "detail": "使用验电器对#1主变两侧进行验电",
                        "safety_note": "确认无电压"
                    },
                    {
                        "seq": 8,
                        "action": "挂接地线",
                        "detail": "在#1主变110kV侧、10kV侧装设接地线",
                        "safety_note": "先接接地端，后接导体端"
                    },
                    {
                        "seq": 9,
                        "action": "悬挂标示牌",
                        "detail": "在101、1011开关操作把手处悬挂'禁止合闸，有人工作'标示牌",
                        "safety_note": "标示牌应醒目牢固"
                    },
                    {
                        "seq": 10,
                        "action": "汇报调度",
                        "detail": "向地区调度汇报操作完成情况",
                        "safety_note": "记录完成时间"
                    }
                ],
                "estimated_time": "约45分钟",
                "prerequisites": [
                    "天气条件良好",
                    "操作人员持有效资格证",
                    "备用主变可用",
                    "工器具检查合格"
                ]
            }
        elif operation_type == "母线倒闸操作":
            return {
                "ticket_no": "OT-2024-1124-002",
                "title": "110kV母线I母转II母",
                "equipment": "110kV母线系统",
                "voltage_level": "110kV",
                "steps": [
                    {
                        "seq": 1,
                        "action": "检查母联开关状态",
                        "detail": "确认110kV母联开关在合位，I、II母并列运行",
                        "safety_note": "禁止单母运行时倒闸"
                    },
                    {
                        "seq": 2,
                        "action": "投入母差保护停用压板",
                        "detail": "投入母差保护装置'母联解列停用'压板",
                        "safety_note": "防止母差保护误动"
                    },
                    {
                        "seq": 3,
                        "action": "合II母隔离开关",
                        "detail": "合#1主变110kV侧II母隔离刀闸101G2",
                        "safety_note": "确认开关已断开"
                    },
                    {
                        "seq": 4,
                        "action": "合110kV侧开关",
                        "detail": "合101开关，使#1主变接入II母",
                        "safety_note": "确认电压正常"
                    },
                    {
                        "seq": 5,
                        "action": "分I母隔离开关",
                        "detail": "分#1主变110kV侧I母隔离刀闸101G1",
                        "safety_note": "确认无负荷通过"
                    },
                    {
                        "seq": 6,
                        "action": "退出保护停用压板",
                        "detail": "退出母差保护'母联解列停用'压板，恢复保护正常运行",
                        "safety_note": "恢复保护功能"
                    },
                    {
                        "seq": 7,
                        "action": "汇报完成",
                        "detail": "向调度汇报操作完成，#1主变已由I母转至II母运行",
                        "safety_note": "记录完成时间"
                    }
                ],
                "estimated_time": "约30分钟"
            }
        else:
            return {
                "ticket_no": "OT-2024-1124-XXX",
                "title": "待定操作",
                "steps": [],
                "message": "请提供更详细的操作描述"
            }

    def _perform_safety_check(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """执行安全性检查 (Mock)"""
        return {
            "five_prevention_check": "✅ 通过",
            "sequence_check": "✅ 步骤顺序正确",
            "completeness_check": "✅ 步骤完整",
            "regulation_compliance": "✅ 符合安规要求",
            "warnings": [],
            "suggestions": [
                "建议操作前再次确认天气情况",
                "建议准备应急预案"
            ]
        }

    def _format_operation_ticket(self, ticket: Dict[str, Any], safety_check: Dict[str, Any]) -> str:
        """格式化操作票输出"""
        report = "## 📋 操作票\n\n"
        report += f"**票号**: {ticket.get('ticket_no', 'N/A')}\n"
        report += f"**操作任务**: {ticket.get('title', 'N/A')}\n"
        report += f"**设备名称**: {ticket.get('equipment', 'N/A')}\n"
        report += f"**电压等级**: {ticket.get('voltage_level', 'N/A')}\n"
        report += f"**计划日期**: {ticket.get('operation_date', 'N/A')}\n"
        report += f"**预计用时**: {ticket.get('estimated_time', 'N/A')}\n\n"

        if ticket.get('prerequisites'):
            report += "### 操作前提条件\n"
            for prereq in ticket['prerequisites']:
                report += f"- {prereq}\n"
            report += "\n"

        if ticket.get('steps'):
            report += "### 操作步骤\n\n"
            for step in ticket['steps']:
                report += f"**第{step['seq']}步**: {step['action']}\n"
                report += f"- 具体内容: {step['detail']}\n"
                if step.get('safety_note'):
                    report += f"- ⚠️ 注意事项: {step['safety_note']}\n"
                report += "\n"

        report += "### 安全性检查\n"
        for check_name, result in safety_check.items():
            if check_name not in ['warnings', 'suggestions']:
                report += f"- {result} {check_name}\n"

        if safety_check.get('suggestions'):
            report += "\n### 建议\n"
            for suggestion in safety_check['suggestions']:
                report += f"- 💡 {suggestion}\n"

        report += "\n---\n"
        report += "**操作人**: ________  **时间**: ________  **签字**: ________\n"
        report += "**监护人**: ________  **时间**: ________  **签字**: ________\n"

        return report

    async def _review_operation_ticket(self, state: AgentState, query: str) -> Dict[str, Any]:
        """审核操作票"""
        self._log_thought(state, "action", "正在审核操作票...")

        # Mock审核结果
        review_result = {
            "ticket_no": "OT-2024-1120-005",
            "issues": [
                {
                    "severity": "严重",
                    "location": "第3步",
                    "description": "断开开关前未投入保护停用压板",
                    "suggestion": "应在第2步增加'投入保护停用压板'"
                }
            ],
            "approved": False
        }

        report = "## 🔍 操作票审核报告\n\n"
        report += f"**票号**: {review_result['ticket_no']}\n\n"

        if review_result['issues']:
            report += f"### ❌ 审核结果: 不通过\n\n"
            report += f"发现 {len(review_result['issues'])} 处问题:\n\n"
            for idx, issue in enumerate(review_result['issues']):
                report += f"{idx+1}. 🔴 **{issue['severity']}** - {issue['location']}\n"
                report += f"   - 问题: {issue['description']}\n"
                report += f"   - 建议: {issue['suggestion']}\n\n"
        else:
            report += "### ✅ 审核结果: 通过\n\n"
            report += "操作票步骤完整、顺序正确、符合安全规程。\n"

        return {
            "answer": report,
            "review_result": review_result
        }

    async def _optimize_operation_steps(self, state: AgentState, query: str) -> Dict[str, Any]:
        """优化操作步骤"""
        return {
            "answer": "操作步骤优化功能开发中...\n"
            "将基于历史操作数据和最佳实践，优化操作步骤顺序，减少操作时间。"
        }

    async def _general_guidance(self, state: AgentState, query: str) -> Dict[str, Any]:
        """通用指导"""
        return {
            "answer": "操作票专家为您服务！我可以:\n"
            "1. 📝 智能生成操作票 (如: '生成#1主变转冷备用操作票')\n"
            "2. 🔍 审核操作票合规性 (如: '审核操作票OT-XXX')\n"
            "3. ⚡ 优化操作步骤顺序\n\n"
            "请告诉我具体的操作任务或需要审核的票号。"
        }
