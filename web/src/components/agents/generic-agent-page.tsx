'use client';

import { useState } from 'react';
import { LucideIcon, FileText } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useAppContext } from '@/components/providers/app-provider';
import { agentAPI, BaseAgentResponse, ThinkingStep } from '@/lib/api/agents';
import { useAgentWithQuery } from '@/hooks/use-agent';

// 引入可复用组件
import {
    AgentWorkspaceLayout,
    ThinkingStreamCard,
    ResultCard,
    LoadingCard,
    TaskInputPanel,
    QuickTaskItem,
    QuickExample
} from '@/components/agents';

export interface GenericAgentPageProps {
    /** 智能体类型标识符 (用于 API 调用) */
    agentType: string;
    /** 页面标题 */
    title: string;
    /** 页面描述 */
    description: string;
    /** 图标组件 */
    icon: LucideIcon;
    /** 主题颜色 */
    color: string;
    /** 快捷任务列表 */
    quickTasks: QuickTaskItem[];
    /** 快速示例列表 */
    quickExamples?: QuickExample[];
    /** 输入框占位符 */
    placeholder?: string;
    /** 成功消息 */
    successMessage?: string;
    /** 面包屑导航标题 */
    breadcrumbTitle: string;
}

/**
 * 通用智能体页面组件
 * 
 * 提供一个可配置的智能体工作区页面模板
 * 支持快捷任务、查询输入、结果展示等功能
 */
export function GenericAgentPage({
    agentType,
    title,
    description,
    icon,
    color,
    quickTasks,
    quickExamples = [],
    placeholder = '请输入任务指令...',
    successMessage = '任务执行成功',
    breadcrumbTitle
}: GenericAgentPageProps) {
    const t = useTranslations('sidebar_workspace');
    const { user } = useAppContext();

    // 使用通用智能体 API
    const executeAgent = async (req: { query: string; user_id: string }) => {
        return agentAPI.executeGenericAgent(agentType, req);
    };

    // 使用通用 Hook
    const {
        query,
        setQuery,
        loading,
        result,
        handleStartTask,
        handleQuickTask
    } = useAgentWithQuery(executeAgent, user?.id, {
        successMessage,
        errorMessage: '任务执行失败，请稍后重试'
    });

    return (
        <AgentWorkspaceLayout
            breadcrumbs={[
                { title: t('agents'), href: '/workspace/agents' },
                { title: breadcrumbTitle }
            ]}
            title={title}
            description={description}
            icon={icon}
            color={color}
        >
            {/* Loading State */}
            {loading && (
                <LoadingCard
                    title="正在处理任务..."
                    description="智能体正在分析并生成结果，请稍候"
                    color={color}
                />
            )}

            {/* Results Section */}
            {result && !loading && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {/* Thinking Stream */}
                    {result.thinking_stream && (
                        <ThinkingStreamCard thinkingStream={result.thinking_stream} />
                    )}

                    {/* Main Answer */}
                    {result.answer && (
                        <ResultCard
                            title="执行结果"
                            icon={FileText}
                            content={result.answer}
                            color={color}
                        />
                    )}
                </div>
            )}

            {/* Initial Dashboard (Hide when showing results) */}
            {!result && !loading && (
                <TaskInputPanel
                    color={color}
                    quickTasks={quickTasks}
                    quickExamples={quickExamples}
                    query={query}
                    onQueryChange={setQuery}
                    onSubmit={() => handleStartTask()}
                    onQuickTask={(task) => handleQuickTask(task.query)}
                    loading={loading}
                    placeholder={placeholder}
                    submitText="发送指令"
                />
            )}
        </AgentWorkspaceLayout>
    );
}

export default GenericAgentPage;
