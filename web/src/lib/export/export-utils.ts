/**
 * 智能体结果导出工具
 * 支持导出为 Word、PDF、Markdown、JSON 格式
 */

// ========== 类型定义 ==========

export type ExportFormat = 'word' | 'pdf' | 'markdown' | 'json' | 'html';

export interface ExportOptions {
    /** 文件名（不含扩展名） */
    filename: string;
    /** 导出格式 */
    format: ExportFormat;
    /** 标题 */
    title: string;
    /** 智能体名称 */
    agentName?: string;
    /** 生成时间 */
    generatedAt?: Date;
    /** 用户名 */
    userName?: string;
}

export interface ExportContent {
    /** 主要内容（Markdown 格式） */
    content: string;
    /** 思考过程 */
    thinkingStream?: Array<{
        step_type: string;
        description: string;
    }>;
    /** 附加数据（如票据详情、危险点等） */
    metadata?: Record<string, any>;
}

// ========== 模板定义 ==========

const WORD_TEMPLATE = `
<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word">
<head>
  <meta charset="utf-8">
  <title>{{TITLE}}</title>
  <style>
    body { font-family: "Microsoft YaHei", "SimSun", Arial, sans-serif; margin: 40px; }
    h1 { color: #1a1a2e; border-bottom: 2px solid #4a90d9; padding-bottom: 10px; }
    h2 { color: #16213e; margin-top: 20px; }
    h3 { color: #0f3460; }
    .header { margin-bottom: 30px; }
    .meta { color: #666; font-size: 12px; margin-bottom: 20px; }
    .content { line-height: 1.8; }
    .thinking { background: #f5f5f5; padding: 15px; border-left: 4px solid #4a90d9; margin: 15px 0; }
    .thinking-step { margin: 5px 0; }
    .step-type { background: #e3f2fd; padding: 2px 8px; border-radius: 4px; font-size: 12px; color: #1976d2; }
    table { border-collapse: collapse; width: 100%; margin: 15px 0; }
    th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
    th { background: #f5f5f5; }
    .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; }
  </style>
</head>
<body>
  <div class="header">
    <h1>{{TITLE}}</h1>
    <div class="meta">
      <p>智能体：{{AGENT_NAME}}</p>
      <p>生成时间：{{GENERATED_AT}}</p>
      {{#USER_NAME}}<p>操作人：{{USER_NAME}}</p>{{/USER_NAME}}
    </div>
  </div>
  
  {{#THINKING}}
  <div class="thinking">
    <h3>📝 思考过程</h3>
    {{THINKING_CONTENT}}
  </div>
  {{/THINKING}}
  
  <div class="content">
    {{CONTENT}}
  </div>
  
  {{#METADATA}}
  <div class="metadata">
    {{METADATA_CONTENT}}
  </div>
  {{/METADATA}}
  
  <div class="footer">
    <p>本文档由智能体自动生成，仅供参考。</p>
    <p>ApeRAG 智能电力运维系统</p>
  </div>
</body>
</html>
`;

// ========== Markdown 转 HTML ==========

function markdownToHtml(markdown: string): string {
    if (!markdown) return '';

    let html = markdown;

    // 标题
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // 粗体和斜体
    html = html.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // 代码块
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // 列表
    html = html.replace(/^\s*[-*+]\s+(.*$)/gim, '<li>$1</li>');
    // 使用非贪婪匹配代替 's' 标志
    html = html.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');

    // 有序列表
    html = html.replace(/^\d+\.\s+(.*$)/gim, '<li>$1</li>');

    // 表格（简化处理）
    const tableRegex = /\|(.+)\|\n\|[-\s|]+\|\n((?:\|.+\|\n?)+)/g;
    html = html.replace(tableRegex, (match, header, body) => {
        const headers = header.split('|').filter((h: string) => h.trim()).map((h: string) => `<th>${h.trim()}</th>`).join('');
        const rows = body.trim().split('\n').map((row: string) => {
            const cells = row.split('|').filter((c: string) => c.trim()).map((c: string) => `<td>${c.trim()}</td>`).join('');
            return `<tr>${cells}</tr>`;
        }).join('');
        return `<table><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>`;
    });

    // 换行
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');

    // 包裹段落
    if (!html.startsWith('<')) {
        html = '<p>' + html + '</p>';
    }

    return html;
}

// ========== 模板渲染 ==========

function renderTemplate(template: string, data: Record<string, any>): string {
    let result = template;

    // 处理条件块 {{#KEY}}...{{/KEY}}
    const conditionalRegex = /\{\{#(\w+)\}\}([\s\S]*?)\{\{\/\1\}\}/g;
    result = result.replace(conditionalRegex, (match, key, content) => {
        return data[key] ? content : '';
    });

    // 替换变量 {{KEY}}
    Object.entries(data).forEach(([key, value]) => {
        const regex = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
        result = result.replace(regex, String(value || ''));
    });

    return result;
}

// ========== 导出函数 ==========

/**
 * 导出为 Word 文档
 */
export function exportToWord(content: ExportContent, options: ExportOptions): void {
    const thinkingContent = content.thinkingStream?.map(step =>
        `<div class="thinking-step"><span class="step-type">${step.step_type}</span> ${step.description}</div>`
    ).join('') || '';

    const metadataContent = content.metadata ?
        formatMetadataAsHtml(content.metadata) : '';

    const data = {
        TITLE: options.title,
        AGENT_NAME: options.agentName || '智能体',
        GENERATED_AT: (options.generatedAt || new Date()).toLocaleString('zh-CN'),
        USER_NAME: options.userName,
        THINKING: content.thinkingStream && content.thinkingStream.length > 0,
        THINKING_CONTENT: thinkingContent,
        CONTENT: markdownToHtml(content.content),
        METADATA: content.metadata && Object.keys(content.metadata).length > 0,
        METADATA_CONTENT: metadataContent
    };

    const html = renderTemplate(WORD_TEMPLATE, data);

    // 创建 Blob 并下载
    const blob = new Blob([html], {
        type: 'application/msword;charset=utf-8'
    });

    downloadBlob(blob, `${options.filename}.doc`);
}

/**
 * 导出为 Markdown
 */
export function exportToMarkdown(content: ExportContent, options: ExportOptions): void {
    let md = `# ${options.title}\n\n`;
    md += `> 智能体：${options.agentName || '智能体'}  \n`;
    md += `> 生成时间：${(options.generatedAt || new Date()).toLocaleString('zh-CN')}  \n`;
    if (options.userName) {
        md += `> 操作人：${options.userName}  \n`;
    }
    md += '\n---\n\n';

    // 思考过程
    if (content.thinkingStream && content.thinkingStream.length > 0) {
        md += '## 📝 思考过程\n\n';
        content.thinkingStream.forEach(step => {
            md += `- **[${step.step_type}]** ${step.description}\n`;
        });
        md += '\n---\n\n';
    }

    // 主要内容
    md += '## 📄 内容\n\n';
    md += content.content + '\n\n';

    // 元数据
    if (content.metadata && Object.keys(content.metadata).length > 0) {
        md += '## 📊 附加信息\n\n';
        md += formatMetadataAsMarkdown(content.metadata);
    }

    md += '\n---\n\n*本文档由 ApeRAG 智能电力运维系统自动生成*\n';

    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    downloadBlob(blob, `${options.filename}.md`);
}

/**
 * 导出为 JSON
 */
export function exportToJson(content: ExportContent, options: ExportOptions): void {
    const data = {
        title: options.title,
        agentName: options.agentName,
        generatedAt: (options.generatedAt || new Date()).toISOString(),
        userName: options.userName,
        content: content.content,
        thinkingStream: content.thinkingStream,
        metadata: content.metadata
    };

    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json;charset=utf-8' });
    downloadBlob(blob, `${options.filename}.json`);
}

/**
 * 导出为 HTML（可用于打印为 PDF）
 */
export function exportToHtml(content: ExportContent, options: ExportOptions): void {
    const thinkingContent = content.thinkingStream?.map(step =>
        `<div class="thinking-step"><span class="step-type">${step.step_type}</span> ${step.description}</div>`
    ).join('') || '';

    const metadataContent = content.metadata ?
        formatMetadataAsHtml(content.metadata) : '';

    const data = {
        TITLE: options.title,
        AGENT_NAME: options.agentName || '智能体',
        GENERATED_AT: (options.generatedAt || new Date()).toLocaleString('zh-CN'),
        USER_NAME: options.userName,
        THINKING: content.thinkingStream && content.thinkingStream.length > 0,
        THINKING_CONTENT: thinkingContent,
        CONTENT: markdownToHtml(content.content),
        METADATA: content.metadata && Object.keys(content.metadata).length > 0,
        METADATA_CONTENT: metadataContent
    };

    const html = renderTemplate(WORD_TEMPLATE, data);
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    downloadBlob(blob, `${options.filename}.html`);
}

/**
 * 通用导出函数
 */
export function exportResult(
    content: ExportContent,
    options: ExportOptions
): void {
    switch (options.format) {
        case 'word':
            exportToWord(content, options);
            break;
        case 'markdown':
            exportToMarkdown(content, options);
            break;
        case 'json':
            exportToJson(content, options);
            break;
        case 'html':
        case 'pdf':
            exportToHtml(content, options);
            break;
        default:
            console.error(`Unsupported export format: ${options.format}`);
    }
}

// ========== 辅助函数 ==========

function downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function formatMetadataAsHtml(metadata: Record<string, any>, level: number = 0): string {
    let html = '';

    for (const [key, value] of Object.entries(metadata)) {
        if (value === null || value === undefined) continue;

        const label = formatLabel(key);

        if (Array.isArray(value)) {
            html += `<h${Math.min(level + 3, 6)}>${label}</h${Math.min(level + 3, 6)}>`;
            html += '<ul>';
            value.forEach((item) => {
                if (typeof item === 'object') {
                    html += '<li>' + formatMetadataAsHtml(item, level + 1) + '</li>';
                } else {
                    html += `<li>${item}</li>`;
                }
            });
            html += '</ul>';
        } else if (typeof value === 'object') {
            html += `<h${Math.min(level + 3, 6)}>${label}</h${Math.min(level + 3, 6)}>`;
            html += formatMetadataAsHtml(value, level + 1);
        } else {
            html += `<p><strong>${label}：</strong>${value}</p>`;
        }
    }

    return html;
}

function formatMetadataAsMarkdown(metadata: Record<string, any>, indent: string = ''): string {
    let md = '';

    for (const [key, value] of Object.entries(metadata)) {
        if (value === null || value === undefined) continue;

        const label = formatLabel(key);

        if (Array.isArray(value)) {
            md += `${indent}### ${label}\n\n`;
            value.forEach((item, idx) => {
                if (typeof item === 'object') {
                    md += `${indent}#### ${idx + 1}.\n`;
                    md += formatMetadataAsMarkdown(item, indent + '  ');
                } else {
                    md += `${indent}- ${item}\n`;
                }
            });
            md += '\n';
        } else if (typeof value === 'object') {
            md += `${indent}### ${label}\n\n`;
            md += formatMetadataAsMarkdown(value, indent + '  ');
        } else {
            md += `${indent}- **${label}**: ${value}\n`;
        }
    }

    return md;
}

function formatLabel(key: string): string {
    const labelMap: Record<string, string> = {
        permit_no: '票号',
        ticket_no: '票号',
        permit_type: '票种',
        work_location: '工作地点',
        equipment: '设备',
        voltage_level: '电压等级',
        work_content: '工作内容',
        planned_start: '计划开始时间',
        planned_end: '计划结束时间',
        safety_measures: '安全措施',
        hazards: '危险点',
        possible_causes: '可能原因',
        immediate_actions: '应急措施',
        severity: '严重程度',
        probability: '可能性',
        description: '描述',
        steps: '操作步骤',
        seq: '序号',
        action: '操作',
        detail: '详情',
        category: '类别',
        content: '内容',
        plan: '方案',
        risk_assessment: '风险评估'
    };

    return labelMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}
