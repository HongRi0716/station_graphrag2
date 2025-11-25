# 操作票

**票号**: {{ ticket_no }}  
**操作任务**: {{ title }}  
**设备名称**: {{ equipment }}  
**电压等级**: {{ voltage_level }}  
**计划日期**: {{ operation_date }}  
**预计用时**: {{ estimated_time }}

---

## 操作人员

| 角色 | 姓名 | 时间 | 签字 |
|------|------|------|------|
| 操作人 | {{ operator|default("________") }} | ________ | ________ |
| 监护人 | {{ supervisor|default("________") }} | ________ | ________ |
| 值班负责人 | ________ | ________ | ________ |

---

## 操作前提条件

{% if prerequisites %}
{% for prereq in prerequisites %}
- [ ] {{ prereq }}
{% endfor %}
{% else %}
- [ ] 天气条件良好
- [ ] 操作人员持有效资格证
- [ ] 工器具检查合格
{% endif %}

---

## 操作步骤

{% for step in steps %}
### 第{{ step.seq }}步: {{ step.action }}

**具体内容**: {{ step.detail }}

{% if step.safety_note %}
⚠️ **安全注意事项**: {{ step.safety_note }}
{% endif %}

**执行情况**:
- [ ] 已执行
- 执行时间: ________
- 执行人签字: ________

---
{% endfor %}

## 安全性检查

{% if safety_check %}
| 检查项 | 结果 |
|--------|------|
{% for check_name, result in safety_check.items() %}
{% if check_name not in ['warnings', 'suggestions'] %}
| {{ check_name }} | {{ result }} |
{% endif %}
{% endfor %}
{% endif %}

{% if safety_check and safety_check.warnings %}
### ⚠️ 警告
{% for warning in safety_check.warnings %}
- {{ warning }}
{% endfor %}
{% endif %}

{% if safety_check and safety_check.suggestions %}
### 💡 建议
{% for suggestion in safety_check.suggestions %}
- {{ suggestion }}
{% endfor %}
{% endif %}

---

## 操作完成确认

**完成时间**: ________  
**值班负责人签字**: ________  
**调度许可**: ________

---

*本操作票由ApeRAG智能体系统自动生成，请人工审核后执行*
