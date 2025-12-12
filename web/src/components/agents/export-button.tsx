"use client";

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
    DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Download, FileText, FileJson, FileCode, Printer, Loader2 } from "lucide-react";
import { toast } from 'sonner';
import {
    exportResult,
    ExportFormat,
    ExportContent,
    ExportOptions
} from '@/lib/export/export-utils';

interface ExportButtonProps {
    /** 导出内容 */
    content: ExportContent;
    /** 文件名（不含扩展名） */
    filename: string;
    /** 标题 */
    title: string;
    /** 智能体名称 */
    agentName: string;
    /** 用户名 */
    userName?: string;
    /** 禁用状态 */
    disabled?: boolean;
    /** 按钮变体 */
    variant?: "default" | "outline" | "secondary" | "ghost";
    /** 按钮大小 */
    size?: "default" | "sm" | "lg" | "icon";
    /** 自定义类名 */
    className?: string;
}

const FORMAT_OPTIONS: Array<{
    format: ExportFormat;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    description: string;
}> = [
        {
            format: 'word',
            label: 'Word 文档',
            icon: FileText,
            description: '导出为 .doc 格式'
        },
        {
            format: 'html',
            label: 'HTML 网页',
            icon: FileCode,
            description: '可打印为 PDF'
        },
        {
            format: 'markdown',
            label: 'Markdown',
            icon: FileCode,
            description: '纯文本格式'
        },
        {
            format: 'json',
            label: 'JSON 数据',
            icon: FileJson,
            description: '结构化数据'
        }
    ];

/**
 * 导出按钮组件
 * 
 * 提供下拉菜单选择导出格式
 */
export function ExportButton({
    content,
    filename,
    title,
    agentName,
    userName,
    disabled = false,
    variant = "outline",
    size = "default",
    className
}: ExportButtonProps) {
    const [exporting, setExporting] = useState(false);

    const handleExport = async (format: ExportFormat) => {
        if (!content.content) {
            toast.error('没有可导出的内容');
            return;
        }

        setExporting(true);

        try {
            const options: ExportOptions = {
                filename: `${filename}_${new Date().toISOString().slice(0, 10)}`,
                format,
                title,
                agentName,
                generatedAt: new Date(),
                userName
            };

            exportResult(content, options);

            toast.success(`已导出为 ${format.toUpperCase()} 格式`);
        } catch (error) {
            console.error('Export failed:', error);
            toast.error('导出失败，请稍后重试');
        } finally {
            setExporting(false);
        }
    };

    const handlePrint = () => {
        window.print();
    };

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant={variant}
                    size={size}
                    disabled={disabled || exporting}
                    className={className}
                >
                    {exporting ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                        <Download className="h-4 w-4 mr-2" />
                    )}
                    导出
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuLabel>选择格式</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {FORMAT_OPTIONS.map(({ format, label, icon: Icon, description }) => (
                    <DropdownMenuItem
                        key={format}
                        onClick={() => handleExport(format)}
                        className="cursor-pointer"
                    >
                        <Icon className="h-4 w-4 mr-2" />
                        <div className="flex flex-col">
                            <span>{label}</span>
                            <span className="text-xs text-muted-foreground">{description}</span>
                        </div>
                    </DropdownMenuItem>
                ))}
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handlePrint} className="cursor-pointer">
                    <Printer className="h-4 w-4 mr-2" />
                    直接打印
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}

export default ExportButton;
