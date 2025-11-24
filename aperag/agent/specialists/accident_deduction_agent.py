import logging
from typing import Any, Dict, List

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class AccidentDeductionAgent(BaseAgent):
    """
    事故预想与应急演练专家 (Accident Deduction Agent)
    职责：生成事故预想报告、制定应急预案、模拟事故处置流程。
    特点：基于历史事故案例和设备状况，预测可能发生的事故并提供处置方案。
    """

    def __init__(self, llm_service: Any = None):
        super().__init__(
            role=AgentRole.ACCIDENT_DEDUCTION,
            name="事故预想专家 (Accident Deduction Agent)",
            description="编制事故预想报告，制定应急预案，指导应急演练。",
            tools=["accident_database", "scenario_generator", "drill_designer"],
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行事故预想或应急演练任务
        """
        query = input_data.get("task", "")

        self._log_thought(state, "thought", f"收到事故预想任务: {query}")

        # 判断任务类型
        if "预想" in query or "事故" in query:
            return await self._generate_accident_deduction(state, query)
        elif "应急预案" in query or "预案" in query:
            return await self._generate_emergency_plan(state, query)
        elif "演练" in query or "推演" in query:
            return await self._design_drill(state, query)
        elif "案例" in query or "历史" in query:
            return await self._search_historical_cases(state, query)
        else:
            return await self._general_guidance(state, query)

    async def _generate_accident_deduction(self, state: AgentState, query: str) -> Dict[str, Any]:
        """生成事故预想报告 (Mock)"""
        self._log_thought(state, "plan", "开始编制事故预想报告...")

        # 识别设备和场景
        equipment, scenario = self._parse_accident_scenario(query)

        self._log_thought(
            state,
            "action",
            f"分析场景: {equipment} - {scenario}",
            detail={"equipment": equipment, "scenario": scenario}
        )

        # 查询历史案例
        self._log_thought(
            state,
            "action",
            "检索相关历史事故案例...",
            detail={"data_source": "事故案例库"}
        )

        # 生成事故预想
        deduction = self._create_accident_deduction(equipment, scenario)

        self._log_thought(
            state,
            "observation",
            f"已生成事故预想，包含 {len(deduction['possible_faults'])} 种可能故障",
            detail=deduction
        )

        # 格式化输出
        report = self._format_accident_deduction(deduction)

        return {
            "answer": report,
            "deduction": deduction
        }

    def _parse_accident_scenario(self, query: str) -> tuple:
        """解析事故场景"""
        equipment = "未指定设备"
        scenario = "常规事故预想"

        if "#1主变" in query or "1号主变" in query or "主变" in query:
            equipment = "#1主变压器"
        elif "母线" in query:
            equipment = "110kV母线"
        elif "线路" in query:
            equipment = "110kV线路"
        elif "开关" in query or "断路器" in query:
            equipment = "断路器设备"

        if "重瓦斯" in query or "瓦斯" in query:
            scenario = "重瓦斯保护动作"
        elif "差动" in query:
            scenario = "差动保护动作"
        elif "火灾" in query:
            scenario = "设备火灾"
        elif "雷击" in query:
            scenario = "雷击故障"
        elif "过负荷" in query:
            scenario = "设备过负荷"

        return equipment, scenario

    def _create_accident_deduction(self, equipment: str, scenario: str) -> Dict[str, Any]:
        """创建事故预想 (Mock)"""

        if "主变" in equipment and "瓦斯" in scenario:
            return {
                "title": "#1主变重瓦斯保护动作事故预想",
                "equipment": equipment,
                "accident_type": "主变重瓦斯保护动作跳闸",
                "possible_causes": [
                    {
                        "cause": "主变内部故障",
                        "details": [
                            "绕组匝间短路",
                            "铁芯烧损",
                            "引线接触不良发热",
                            "油箱内部放电"
                        ],
                        "probability": "高"
                    },
                    {
                        "cause": "油系统故障",
                        "details": [
                            "油位急剧下降",
                            "油管破裂",
                            "冷却器管道泄漏"
                        ],
                        "probability": "中"
                    },
                    {
                        "cause": "保护误动",
                        "details": [
                            "瓦斯继电器故障",
                            "二次回路异常",
                            "保护装置误动作"
                        ],
                        "probability": "低"
                    }
                ],
                "possible_faults": [
                    "主变跳闸，110kV和10kV侧开关跳开",
                    "主变供电中断",
                    "下级用户失电",
                    "可能伴随声音、气味异常"
                ],
                "immediate_actions": [
                    {
                        "seq": 1,
                        "action": "立即汇报调度",
                        "detail": "向地区调度汇报主变跳闸情况",
                        "responsible": "值班员"
                    },
                    {
                        "seq": 2,
                        "action": "负荷转移",
                        "detail": "请示调度，将10kV负荷倒至#2主变或其他变电站",
                        "responsible": "值班员"
                    },
                    {
                        "seq": 3,
                        "action": "现场检查",
                        "detail": "检查主变本体外观、油位、油色、气体继电器",
                        "responsible": "值班员（两人及以上）"
                    },
                    {
                        "seq": 4,
                        "action": "保护分析",
                        "detail": "查看保护动作报告，打印故障录波",
                        "responsible": "值班员"
                    },
                    {
                        "seq": 5,
                        "action": "安全措施",
                        "detail": "拉开主变各侧隔离开关，装设接地线，设置围栏",
                        "responsible": "值班员（经调度同意）"
                    }
                ],
                "inspection_points": [
                    {
                        "location": "瓦斯继电器",
                        "check_items": ["是否有气体", "气体颜色和气味", "油位是否下降"]
                    },
                    {
                        "location": "主变本体",
                        "check_items": ["外观是否破损", "有无漏油痕迹", "是否有异味", "是否有异常声响"]
                    },
                    {
                        "location": "套管",
                        "check_items": ["是否完好", "有无放电痕迹", "油位是否正常"]
                    },
                    {
                        "location": "冷却器",
                        "check_items": ["风扇运行状态", "油泵运行状态", "管路有无泄漏"]
                    }
                ],
                "handling_principles": [
                    "严禁强送电！主变内部故障可能扩大，必须经试验合格后方可投运",
                    "如瓦斯继电器内有气体，应采集气体样本送检",
                    "如属保护误动，应查明原因后方可投运",
                    "如发现严重故障征兆（喷油、冒烟），应立即灭火并疏散人员"
                ],
                "recovery_conditions": [
                    "查明跳闸原因",
                    "消除设备缺陷",
                    "完成必要的试验（绝缘、色谱等）",
                    "试验结果合格",
                    "得到调度许可",
                    "完成操作票审批"
                ]
            }
        elif "母线" in equipment:
            return {
                "title": "110kV母线故障事故预想",
                "equipment": equipment,
                "accident_type": "母线故障跳闸",
                "possible_causes": [
                    {"cause": "母线或设备绝缘击穿", "probability": "高"},
                    {"cause": "小动物侵入引起短路", "probability": "中"},
                    {"cause": "设备外绝缘污闪", "probability": "中"},
                    {"cause": "保护误动", "probability": "低"}
                ],
                "possible_faults": [
                    "母差保护动作，母线及所有连接元件跳闸",
                    "全站失电",
                    "大面积用户停电"
                ],
                "immediate_actions": [
                    {"seq": 1, "action": "立即汇报调度", "responsible": "值班员"},
                    {"seq": 2, "action": "检查保护动作情况", "responsible": "值班员"},
                    {"seq": 3, "action": "外观检查",
                        "detail": "检查母线及设备有无明显故障点", "responsible": "值班员"},
                    {"seq": 4, "action": "试送电",
                        "detail": "经调度同意后，可尝试分段送电查找故障点", "responsible": "值班员"}
                ],
                "handling_principles": [
                    "如确定故障在某段母线，应隔离故障段后恢复其他段送电",
                    "如属保护误动，查明原因后可送电",
                    "如有明确的设备故障，应隔离该设备"
                ]
            }
        else:
            return {
                "title": f"{equipment}事故预想",
                "equipment": equipment,
                "accident_type": "待分析",
                "possible_causes": [],
                "possible_faults": [],
                "immediate_actions": [],
                "message": "请提供更详细的设备和事故类型信息"
            }

    def _format_accident_deduction(self, deduction: Dict[str, Any]) -> str:
        """格式化事故预想报告"""

        report = f"## 🚨 {deduction['title']}\n\n"
        report += f"**设备名称**: {deduction['equipment']}\n"
        report += f"**事故类型**: {deduction['accident_type']}\n\n"

        if deduction.get('possible_causes'):
            report += "### 一、可能的事故原因\n\n"
            for idx, cause in enumerate(deduction['possible_causes']):
                report += f"{idx+1}. **{cause['cause']}** (可能性: {cause.get('probability', '未知')})\n"
                if 'details' in cause:
                    for detail in cause['details']:
                        report += f"   - {detail}\n"
                report += "\n"

        if deduction.get('possible_faults'):
            report += "### 二、可能产生的后果\n\n"
            for fault in deduction['possible_faults']:
                report += f"- {fault}\n"
            report += "\n"

        if deduction.get('immediate_actions'):
            report += "### 三、应急处置步骤\n\n"
            for action in deduction['immediate_actions']:
                report += f"**第{action['seq']}步**: {action['action']}\n"
                if 'detail' in action:
                    report += f"- 具体操作: {action['detail']}\n"
                report += f"- 责任人: {action['responsible']}\n\n"

        if deduction.get('inspection_points'):
            report += "### 四、现场检查要点\n\n"
            for point in deduction['inspection_points']:
                report += f"**{point['location']}**\n"
                for item in point['check_items']:
                    report += f"- {item}\n"
                report += "\n"

        if deduction.get('handling_principles'):
            report += "### 五、处理原则\n\n"
            for idx, principle in enumerate(deduction['handling_principles']):
                report += f"{idx+1}. {principle}\n"
            report += "\n"

        if deduction.get('recovery_conditions'):
            report += "### 六、恢复运行条件\n\n"
            for idx, condition in enumerate(deduction['recovery_conditions']):
                report += f"{idx+1}. {condition}\n"
            report += "\n"

        report += "---\n"
        report += "*本事故预想报告供参考，实际处置应根据现场情况灵活调整*\n"

        return report

    async def _generate_emergency_plan(self, state: AgentState, query: str) -> Dict[str, Any]:
        """生成应急预案 (Mock)"""
        self._log_thought(state, "action", "正在生成应急预案...")

        plan = {
            "plan_name": "变电站火灾应急预案",
            "applicable_scope": "全站设备火灾事故",
            "emergency_organization": {
                "commander": "站长",
                "members": ["值班长", "值班员", "安全员"],
                "emergency_contacts": {
                    "消防": "119",
                    "调度": "XXXX-XXXX",
                    "公司领导": "XXXX-XXXX"
                }
            },
            "response_procedure": [
                {
                    "phase": "发现火情",
                    "actions": ["立即报警", "启动预案", "通知人员"]
                },
                {
                    "phase": "初期处置",
                    "actions": ["切断电源", "使用灭火器", "疏散人员"]
                },
                {
                    "phase": "专业救援",
                    "actions": ["配合消防", "警戒隔离", "监测扩散"]
                }
            ]
        }

        report = f"## 🚒 {plan['plan_name']}\n\n"
        report += f"**适用范围**: {plan['applicable_scope']}\n\n"
        report += "### 应急组织\n"
        report += f"- 指挥: {plan['emergency_organization']['commander']}\n"
        report += f"- 成员: {', '.join(plan['emergency_organization']['members'])}\n\n"
        report += "### 应急响应流程\n"
        for phase in plan['response_procedure']:
            report += f"**{phase['phase']}**\n"
            for action in phase['actions']:
                report += f"- {action}\n"
            report += "\n"

        return {
            "answer": report,
            "plan": plan
        }

    async def _design_drill(self, state: AgentState, query: str) -> Dict[str, Any]:
        """设计应急演练 (Mock)"""
        self._log_thought(state, "plan", "正在设计应急演练方案...")

        drill = {
            "drill_name": "主变跳闸应急演练",
            "objective": "检验人员应急处置能力，熟悉事故处理流程",
            "participants": ["值班人员", "检修人员", "调度人员"],
            "scenario": "#1主变重瓦斯保护动作跳闸",
            "steps": [
                {"time": "T+0分钟", "event": "模拟主变跳闸告警",
                    "expected_action": "值班员发现告警，汇报值班长"},
                {"time": "T+2分钟", "event": "值班长指令",
                    "expected_action": "汇报调度，启动应急预案"},
                {"time": "T+5分钟", "event": "现场检查",
                    "expected_action": "检查瓦斯继电器、主变本体"},
                {"time": "T+10分钟", "event": "负荷转移",
                    "expected_action": "操作将负荷转至备用电源"},
                {"time": "T+15分钟", "event": "演练总结",
                    "expected_action": "评估演练效果，总结经验"}
            ],
            "evaluation_points": [
                "反应速度",
                "操作规范性",
                "团队协作",
                "应急预案执行情况"
            ]
        }

        report = f"## 🎯 {drill['drill_name']}方案\n\n"
        report += f"**演练目标**: {drill['objective']}\n"
        report += f"**参演人员**: {', '.join(drill['participants'])}\n"
        report += f"**模拟场景**: {drill['scenario']}\n\n"
        report += "### 演练脚本\n"
        for step in drill['steps']:
            report += f"- **{step['time']}**: {step['event']}\n"
            report += f"  预期动作: {step['expected_action']}\n\n"
        report += "### 考核要点\n"
        for point in drill['evaluation_points']:
            report += f"- {point}\n"

        return {
            "answer": report,
            "drill": drill
        }

    async def _search_historical_cases(self, state: AgentState, query: str) -> Dict[str, Any]:
        """检索历史案例"""
        self._log_thought(state, "action", "检索历史事故案例...")

        # Mock历史案例
        cases = [
            {
                "case_id": "AC-2023-045",
                "date": "2023-06-15",
                "location": "XX市XX变电站",
                "equipment": "#2主变",
                "fault_type": "重瓦斯保护动作",
                "cause": "主变绕组匝间短路",
                "lesson": "应加强油色谱在线监测，及时发现设备隐患"
            },
            {
                "case_id": "AC-2022-128",
                "date": "2022-09-20",
                "location": "XX省XX变电站",
                "equipment": "110kV母线",
                "fault_type": "母差保护动作",
                "cause": "鸟害引起母线短路",
                "lesson": "应加强防小动物措施"
            }
        ]

        report = "## 📚 历史事故案例\n\n"
        for idx, case in enumerate(cases):
            report += f"### 案例{idx+1}: {case['case_id']}\n"
            report += f"- **时间**: {case['date']}\n"
            report += f"- **地点**: {case['location']}\n"
            report += f"- **设备**: {case['equipment']}\n"
            report += f"- **故障类型**: {case['fault_type']}\n"
            report += f"- **原因**: {case['cause']}\n"
            report += f"- **教训**: {case['lesson']}\n\n"

        return {
            "answer": report,
            "cases": cases
        }

    async def _general_guidance(self, state: AgentState, query: str) -> Dict[str, Any]:
        """通用指导"""
        return {
            "answer": "事故预想专家为您服务！我可以:\n"
            "1. 🚨 生成事故预想报告 (如: '#1主变重瓦斯保护动作事故预想')\n"
            "2. 🚒 编制应急预案\n"
            "3. 🎯 设计应急演练方案\n"
            "4. 📚 检索历史事故案例\n\n"
            "请告诉我具体的设备或事故类型。"
        }
