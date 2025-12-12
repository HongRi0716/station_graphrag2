"use client";

import { useState } from 'react';
import { PageContainer, PageHeader, PageContent } from "@/components/page-container";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Shield, Search, Layers, Zap, MessageSquare, Loader2, Brain, ChevronRight, ChevronDown, ClipboardList, AlertTriangle, Package } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useTranslations } from "next-intl";
import { useAppContext } from '@/components/providers/app-provider';
import { agentAPI, PowerGuaranteeResponse, ThinkingStep } from '@/lib/api/agents';
import { toast } from 'sonner';
import { Markdown } from '@/components/markdown';
import { ExportButton } from '@/components/agents';

export default function GuardianWorkspacePage() {
  const t = useTranslations("sidebar_workspace");
  const { user } = useAppContext();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PowerGuaranteeResponse | null>(null);
  const [showThinking, setShowThinking] = useState(true);

  const handleStartTask = async () => {
    if (!query.trim()) {
      toast.error('请输入任务指令');
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      // 根据关键词判断调用哪个API
      let response;
      if (query.includes('巡检')) {
        response = await agentAPI.generateInspectionPlan({
          query,
          user_id: user?.id || 'user-1',
        });
      } else if (query.includes('资源') || query.includes('物资')) {
        response = await agentAPI.prepareResources({
          query,
          user_id: user?.id || 'user-1',
        });
      } else {
        response = await agentAPI.generatePowerGuaranteePlan({
          query,
          user_id: user?.id || 'user-1',
        });
      }

      setResult(response);
      if (response.success) {
        toast.success('任务执行成功');
      }
    } catch (error) {
      console.error('Task failed:', error);
      toast.error('任务执行失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickTask = async (taskQuery: string) => {
    setQuery(taskQuery);
    setLoading(true);
    setResult(null);
    try {
      let response;
      if (taskQuery.includes('巡检')) {
        response = await agentAPI.generateInspectionPlan({
          query: taskQuery,
          user_id: user?.id || 'user-1',
        });
      } else if (taskQuery.includes('资源') || taskQuery.includes('物资')) {
        response = await agentAPI.prepareResources({
          query: taskQuery,
          user_id: user?.id || 'user-1',
        });
      } else {
        response = await agentAPI.generatePowerGuaranteePlan({
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
          { title: "电网安全卫士 工作台" }
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Header Section */}
          <div className="relative overflow-hidden rounded-xl border border-emerald-600/20 bg-gradient-to-br from-emerald-600/10 via-emerald-600/5 to-background p-8">
            <div className="relative z-10">
              <div className="flex items-center space-x-4 mb-6">
                <div className="p-3 rounded-full bg-emerald-600/20 backdrop-blur-sm">
                  <Shield className="w-8 h-8 text-emerald-600" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">电网安全卫士 (The Guardian)</h1>
                  <p className="text-muted-foreground mt-1">
                    您的全天候保电专家。负责制定重要活动保电方案、设备巡检计划及应急资源配置，确保供电万无一失。
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <Card className="border-emerald-200 bg-emerald-50/30 dark:border-emerald-900/30 dark:bg-emerald-900/5">
              <CardContent className="py-12">
                <div className="flex flex-col items-center justify-center space-y-4">
                  <Loader2 className="w-12 h-12 text-emerald-600 animate-spin" />
                  <div className="text-center">
                    <h3 className="text-lg font-medium mb-1">正在执行保电任务...</h3>
                    <p className="text-sm text-muted-foreground">智能体正在分析风险、调配资源并生成方案，请稍候</p>
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
                <Card className="border-emerald-100 bg-emerald-50/50 dark:border-emerald-900/50 dark:bg-emerald-900/10">
                  <CardHeader className="pb-2">
                    <div
                      className="flex items-center justify-between cursor-pointer"
                      onClick={() => setShowThinking(!showThinking)}
                    >
                      <CardTitle className="flex items-center text-base text-emerald-700 dark:text-emerald-400">
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
                          <Badge variant="secondary" className="mt-0.5 shrink-0 bg-emerald-100 text-emerald-700 hover:bg-emerald-200 dark:bg-emerald-900/40 dark:text-emerald-300">
                            {step.step_type}
                          </Badge>
                          <span className="text-muted-foreground">{step.description}</span>
                        </div>
                      ))}
                    </CardContent>
                  )}
                </Card>
              )}

              {/* Report Content */}
              {result.answer && (
                <Card className="border-emerald-200 bg-emerald-50/30 dark:border-emerald-900/30 dark:bg-emerald-900/5">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center text-lg">
                        <ClipboardList className="mr-2 h-5 w-5 text-emerald-600" />
                        方案报告
                      </CardTitle>
                      <ExportButton
                        content={{
                          content: result.answer || '',
                          thinkingStream: result.thinking_stream,
                          metadata: {
                            plan: result.plan
                          }
                        }}
                        filename="保电方案"
                        title="保电方案报告"
                        agentName="电网安全卫士"
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

              {/* Structured Plan Data (Optional Visualization) */}
              {result.plan && result.plan.risk_assessment && (
                <div className="grid gap-4 md:grid-cols-3">
                  {Object.entries(result.plan.risk_assessment).map(([key, value]: [string, any]) => (
                    <Card key={key} className="border-l-4 border-l-yellow-500">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          {key === 'weather_risk' ? '天气风险' :
                            key === 'equipment_risk' ? '设备风险' :
                              key === 'load_risk' ? '负荷风险' : key}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <span className="text-2xl font-bold">{value.level}</span>
                          {value.level === '高' && <AlertTriangle className="h-6 w-6 text-red-500" />}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">{value.description}</p>
                      </CardContent>
                    </Card>
                  ))}
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
                    <Zap className="w-5 h-5 text-emerald-600" />
                    <span>核心能力 (Core Capabilities)</span>
                  </CardTitle>
                  <CardDescription>选择一项能力开始任务，或直接在下方输入指令。</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div
                      className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-emerald-600/50"
                      onClick={() => handleQuickTask('编制高考保电方案')}
                    >
                      <h4 className="font-medium text-sm mb-1">高考保电</h4>
                      <p className="text-xs text-muted-foreground">生成高考期间的特级保电方案。</p>
                    </div>
                    <div
                      className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-emerald-600/50"
                      onClick={() => handleQuickTask('生成设备巡检计划')}
                    >
                      <h4 className="font-medium text-sm mb-1">巡检计划</h4>
                      <p className="text-xs text-muted-foreground">制定关键设备的专项巡检计划。</p>
                    </div>
                    <div
                      className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-emerald-600/50"
                      onClick={() => handleQuickTask('准备应急抢修物资清单')}
                    >
                      <h4 className="font-medium text-sm mb-1">应急资源</h4>
                      <p className="text-xs text-muted-foreground">生成应急抢修所需的人员物资清单。</p>
                    </div>
                  </div>
                  <Separator />
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">任务指令</h3>
                    <Textarea
                      placeholder="例如：编制2024年春节保电方案"
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
                    className="w-full bg-emerald-600 hover:bg-emerald-700"
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
                        onClick={() => setQuery('编制重要会议保电方案')}
                      >
                        重要会议保电
                      </Button>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-xs"
                        onClick={() => setQuery('生成防汛应急预案')}
                      >
                        防汛应急预案
                      </Button>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-xs"
                        onClick={() => setQuery('准备变电站全停应急资源')}
                      >
                        全停应急资源
                      </Button>
                    </div>
                  </div>
                  <Separator />
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">保电级别</h3>
                    <div className="text-xs text-muted-foreground space-y-1">
                      <p>🔴 一级保电 (特级): 高考、重大会议</p>
                      <p>🟡 二级保电: 节假日、大型活动</p>
                      <p>🟢 三级保电: 常规重要任务</p>
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