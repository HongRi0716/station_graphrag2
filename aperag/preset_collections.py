# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Preset Collections Configuration for Substation Inspection System
预设知识库配置 - 变电站巡检系统
"""

PRESET_COLLECTIONS = [
    {
        "id": "substation_draw ings",
        "title_zh": "变电站图纸库",
        "title_en": "Substation Drawings",
        "description_zh": """存放电气图纸、设计图、竣工图等技术图纸

包含内容:
• 一次接线图
• 二次接线图
• 平面布置图
• 设备安装图
• 电缆走向图
• 保护配置图""",
        "description_en": """Electrical drawings, design diagrams, and as-built drawings

Contents:
• Primary wiring diagrams
• Secondary wiring diagrams
• Layout plans
• Equipment installation drawings
• Cable routing diagrams
• Protection configuration diagrams""",
        "category": "technical_documents",
        "tags": ["drawings", "schematics", "blueprints", "electrical"],
        "icon": "📐",
        "recommended_agents": ["detective"],
        "auto_create": True,
        "order": 1
    },
    {
        "id": "equipment_manuals",
        "title_zh": "设备技术手册",
        "title_en": "Equipment Technical Manual",
        "description_zh": """设备说明书、技术参数、产品手册等技术文档

包含内容:
• 变压器技术手册
• 断路器说明书
• 保护装置手册
• 监控系统文档
• 设备技术参数表
• 产品合格证书""",
        "description_en": """Equipment manuals, technical specifications, and product documentation

Contents:
• Transformer technical manuals
• Circuit breaker manuals
• Protection device manuals
• Monitoring system documentation
• Equipment specification sheets
• Product certificates""",
        "category": "technical_documents",
        "tags": ["manuals", "specifications", "equipment", "technical"],
        "icon": "📋",
        "recommended_agents": ["archivist", "diagnostician"],
        "auto_create": True,
        "order": 2
    },
    {
        "id": "operation_procedures",
        "title_zh": "运维规程文档",
        "title_en": "O&M Procedures",
        "description_zh": """操作规程、安全规范、作业指导书等管理文档

包含内容:
• 倒闸操作票
• 巡检作业指导书
• 安全操作规程
• 应急预案
• 工作票管理规定
• 设备检修规程""",
        "description_en": """Operation procedures, safety regulations, and work instructions

Contents:
• Switching operation tickets
• Inspection work instructions
• Safety operation procedures
• Emergency response plans
• Work permit regulations
• Equipment maintenance procedures""",
        "category": "management_documents",
        "tags": ["procedures", "safety", "operations", "regulations"],
        "icon": "📝",
        "recommended_agents": ["instructor", "gatekeeper"],
        "auto_create": True,
        "order": 3
    },
    {
        "id": "fault_cases",
        "title_zh": "故障案例库",
        "title_en": "Fault Case Database",
        "description_zh": """历史故障记录、处理方案、经验总结等案例文档

包含内容:
• 故障分析报告
• 缺陷处理记录
• 事故调查报告
• 经验总结文档
• 典型案例分析
• 改进措施记录""",
        "description_en": """Historical fault records, solutions, and lessons learned

Contents:
• Fault analysis reports
• Defect handling records
• Accident investigation reports
• Lessons learned documentation
• Typical case analyses
• Improvement action records""",
        "category": "knowledge_base",
        "tags": ["faults", "cases", "troubleshooting", "analysis"],
        "icon": "🔧",
        "recommended_agents": ["diagnostician", "prophet"],
        "auto_create": True,
        "order": 4
    },
    {
        "id": "relay_protection",
        "title_zh": "继电保护资料",
        "title_en": "Relay Protection Documentation",
        "description_zh": """整定计算、保护配置、定值单等保护相关文档

包含内容:
• 保护整定计算书
• 保护定值单
• 保护配置图
• 试验报告
• 保护动作记录
• 整定方案说明""",
        "description_en": """Setting calculations, protection configurations, and related documents

Contents:
• Protection setting calculation sheets
• Protection setting lists
• Protection configuration diagrams
• Test reports
• Protection operation records
• Setting scheme descriptions""",
        "category": "technical_documents",
        "tags": ["protection", "relay", "settings", "calculations"],
        "icon": "⚡",
        "recommended_agents": ["calculator"],
        "auto_create": True,
        "order": 5
    },
    {
        "id": "inspection_reports",
        "title_zh": "巡检报告归档",
        "title_en": "Inspection Report Archive",
        "description_zh": """巡检记录、测温报告、状态评估等巡检文档

包含内容:
• 日常巡检记录
• 红外测温报告
• 设备状态评估
• 趋势分析报告
• 特巡记录
• 缺陷统计分析""",
        "description_en": """Inspection records, thermal imaging reports, and condition assessments

Contents:
• Daily inspection records
• Infrared thermography reports
• Equipment condition assessments
• Trend analysis reports
• Special inspection records
• Defect statistical analysis""",
        "category": "operational_records",
        "tags": ["inspection", "reports", "monitoring", "assessment"],
        "icon": "📊",
        "recommended_agents": ["sentinel", "scribe"],
        "auto_create": True,
        "order": 6
    }
]

# Category definitions
COLLECTION_CATEGORIES = {
    "technical_documents": {
        "name_zh": "技术文档",
        "name_en": "Technical Documents",
        "description_zh": "技术图纸、设备手册等专业技术资料",
        "description_en": "Technical drawings, equipment manuals, and professional documentation"
    },
    "management_documents": {
        "name_zh": "管理文档",
        "name_en": "Management Documents",
        "description_zh": "操作规程、管理制度等规范性文件",
        "description_en": "Operation procedures, regulations, and normative documents"
    },
    "knowledge_base": {
        "name_zh": "知识库",
        "name_en": "Knowledge Base",
        "description_zh": "案例分析、经验总结等知识积累",
        "description_en": "Case studies, lessons learned, and knowledge accumulation"
    },
    "operational_records": {
        "name_zh": "运行记录",
        "name_en": "Operational Records",
        "description_zh": "巡检记录、运行数据等日常记录",
        "description_en": "Inspection records, operational data, and daily logs"
    }
}


def get_preset_collections():
    """Get all preset collection configurations"""
    return PRESET_COLLECTIONS


def get_preset_collection_by_id(collection_id: str):
    """Get a specific preset collection by ID"""
    for collection in PRESET_COLLECTIONS:
        if collection["id"] == collection_id:
            return collection
    return None


def get_collections_by_category(category: str):
    """Get all collections in a specific category"""
    return [c for c in PRESET_COLLECTIONS if c["category"] == category]


def get_collections_by_agent(agent_id: str):
    """Get recommended collections for a specific agent"""
    return [c for c in PRESET_COLLECTIONS if agent_id in c.get("recommended_agents", [])]
