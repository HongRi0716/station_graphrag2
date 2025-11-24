import logging
from typing import Any, Dict, List

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class WorkPermitAgent(BaseAgent):
    """
    工作票智能编制与审核专家 (Work Permit Agent)
    职责：自动生成工作票、审核工作票合规性、安全措施完整性检查。
    特点：精通电力安全工作规程，确保作业安全。
    """

    def __init__(self, llm_service: Any = None):
        super().__init__(
            role=AgentRole.WORK_PERMIT,
            name="工作票专家 (Work Permit Agent)",
            description="智能生成和审核工作票，确保作业的安全性和规范性。",
            tools=["permit_template",
                   "safety_measure_validator", "hazard_identifier"],
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工作票编制或审核任务
        """
        query = input_data.get("task", "")

        self._log_thought(state, "thought", f"收到工作票任务: {query}")

        # 判断任务类型
        if "生成" in query or "编制" in query or "开票" in query:
            return await self._generate_work_permit(state, query)
        elif "审核" in query or "检查" in query:
            return await self._review_work_permit(state, query)
        elif "延期" in query or "变更" in query:
            return await self._handle_permit_change(state, query)
        else:
            return await self._general_guidance(state, query)

    async def _generate_work_permit(self, state: AgentState, query: str) -> Dict[str, Any]:
        """生成工作票 (Mock)"""
        self._log_thought(state, "plan", "开始智能生成工作票...")

        # 识别工作类型
        work_type = self._identify_work_type(query)

        self._log_thought(
            state,
            "action",
            f"识别工作类型: {work_type}",
            detail={"query": query}
        )

        # 生成工作票
        permit = self._create_permit_template(work_type, query)

        # 识别危险点
        hazards = self._identify_hazards(permit)
        self._log_thought(
            state,
            "observation",
            f"识别到 {len(hazards)} 个危险点",
            detail={"hazards": hazards}
        )

        # 生成安全措施
        safety_measures = self._generate_safety_measures(permit, hazards)
        permit['safety_measures'] = safety_measures

        self._log_thought(
            state,
            "thought",
            f"已生成 {len(safety_measures)} 项安全措施",
            detail={"measures": safety_measures}
        )

        # 格式化输出
        report = self._format_work_permit(permit, hazards)

        return {
            "answer": report,
            "permit": permit,
            "hazards": hazards
        }

    def _identify_work_type(self, query: str) -> str:
        """识别工作类型"""
        if "高压" in query or "110kV" in query or "220kV" in query:
            if "停电" in query or "检修" in query:
                return "第一种工作票"
            else:
                return "第二种工作票"
        elif "带电作业" in query:
            return "带电作业工作票"
        elif "低压" in query or "10kV" in query or "配电" in query:
            return "第二种工作票"
        else:
            return "第一种工作票"

    def _create_permit_template(self, work_type: str, query: str) -> Dict[str, Any]:
        """创建工作票模板 (Mock)"""

        base_permit = {
            "permit_no": "WP-2024-1124-001",
            "permit_type": work_type,
            "application_date": "2024-11-24",
            "applicant": "待填写",
            "work_leader": "待指定",
            "work_members": [],
        }

        if "#1主变" in query or "主变" in query:
            base_permit.update({
                "work_location": "110kV变电站 #1主变场地",
                "equipment": "#1主变压器",
                "voltage_level": "110kV/10kV",
                "work_content": "#1主变年度预防性试验",
                "work_description": [
                    "测量绝缘电阻",
                    "测量直流电阻",
                    "测量变比和极性",
                    "测量介质损耗",
                    "油色谱分析"
                ],
                "planned_start": "2024-11-25 08:00",
                "planned_end": "2024-11-25 17:00",
                "work_duration": "1天"
            })
        elif "开关" in query or "断路器" in query:
            base_permit.update({
                "work_location": "10kV开关室 #2出线柜",
                "equipment": "#2出线断路器",
                "voltage_level": "10kV",
                "work_content": "#2出线断路器例行检修",
                "work_description": [
                    "断路器机械特性测试",
                    "触头磨损检查",
                    "操作机构检查",
                    "二次回路检查",
                    "清扫维护"
                ],
                "planned_start": "2024-11-25 09:00",
                "planned_end": "2024-11-25 16:00",
                "work_duration": "1天"
            })
        else:
            base_permit.update({
                "work_location": "待明确",
                "equipment": "待明确",
                "work_content": "待明确",
                "work_description": []
            })

        return base_permit

    def _identify_hazards(self, permit: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别危险点 (Mock)"""

        voltage_level = permit.get('voltage_level', '')
        work_content = permit.get('work_content', '')

        hazards = []

        # 高压作业通用危险点
        if "110kV" in voltage_level or "220kV" in voltage_level:
            hazards.extend([
                {
                    "id": "H001",
                    "type": "触电风险",
                    "description": "高压设备带电部分外露，存在人员触电危险",
                    "severity": "极高",
                    "location": "高压侧设备区域"
                },
                {
                    "id": "H002",
                    "type": "误送电",
                    "description": "存在误合开关导致设备带电的风险",
                    "severity": "高",
                    "location": "操作机构"
                }
            ])

        # 试验作业危险点
        if "试验" in work_content:
            hazards.extend([
                {
                    "id": "H003",
                    "type": "试验设备风险",
                    "description": "高压试验设备操作不当可能造成人身伤害",
                    "severity": "高",
                    "location": "试验区域"
                },
                {
                    "id": "H004",
                    "type": "感应电压",
                    "description": "邻近带电设备可能产生感应电压",
                    "severity": "中",
                    "location": "工作区域"
                }
            ])

        # 高处作业危险点
        if "主变" in permit.get('equipment', ''):
            hazards.append({
                "id": "H005",
                "type": "高处坠落",
                "description": "攀登主变本体存在坠落风险",
                "severity": "高",
                "location": "主变顶部"
            })

        return hazards

    def _generate_safety_measures(self, permit: Dict[str, Any], hazards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成安全措施 (Mock)"""

        measures = []

        # 基本安全措施
        measures.extend([
            {
                "category": "停电措施",
                "content": "断开{equipment}所有电源（包括各侧断路器、隔离开关）".format(
                    equipment=permit.get('equipment', '设备')
                ),
                "responsible": "工作票签发人",
                "mandatory": True
            },
            {
                "category": "验电措施",
                "content": "使用合格的验电器对设备各侧进行验电，确认无电压",
                "responsible": "工作负责人",
                "mandatory": True
            },
            {
                "category": "接地措施",
                "content": "在设备各侧装设接地线，接地线应使用专用线夹，先接接地端后接导体端",
                "responsible": "工作负责人",
                "mandatory": True
            },
            {
                "category": "标示措施",
                "content": "在设备开关操作把手悬挂'禁止合闸，有人工作！'标示牌",
                "responsible": "工作负责人",
                "mandatory": True
            },
            {
                "category": "围栏措施",
                "content": "在工作地点设置围栏或遮栏，悬挂'止步，高压危险！'标示牌",
                "responsible": "工作班成员",
                "mandatory": True
            }
        ])

        # 根据危险点添加针对性措施
        for hazard in hazards:
            if hazard['type'] == "高处坠落":
                measures.append({
                    "category": "高处作业措施",
                    "content": "攀登设备时必须佩戴安全带，使用合格的梯子或脚手架",
                    "responsible": "全体作业人员",
                    "mandatory": True
                })
            elif hazard['type'] == "感应电压":
                measures.append({
                    "category": "防感应措施",
                    "content": "在可能产生感应电压的部位加装临时接地线",
                    "responsible": "工作负责人",
                    "mandatory": True
                })
            elif hazard['type'] == "试验设备风险":
                measures.append({
                    "category": "试验安全措施",
                    "content": "试验设备使用前应检查，试验过程中非试验人员不得进入试验区域",
                    "responsible": "试验人员",
                    "mandatory": True
                })

        # 个人防护措施
        measures.append({
            "category": "个人防护",
            "content": "全体作业人员应佩戴安全帽、绝缘手套、绝缘鞋等防护用品",
            "responsible": "全体作业人员",
            "mandatory": True
        })

        return measures

    def _format_work_permit(self, permit: Dict[str, Any], hazards: List[Dict[str, Any]]) -> str:
        """格式化工作票输出"""

        report = "## 📄 工作票\n\n"
        report += f"**票号**: {permit.get('permit_no', 'N/A')}\n"
        report += f"**票种**: {permit.get('permit_type', 'N/A')}\n"
        report += f"**申请日期**: {permit.get('application_date', 'N/A')}\n\n"

        report += "### 工作任务\n"
        report += f"**工作地点**: {permit.get('work_location', 'N/A')}\n"
        report += f"**工作设备**: {permit.get('equipment', 'N/A')}\n"
        report += f"**电压等级**: {permit.get('voltage_level', 'N/A')}\n"
        report += f"**工作内容**: {permit.get('work_content', 'N/A')}\n"
        report += f"**计划工期**: {permit.get('work_duration', 'N/A')}\n"
        report += f"**计划时间**: {permit.get('planned_start', 'N/A')} 至 {permit.get('planned_end', 'N/A')}\n\n"

        if permit.get('work_description'):
            report += "### 工作任务详细说明\n"
            for idx, task in enumerate(permit['work_description']):
                report += f"{idx+1}. {task}\n"
            report += "\n"

        if hazards:
            report += "### ⚠️ 危险点分析\n\n"
            for hazard in hazards:
                severity_icon = {"极高": "🔴", "高": "🟠", "中": "🟡",
                                 "低": "🟢"}.get(hazard['severity'], "⚪")
                report += f"**{hazard['id']}**: {severity_icon} **{hazard['type']}** (风险等级: {hazard['severity']})\n"
                report += f"- 描述: {hazard['description']}\n"
                report += f"- 位置: {hazard['location']}\n\n"

        if permit.get('safety_measures'):
            report += "### 🛡️ 安全措施\n\n"
            for idx, measure in enumerate(permit['safety_measures']):
                mandatory = "【必须】" if measure.get('mandatory') else "【建议】"
                report += f"**{idx+1}. {measure['category']}** {mandatory}\n"
                report += f"- 措施内容: {measure['content']}\n"
                report += f"- 责任人: {measure['responsible']}\n\n"

        report += "### 📝 签名栏\n\n"
        report += "| 角色 | 姓名 | 日期时间 | 签名 |\n"
        report += "|------|------|---------|------|\n"
        report += "| 工作票签发人 | | | |\n"
        report += "| 工作许可人 | | | |\n"
        report += "| 工作负责人 | | | |\n"
        report += "| 工作班成员 | | | |\n\n"

        report += "---\n"
        report += "*本工作票由AI智能生成，请人工复核后使用*\n"

        return report

    async def _review_work_permit(self, state: AgentState, query: str) -> Dict[str, Any]:
        """审核工作票"""
        self._log_thought(state, "action", "正在审核工作票...")

        # Mock审核结果
        review_result = {
            "permit_no": "WP-2024-1120-008",
            "completeness_check": {
                "basic_info": "✅ 完整",
                "work_content": "✅ 明确",
                "safety_measures": "⚠️ 需完善",
                "signatures": "❌ 缺失"
            },
            "issues": [
                {
                    "category": "安全措施",
                    "severity": "重要",
                    "description": "未明确验电步骤和验电器型号",
                    "suggestion": "补充验电措施，注明使用的验电器型号"
                },
                {
                    "category": "危险点分析",
                    "severity": "一般",
                    "description": "危险点分析不够全面",
                    "suggestion": "补充高处作业和感应电压危险点"
                },
                {
                    "category": "审批流程",
                    "severity": "严重",
                    "description": "缺少工作票签发人签字",
                    "suggestion": "必须完成签发人签字后方可执行"
                }
            ],
            "approved": False
        }

        report = "## 🔍 工作票审核报告\n\n"
        report += f"**票号**: {review_result['permit_no']}\n\n"

        report += "### 完整性检查\n"
        for item, status in review_result['completeness_check'].items():
            report += f"- {status} {item}\n"
        report += "\n"

        if review_result['issues']:
            report += f"### 发现的问题 ({len(review_result['issues'])}项)\n\n"
            for idx, issue in enumerate(review_result['issues']):
                severity_icon = {"严重": "🔴", "重要": "🟡",
                                 "一般": "🟢"}.get(issue['severity'], "⚪")
                report += f"{idx+1}. {severity_icon} **{issue['category']}** ({issue['severity']})\n"
                report += f"   - 问题: {issue['description']}\n"
                report += f"   - 建议: {issue['suggestion']}\n\n"

        if review_result['approved']:
            report += "### ✅ 审核结论: 通过\n"
        else:
            report += "### ❌ 审核结论: 不通过\n"
            report += "请按照上述建议完善后重新提交审核。\n"

        return {
            "answer": report,
            "review_result": review_result
        }

    async def _handle_permit_change(self, state: AgentState, query: str) -> Dict[str, Any]:
        """处理工作票变更/延期"""
        return {
            "answer": "工作票变更/延期功能提示:\n"
            "1. 工作票延期需重新办理许可手续\n"
            "2. 工作内容变更需重新办票\n"
            "3. 工作负责人变更需办理交接手续\n\n"
            "请说明具体的变更需求。"
        }

    async def _general_guidance(self, state: AgentState, query: str) -> Dict[str, Any]:
        """通用指导"""
        return {
            "answer": "工作票专家为您服务！我可以:\n"
            "1. 📄 智能生成工作票 (如: '生成#1主变检修工作票')\n"
            "2. 🔍 审核工作票合规性\n"
            "3. ⚠️ 识别作业危险点\n"
            "4. 🛡️ 生成安全措施清单\n\n"
            "请告诉我具体的工作任务或需要审核的票号。"
        }
