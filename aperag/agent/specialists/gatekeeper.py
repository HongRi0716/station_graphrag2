import logging
from typing import Any, Dict, List

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class GatekeeperAgent(BaseAgent):
    """
    安监卫士 (The Gatekeeper)
    职责：安全规程校验、五防逻辑检查、两票审查、风险评估。
    特点：严格遵循安规，守护电网安全底线。
    """

    def __init__(self, llm_service: Any = None):
        super().__init__(
            role=AgentRole.GATEKEEPER,
            name="安监卫士 (Gatekeeper)",
            description="负责安全规程校验、五防逻辑检查和操作票/工作票的合规性审查。",
            tools=["safety_rule_engine",
                   "five_prevention_checker", "risk_assessor"],
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行安全校验任务
        """
        query = input_data.get("task", "")

        self._log_thought(state, "thought", f"收到安全校验请求: {query}")

        # 判断任务类型
        if "操作票" in query:
            return await self._check_operation_ticket(state, query)
        elif "工作票" in query:
            return await self._check_work_permit(state, query)
        elif "五防" in query:
            return await self._check_five_prevention(state, query)
        elif "风险" in query or "评估" in query:
            return await self._assess_risk(state, query)
        else:
            return await self._general_safety_check(state, query)

    async def _check_operation_ticket(self, state: AgentState, query: str) -> Dict[str, Any]:
        """操作票审查 (Mock)"""
        self._log_thought(state, "plan", "开始操作票合规性审查...")

        # Mock操作票内容
        ticket_content = {
            "ticket_no": "OT-2024-001",
            "operation": "#1主变转冷备用",
            "operator": "张三",
            "steps": [
                "断开10kV侧1011开关",
                "断开110kV侧101开关",
                "断开主变中性点接地刀闸",
                "投入主变保护停用压板"
            ]
        }

        self._log_thought(
            state,
            "action",
            "正在执行安规校验...",
            detail={"ticket": ticket_content}
        )

        # Mock校验结果
        violations = [
            {
                "step": 4,
                "issue": "顺序错误",
                "description": "应先投入保护停用压板，再断开开关",
                "severity": "严重",
                "reference": "《变电安规》第5.2.3条"
            },
            {
                "step": 3,
                "issue": "缺少必要步骤",
                "description": "断开中性点接地刀闸前应先验电",
                "severity": "一般",
                "reference": "《电气安全规程》第3.4条"
            }
        ]

        self._log_thought(
            state,
            "observation",
            f"发现 {len(violations)} 处违规操作",
            detail={"violations": violations}
        )

        # 生成审查报告
        report = "## 🛡️ 操作票安全审查报告\n\n"
        report += f"**票号**: {ticket_content['ticket_no']}\n"
        report += f"**操作任务**: {ticket_content['operation']}\n"
        report += f"**操作人**: {ticket_content['operator']}\n\n"

        if violations:
            report += f"### ❌ 审查结果: 不通过\n\n"
            report += f"发现 **{len(violations)}** 处安全隐患:\n\n"
            for idx, v in enumerate(violations):
                severity_icon = "🔴" if v["severity"] == "严重" else "🟡"
                report += f"{idx+1}. {severity_icon} **第{v['step']}步 - {v['issue']}**\n"
                report += f"   - 问题: {v['description']}\n"
                report += f"   - 依据: {v['reference']}\n\n"

            report += "### 建议\n"
            report += "请按照以下顺序修改操作步骤:\n"
            report += "1. 投入主变保护停用压板\n"
            report += "2. 断开10kV侧1011开关\n"
            report += "3. 断开110kV侧101开关\n"
            report += "4. 验电确认无电压\n"
            report += "5. 断开主变中性点接地刀闸\n"
        else:
            report += "### ✅ 审查结果: 通过\n\n"
            report += "操作票符合安全规程要求，可以执行。"

        return {
            "answer": report,
            "violations": violations,
            "approved": len(violations) == 0
        }

    async def _check_work_permit(self, state: AgentState, query: str) -> Dict[str, Any]:
        """工作票审查 (Mock)"""
        self._log_thought(state, "plan", "开始工作票审查...")

        permit_data = {
            "permit_no": "WP-2024-056",
            "work_type": "一类工作票",
            "location": "10kV开关室",
            "description": "#2出线柜断路器检修",
            "safety_measures": [
                "断开#2出线开关",
                '悬挂"禁止合闸"标示牌',
                "装设接地线",
                "设置遮栏"
            ]
        }

        # Mock审查结果
        issues = [
            {
                "category": "安全措施不足",
                "description": "未明确验电步骤",
                "suggestion": "在装设接地线前应先验电",
                "severity": "重要"
            }
        ]

        self._log_thought(
            state,
            "observation",
            f"工作票审查完成，发现 {len(issues)} 处问题",
            detail={"issues": issues}
        )

        report = "## 📝 工作票审查报告\n\n"
        report += f"**票号**: {permit_data['permit_no']}\n"
        report += f"**类型**: {permit_data['work_type']}\n"
        report += f"**工作地点**: {permit_data['location']}\n"
        report += f"**工作内容**: {permit_data['description']}\n\n"

        report += "### 安全措施审查\n"
        if issues:
            report += f"⚠️ 发现 {len(issues)} 处需要完善的地方:\n\n"
            for idx, issue in enumerate(issues):
                report += f"{idx+1}. **{issue['category']}**\n"
                report += f"   - 问题: {issue['description']}\n"
                report += f"   - 建议: {issue['suggestion']}\n\n"
        else:
            report += "✅ 安全措施完备，符合要求。\n"

        return {
            "answer": report,
            "issues": issues,
            "approved": len(issues) == 0
        }

    async def _check_five_prevention(self, state: AgentState, query: str) -> Dict[str, Any]:
        """五防逻辑检查 (Mock)"""
        self._log_thought(state, "action", "执行五防逻辑校验...")

        # Mock五防检查
        five_prevention_results = {
            "防止误分误合断路器": "✅ 通过",
            "防止带负荷拉合隔离开关": "✅ 通过",
            "防止带电挂接地线": "⚠️ 警告 - 存在风险",
            "防止带地线合闸": "✅ 通过",
            "防止误入带电间隔": "✅ 通过"
        }

        warnings = [
            {
                "rule": "防止带电挂接地线",
                "risk": "当前101开关在合位，若直接挂接地线存在人身触电风险",
                "suggestion": "应先断开101开关并验电"
            }
        ]

        report = "## ⚡ 五防逻辑检查报告\n\n"
        for rule, result in five_prevention_results.items():
            report += f"- {result} {rule}\n"

        if warnings:
            report += "\n### 警告事项\n"
            for w in warnings:
                report += f"⚠️ **{w['rule']}**\n"
                report += f"   - 风险: {w['risk']}\n"
                report += f"   - 建议: {w['suggestion']}\n\n"

        return {
            "answer": report,
            "check_results": five_prevention_results,
            "warnings": warnings
        }

    async def _assess_risk(self, state: AgentState, query: str) -> Dict[str, Any]:
        """风险评估 (Mock)"""
        self._log_thought(state, "thought", "正在进行风险评估...")

        risk_assessment = {
            "operation": "110kV母线倒闸操作",
            "risk_level": "中等",
            "risks": [
                {
                    "type": "操作风险",
                    "description": "母差保护可能误动",
                    "probability": "低",
                    "impact": "高",
                    "mitigation": "操作前投入母差保护停用压板"
                },
                {
                    "type": "人身风险",
                    "description": "高压设备带电部分外露",
                    "probability": "中",
                    "impact": "极高",
                    "mitigation": "保持安全距离，佩戴防护用具"
                }
            ]
        }

        report = "## 🎯 风险评估报告\n\n"
        report += f"**评估对象**: {risk_assessment['operation']}\n"
        report += f"**风险等级**: {risk_assessment['risk_level']}\n\n"
        report += "### 风险清单\n"
        for idx, risk in enumerate(risk_assessment['risks']):
            report += f"{idx+1}. **{risk['type']}**: {risk['description']}\n"
            report += f"   - 可能性: {risk['probability']}\n"
            report += f"   - 影响: {risk['impact']}\n"
            report += f"   - 控制措施: {risk['mitigation']}\n\n"

        return {
            "answer": report,
            "risk_assessment": risk_assessment
        }

    async def _general_safety_check(self, state: AgentState, query: str) -> Dict[str, Any]:
        """通用安全检查"""
        return {
            "answer": "安监卫士随时待命！我可以为您提供:\n"
            "1. 🎫 操作票审查\n"
            "2. 📋 工作票审查\n"
            "3. ⚡ 五防逻辑校验\n"
            "4. 🎯 风险评估\n\n"
            "请告诉我需要检查的具体内容。"
        }
