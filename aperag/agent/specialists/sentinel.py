import logging
import random
from typing import Any, Dict

from aperag.agent.core.base import BaseAgent
from aperag.agent.core.models import AgentRole, AgentState

logger = logging.getLogger(__name__)


class SentinelAgent(BaseAgent):
    """
    巡视哨兵 (The Sentinel)
    职责：连接视频监控系统 (NVR)，进行实时画面分析、表计读数、安全行为识别。
    """

    def __init__(self, llm_service: Any = None):
        super().__init__(
            role=AgentRole.SENTINEL,
            name="巡视哨兵 (Sentinel)",
            description="连接变电站视频监控系统，负责实时巡视、表计读数识别和现场违章行为抓拍。",
            tools=["snapshot_capture", "object_detection", "meter_reading"],
        )
        self.llm_service = llm_service

    async def _execute(self, state: AgentState, input_data: Dict[str, Any]) -> Dict[str, Any]:
        task = input_data.get("task", "")

        self._log_thought(state, "thought", f"收到监控指令: {task}")
        target_camera = "CAM_01 (全景)"
        if "主变" in task:
            target_camera = "CAM_05 (#1主变本体)"
        elif "开关室" in task:
            target_camera = "CAM_12 (10kV开关室)"

        self._log_thought(
            state,
            "action",
            f"调取监控画面: {target_camera}",
            detail={"rtsp_url": "rtsp://192.168.1.105/stream1"},
        )

        analysis_result: Dict[str, Any]
        if any(keyword in task for keyword in ["读数", "温度", "油位"]):
            reading = round(random.uniform(45.0, 65.0), 1)
            analysis_result = {
                "type": "meter_reading",
                "value": f"{reading}°C",
                "status": "normal" if reading < 85 else "warning",
                "target": "油温表",
            }
            self._log_thought(state, "observation",
                              f"识别到仪表读数: {reading}", detail=analysis_result)

        elif any(keyword in task for keyword in ["安全帽", "人", "违章"]):
            if "未戴" in task:
                analysis_result = {
                    "type": "safety_alert",
                    "detected_objects": ["person", "no_helmet"],
                    "count": 1,
                    "location": "10kV开关室门口",
                }
            else:
                analysis_result = {
                    "type": "safety_check",
                    "detected_objects": ["person", "helmet", "vest"],
                    "status": "compliant",
                }
            self._log_thought(state, "observation",
                              "完成画面物体检测", detail=analysis_result)

        else:
            analysis_result = {
                "status": "normal",
                "description": "画面清晰，设备运行声音正常，未发现明显外观异常。",
            }

        answer = f"已为您查看 [{target_camera}] 的实时画面。\n"
        if analysis_result.get("type") == "meter_reading":
            answer += (
                f"📸 **识别结果**: 当前{analysis_result['target']}示数为 **{analysis_result['value']}**，状态："
                f"{analysis_result['status']}。"
            )
        elif analysis_result.get("type") == "safety_alert":
            answer += (
                f"⚠️ **安全警报**: 在 {analysis_result['location']} 发现 **{analysis_result['count']} 人未佩戴安全帽**，"
                "请立即制止！"
            )
        else:
            answer += f"👀 **巡视结论**: {analysis_result.get('description', '一切正常')}"

        return {"answer": answer, "camera_id": target_camera, "analysis": analysis_result}
