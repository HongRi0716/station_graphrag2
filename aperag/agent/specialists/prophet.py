import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class ProphetAgent(BaseAgent):
    """
    趋势预言家 (The Prophet)
    职责：时序数据分析、设备状态预测、故障趋势预警、负荷预测。
    特点：基于历史数据进行趋势分析和预测性维护。
    """

    def __init__(self, llm_service: Any = None):
        super().__init__(
            role=AgentRole.PROPHET,
            name="趋势预言家 (Prophet)",
            description="分析历史运行数据，预测设备故障趋势，提供预防性维护建议。",
            tools=["time_series_analyzer",
                   "anomaly_detector", "trend_predictor"],
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行趋势分析和预测任务
        """
        query = input_data.get("task", "")

        self._log_thought(state, "thought", f"收到预测分析请求: {query}")

        # 判断任务类型
        if "温度" in query or "油温" in query or "测温" in query:
            return await self._analyze_temperature_trend(state, query)
        elif "负荷" in query or "电流" in query or "功率" in query:
            return await self._predict_load(state, query)
        elif "异常" in query or "故障" in query:
            return await self._detect_anomaly(state, query)
        elif "寿命" in query or "健康" in query:
            return await self._assess_equipment_health(state, query)
        else:
            return await self._general_trend_analysis(state, query)

    async def _analyze_temperature_trend(self, state: AgentState, query: str) -> Dict[str, Any]:
        """温度趋势分析 (Mock)"""
        self._log_thought(state, "plan", "开始分析设备温度趋势...")

        # Mock生成历史温度数据
        base_temp = 65.0
        temperature_data = []
        now = datetime.now()

        for i in range(30):  # 最近30天
            date = (now - timedelta(days=29-i)).strftime("%Y-%m-%d")
            temp = base_temp + random.uniform(-5, 8) + (i * 0.3)  # 模拟上升趋势
            temperature_data.append({
                "date": date,
                "temperature": round(temp, 1),
                "status": "normal" if temp < 85 else "warning"
            })

        self._log_thought(
            state,
            "action",
            "从SCADA系统提取最近30天温度数据",
            detail={"data_points": len(temperature_data)}
        )

        # 趋势分析
        current_temp = temperature_data[-1]["temperature"]
        avg_temp = sum(d["temperature"]
                       for d in temperature_data) / len(temperature_data)
        trend_slope = (
            temperature_data[-1]["temperature"] - temperature_data[0]["temperature"]) / 30

        # 预测
        predicted_7days = current_temp + (trend_slope * 7)
        predicted_30days = current_temp + (trend_slope * 30)

        analysis_result = {
            "equipment": "#1主变上层油温",
            "current": current_temp,
            "average_30d": round(avg_temp, 1),
            "trend": "上升" if trend_slope > 0 else "下降",
            "trend_rate": round(trend_slope, 2),
            "prediction_7d": round(predicted_7days, 1),
            "prediction_30d": round(predicted_30days, 1)
        }

        self._log_thought(
            state,
            "observation",
            "趋势分析完成",
            detail=analysis_result
        )

        # 生成报告
        report = "## 📈 温度趋势分析报告\n\n"
        report += f"**监测设备**: {analysis_result['equipment']}\n"
        report += f"**当前温度**: {analysis_result['current']}°C\n"
        report += f"**30日均温**: {analysis_result['average_30d']}°C\n\n"

        report += "### 趋势分析\n"
        trend_icon = "📈" if trend_slope > 0 else "📉"
        report += f"{trend_icon} 温度呈 **{analysis_result['trend']}** 趋势 (速率: {analysis_result['trend_rate']}°C/天)\n\n"

        report += "### 预测结果\n"
        report += f"- 7天后预计: **{analysis_result['prediction_7d']}°C**\n"
        report += f"- 30天后预计: **{analysis_result['prediction_30d']}°C**\n\n"

        # 预警判断
        if predicted_7days > 85:
            report += "### ⚠️ 预警提示\n"
            report += f"预测温度将在7天内超过告警阈值(85°C)，建议:\n"
            report += "1. 检查冷却系统运行状态\n"
            report += "2. 确认负荷是否异常增长\n"
            report += "3. 安排设备巡检，重点检查散热器\n"
        elif predicted_30days > 85:
            report += "### 💡 维护建议\n"
            report += "预测温度在30天内可能接近告警值，建议提前安排预防性检修。\n"
        else:
            report += "### ✅ 状态评估\n"
            report += "温度趋势正常，设备运行稳定。\n"

        return {
            "answer": report,
            "analysis": analysis_result,
            "raw_data": temperature_data
        }

    async def _predict_load(self, state: AgentState, query: str) -> Dict[str, Any]:
        """负荷预测 (Mock)"""
        self._log_thought(state, "action", "正在分析历史负荷数据...")

        # Mock负荷预测
        load_prediction = {
            "target": "#1主变",
            "current_load": 32.5,  # MW
            "rated_capacity": 50.0,  # MVA
            "load_rate": 65.0,  # %
            "peak_prediction": {
                "tomorrow": {"value": 38.2, "time": "14:00-16:00"},
                "next_week": {"value": 42.1, "time": "周五 15:00"}
            },
            "trend": "稳定增长"
        }

        self._log_thought(
            state,
            "observation",
            "负荷预测完成",
            detail=load_prediction
        )

        report = "## ⚡ 负荷预测报告\n\n"
        report += f"**设备**: {load_prediction['target']}\n"
        report += f"**当前负荷**: {load_prediction['current_load']} MW\n"
        report += f"**额定容量**: {load_prediction['rated_capacity']} MVA\n"
        report += f"**负荷率**: {load_prediction['load_rate']}%\n\n"

        report += "### 峰值预测\n"
        report += f"- 明日峰值: **{load_prediction['peak_prediction']['tomorrow']['value']} MW** "
        report += f"(预计时段: {load_prediction['peak_prediction']['tomorrow']['time']})\n"
        report += f"- 下周峰值: **{load_prediction['peak_prediction']['next_week']['value']} MW** "
        report += f"(预计时间: {load_prediction['peak_prediction']['next_week']['time']})\n\n"

        report += "### 运行建议\n"
        if load_prediction['load_rate'] > 80:
            report += "⚠️ 负荷率偏高，建议:\n"
            report += "1. 密切关注负荷变化\n"
            report += "2. 做好过载应急预案\n"
            report += "3. 考虑负荷转移方案\n"
        else:
            report += "✅ 负荷率正常，设备运行安全裕度充足。\n"

        return {
            "answer": report,
            "prediction": load_prediction
        }

    async def _detect_anomaly(self, state: AgentState, query: str) -> Dict[str, Any]:
        """异常检测 (Mock)"""
        self._log_thought(state, "action", "执行异常检测算法...")

        # Mock异常检测结果
        anomalies = [
            {
                "time": "2024-11-20 14:23:15",
                "equipment": "10kV II段母线电压",
                "metric": "电压波动",
                "value": 10.8,  # kV
                "expected_range": "10.0-10.5 kV",
                "deviation": "+2.9%",
                "severity": "低"
            },
            {
                "time": "2024-11-22 09:15:42",
                "equipment": "#2主变油温",
                "metric": "温度突增",
                "value": 78.5,  # °C
                "previous": 65.2,
                "increase": 13.3,
                "severity": "中"
            }
        ]

        self._log_thought(
            state,
            "observation",
            f"检测到 {len(anomalies)} 个异常事件",
            detail={"anomalies": anomalies}
        )

        report = "## 🔍 异常检测报告\n\n"
        report += f"**检测时段**: 最近7天\n"
        report += f"**异常事件**: {len(anomalies)} 个\n\n"

        for idx, anomaly in enumerate(anomalies):
            severity_icon = {"低": "🟢", "中": "🟡", "高": "🔴"}.get(
                anomaly["severity"], "⚪")
            report += f"### {idx+1}. {severity_icon} {anomaly['equipment']}\n"
            report += f"- **时间**: {anomaly['time']}\n"
            report += f"- **异常类型**: {anomaly['metric']}\n"

            if "deviation" in anomaly:
                report += f"- **实际值**: {anomaly['value']} ({anomaly['deviation']}偏离)\n"
                report += f"- **正常范围**: {anomaly['expected_range']}\n"
            else:
                report += f"- **当前值**: {anomaly['value']}°C (从 {anomaly['previous']}°C 上升)\n"
                report += f"- **增幅**: {anomaly['increase']}°C\n"

            report += "\n"

        report += "### 建议措施\n"
        report += "1. 对检测到的异常设备进行现场巡视\n"
        report += "2. 调阅相关设备的历史运行曲线\n"
        report += "3. 必要时进行专项试验或检修\n"

        return {
            "answer": report,
            "anomalies": anomalies
        }

    async def _assess_equipment_health(self, state: AgentState, query: str) -> Dict[str, Any]:
        """设备健康评估 (Mock)"""
        self._log_thought(state, "thought", "正在评估设备健康状态...")

        health_assessment = {
            "equipment": "#1主变压器",
            "health_score": 82,  # 满分100
            "health_level": "良好",
            "indicators": {
                "油色谱": {"score": 90, "status": "正常"},
                "绝缘电阻": {"score": 85, "status": "良好"},
                "温升特性": {"score": 75, "status": "关注"},
                "冷却系统": {"score": 80, "status": "良好"},
                "声音振动": {"score": 88, "status": "正常"}
            },
            "remaining_life": "预计剩余寿命: 8-10年"
        }

        report = "## 🏥 设备健康评估报告\n\n"
        report += f"**设备**: {health_assessment['equipment']}\n"
        report += f"**综合评分**: {health_assessment['health_score']}/100\n"
        report += f"**健康等级**: {health_assessment['health_level']}\n\n"

        report += "### 指标详情\n"
        for indicator, data in health_assessment['indicators'].items():
            status_icon = {"正常": "✅", "良好": "🟢", "关注": "🟡",
                           "异常": "🔴"}.get(data["status"], "⚪")
            report += f"- {status_icon} {indicator}: {data['score']}/100 ({data['status']})\n"

        report += f"\n### 寿命预测\n"
        report += f"{health_assessment['remaining_life']}\n\n"

        report += "### 维护建议\n"
        report += "1. 温升特性需要重点关注，建议下次检修时检查散热系统\n"
        report += "2. 定期进行油色谱在线监测\n"
        report += "3. 建议半年后进行全面健康体检\n"

        return {
            "answer": report,
            "health_assessment": health_assessment
        }

    async def _general_trend_analysis(self, state: AgentState, query: str) -> Dict[str, Any]:
        """通用趋势分析"""
        return {
            "answer": "趋势预言家为您服务！我可以提供:\n"
            "1. 📈 温度趋势分析与预测\n"
            "2. ⚡ 负荷预测与峰值预警\n"
            "3. 🔍 异常检测与早期预警\n"
            "4. 🏥 设备健康评估与寿命预测\n\n"
            "请告诉我需要分析的具体设备或指标。"
        }
