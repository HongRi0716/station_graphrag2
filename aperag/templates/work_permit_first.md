# 电力线路第一种工作票

**工作票编号**: {{ ticket_no }}  
**工作地点**: {{ work_location }}  
**设备名称**: {{ equipment }}  
**电压等级**: {{ voltage_level }}  
**工作日期**: {{ work_date }}

---

## 工作负责人及工作班成员

| 角色 | 姓名 | 资格证号 | 签字 |
|------|------|----------|------|
| 工作负责人 | {{ work_leader|default("________") }} | ________ | ________ |
{% if work_members %}
{% for member in work_members %}
| 工作班成员 | {{ member.name|default("________") }} | {{ member.cert|default("________") }} | ________ |
{% endfor %}
{% else %}
| 工作班成员 | ________ | ________ | ________ |
{% endif %}

---

## 工作任务

{{ work_task }}

---

## 工作范围

{% if work_scope %}
{% for scope in work_scope %}
- {{ scope }}
{% endfor %}
{% else %}
- 待填写
{% endif %}

---

## 停电范围

{% if power_outage_scope %}
{% for scope in power_outage_scope %}
- {{ scope }}
{% endfor %}
{% else %}
- 待填写
{% endif %}

---

## 安全措施

### 1. 停电

{% if safety_measures.power_off %}
{% for measure in safety_measures.power_off %}
- [ ] {{ measure }}
{% endfor %}
{% else %}
- [ ] 断开相关断路器和隔离开关
- [ ] 确认设备无电压
{% endif %}

### 2. 验电

{% if safety_measures.voltage_test %}
{% for measure in safety_measures.voltage_test %}
- [ ] {{ measure }}
{% endfor %}
{% else %}
- [ ] 使用合格的验电器验电
- [ ] 在工作设备各侧验电
{% endif %}

### 3. 装设接地线

{% if safety_measures.grounding %}
{% for measure in safety_measures.grounding %}
- [ ] {{ measure }}
{% endfor %}
{% else %}
- [ ] 在工作设备各侧装设接地线
- [ ] 先接接地端，后接导体端
{% endif %}

### 4. 悬挂标示牌和装设遮栏

{% if safety_measures.signs %}
{% for measure in safety_measures.signs %}
- [ ] {{ measure }}
{% endfor %}
{% else %}
- [ ] 在断路器和隔离开关操作把手上悬挂"禁止合闸，有人工作"标示牌
- [ ] 在工作地点装设围栏
{% endif %}

---

## 风险识别

{% if risks %}
| 风险类型 | 风险描述 | 控制措施 |
|----------|----------|----------|
{% for risk in risks %}
| {{ risk.type }} | {{ risk.description }} | {{ risk.control }} |
{% endfor %}
{% else %}
| 风险类型 | 风险描述 | 控制措施 |
|----------|----------|----------|
| 待识别 | 待识别 | 待制定 |
{% endif %}

---

## 工作票签发

| 角色 | 姓名 | 时间 | 签字 |
|------|------|------|------|
| 工作票签发人 | ________ | ________ | ________ |
| 工作许可人 | ________ | ________ | ________ |

---

## 工作许可

**工作许可时间**: ________  
**工作许可人签字**: ________

安全措施已按工作票要求执行完毕，可以开始工作。

---

## 工作间断

| 间断时间 | 恢复时间 | 许可人签字 |
|----------|----------|------------|
| ________ | ________ | ________ |

---

## 工作终结

**工作终结时间**: ________  
**工作负责人签字**: ________  
**工作许可人签字**: ________

工作已全部完成，工作人员已全部撤离，接地线已全部拆除，现场已清理完毕。

---

## 工作票延期

**延期至**: ________  
**延期原因**: ________  
**签发人签字**: ________

---

*本工作票由ApeRAG智能体系统自动生成，请人工审核后使用*
