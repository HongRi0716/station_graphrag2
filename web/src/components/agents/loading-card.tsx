"use client";

import React from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

interface LoadingCardProps {
    /** 加载标题 */
    title?: string;
    /** 加载描述 */
    description?: string;
    /** 主题颜色 */
    color?: string;
}

/**
 * 加载状态卡片
 * 
 * 用于展示智能体任务执行中的加载状态
 */
export function LoadingCard({
    title = "正在处理任务...",
    description = "智能体正在分析并生成结果，请稍候",
    color = "violet"
}: LoadingCardProps) {
    return (
        <Card className="border-blue-200 bg-blue-50/30 dark:border-blue-900/30 dark:bg-blue-900/5">
            <CardContent className="py-12">
                <div className="flex flex-col items-center justify-center space-y-4">
                    <Loader2 className={`w-12 h-12 text-${color}-500 animate-spin`} />
                    <div className="text-center">
                        <h3 className="text-lg font-medium mb-1">{title}</h3>
                        <p className="text-sm text-muted-foreground">{description}</p>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

export default LoadingCard;
