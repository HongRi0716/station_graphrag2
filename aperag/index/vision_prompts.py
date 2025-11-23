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
Vision Index Prompt Templates for Different Document Types

This module provides specialized prompts for Vision LLM to analyze different types
of technical documents, particularly for substation and electrical equipment documentation.
"""

import re
from typing import Dict

# Vision prompt templates for different document types
VISION_PROMPT_TEMPLATES: Dict[str, str] = {
    "technical_drawing": """分析这张技术图纸,提取以下信息用于检索和知识图谱构建:

## 图纸类型识别
首先判断图纸类型:一次接线图、二次接线图、平面布置图、设备安装图、电缆走向图

## 提取要求

### 1. 设备实体 (Equipment Entities)
提取所有电气设备,包括:
- **设备名称**: 完整的设备标识(如"110kV母线I段"、"主变T1")
- **设备类型**: 变压器、断路器、隔离开关、互感器、母线等
- **技术参数**: 电压等级、容量、型号等
- **位置信息**: 间隔编号、柜体编号、所在区域

### 2. 连接关系 (Connection Relationships)
提取所有电气连接,必须明确指出两端设备:
- **格式**: "设备A --连接类型--> 设备B"
- **示例**: "110kV母线I段 --通过断路器CB1--> 主变T1高压侧"
- **连接类型**: 直接连接、通过断路器、通过隔离开关、电缆连接等

### 3. 标注信息 (Annotations)
- 图纸编号、版本号
- 日期、设计单位
- 重要备注和说明

## 输出格式
使用结构化格式,便于解析:

**图纸类型**: [类型]

**设备列表**:
1. [设备名称] - [设备类型] - [参数] - [位置]
2. ...

**连接关系**:
1. [设备A] --[连接方式]--> [设备B]
2. ...

**关键标注**:
- [标注内容]

## 注意事项
- 使用图纸上的准确名称,保留原始编号
- 所有设备必须在连接关系中明确提及
- 提取所有可见的技术参数""",

    "equipment_manual": """分析这张设备手册图片,提取技术信息:

## 提取重点

### 1. 设备信息
- **设备名称和型号**: 完整的产品型号
- **制造商**: 生产厂家
- **技术规格**: 额定参数、性能指标

### 2. 技术参数表
如果是参数表格,提取:
- 参数名称和数值
- 单位
- 适用条件

### 3. 结构说明
如果是结构图:
- 主要部件名称
- 部件功能
- 部件间关系

### 4. 操作说明
- 操作步骤
- 注意事项
- 警告信息

## 输出格式
**设备**: [型号] - [制造商]

**技术参数**:
- [参数名]: [数值] [单位]

**结构部件**:
1. [部件名] - [功能]

**操作要点**:
- [要点]""",

    "operation_procedure": """分析这张操作规程图片,提取关键信息:

## 提取重点

### 1. 操作步骤
- 步骤编号和顺序
- 每步具体操作
- 操作对象(设备、开关等)

### 2. 安全要求
- 安全措施
- 警告标识
- 禁止事项

### 3. 检查项目
- 检查点
- 检查标准
- 记录要求

### 4. 流程图
如果是流程图:
- 起始条件
- 决策点
- 分支路径
- 结束条件

## 输出格式
**操作名称**: [名称]

**操作步骤**:
1. [步骤描述]
2. ...

**安全要求**:
- [要求]

**检查项目**:
- [项目] - [标准]""",

    "inspection_report": """分析这张巡检报告图片,提取检查信息:

## 提取重点

### 1. 基本信息
- 巡检日期和时间
- 巡检人员
- 巡检区域/设备

### 2. 检查结果
- 检查项目
- 正常/异常状态
- 测量数据(温度、电流等)

### 3. 缺陷记录
- 缺陷描述
- 严重程度
- 位置

### 4. 图表数据
如果包含图表:
- 趋势变化
- 异常点
- 对比数据

## 输出格式
**巡检信息**: [日期] - [区域] - [人员]

**检查结果**:
- [项目]: [状态] - [数据]

**发现缺陷**:
1. [位置] - [描述] - [等级]""",

    "fault_case": """分析这张故障案例图片,提取故障信息:

## 提取重点

### 1. 故障基本信息
- 故障时间
- 故障设备
- 故障现象

### 2. 故障分析
- 原因分析
- 影响范围
- 损失评估

### 3. 处理措施
- 应急处理
- 修复方案
- 恢复时间

### 4. 经验教训
- 根本原因
- 预防措施
- 改进建议

## 输出格式
**故障概况**: [时间] - [设备] - [现象]

**原因分析**:
- [分析内容]

**处理措施**:
1. [措施]

**经验总结**:
- [总结]""",

    "relay_protection": """分析这张继电保护图片,提取保护配置信息:

## 提取重点

### 1. 保护配置
- 保护类型(主保护、后备保护)
- 保护原理
- 保护范围

### 2. 定值信息
- 定值项目
- 定值数值
- 整定依据

### 3. 逻辑关系
- 保护逻辑
- 跳闸条件
- 闭锁条件

### 4. 接线方式
- CT/PT 接线
- 保护装置连接
- 出口回路

## 输出格式
**保护类型**: [类型]

**定值清单**:
- [项目]: [数值] - [依据]

**保护逻辑**:
- [逻辑描述]

**接线配置**:
- [配置说明]""",

    "general": """提取图片中的关键信息用于检索和知识图谱构建:

## 提取要求

### 1. 主要内容
- 图片类型和主题
- 核心信息

### 2. 实体识别
- 人物、地点、设备、概念
- 使用准确名称

### 3. 关系提取
- 实体间的关联
- 因果关系
- 层级关系

### 4. 关键数据
- 数值、日期
- 参数、指标

## 输出格式
**内容类型**: [类型]

**主要实体**:
- [实体]

**关系**:
- [实体A] --[关系]--> [实体B]

**关键信息**:
- [信息]"""
}

# Collection type to prompt template mapping
COLLECTION_TYPE_MAPPING: Dict[str, str] = {
    "变电站图纸库": "technical_drawing",
    "设备技术手册": "equipment_manual",
    "运维规程文档": "operation_procedure",
    "巡检报告归档": "inspection_report",
    "故障案例库": "fault_case",
    "继电保护资料": "relay_protection",
}

# Keyword-based mapping for automatic detection
KEYWORD_MAPPING: Dict[str, str] = {
    "图纸": "technical_drawing",
    "接线图": "technical_drawing",
    "布置图": "technical_drawing",
    "设计图": "technical_drawing",
    "手册": "equipment_manual",
    "说明书": "equipment_manual",
    "技术资料": "equipment_manual",
    "规程": "operation_procedure",
    "操作": "operation_procedure",
    "流程": "operation_procedure",
    "巡检": "inspection_report",
    "测温": "inspection_report",
    "检查": "inspection_report",
    "故障": "fault_case",
    "缺陷": "fault_case",
    "事故": "fault_case",
    "保护": "relay_protection",
    "整定": "relay_protection",
    "定值": "relay_protection",
}


def get_vision_prompt_for_collection(collection_title: str, collection_description: str = "") -> str:
    """
    Get appropriate Vision prompt based on collection title and description
    
    Args:
        collection_title: Collection title
        collection_description: Collection description
        
    Returns:
        Appropriate Vision prompt template
    """
    # 1. Exact match
    if collection_title in COLLECTION_TYPE_MAPPING:
        template_key = COLLECTION_TYPE_MAPPING[collection_title]
        return VISION_PROMPT_TEMPLATES[template_key]
    
    # 2. Keyword matching
    combined_text = collection_title + " " + collection_description
    for keyword, template_key in KEYWORD_MAPPING.items():
        if keyword in combined_text:
            return VISION_PROMPT_TEMPLATES[template_key]
    
    # 3. Default to general template
    return VISION_PROMPT_TEMPLATES["general"]


def get_vision_prompt_by_metadata(file_metadata: dict) -> str:
    """
    Get Vision prompt based on file metadata (filename, tags, etc.)
    
    Args:
        file_metadata: File metadata containing name, tags, etc.
        
    Returns:
        Appropriate Vision prompt template
    """
    filename = file_metadata.get("name", "").lower()
    tags = file_metadata.get("tags", [])
    
    # Filename pattern matching
    patterns = {
        r".*一次接线.*": "technical_drawing",
        r".*二次接线.*": "technical_drawing",
        r".*平面布置.*": "technical_drawing",
        r".*说明书.*": "equipment_manual",
        r".*手册.*": "equipment_manual",
        r".*操作票.*": "operation_procedure",
        r".*巡检.*": "inspection_report",
        r".*测温.*": "inspection_report",
        r".*故障.*": "fault_case",
        r".*整定.*": "relay_protection",
    }
    
    for pattern, template_key in patterns.items():
        if re.match(pattern, filename):
            return VISION_PROMPT_TEMPLATES[template_key]
    
    # Tag matching
    tag_mapping = {
        "drawing": "technical_drawing",
        "manual": "equipment_manual",
        "procedure": "operation_procedure",
        "inspection": "inspection_report",
        "fault": "fault_case",
        "protection": "relay_protection",
    }
    
    for tag in tags:
        if tag.lower() in tag_mapping:
            return VISION_PROMPT_TEMPLATES[tag_mapping[tag.lower()]]
    
    return VISION_PROMPT_TEMPLATES["general"]
