"use client";

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, ChevronRight, ChevronDown } from "lucide-react";
import { ThinkingStep } from '@/lib/api/agents';

interface ThinkingStreamCardProps {
    /** 思考步骤列表 */
    thinkingStream: ThinkingStep[];
    /** 是否默认展开 */
    defaultExpanded?: boolean;
    /** 标题 */
    title?: string;
}

/**
 * 思考过程展示卡片
 * 
 * 以可折叠的形式展示智能体的思考步骤
 */
export function ThinkingStreamCard({
    thinkingStream,
    defaultExpanded = true,
    title = "思考过程"
}: ThinkingStreamCardProps) {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);

    if (!thinkingStream || thinkingStream.length === 0) {
        return null;
    }

    return (
        <Card className="border-blue-100 bg-blue-50/50 dark:border-blue-900/50 dark:bg-blue-900/10">
            <CardHeader className="pb-2">
                <div
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    <CardTitle className="flex items-center text-base text-blue-700 dark:text-blue-400">
                        <Brain className="mr-2 h-5 w-5" />
                        {title}
                    </CardTitle>
                    {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                    ) : (
                        <ChevronRight className="h-4 w-4" />
                    )}
                </div>
            </CardHeader>
            {isExpanded && (
                <CardContent className="space-y-3 pt-0">
                    {thinkingStream.map((step, index) => (
                        <div key={index} className="flex items-start gap-3 text-sm">
                            <Badge
                                variant="secondary"
                                className="mt-0.5 shrink-0 bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/40 dark:text-blue-300"
                            >
                                {step.step_type}
                            </Badge>
                            <span className="text-muted-foreground">{step.description}</span>
                        </div>
                    ))}
                </CardContent>
            )}
        </Card>
    );
}

export default ThinkingStreamCard;
