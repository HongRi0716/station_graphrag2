import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class PowerGuaranteeAgent(BaseAgent):
    """
    保电方案编制专家 (Power Guarantee Agent)
    职责：制定重要活动保电方案、设备巡检计划、应急资源配置。
    特点：综合考虑设备状况、天气因素、应急资源，确保重要时段供电可靠性。
    """

    def __init__(self, llm_service: Any = None):
        super().__init__(
            role=AgentRole.POWER_GUARANTEE,
            name="保电方案专家 (Power Guarantee Agent)",
            description="编制重要活动保电方案，确保关键时期供电万无一失。",
            tools=["resource_manager", "weather_analyzer", "risk_assessor"],
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行保电方案编制任务
        """
        query = input_data.get("task", "")
        
        self._log_thought(state, "thought", f"收到保电任务: {query}")

        # 判断任务类型
        if "方案" in query or "编制" in query or "保电" in query:
            return await self._generate_power_guarantee_plan(state, query)
        elif "巡检" in query or "检查" in query:
            return await self._generate_inspection_plan(state, query)
        elif "应急" in query or "预案" in query:
            return await self._generate_emergency_response(state, query)
        elif "资源" in query or "物资" in query:
            return await self._prepare_resources(state, query)
        else:
            return await self._general_guidance(state, query)

    async def _generate_power_guarantee_plan(self, state: AgentState, query: str) -> Dict[str, Any]:
        """生成保电方案 (Mock)"""
        self._log_thought(state, "plan", "开始编制保电方案...")
        
        # 解析保电任务
        event_info = self._parse_power_guarantee_event(query)
        
        self._log_thought(
            state,
            "action",
            f"识别保电任务: {event_info['event_name']}",
            detail=event_info
        )

        # 评估风险
        self._log_thought(
            state,
            "action",
            "正在评估供电风险...",
            detail={"analysis": "设备状况 + 天气预报 + 负荷预测"}
        )

        # 查询设备状态
        self._log_thought(
            state,
            "action",
            "查询关键设备运行状态...",
            detail={"data_source": "SCADA实时数据 + 设备台账"}
        )

        # 生成保电方案
        plan = self._create_power_guarantee_plan(event_info)
        
        self._log_thought(
            state,
            "observation",
            f"保电方案生成完成，包含 {len(plan['measures'])} 项保障措施",
            detail=plan
        )

        # 格式化输出
        report = self._format_power_guarantee_plan(plan)

        return {
            "answer": report,
            "plan": plan
        }

    def _parse_power_guarantee_event(self, query: str) -> Dict[str, Any]:
        """解析保电活动信息"""
        
        event_info = {
            "event_name": "待明确",
            "event_level": "重要",
            "start_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "key_locations": []
        }

        # 识别活动类型
        if "高考" in query or "中考" in query:
            event_info["event_name"] = "高考保电"
            event_info["event_level"] = "一级（特级保电）"
            event_info["key_locations"] = ["XX中学", "XX考点"]
        elif "会议" in query or "大会" in query:
            event_info["event_name"] = "重要会议保电"
            event_info["event_level"] = "一级"
            event_info["key_locations"] = ["会议中心", "会展中心"]
        elif "节假日" in query or "春节" in query or "国庆" in query:
            event_info["event_name"] = "春节保电"
            event_info["event_level"] = "二级"
            event_info["key_locations"] = ["全网"]
        elif "演唱会" in query or "演出" in query:
            event_info["event_name"] = "大型活动保电"
            event_info["event_level"] = "二级"
            event_info["key_locations"] = ["体育场", "演出场馆"]
        else:
            event_info["event_name"] = "常规保电任务"
            event_info["event_level"] = "三级"

        return event_info

    def _create_power_guarantee_plan(self, event_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建保电方案 (Mock)"""
        
        plan = {
            "plan_no": f"PG-{datetime.now().strftime('%Y%m%d')}-001",
            "plan_name": f"{event_info['event_name']}保电工作方案",
            "event_info": event_info,
            "organization": {
                "leader": "分管副总经理",
                "deputy_leader": "运维部主任",
                "members": ["运维班长", "调度值班长", "检修负责人", "应急抢修队长"],
                "emergency_contact": {
                    "调度中心": "XXXX-1234",
                    "运维部": "XXXX-5678",
                    "应急队": "XXXX-9012"
                }
            },
            "risk_assessment": {
                "weather_risk": {
                    "level": "低",
                    "description": "保电期间天气良好，无极端天气预警"
                },
                "equipment_risk": {
                    "level": "中",
                    "description": "#2主变运行年限较长，需加强监视",
                    "key_equipment": ["#2主变", "110kV线路1", "10kV出线3"]
                },
                "load_risk": {
                    "level": "低",
                    "description": "负荷预测在正常范围内"
                }
            },
            "measures": [
                {
                    "category": "组织措施",
                    "items": [
                        "成立保电工作领导小组",
                        "明确各级职责分工",
                        "建立24小时值班制度",
                        "开展保电动员培训"
                    ]
                },
                {
                    "category": "设备检查",
                    "items": [
                        "对关键供电设备进行全面巡视和检查",
                        "提前消除设备缺陷和隐患",
                        "测试继电保护和自动装置",
                        "检查备用电源和应急发电设备"
                    ]
                },
                {
                    "category": "运行措施",
                    "items": [
                        "优化运行方式，确保供电路径冗余",
                        "重点设备实行双人值守",
                        "加密巡视频次（每2小时一次）",
                        "实时监控关键设备运行参数"
                    ]
                },
                {
                    "category": "应急准备",
                    "items": [
                        "应急抢修队伍24小时待命",
                        "准备充足的抢修物资和备品备件",
                        "应急发电车提前到位",
                        "应急通信设备测试正常"
                    ]
                },
                {
                    "category": "禁止性措施",
                    "items": [
                        "保电期间禁止安排计划检修",
                        "禁止进行可能影响供电的操作",
                        "禁止擅自变更运行方式",
                        "严禁无关人员进入设备区"
                    ]
                }
            ],
            "inspection_plan": {
                "before_event": [
                    {
                        "time": "保电前3天",
                        "content": "全面设备检查，消除缺陷",
                        "responsible": "运维班"
                    },
                    {
                        "time": "保电前1天",
                        "content": "再次巡视关键设备，确认状态良好",
                        "responsible": "值班人员"
                    }
                ],
                "during_event": [
                    {
                        "frequency": "每2小时",
                        "content": "巡视关键设备，记录运行参数",
                        "responsible": "值班人员"
                    },
                    {
                        "frequency": "每4小时",
                        "content": "汇总设备运行情况，上报保电小组",
                        "responsible": "值班长"
                    }
                ],
                "after_event": [
                    {
                        "time": "保电结束后1天",
                        "content": "全面检查设备，统计保电数据",
                        "responsible": "运维班"
                    }
                ]
            },
            "emergency_scenarios": [
                {
                    "scenario": "主变跳闸",
                    "response": "立即启动应急预案，投入备用主变，确保5分钟内恢复供电"
                },
                {
                    "scenario": "线路故障",
                    "response": "自动重合闸，若不成功则切换至备用线路供电"
                },
                {
                    "scenario": "全站失电",
                    "response": "启动应急发电车，对关键负荷供电"
                }
            ],
            "resource_preparation": {
                "personnel": {
                    "on_site": "值班人员2名",
                    "standby": "应急抢修队5名",
                    "support": "技术专家1名"
                },
                "equipment": {
                    "emergency_generator": "1台（500kVA），提前到位",
                    "vehicles": "应急抢修车2辆",
                    "tools": "完整应急工器具包"
                },
                "materials": {
                    "spare_parts": ["开关备件", "电缆接头", "熔断器"],
                    "consumables": ["绝缘胶布", "标示牌", "接地线"]
                }
            },
            "communication_plan": {
                "daily_report": "每日18:00向上级汇报当日保电情况",
                "emergency_report": "突发事件立即上报，15分钟内提交初步情况",
                "completion_report": "保电结束后24小时内提交总结报告"
            }
        }

        return plan

    def _format_power_guarantee_plan(self, plan: Dict[str, Any]) -> str:
        """格式化保电方案输出"""
        
        report = f"## 🛡️ {plan['plan_name']}\n\n"
        report += f"**方案编号**: {plan['plan_no']}\n"
        report += f"**保电级别**: {plan['event_info']['event_level']}\n"
        report += f"**保电时间**: {plan['event_info']['start_date']} 至 {plan['event_info']['end_date']}\n"
        
        if plan['event_info'].get('key_locations'):
            report += f"**重点保障**: {', '.join(plan['event_info']['key_locations'])}\n"
        report += "\n"

        # 组织机构
        report += "### 一、保电组织机构\n\n"
        report += f"**组长**: {plan['organization']['leader']}\n"
        report += f"**副组长**: {plan['organization']['deputy_leader']}\n"
        report += f"**成员**: {', '.join(plan['organization']['members'])}\n\n"
        report += "**应急联系方式**\n"
        for role, phone in plan['organization']['emergency_contact'].items():
            report += f"- {role}: {phone}\n"
        report += "\n"

        # 风险评估
        report += "### 二、风险评估\n\n"
        for risk_type, risk_data in plan['risk_assessment'].items():
            risk_name = {"weather_risk": "天气风险", "equipment_risk": "设备风险", "load_risk": "负荷风险"}.get(risk_type, risk_type)
            level_icon = {"低": "🟢", "中": "🟡", "高": "🔴"}.get(risk_data['level'], "⚪")
            report += f"**{risk_name}**: {level_icon} {risk_data['level']}\n"
            report += f"- {risk_data['description']}\n"
            if risk_data.get('key_equipment'):
                report += f"- 重点关注设备: {', '.join(risk_data['key_equipment'])}\n"
            report += "\n"

        # 保障措施
        report += "### 三、保障措施\n\n"
        for measure in plan['measures']:
            report += f"#### {measure['category']}\n"
            for idx, item in enumerate(measure['items']):
                report += f"{idx+1}. {item}\n"
            report += "\n"

        # 巡检计划
        report += "### 四、巡检计划\n\n"
        report += "**保电前**\n"
        for task in plan['inspection_plan']['before_event']:
            report += f"- {task['time']}: {task['content']} (责任人: {task['responsible']})\n"
        report += "\n**保电期间**\n"
        for task in plan['inspection_plan']['during_event']:
            report += f"- {task['frequency']}: {task['content']} (责任人: {task['responsible']})\n"
        report += "\n**保电后**\n"
        for task in plan['inspection_plan']['after_event']:
            report += f"- {task['time']}: {task['content']} (责任人: {task['responsible']})\n"
        report += "\n"

        # 应急预案
        report += "### 五、应急处置预案\n\n"
        for idx, scenario in enumerate(plan['emergency_scenarios']):
            report += f"{idx+1}. **{scenario['scenario']}**\n"
            report += f"   - 处置措施: {scenario['response']}\n\n"

        # 资源准备
        report += "### 六、资源准备\n\n"
        report += "**人员配置**\n"
        for key, value in plan['resource_preparation']['personnel'].items():
            report += f"- {key}: {value}\n"
        report += "\n**装备配置**\n"
        for key, value in plan['resource_preparation']['equipment'].items():
            report += f"- {key}: {value}\n"
        report += "\n**物资储备**\n"
        for category, items in plan['resource_preparation']['materials'].items():
            report += f"- {category}: {', '.join(items)}\n"
        report += "\n"

        # 信息报送
        report += "### 七、信息报送机制\n\n"
        for key, value in plan['communication_plan'].items():
            report += f"- {value}\n"
        report += "\n"

        report += "---\n"
        report += f"**编制单位**: XX供电公司\n"
        report += f"**编制日期**: {datetime.now().strftime('%Y年%m月%d日')}\n"
        report += f"**审批**: ________  **日期**: ________\n"

        return report

    async def _generate_inspection_plan(self, state: AgentState, query: str) -> Dict[str, Any]:
        """生成巡检计划"""
        self._log_thought(state, "action", "生成设备巡检计划...")
        
        plan = {
            "plan_name": "保电专项巡检计划",
            "inspections": [
                {"equipment": "#1主变", "frequency": "每2小时", "focus": "油温、油位、声音"},
                {"equipment": "#2主变", "frequency": "每2小时", "focus": "油温、油位、声音"},
                {"equipment": "110kV母线", "frequency": "每4小时", "focus": "外观、温度"},
                {"equipment": "关键开关柜", "frequency": "每4小时", "focus": "指示灯、温度"}
            ]
        }

        report = f"## 📋 {plan['plan_name']}\n\n"
        for insp in plan['inspections']:
            report += f"- **{insp['equipment']}**: {insp['frequency']}，重点检查{insp['focus']}\n"

        return {"answer": report, "plan": plan}

    async def _generate_emergency_response(self, state: AgentState, query: str) -> Dict[str, Any]:
        """生成应急响应方案"""
        return {
            "answer": "应急响应方案包括:\n"
                     "1. 应急组织架构\n"
                     "2. 应急处置流程\n"
                     "3. 应急资源配置\n"
                     "4. 应急演练计划\n\n"
                     "详细方案正在生成中..."
        }

    async def _prepare_resources(self, state: AgentState, query: str) -> Dict[str, Any]:
        """准备应急资源"""
        resources = {
            "人员": ["应急队5人", "值班人员2人"],
            "装备": ["应急发电车1台", "抢修车2辆"],
            "物资": ["备品备件若干", "应急工器具"]
        }

        report = "## 🎒 应急资源清单\n\n"
        for category, items in resources.items():
            report += f"### {category}\n"
            for item in items:
                report += f"- {item}\n"
            report += "\n"

        return {"answer": report, "resources": resources}

    async def _general_guidance(self, state: AgentState, query: str) -> Dict[str, Any]:
        """通用指导"""
        return {
            "answer": "保电方案专家为您服务！我可以:\n"
                     "1. 🛡️ 编制保电工作方案 (如: '高考保电方案')\n"
                     "2. 📋 制定设备巡检计划\n"
                     "3. 🚨 生成应急响应预案\n"
                     "4. 🎒 准备应急资源清单\n\n"
                     "请告诉我具体的保电任务或活动名称。"
        }

