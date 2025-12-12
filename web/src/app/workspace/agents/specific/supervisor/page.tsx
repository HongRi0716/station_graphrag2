'use client';

import { Zap, MessageSquare, Search, Users, Layers, FileText, Loader2 } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useAppContext } from '@/components/providers/app-provider';
import { agentAPI, SupervisorResponse } from '@/lib/api/agents';
import { useAgentWithQuery } from '@/hooks/use-agent';
import { Markdown } from '@/components/markdown';

// 引入可复用组件
import {
  AgentWorkspaceLayout,
  ThinkingStreamCard,
  ResultCard,
  LoadingCard,
  TaskInputPanel,
  QuickTaskItem,
  QuickExample,
  ExportButton
} from '@/components/agents';

export default function SupervisorWorkspacePage() {
  const t = useTranslations('sidebar_workspace');
  const { user } = useAppContext();

  // 使用通用 Hook
  const {
    query,
    setQuery,
    loading,
    result,
    handleStartTask,
    handleQuickTask
  } = useAgentWithQuery<
    { query: string; user_id: string },
    SupervisorResponse
  >(agentAPI.dispatchTask, user?.id, {
    successMessage: '任务分发成功',
    errorMessage: '任务执行失败，请稍后重试'
  });


  // 快捷任务定义
  const quickTasks: QuickTaskItem[] = [
    {
      id: 'orchestration',
      title: '任务编排 (Task Orchestration)',
      description: '将复杂的运维任务拆解为子任务，并分发给相应的专家智能体。',
      query: '请制定一份针对主变压器油温过高的应急处理方案，并指挥相关人员进行检查。'
    },
    {
      id: 'analysis',
      title: '综合研判 (Comprehensive Analysis)',
      description: '汇总各方信息，提供全局视角的决策建议。',
      query: '分析当前变电站运行状态，识别潜在风险并给出建议。'
    },
    {
      id: 'sop',
      title: 'SOP生成 (SOP Generation)',
      description: '根据当前场景自动生成标准作业程序 (SOP)。',
      query: '生成主变故障应急处置标准作业程序。'
    }
  ];

  // 快速示例
  const quickExamples: QuickExample[] = [
    { label: '主变油温异常应急方案', query: '请制定一份针对主变压器油温过高的应急处理方案' },
    { label: '日常巡检任务分配', query: '安排今日变电站设备巡检任务' },
    { label: '故障诊断协调', query: '协调诊断110kV母线接地故障原因' }
  ];

  return (
    <AgentWorkspaceLayout
      breadcrumbs={[
        { title: t('agents'), href: '/workspace/agents' },
        { title: '值班长 (Supervisor)' }
      ]}
      title="值班长工作台 (Supervisor Dashboard)"
      description="变电站总控大脑。负责意图识别、任务拆解、指挥其他专家协同工作。"
      icon={Zap}
      color="yellow"
    >
      {/* Loading State */}
      {loading && (
        <LoadingCard
          title="值班长正在处理任务..."
          description="正在分析任务并协调智能体，请稍候"
          color="yellow"
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
            <Card className="border-yellow-200 bg-yellow-50/30 dark:border-yellow-900/30 dark:bg-yellow-900/5">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center text-lg">
                    <FileText className="mr-2 h-5 w-5 text-yellow-500" />
                    执行结果
                  </CardTitle>
                  <ExportButton
                    content={{
                      content: result.answer || '',
                      thinkingStream: result.thinking_stream,
                      metadata: {
                        task_analysis: result.task_analysis
                      }
                    }}
                    filename="任务分发报告"
                    title="任务分发报告"
                    agentName="值班长"
                    userName={user?.id}
                    disabled={!result.answer}
                    size="sm"
                  />
                </div>
              </CardHeader>
              <CardContent>
                <Markdown>{result.answer}</Markdown>
              </CardContent>
            </Card>
          )}

          {/* Task Analysis */}
          {result.task_analysis && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center">
                  <Users className="mr-2 h-5 w-5 text-yellow-500" />
                  任务分析
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {result.task_analysis.task_type && (
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">任务类型</Badge>
                    <span>{result.task_analysis.task_type}</span>
                  </div>
                )}
                {result.task_analysis.priority && (
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">优先级</Badge>
                    <span>{result.task_analysis.priority}</span>
                  </div>
                )}
                {result.task_analysis.assigned_agents && result.task_analysis.assigned_agents.length > 0 && (
                  <div>
                    <Badge variant="outline" className="mb-2">分配智能体</Badge>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {result.task_analysis.assigned_agents.map((agent, idx) => (
                        <Badge key={idx} variant="secondary">{agent}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Task Input Panel - Always Visible */}
      <TaskInputPanel
        color="yellow"
        quickTasks={quickTasks}
        quickExamples={quickExamples}
        query={query}
        onQueryChange={setQuery}
        onSubmit={() => handleStartTask()}
        onQuickTask={(task) => handleQuickTask(task.query)}
        loading={loading}
        placeholder="例如：请制定一份针对主变压器油温过高的应急处理方案，并指挥相关人员进行检查。"
        submitText="发送指令"
      />
    </AgentWorkspaceLayout>
  );
}

