import logging
from typing import Any, Dict, List

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class AuditorAgent(BaseAgent):
    """
    合规审计师 (The Auditor)
    职责：文档合规性审查、标准符合性检查、报告审核、质量验收。
    特点：精通各类行业标准和规范，确保文档质量。
    """

    def __init__(self, llm_service: Any = None):
        super().__init__(
            role=AgentRole.AUDITOR,
            name="合规审计师 (Auditor)",
            description="审查各类技术文档的合规性，确保符合最新行业标准和规范要求。",
            tools=["standard_checker", "document_validator", "compliance_engine"],
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行文档审计任务
        """
        query = input_data.get("task", "")

        self._log_thought(state, "thought", f"收到审计请求: {query}")

        # 判断任务类型
        if "检修报告" in query or "检修记录" in query:
            return await self._audit_maintenance_report(state, query)
        elif "试验报告" in query:
            return await self._audit_test_report(state, query)
        elif "竣工资料" in query or "验收" in query:
            return await self._audit_completion_docs(state, query)
        elif "定值" in query or "整定" in query:
            return await self._audit_setting_calculation(state, query)
        else:
            return await self._general_compliance_check(state, query)

    async def _audit_maintenance_report(self, state: AgentState, query: str) -> Dict[str, Any]:
        """检修报告审计 (Mock)"""
        self._log_thought(state, "plan", "开始审查检修报告合规性...")

        # Mock报告信息
        report_info = {
            "title": "#1主变年度检修报告",
            "date": "2024-10-15",
            "department": "运维班",
            "standard": "DL/T 596-2021 电力设备预防性试验规程"
        }

        self._log_thought(
            state,
            "action",
            "对比行业标准要求...",
            detail=report_info
        )

        # Mock审计发现
        findings = [
            {
                "category": "必备项缺失",
                "item": "绝缘电阻测试数据",
                "description": "报告中未包含主变各侧绝缘电阻测试数据",
                "reference": "DL/T 596-2021 第5.2.1条",
                "severity": "严重"
            },
            {
                "category": "格式不规范",
                "item": "油色谱数据表格",
                "description": "表格未注明测试方法和判断标准",
                "reference": "DL/T 722-2014",
                "severity": "一般"
            },
            {
                "category": "签字审批",
                "item": "缺少技术负责人签字",
                "description": "报告仅有操作人员签字，缺少技术负责人审核签字",
                "reference": "内部管理规定",
                "severity": "重要"
            }
        ]

        compliant_items = [
            "设备基本信息完整",
            "检修项目清单明确",
            "工作票编号规范",
            "检修前后数据对比清晰"
        ]

        self._log_thought(
            state,
            "observation",
            f"审计完成: 发现 {len(findings)} 项问题，{len(compliant_items)} 项符合要求",
            detail={"findings": findings, "compliant": compliant_items}
        )

        # 生成审计报告
        report = "## 📋 检修报告审计报告\n\n"
        report += f"**审计对象**: {report_info['title']}\n"
        report += f"**报告日期**: {report_info['date']}\n"
        report += f"**编制部门**: {report_info['department']}\n"
        report += f"**适用标准**: {report_info['standard']}\n\n"

        report += "### 审计发现\n\n"
        if findings:
            for idx, finding in enumerate(findings):
                severity_icon = {"严重": "🔴", "重要": "🟡", "一般": "🟢"}.get(
                    finding["severity"], "⚪")
                report += f"{idx+1}. {severity_icon} **{finding['category']}** - {finding['item']}\n"
                report += f"   - 问题描述: {finding['description']}\n"
                report += f"   - 依据标准: {finding['reference']}\n\n"

        report += "### 符合项\n\n"
        for item in compliant_items:
            report += f"- ✅ {item}\n"

        report += "\n### 审计结论\n"
        severe_count = sum(1 for f in findings if f["severity"] == "严重")
        if severe_count > 0:
            report += f"❌ **不通过** - 存在 {severe_count} 项严重问题，需整改后重新提交。\n\n"
        elif len(findings) > 0:
            report += f"⚠️ **有条件通过** - 存在 {len(findings)} 项问题，建议完善后归档。\n\n"
        else:
            report += "✅ **通过** - 报告符合标准要求。\n\n"

        report += "### 整改建议\n"
        report += "1. 补充缺失的试验数据，特别是绝缘电阻测试\n"
        report += "2. 规范表格格式，添加必要的说明和依据\n"
        report += "3. 完善审批流程，确保技术负责人签字\n"

        return {
            "answer": report,
            "findings": findings,
            "compliant_items": compliant_items,
            "audit_result": "conditional_pass" if len(findings) > 0 else "pass"
        }

    async def _audit_test_report(self, state: AgentState, query: str) -> Dict[str, Any]:
        """试验报告审计 (Mock)"""
        self._log_thought(state, "action", "审查试验报告...")

        audit_result = {
            "report_type": "交流耐压试验报告",
            "equipment": "110kV GIS设备",
            "compliance_score": 85,
            "issues": [
                {
                    "item": "试验电压未标注有效值/峰值",
                    "severity": "一般"
                },
                {
                    "item": "环境温湿度记录不完整",
                    "severity": "一般"
                }
            ]
        }

        report = "## 🔬 试验报告审计报告\n\n"
        report += f"**报告类型**: {audit_result['report_type']}\n"
        report += f"**试验设备**: {audit_result['equipment']}\n"
        report += f"**合规评分**: {audit_result['compliance_score']}/100\n\n"

        report += "### 发现的问题\n"
        for idx, issue in enumerate(audit_result['issues']):
            report += f"{idx+1}. {issue['item']} (严重程度: {issue['severity']})\n"

        report += "\n### 整改建议\n"
        report += "- 明确标注试验电压的类型(有效值/峰值)\n"
        report += "- 补充完整的环境条件记录\n"

        return {
            "answer": report,
            "audit_result": audit_result
        }

    async def _audit_completion_docs(self, state: AgentState, query: str) -> Dict[str, Any]:
        """竣工资料审计 (Mock)"""
        self._log_thought(state, "plan", "审查竣工验收资料完整性...")

        required_docs = [
            {"name": "施工组织设计", "status": "✅ 已提交", "compliant": True},
            {"name": "设备出厂合格证", "status": "✅ 已提交", "compliant": True},
            {"name": "隐蔽工程验收记录", "status": "❌ 缺失", "compliant": False},
            {"name": "交接试验报告", "status": "✅ 已提交", "compliant": True},
            {"name": "竣工图纸(盖章)", "status": "⚠️ 未盖章", "compliant": False},
            {"name": "设备调试记录", "status": "✅ 已提交", "compliant": True}
        ]

        compliant_count = sum(1 for doc in required_docs if doc["compliant"])
        completeness = (compliant_count / len(required_docs)) * 100

        report = "## 📦 竣工资料审计报告\n\n"
        report += f"**资料完整性**: {compliant_count}/{len(required_docs)} ({completeness:.1f}%)\n\n"

        report += "### 资料清单\n"
        for doc in required_docs:
            report += f"- {doc['status']} {doc['name']}\n"

        report += "\n### 审计结论\n"
        if completeness < 100:
            report += f"⚠️ 资料不完整，需补充缺失项后方可验收。\n"
        else:
            report += "✅ 资料齐全，符合验收要求。\n"

        return {
            "answer": report,
            "required_docs": required_docs,
            "completeness": completeness
        }

    async def _audit_setting_calculation(self, state: AgentState, query: str) -> Dict[str, Any]:
        """定值整定计算审计 (Mock)"""
        self._log_thought(state, "action", "审查保护定值计算...")

        calculation_audit = {
            "protection": "#1主变差动保护",
            "calculation_method": "符合DL/T 584-2017",
            "issues": [
                {
                    "item": "CT变比未标注",
                    "detail": "计算书中使用了CT变比但未明确标注具体数值",
                    "impact": "影响定值复核"
                }
            ],
            "verified_items": [
                "计算公式正确",
                "系数选取合理",
                "定值范围在保护装置允许范围内",
                "与现场设备参数一致"
            ]
        }

        report = "## 🧮 定值计算审计报告\n\n"
        report += f"**保护名称**: {calculation_audit['protection']}\n"
        report += f"**计算方法**: {calculation_audit['calculation_method']}\n\n"

        report += "### 审核通过项\n"
        for item in calculation_audit['verified_items']:
            report += f"- ✅ {item}\n"

        report += "\n### 需要完善的地方\n"
        for issue in calculation_audit['issues']:
            report += f"- ⚠️ {issue['item']}\n"
            report += f"  说明: {issue['detail']}\n"

        report += "\n### 审计意见\n"
        report += "计算逻辑正确，但需补充完整的参数标注信息。\n"

        return {
            "answer": report,
            "calculation_audit": calculation_audit
        }

    async def _general_compliance_check(self, state: AgentState, query: str) -> Dict[str, Any]:
        """通用合规检查"""
        return {
            "answer": "合规审计师随时为您服务！我可以审查:\n"
            "1. 📋 检修报告合规性\n"
            "2. 🔬 试验报告标准符合性\n"
            "3. 📦 竣工资料完整性\n"
            "4. 🧮 定值计算规范性\n\n"
            "请提供需要审查的文档类型。"
        }
