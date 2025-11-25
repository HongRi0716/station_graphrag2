# 电力线路第二种工作票

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

## 工作内容和范围

{% if work_scope %}
{% for scope in work_scope %}
- {{ scope }}
{% endfor %}
{% else %}
- 待填写
{% endif %}

---

## 安全措施和注意事项

### 1. 工作前准备

{% if safety_measures.preparation %}
{% for measure in safety_measures.preparation %}
- [ ] {{ measure }}
{% endfor %}
{% else %}
- [ ] 检查工作票内容是否完整
- [ ] 核对工作地点和设备名称
- [ ] 准备必要的工器具和安全用具
{% endif %}

### 2. 工作中安全措施

{% if safety_measures.during_work %}
{% for measure in safety_measures.during_work %}
- [ ] {{ measure }}
{% endfor %}
{% else %}
- [ ] 在带电设备附近工作时，保持安全距离
- [ ] 使用合格的绝缘工器具
- [ ] 设专人监护
{% endif %}

### 3. 特殊注意事项

{% if safety_measures.special_notes %}
{% for note in safety_measures.special_notes %}
⚠️ {{ note }}
{% endfor %}
{% else %}
⚠️ 本工作票适用于带电作业和在带电设备外壳上的工作
{% endif %}

---

## 工作许可

**工作许可人**: ________  
**许可时间**: ________  
**许可人签字**: ________

工作负责人已确认安全措施，可以开始工作。

---

## 工作监护

| 监护时段 | 监护人 | 签字 |
|----------|--------|------|
{% if guardians %}
{% for guardian in guardians %}
| {{ guardian.time_period|default("________") }} | {{ guardian.name|default("________") }} | ________ |
{% endfor %}
{% else %}
| ________ | ________ | ________ |
{% endif %}

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

工作已全部完成，工作人员已全部撤离，现场已清理完毕。

---

## 备注

{{ notes|default("") }}

---

*本工作票由ApeRAG智能体系统自动生成，请人工审核后使用*
