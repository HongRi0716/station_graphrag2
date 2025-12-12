"use client";

import { useState } from 'react';
import { PageContainer, PageHeader, PageContent } from "@/components/page-container";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity, Search, Layers, Zap, MessageSquare, Loader2, Brain, ChevronRight, ChevronDown, AlertTriangle } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useTranslations } from "next-intl";
import { useAppContext } from '@/components/providers/app-provider';
import { agentAPI, AccidentDeductionResponse, ThinkingStep } from '@/lib/api/agents';
import { toast } from 'sonner';
import { Markdown } from '@/components/markdown';
import { ExportButton } from '@/components/agents';


export default function AccidentDeductionWorkspacePage() {
  const t = useTranslations("sidebar_workspace");
  const { user } = useAppContext();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AccidentDeductionResponse | null>(null);
  const [showThinking, setShowThinking] = useState(true);

  const handleStartTask = async () => {
    if (!query.trim()) {
      toast.error('请输入任务指令');
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      const response = await agentAPI.generateAccidentDeduction({
        query,
        user_id: user?.id || 'user-1',
      });
      setResult(response);
      if (response.success) {
        toast.success('事故预想生成成功');
      }
    } catch (error) {
      console.error('Task failed:', error);
      toast.error('任务执行失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickTask = async (taskType: 'deduction' | 'plan' | 'drill', taskQuery: string) => {
    setQuery(taskQuery);
    setLoading(true);
    setResult(null);
    try {
      let response;
      if (taskType === 'deduction') {
        response = await agentAPI.generateAccidentDeduction({
          query: taskQuery,
          user_id: user?.id || 'user-1',
        });
      } else if (taskType === 'plan') {
        response = await agentAPI.generateEmergencyPlan({
          query: taskQuery,
          user_id: user?.id || 'user-1',
        });
      } else {
        response = await agentAPI.generateDrillDesign({
          query: taskQuery,
          user_id: user?.id || 'user-1',
        });
      }
      setResult(response);
      if (response.success) {
        toast.success('任务执行成功');
      }
    } catch (error) {
      console.error('Quick task failed:', error);
      toast.error('任务执行失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: "事故预想专家 工作台" }
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Header Section */}
          <div className="relative overflow-hidden rounded-xl border border-pink-600/20 bg-gradient-to-br from-pink-600/10 via-pink-600/5 to-background p-8">
            <div className="relative z-10">
              <div className="flex items-center space-x-4 mb-6">
                <div className="p-3 rounded-full bg-pink-600/20 backdrop-blur-sm">
                  <Activity className="w-8 h-8 text-pink-600" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">事故预想专家 工作台</h1>
                  <p className="text-muted-foreground mt-1">
                    事故模拟与应急预案生成。提升应对突发事件的能力。
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
                  <Loader2 className="w-12 h-12 text-pink-600 animate-spin" />
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

              {/* Answer */}
              {result.answer && (
                <Card className="border-pink-200 bg-pink-50/30 dark:border-pink-900/30 dark:bg-pink-900/5">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center text-lg">
                        <AlertTriangle className="mr-2 h-5 w-5 text-pink-600" />
                        事故预想报告
                      </CardTitle>
                      <ExportButton
                        content={{
                          content: result.answer || '',
                          thinkingStream: result.thinking_stream,
                          metadata: {
                            deduction: result.deduction
                          }
                        }}
                        filename="事故预想报告"
                        title="事故预想报告"
                        agentName="事故预想专家"
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


              {/* Deduction Details */}
              {result.deduction && (
                <div className="grid gap-4 md:grid-cols-2">
                  {/* Possible Causes */}
                  {result.deduction.possible_causes && result.deduction.possible_causes.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">可能原因分析</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {result.deduction.possible_causes.map((cause, index) => (
                          <div key={index} className="border-l-2 border-orange-500 pl-3">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium text-sm">{cause.cause}</span>
                              <Badge variant="outline" className="text-xs">{cause.probability}</Badge>
                            </div>
                            <p className="text-xs text-muted-foreground">{cause.description}</p>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  )}

                  {/* Immediate Actions */}
                  {result.deduction.immediate_actions && result.deduction.immediate_actions.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">应急处置措施</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        {result.deduction.immediate_actions.map((action, index) => (
                          <div key={index} className="flex items-start gap-2">
                            <Badge variant="secondary" className="mt-0.5 shrink-0">{action.priority}</Badge>
                            <span className="text-sm">{action.action}</span>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  )}
                </div>
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
                    <Zap className="w-5 h-5 text-pink-600" />
                    <span>核心能力 (Core Capabilities)</span>
                  </CardTitle>
                  <CardDescription>选择一项能力开始任务，或直接在下方输入指令。</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

                    <div
                      className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-pink-600/50"
                      onClick={() => handleQuickTask('deduction', '#1主变重瓦斯保护动作事故预想')}
                    >
                      <h4 className="font-medium text-sm mb-1">事故演练 (Accident Drill)</h4>
                      <p className="text-xs text-muted-foreground">生成事故演练场景和操作步骤。</p>
                    </div>
                    <div
                      className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-pink-600/50"
                      onClick={() => handleQuickTask('plan', '生成变电站火灾应急预案')}
                    >
                      <h4 className="font-medium text-sm mb-1">预案生成 (Plan Generation)</h4>
                      <p className="text-xs text-muted-foreground">自动生成针对性的应急处置预案。</p>
                    </div>
                    <div
                      className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-pink-600/50"
                      onClick={() => handleQuickTask('drill', '设计主变跳闸应急演练方案')}
                    >
                      <h4 className="font-medium text-sm mb-1">后果分析 (Consequence Analysis)</h4>
                      <p className="text-xs text-muted-foreground">分析故障可能导致的系统后果。</p>
                    </div>
                  </div>
                  <Separator />
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">任务指令</h3>
                    <Textarea
                      placeholder="例如：模拟主变重瓦斯保护动作后的应急处置流程。"
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
                    onClick={handleStartTask}
                    disabled={loading || !query.trim()}
                    className="w-full bg-pink-600 hover:bg-pink-700"
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
                        onClick={() => setQuery('#1主变重瓦斯保护动作事故预想')}
                      >
                        主变重瓦斯保护动作
                      </Button>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-xs"
                        onClick={() => setQuery('生成变电站火灾应急预案')}
                      >
                        变电站火灾应急预案
                      </Button>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-xs"
                        onClick={() => setQuery('设计主变跳闸应急演练方案')}
                      >
                        主变跳闸应急演练
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
