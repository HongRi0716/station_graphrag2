"use client";

import { useState } from 'react';
import { PageContainer, PageHeader, PageContent } from "@/components/page-container";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Layers, Zap, MessageSquare, Loader2, Brain, ChevronRight, ChevronDown } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useTranslations } from "next-intl";
import { useAppContext } from '@/components/providers/app-provider';
import { agentAPI, WorkPermitResponse } from '@/lib/api/agents';
import { useAgentWithQuery } from '@/hooks/use-agent';
import { Markdown } from '@/components/markdown';
import { ExportButton } from '@/components/agents';

export default function WorkPermitWorkspacePage() {
  const t = useTranslations("sidebar_workspace");
  const { user } = useAppContext();
  const [showThinking, setShowThinking] = useState(true);

  // 使用通用 Hook 管理智能体调用
  const {
    query,
    setQuery,
    loading,
    result,
    handleStartTask,
    handleQuickTask
  } = useAgentWithQuery<
    { query: string; user_id: string },
    WorkPermitResponse
  >(agentAPI.generateWorkPermit, user?.id, {
    successMessage: '工作票生成成功',
    errorMessage: '任务执行失败，请稍后重试'
  });

  // 快捷任务处理
  const handleQuickTaskByType = async (
    taskType: 'generate' | 'review' | 'hazards',
    taskQuery: string
  ) => {
    let apiMethod;
    switch (taskType) {
      case 'generate':
        apiMethod = agentAPI.generateWorkPermit;
        break;
      case 'review':
        apiMethod = agentAPI.reviewWorkPermit;
        break;
      case 'hazards':
        apiMethod = agentAPI.identifyHazards;
        break;
    }

    setQuery(taskQuery);
    try {
      const response = await apiMethod({
        query: taskQuery,
        user_id: user?.id || 'user-1',
      });
      // 直接使用 result setter（如果需要的话可以扩展 hook）
    } catch (error) {
      console.error('Quick task failed:', error);
    }
  };

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: "工作票专家 工作台" }
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Header Section */}
          <div className="relative overflow-hidden rounded-xl border border-violet-500/20 bg-gradient-to-br from-violet-500/10 via-violet-500/5 to-background p-8">
            <div className="relative z-10">
              <div className="flex items-center space-x-4 mb-6">
                <div className="p-3 rounded-full bg-violet-500/20 backdrop-blur-sm">
                  <FileText className="w-8 h-8 text-violet-500" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">工作票专家 工作台</h1>
                  <p className="text-muted-foreground mt-1">
                    工作票智能编制、合规性审查与危险点分析。
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <Card className="border-blue-200 bg-blue-50/30 dark:border-blue-900/30 dark:bg-blue-900/5">
              <CardContent className="py-12">
                <div className="flex flex-col items-center justify-center space-y-4">
                  <Loader2 className="w-12 h-12 text-violet-500 animate-spin" />
                  <div className="text-center">
                    <h3 className="text-lg font-medium mb-1">正在处理任务...</h3>
                    <p className="text-sm text-muted-foreground">智能体正在分析并生成结果，请稍候</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Results Section */}
          {result && !loading && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* Thinking Stream */}
              {result.thinking_stream && result.thinking_stream.length > 0 && (
                <Card className="border-blue-100 bg-blue-50/50 dark:border-blue-900/50 dark:bg-blue-900/10">
                  <CardHeader className="pb-2">
                    <div
                      className="flex items-center justify-between cursor-pointer"
                      onClick={() => setShowThinking(!showThinking)}
                    >
                      <CardTitle className="flex items-center text-base text-blue-700 dark:text-blue-400">
                        <Brain className="mr-2 h-5 w-5" />
                        思考过程
                      </CardTitle>
                      {showThinking ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </div>
                  </CardHeader>
                  {showThinking && (
                    <CardContent className="space-y-3 pt-0">
                      {result.thinking_stream.map((step, index) => (
                        <div key={index} className="flex items-start gap-3 text-sm">
                          <Badge variant="secondary" className="mt-0.5 shrink-0 bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/40 dark:text-blue-300">
                            {step.step_type}
                          </Badge>
                          <span className="text-muted-foreground">{step.description}</span>
                        </div>
                      ))}
                    </CardContent>
                  )}
                </Card>
              )}

              {/* Answer / Report */}
              {result.answer && (
                <Card className="border-violet-200 bg-violet-50/30 dark:border-violet-900/30 dark:bg-violet-900/5">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center text-lg">
                        <FileText className="mr-2 h-5 w-5 text-violet-500" />
                        生成报告
                      </CardTitle>
                      <ExportButton
                        content={{
                          content: result.answer || '',
                          thinkingStream: result.thinking_stream,
                          metadata: {
                            ticket: result.ticket,
                            hazards: result.hazards
                          }
                        }}
                        filename="工作票"
                        title="工作票生成报告"
                        agentName="工作票专家"
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

              {/* Ticket Details (if available) */}
              {result.ticket && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">工作票详情</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div><span className="font-semibold">票号:</span> {result.ticket.permit_no || result.ticket.ticket_no}</div>
                      <div><span className="font-semibold">票种:</span> {result.ticket.permit_type}</div>
                      <div><span className="font-semibold">工作地点:</span> {result.ticket.work_location}</div>
                      <div><span className="font-semibold">设备:</span> {result.ticket.equipment}</div>
                      <div className="col-span-2"><span className="font-semibold">工作内容:</span> {result.ticket.work_content}</div>
                    </div>

                    {result.ticket.safety_measures && (
                      <div className="mt-4">
                        <h4 className="font-semibold mb-2">安全措施</h4>
                        <ul className="list-disc pl-5 space-y-1 text-sm">
                          {result.ticket.safety_measures.map((m, i) => (
                            <li key={i}>
                              <span className="font-medium">{m.category}:</span> {m.content}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Hazards (if available) */}
              {result.hazards && result.hazards.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">识别的危险点</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {result.hazards.map((hazard, index) => (
                        <div key={index} className="flex items-start gap-2 text-sm border-l-2 border-orange-500 pl-3">
                          <Badge variant="outline" className={`shrink-0 ${hazard.severity === '高' ? 'border-red-500 text-red-600' :
                            hazard.severity === '中' ? 'border-yellow-500 text-yellow-600' :
                              'border-green-500 text-green-600'
                            }`}>
                            {hazard.severity}
                          </Badge>
                          <div>
                            <span className="font-medium">{hazard.type}</span>
                            <p className="text-muted-foreground">{hazard.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Initial Dashboard (Hide when showing results) */}
          {!result && !loading && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Main Task Area */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2 text-lg">
                    <Zap className="w-5 h-5 text-violet-500" />
                    <span>核心能力 (Core Capabilities)</span>
                  </CardTitle>
                  <CardDescription>选择一项能力开始任务，或直接在下方输入指令。</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

                    <div
                      className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-violet-500/50"
                      onClick={() => handleQuickTask('生成#1主变年度检修工作票')}
                    >
                      <h4 className="font-medium text-sm mb-1">智能开票 (Smart Generation)</h4>
                      <p className="text-xs text-muted-foreground">自动生成标准工作票，包含安全措施。</p>
                    </div>
                    <div
                      className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-violet-500/50"
                      onClick={() => handleQuickTaskByType('review', '审核工作票 WP-2024-1120-008')}
                    >
                      <h4 className="font-medium text-sm mb-1">合规审查 (Compliance Review)</h4>
                      <p className="text-xs text-muted-foreground">审查工作票内容的完整性和规范性。</p>
                    </div>
                    <div
                      className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-violet-500/50"
                      onClick={() => handleQuickTaskByType('hazards', '识别主变高处作业的危险点')}
                    >
                      <h4 className="font-medium text-sm mb-1">危险点分析 (Hazard Analysis)</h4>
                      <p className="text-xs text-muted-foreground">识别作业过程中的潜在安全风险。</p>
                    </div>
                  </div>
                  <Separator />
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">任务指令</h3>
                    <Textarea
                      placeholder="例如：生成#1主变检修工作票，工作内容包括更换呼吸器。"
                      rows={4}
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && e.ctrlKey) {
                          handleStartTask();
                        }
                      }}
                    />
                    <p className="text-xs text-muted-foreground">提示: 按 Ctrl+Enter 快速发送</p>
                  </div>
                  <Button
                    onClick={() => handleStartTask()}
                    disabled={loading || !query.trim()}
                    className="w-full bg-violet-600 hover:bg-violet-700"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        生成中...
                      </>
                    ) : (
                      <>
                        <MessageSquare className="w-4 h-4 mr-2" />
                        发送指令
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Side Panel: Quick Tools / Context */}
              <Card className="lg:col-span-1">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center space-x-2">
                    <Layers className="w-5 h-5 text-primary" />
                    <span>快捷工具</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">快速示例</h3>
                    <div className="space-y-2">
                      <Button
                        variant="outline"
                        className="w-full justify-start text-xs"
                        onClick={() => setQuery('生成#1主变检修工作票')}
                      >
                        #1主变检修工作票
                      </Button>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-xs"
                        onClick={() => setQuery('审核工作票 WP-2024-1120-008')}
                      >
                        审核工作票
                      </Button>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-xs"
                        onClick={() => setQuery('识别10kV开关柜检修危险点')}
                      >
                        开关柜检修危险点
                      </Button>
                    </div>
                  </div>
                  <Separator />
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">历史记录</h3>
                    <div className="text-sm text-muted-foreground text-center py-4">
                      暂无最近任务记录
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </PageContent>
    </PageContainer>
  );
}
