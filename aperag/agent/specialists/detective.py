import logging
from typing import Any, Dict, List

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class DetectiveAgent(BaseAgent):
    """
    图纸侦探 (The Detective)
    职责：CAD图纸解析、OCR识别、拓扑关系提取、图纸比对。
    特点：擅长处理电气图纸，提取设备信息和连接关系。
    """

    def __init__(self, llm_service: Any = None, vision_service: Any = None):
        super().__init__(
            role=AgentRole.DETECTIVE,
            name="图纸侦探 (Detective)",
            description="专注于电气图纸分析，能够识别CAD图元、提取设备参数、分析拓扑关系。",
            tools=["cad_parser", "ocr_engine",
                   "topology_analyzer", "image_comparator"],
        )
        self.llm_service = llm_service
        self.vision_service = vision_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行图纸分析任务
        """
        query = input_data.get("task", "")
        original_query = input_data.get("original_query", "")

        self._log_thought(state, "thought", f"收到图纸分析请求: {query}")

        # 判断任务类型
        if "比对" in query or "差异" in query or "变更" in query:
            return await self._compare_drawings(state, query)
        elif "拓扑" in query or "连接" in query or "关系" in query:
            return await self._analyze_topology(state, query)
        elif "识别" in query or "OCR" in query or "设备" in query:
            return await self._extract_equipment(state, query)
        else:
            return await self._general_analysis(state, query)

    async def _compare_drawings(self, state: AgentState, query: str) -> Dict[str, Any]:
        """图纸比对功能 (Mock)"""
        self._log_thought(state, "plan", "准备进行图纸版本比对...")

        # Mock: 模拟CAD解析
        self._log_thought(
            state,
            "action",
            "正在解析CAD图纸 V1.0 和 V2.0",
            detail={"parser": "AutoCAD DXF Parser", "status": "parsing"}
        )

        # Mock差异结果
        differences = [
            {
                "type": "设备变更",
                "location": "110kV I母间隔",
                "old_value": "101开关 - ABB VD4-12/630-25",
                "new_value": "101开关 - 西门子 3AH5",
                "severity": "重要"
            },
            {
                "type": "电气连接变更",
                "location": "#1主变高压侧",
                "description": "新增110kV母线PT",
                "severity": "一般"
            },
            {
                "type": "保护配置变更",
                "location": "主变保护屏",
                "old_value": "南瑞RCS-985",
                "new_value": "南瑞RCS-985G (升级版)",
                "severity": "重要"
            }
        ]

        self._log_thought(
            state,
            "observation",
            f"图纸比对完成，发现 {len(differences)} 处差异",
            detail={"differences": differences}
        )

        # 生成比对报告
        report = "## 📐 图纸版本比对报告\n\n"
        report += "**比对文件**: V1.0 vs V2.0\n\n"
        report += "### 差异汇总\n\n"

        for idx, diff in enumerate(differences):
            severity_icon = "🔴" if diff["severity"] == "重要" else "🟡"
            report += f"{idx+1}. {severity_icon} **{diff['type']}** - {diff['location']}\n"
            if "old_value" in diff:
                report += f"   - 变更前: {diff['old_value']}\n"
                report += f"   - 变更后: {diff['new_value']}\n"
            else:
                report += f"   - 说明: {diff['description']}\n"
            report += "\n"

        report += "### 风险提示\n"
        report += "⚠️ 发现2处重要变更，建议组织技术交底会议，确保施工人员知晓变更内容。"

        return {
            "answer": report,
            "differences": differences,
            "comparison_type": "CAD图纸比对"
        }

    async def _analyze_topology(self, state: AgentState, query: str) -> Dict[str, Any]:
        """拓扑关系分析 (Mock)"""
        self._log_thought(state, "plan", "开始分析电气拓扑关系...")

        # Mock拓扑分析结果
        topology_data = {
            "device": "#1主变",
            "voltage_level": "110kV/10kV",
            "connections": [
                {"from": "110kV I母", "to": "#1主变 110kV侧", "via": "101开关"},
                {"from": "#1主变 10kV侧", "to": "10kV I段母线", "via": "1011开关"},
                {"from": "#1主变", "to": "主变保护屏", "via": "CT/PT"},
            ],
            "protection_devices": ["主变差动保护", "后备保护", "瓦斯保护"],
            "adjacent_bays": ["110kV线路间隔", "10kV出线间隔"]
        }

        self._log_thought(
            state,
            "observation",
            "拓扑分析完成",
            detail=topology_data
        )

        report = "## 🔌 电气拓扑关系分析\n\n"
        report += f"**分析对象**: {topology_data['device']}\n"
        report += f"**电压等级**: {topology_data['voltage_level']}\n\n"
        report += "### 一次连接关系\n"
        for conn in topology_data['connections']:
            report += f"- {conn['from']} ➜ {conn['to']} (经由: {conn['via']})\n"
        report += f"\n### 保护配置\n"
        for prot in topology_data['protection_devices']:
            report += f"- {prot}\n"

        return {
            "answer": report,
            "topology": topology_data
        }

    async def _extract_equipment(self, state: AgentState, query: str) -> Dict[str, Any]:
        """设备信息提取 (Mock)"""
        self._log_thought(state, "action", "正在进行OCR识别...")

        # Mock设备信息
        equipment_list = [
            {
                "name": "101断路器",
                "type": "SF6断路器",
                "model": "LW38-110",
                "manufacturer": "平高电气",
                "parameters": {"额定电压": "110kV", "额定电流": "1250A"}
            },
            {
                "name": "#1主变压器",
                "type": "油浸式变压器",
                "model": "SFZ11-50000/110",
                "manufacturer": "特变电工",
                "parameters": {"容量": "50MVA", "电压比": "110/10.5kV"}
            }
        ]

        self._log_thought(
            state,
            "observation",
            f"识别到 {len(equipment_list)} 个设备",
            detail={"equipment": equipment_list}
        )

        report = "## 📋 图纸设备清单\\n\\n"
        for eq in equipment_list:
            report += f"### {eq['name']}\\n"
            report += f"- **类型**: {eq['type']}\\n"
            report += f"- **型号**: {eq['model']}\\n"
            report += f"- **厂家**: {eq['manufacturer']}\\n"
            report += f"- **参数**: {', '.join([f'{k}={v}' for k, v in eq['parameters'].items()])}\\n\\n"

        return {
            "answer": report,
            "equipment_list": equipment_list
        }

    async def _general_analysis(self, state: AgentState, query: str) -> Dict[str, Any]:
        """通用图纸分析"""
        self._log_thought(state, "thought", "执行通用图纸分析...")

        return {
            "answer": "已收到图纸分析请求。图纸侦探可以协助您进行：\n"
            "1. 📊 图纸版本比对\n"
            "2. 🔌 拓扑关系分析\n"
            "3. 📋 设备信息提取\n"
            "4. 🔍 图元识别与OCR\n\n"
            "请提供具体的图纸文件或明确分析需求。",
            "capabilities": ["比对", "拓扑分析", "设备识别", "OCR"]
        }
