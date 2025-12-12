"use client";

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Markdown } from '@/components/markdown';
import { LucideIcon } from 'lucide-react';

interface ResultCardProps {
    /** 卡片标题 */
    title: string;
    /** 图标组件 */
    icon: LucideIcon;
    /** Markdown 内容 */
    content: string;
    /** 主题颜色 */
    color?: string;
}

/**
 * 结果展示卡片
 * 
 * 用于展示智能体生成的报告/答案，支持 Markdown 渲染
 */
export function ResultCard({
    title,
    icon: Icon,
    content,
    color = "violet"
}: ResultCardProps) {
    if (!content) {
        return null;
    }

    const colorClasses = {
        border: `border-${color}-200 dark:border-${color}-900/30`,
        bg: `bg-${color}-50/30 dark:bg-${color}-900/5`,
        iconColor: `text-${color}-500`
    };

    return (
        <Card className={`${colorClasses.border} ${colorClasses.bg}`}>
            <CardHeader>
                <CardTitle className="flex items-center text-lg">
                    <Icon className={`mr-2 h-5 w-5 ${colorClasses.iconColor}`} />
                    {title}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <Markdown>{content}</Markdown>
            </CardContent>
        </Card>
    );
}

export default ResultCard;
