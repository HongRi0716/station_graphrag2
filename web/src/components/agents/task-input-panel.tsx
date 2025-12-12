"use client";

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Zap, MessageSquare, Loader2, Layers, LucideIcon } from "lucide-react";

export interface QuickTaskItem {
    /** 任务 ID */
    id: string;
    /** 任务标题 */
    title: string;
    /** 任务描述 */
    description: string;
    /** 任务查询内容 */
    query: string;
    /** 任务类型（可选） */
    type?: string;
}

export interface QuickExample {
    /** 示例标签 */
    label: string;
    /** 示例查询内容 */
    query: string;
}

interface TaskInputPanelProps {
    /** 主题颜色 */
    color?: string;
    /** 快捷任务列表 */
    quickTasks: QuickTaskItem[];
    /** 快速示例列表 */
    quickExamples?: QuickExample[];
    /** 当前查询内容 */
    query: string;
    /** 查询内容变更回调 */
    onQueryChange: (query: string) => void;
    /** 任务提交回调 */
    onSubmit: () => void;
    /** 快捷任务点击回调 */
    onQuickTask: (task: QuickTaskItem) => void;
    /** 是否正在加载 */
    loading?: boolean;
    /** 输入框占位符 */
    placeholder?: string;
    /** 提交按钮文本 */
    submitText?: string;
}

/**
 * 任务输入面板组件
 * 
 * 包含快捷任务卡片、输入框和快速示例
 */
export function TaskInputPanel({
    color = "violet",
    quickTasks,
    quickExamples = [],
    query,
    onQueryChange,
    onSubmit,
    onQuickTask,
    loading = false,
    placeholder = "请输入任务指令...",
    submitText = "发送指令"
}: TaskInputPanelProps) {
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            onSubmit();
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Task Area */}
            <Card className="lg:col-span-2">
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2 text-lg">
                        <Zap className={`w-5 h-5 text-${color}-500`} />
                        <span>核心能力 (Core Capabilities)</span>
                    </CardTitle>
                    <CardDescription>选择一项能力开始任务，或直接在下方输入指令。</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Quick Task Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {quickTasks.map((task) => (
                            <div
                                key={task.id}
                                className={`p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-${color}-500/50`}
                                onClick={() => onQuickTask(task)}
                            >
                                <h4 className="font-medium text-sm mb-1">{task.title}</h4>
                                <p className="text-xs text-muted-foreground">{task.description}</p>
                            </div>
                        ))}
                    </div>

                    <Separator />

                    {/* Input Area */}
                    <div className="space-y-2">
                        <h3 className="text-sm font-medium">任务指令</h3>
                        <Textarea
                            placeholder={placeholder}
                            rows={4}
                            value={query}
                            onChange={(e) => onQueryChange(e.target.value)}
                            onKeyDown={handleKeyDown}
                        />
                        <p className="text-xs text-muted-foreground">提示: 按 Ctrl+Enter 快速发送</p>
                    </div>

                    <Button
                        onClick={onSubmit}
                        disabled={loading || !query.trim()}
                        className={`w-full bg-${color}-600 hover:bg-${color}-700`}
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                处理中...
                            </>
                        ) : (
                            <>
                                <MessageSquare className="w-4 h-4 mr-2" />
                                {submitText}
                            </>
                        )}
                    </Button>
                </CardContent>
            </Card>

            {/* Side Panel: Quick Tools */}
            <Card className="lg:col-span-1">
                <CardHeader>
                    <CardTitle className="text-lg flex items-center space-x-2">
                        <Layers className="w-5 h-5 text-primary" />
                        <span>快捷工具</span>
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {quickExamples.length > 0 && (
                        <>
                            <div className="space-y-2">
                                <h3 className="text-sm font-medium">快速示例</h3>
                                <div className="space-y-2">
                                    {quickExamples.map((example, index) => (
                                        <Button
                                            key={index}
                                            variant="outline"
                                            className="w-full justify-start text-xs"
                                            onClick={() => onQueryChange(example.query)}
                                        >
                                            {example.label}
                                        </Button>
                                    ))}
                                </div>
                            </div>
                            <Separator />
                        </>
                    )}
                    <div className="space-y-2">
                        <h3 className="text-sm font-medium">历史记录</h3>
                        <div className="text-sm text-muted-foreground text-center py-4">
                            暂无最近任务记录
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

export default TaskInputPanel;
