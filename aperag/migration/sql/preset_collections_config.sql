-- Preset Collections Configuration Initialization
-- 预设知识库配置初始化

-- Insert preset collections configuration into settings table
INSERT INTO setting (key, value, gmt_created, gmt_updated)
VALUES (
    'preset_collections_config',
    '{
        "enabled": true,
        "auto_create_for_new_users": false,
        "collections": [
            {
                "id": "substation_drawings",
                "title_zh": "变电站图纸库",
                "title_en": "Substation Drawings",
                "description_zh": "存放电气图纸、设计图、竣工图等技术图纸\\n\\n包含内容:\\n• 一次接线图\\n• 二次接线图\\n• 平面布置图\\n• 设备安装图\\n• 电缆走向图\\n• 保护配置图",
                "description_en": "Electrical drawings, design diagrams, and as-built drawings\\n\\nContents:\\n• Primary wiring diagrams\\n• Secondary wiring diagrams\\n• Layout plans\\n• Equipment installation drawings\\n• Cable routing diagrams\\n• Protection configuration diagrams",
                "category": "technical_documents",
                "tags": ["drawings", "schematics", "blueprints", "electrical"],
                "icon": "📐",
                "recommended_agents": ["detective"],
                "auto_create": true,
                "order": 1
            },
            {
                "id": "equipment_manuals",
                "title_zh": "设备技术手册",
                "title_en": "Equipment Technical Manuals",
                "description_zh": "设备说明书、技术参数、产品手册等技术文档\\n\\n包含内容:\\n• 变压器技术手册\\n• 断路器说明书\\n• 保护装置手册\\n• 监控系统文档\\n• 设备技术参数表\\n• 产品合格证书",
                "description_en": "Equipment manuals, technical specifications, and product documentation\\n\\nContents:\\n• Transformer technical manuals\\n• Circuit breaker manuals\\n• Protection device manuals\\n• Monitoring system documentation\\n• Equipment specification sheets\\n• Product certificates",
                "category": "technical_documents",
                "tags": ["manuals", "specifications", "equipment", "technical"],
                "icon": "📋",
                "recommended_agents": ["archivist", "diagnostician"],
                "auto_create": true,
                "order": 2
            },
            {
                "id": "operation_procedures",
                "title_zh": "运维规程文档",
                "title_en": "O&M Procedures",
                "description_zh": "操作规程、安全规范、作业指导书等管理文档\\n\\n包含内容:\\n• 倒闸操作票\\n• 巡检作业指导书\\n• 安全操作规程\\n• 应急预案\\n• 工作票管理规定\\n• 设备检修规程",
                "description_en": "Operation procedures, safety regulations, and work instructions\\n\\nContents:\\n• Switching operation tickets\\n• Inspection work instructions\\n• Safety operation procedures\\n• Emergency response plans\\n• Work permit regulations\\n• Equipment maintenance procedures",
                "category": "management_documents",
                "tags": ["procedures", "safety", "operations", "regulations"],
                "icon": "📝",
                "recommended_agents": ["instructor", "gatekeeper"],
                "auto_create": true,
                "order": 3
            },
            {
                "id": "fault_cases",
                "title_zh": "故障案例库",
                "title_en": "Fault Case Database",
                "description_zh": "历史故障记录、处理方案、经验总结等案例文档\\n\\n包含内容:\\n• 故障分析报告\\n• 缺陷处理记录\\n• 事故调查报告\\n• 经验总结文档\\n• 典型案例分析\\n• 改进措施记录",
                "description_en": "Historical fault records, solutions, and lessons learned\\n\\nContents:\\n• Fault analysis reports\\n• Defect handling records\\n• Accident investigation reports\\n• Lessons learned documentation\\n• Typical case analyses\\n• Improvement action records",
                "category": "knowledge_base",
                "tags": ["faults", "cases", "troubleshooting", "analysis"],
                "icon": "🔧",
                "recommended_agents": ["diagnostician", "prophet"],
                "auto_create": true,
                "order": 4
            },
            {
                "id": "relay_protection",
                "title_zh": "继电保护资料",
                "title_en": "Relay Protection Documentation",
                "description_zh": "整定计算、保护配置、定值单等保护相关文档\\n\\n包含内容:\\n• 保护整定计算书\\n• 保护定值单\\n• 保护配置图\\n• 试验报告\\n• 保护动作记录\\n• 整定方案说明",
                "description_en": "Setting calculations, protection configurations, and related documents\\n\\nContents:\\n• Protection setting calculation sheets\\n• Protection setting lists\\n• Protection configuration diagrams\\n• Test reports\\n• Protection operation records\\n• Setting scheme descriptions",
                "category": "technical_documents",
                "tags": ["protection", "relay", "settings", "calculations"],
                "icon": "⚡",
                "recommended_agents": ["calculator"],
                "auto_create": true,
                "order": 5
            },
            {
                "id": "inspection_reports",
                "title_zh": "巡检报告归档",
                "title_en": "Inspection Report Archive",
                "description_zh": "巡检记录、测温报告、状态评估等巡检文档\\n\\n包含内容:\\n• 日常巡检记录\\n• 红外测温报告\\n• 设备状态评估\\n• 趋势分析报告\\n• 特巡记录\\n• 缺陷统计分析",
                "description_en": "Inspection records, thermal imaging reports, and condition assessments\\n\\nContents:\\n• Daily inspection records\\n• Infrared thermography reports\\n• Equipment condition assessments\\n• Trend analysis reports\\n• Special inspection records\\n• Defect statistical analysis",
                "category": "operational_records",
                "tags": ["inspection", "reports", "monitoring", "assessment"],
                "icon": "📊",
                "recommended_agents": ["sentinel", "scribe"],
                "auto_create": true,
                "order": 6
            }
        ],
        "categories": {
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
    }'::jsonb,
    NOW(),
    NOW()
)
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    gmt_updated = NOW();
