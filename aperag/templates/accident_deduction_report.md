# 事故推演报告

**报告编号**: {{ report_no }}  
**推演日期**: {{ deduction_date }}  
**推演人**: {{ deductor|default("________") }}  
**审核人**: {{ reviewer|default("________") }}

---

## 一、事故场景描述

### 1.1 初始故障

**故障设备**: {{ fault_equipment }}  
**故障类型**: {{ fault_type }}  
**故障时间**: {{ fault_time }}  
**初始现象**: 

{{ initial_phenomenon }}

### 1.2 运行方式

**系统运行方式**: {{ operation_mode }}

{% if system_status %}
**关键设备状态**:
{% for device in system_status %}
- {{ device.name }}: {{ device.status }}
{% endfor %}
{% endif %}

---

## 二、事故推演过程

### 2.1 故障传播链

```mermaid
graph TD
{% if fault_chain %}
{% for step in fault_chain %}
    {{ step.from_node }}[{{ step.from_desc }}] -->|{{ step.relation }}| {{ step.to_node }}[{{ step.to_desc }}]
{% endfor %}
{% else %}
    A[初始故障] --> B[一次影响]
    B --> C[二次影响]
    C --> D[最终影响]
{% endif %}
```

### 2.2 详细推演步骤

{% if deduction_steps %}
{% for step in deduction_steps %}
#### 第{{ loop.index }}步: {{ step.title }}

**时间**: {{ step.time }}  
**事件**: {{ step.event }}  
**影响**: {{ step.impact }}  
**保护动作**: {{ step.protection|default("无") }}

{% if step.details %}
**详细说明**:
{{ step.details }}
{% endif %}

---
{% endfor %}
{% else %}
#### 第1步: 初始故障发生

**时间**: T0  
**事件**: 待填写  
**影响**: 待填写  
**保护动作**: 待填写

---
{% endif %}

---

## 三、影响范围分析

### 3.1 停电范围

{% if outage_scope %}
| 序号 | 停电区域/设备 | 电压等级 | 负荷容量 | 影响用户 |
|------|---------------|----------|----------|----------|
{% for item in outage_scope %}
| {{ loop.index }} | {{ item.area }} | {{ item.voltage }} | {{ item.capacity }} | {{ item.users }} |
{% endfor %}
{% else %}
| 序号 | 停电区域/设备 | 电压等级 | 负荷容量 | 影响用户 |
|------|---------------|----------|----------|----------|
| 1 | 待分析 | ________ | ________ | ________ |
{% endif %}

### 3.2 设备影响

{% if equipment_impact %}
| 设备名称 | 影响程度 | 影响描述 | 预计恢复时间 |
|----------|----------|----------|--------------|
{% for item in equipment_impact %}
| {{ item.equipment }} | {{ item.severity }} | {{ item.description }} | {{ item.recovery_time }} |
{% endfor %}
{% else %}
| 设备名称 | 影响程度 | 影响描述 | 预计恢复时间 |
|----------|----------|----------|--------------|
| 待分析 | ________ | ________ | ________ |
{% endif %}

### 3.3 严重程度评估

**事故等级**: {{ accident_level|default("待评估") }}

**评估依据**:
{% if severity_criteria %}
{% for criterion in severity_criteria %}
- {{ criterion }}
{% endfor %}
{% else %}
- 停电范围
- 影响用户数量
- 设备损坏程度
- 社会影响
{% endif %}

---

## 四、应急处置方案

### 4.1 立即行动

{% if immediate_actions %}
{% for action in immediate_actions %}
{{ loop.index }}. **{{ action.title }}**
   - 执行人: {{ action.executor|default("________") }}
   - 时限: {{ action.deadline|default("立即") }}
   - 内容: {{ action.content }}
{% endfor %}
{% else %}
1. **启动应急预案**
   - 执行人: 值班负责人
   - 时限: 立即
   - 内容: 启动相应级别应急预案

2. **汇报调度**
   - 执行人: 值班员
   - 时限: 5分钟内
   - 内容: 向上级调度汇报事故情况
{% endif %}

### 4.2 故障隔离

{% if isolation_steps %}
{% for step in isolation_steps %}
**步骤{{ loop.index }}**: {{ step.action }}
- 操作设备: {{ step.equipment }}
- 操作内容: {{ step.detail }}
- 安全注意: {{ step.safety_note }}
{% endfor %}
{% else %}
**步骤1**: 隔离故障设备
- 操作设备: 待确定
- 操作内容: 待确定
- 安全注意: 待确定
{% endif %}

### 4.3 供电恢复

{% if recovery_plan %}
#### 恢复顺序

{% for step in recovery_plan %}
**阶段{{ loop.index }}**: {{ step.stage }}
- 恢复范围: {{ step.scope }}
- 操作步骤: {{ step.steps }}
- 预计时间: {{ step.estimated_time }}
{% endfor %}
{% else %}
#### 恢复顺序

**阶段1**: 转供电
- 恢复范围: 待确定
- 操作步骤: 待确定
- 预计时间: 待确定
{% endif %}

### 4.4 应急资源

{% if emergency_resources %}
| 资源类型 | 资源名称 | 数量 | 位置 | 联系人 |
|----------|----------|------|------|--------|
{% for resource in emergency_resources %}
| {{ resource.type }} | {{ resource.name }} | {{ resource.quantity }} | {{ resource.location }} | {{ resource.contact }} |
{% endfor %}
{% else %}
| 资源类型 | 资源名称 | 数量 | 位置 | 联系人 |
|----------|----------|------|------|--------|
| 抢修队伍 | ________ | ________ | ________ | ________ |
| 备品备件 | ________ | ________ | ________ | ________ |
| 应急电源 | ________ | ________ | ________ | ________ |
{% endif %}

---

## 五、预防措施建议

### 5.1 技术措施

{% if technical_measures %}
{% for measure in technical_measures %}
{{ loop.index }}. {{ measure.title }}
   - 具体内容: {{ measure.content }}
   - 责任部门: {{ measure.department }}
   - 完成期限: {{ measure.deadline }}
{% endfor %}
{% else %}
1. 设备改造
   - 具体内容: 待制定
   - 责任部门: 待确定
   - 完成期限: 待确定
{% endif %}

### 5.2 管理措施

{% if management_measures %}
{% for measure in management_measures %}
{{ loop.index }}. {{ measure.title }}
   - 具体内容: {{ measure.content }}
   - 责任部门: {{ measure.department }}
   - 完成期限: {{ measure.deadline }}
{% endfor %}
{% else %}
1. 加强巡检
   - 具体内容: 待制定
   - 责任部门: 待确定
   - 完成期限: 待确定
{% endif %}

---

## 六、经验教训

### 6.1 类似事故案例

{% if similar_cases %}
{% for case in similar_cases %}
#### 案例{{ loop.index }}: {{ case.title }}

**发生时间**: {{ case.date }}  
**发生地点**: {{ case.location }}  
**事故原因**: {{ case.cause }}  
**经验教训**: {{ case.lesson }}
{% endfor %}
{% else %}
待补充
{% endif %}

### 6.2 本次推演启示

{% if insights %}
{% for insight in insights %}
- {{ insight }}
{% endfor %}
{% else %}
- 待总结
{% endif %}

---

## 七、推演结论

{{ conclusion|default("待总结") }}

---

## 八、附件

{% if attachments %}
{% for attachment in attachments %}
- {{ attachment.name }}: {{ attachment.description }}
{% endfor %}
{% else %}
- 系统接线图
- 保护配置图
- 应急预案
{% endif %}

---

## 审核意见

**审核人**: {{ reviewer|default("________") }}  
**审核日期**: {{ review_date|default("________") }}  
**审核意见**: 

{{ review_comment|default("") }}

**审核结论**: [ ] 通过  [ ] 需修改  [ ] 不通过

---

*本事故推演报告由ApeRAG智能体系统自动生成，请专业人员审核*
