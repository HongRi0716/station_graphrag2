"use client";

import { useState } from 'react';
import { PageContainer, PageHeader, PageContent } from "@/components/page-container";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Search, Layers, Zap, MessageSquare, Loader2, Brain, ChevronRight, ChevronDown, ClipboardCheck, AlertCircle } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useTranslations } from "next-intl";
import { useAppContext } from '@/components/providers/app-provider';
import { agentAPI, TicketResponse, ThinkingStep } from '@/lib/api/agents';
import { toast } from 'sonner';
import { Markdown } from '@/components/markdown';
import { ExportButton } from '@/components/agents';


export default function OperationTicketWorkspacePage() {
  const t = useTranslations("sidebar_workspace");
  const { user } = useAppContext();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TicketResponse | null>(null);
  const [showThinking, setShowThinking] = useState(true);

  const handleStartTask = async () => {
    if (!query.trim()) {
      toast.error('请输入任务指令');
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      const response = await agentAPI.generateOperationTicket({
        query,
        user_id: user?.id || 'user-1',
      });
      setResult(response);
      if (response.success) {
        toast.success('操作票生成成功');
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
      const response = await agentAPI.generateOperationTicket({
        query: taskQuery,
        user_id: user?.id || 'user-1',
      });
      setResult(response);
      if (response.success) {
        toast.success('操作票生成成功');
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
          { title: "操作票专家 工作台" }
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Header Section */}
          <div className="relative overflow-hidden rounded-xl border border-blue-600/20 bg-gradient-to-br from-blue-600/10 via-blue-600/5 to-background p-8">
            <div className="relative z-10">
              <div className="flex items-center space-x-4 mb-6">
                <div className="p-3 rounded-full bg-blue-600/20 backdrop-blur-sm">
                  <FileText className="w-8 h-8 text-blue-600" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">操作票专家 工作台</h1>
                  <p className="text-muted-foreground mt-1">
                    智能生成倒闸操作票，逻辑闭锁检查，确保操作安全合规。
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
                  <Loader2 className="w-12 h-12 text-blue-600 animate-spin" />
                  <div className="text-center">
                    <h3 className="text-lg font-medium mb-1">正在生成操作票...</h3>
                    <p className="text-sm text-muted-foreground">智能体正在分析并生成操作步骤，请稍候</p>
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

              {/* Operation Ticket Report */}
              {result.answer && (
                <Card className="border-blue-200 bg-blue-50/30 dark:border-blue-900/30 dark:bg-blue-900/5">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center text-lg">
                        <ClipboardCheck className="mr-2 h-5 w-5 text-blue-600" />
                        操作票
                      </CardTitle>
                      <ExportButton
                        content={{
                          content: result.answer || '',
                          thinkingStream: result.thinking_stream,
                          metadata: {
                            ticket: result.ticket
                          }
                        }}
                        filename="操作票"
                        title="操作票生成报告"
                        agentName="操作票专家"
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



              {/* Safety Check Results */}
              {result.ticket?.safety_check && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center">
                      <AlertCircle className="mr-2 h-5 w-5 text-green-600" />
                      安全性检查
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {Object.entries(result.ticket.safety_check).map(([key, value]) => {
                      if (key === 'warnings' || key === 'suggestions') return null;
                      return (
                        <div key={key} className="flex items-center gap-2 text-sm">
                          <span className="text-green-600">✓</span>
                          <span>{value as string}</span>
                        </div>
                      );
                    })}
                    {result.ticket.safety_check.suggestions && result.ticket.safety_check.suggestions.length > 0 && (
                      <div className="mt-4 pt-4 border-t">
                        <h4 className="text-sm font-medium mb-2">建议</h4>
                        {result.ticket.safety_check.suggestions.map((suggestion: string, index: number) => (
                          <div key={index} className="text-sm text-muted-foreground">
                            💡 {suggestion}
                          </div>
                        ))}
                      </div>
                    )}
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
                    <Zap className="w-5 h-5 text-blue-600" />
                    <span>核心能力 (Core Capabilities)</span>
                  </CardTitle>
                  <CardDescription>选择一项能力开始任务，或直接在下方输入指令。</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div
                      className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-blue-600/50"
                      onClick={() => handleQuickTask('生成#1主变转冷备用操作票')}
                    >
                      <h4 className="font-medium text-sm mb-1">主变转检修</h4>
                      <p className="text-xs text-muted-foreground">生成主变转冷备用操作步骤。</p>
                    </div>
                    <div
                      className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-blue-600/50"
                      onClick={() => handleQuickTask('生成110kV母线I母转II母操作票')}
                    >
                      <h4 className="font-medium text-sm mb-1">母线倒闸</h4>
                      <p className="text-xs text-muted-foreground">生成母线切换操作步骤。</p>
                    </div>
                    <div
                      className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors hover:border-blue-600/50"
                      onClick={() => handleQuickTask('生成#2主变投运送电操作票')}
                    >
                      <h4 className="font-medium text-sm mb-1">设备投运</h4>
                      <p className="text-xs text-muted-foreground">生成设备投运操作步骤。</p>
                    </div>
                  </div>
                  <Separator />
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">任务指令</h3>
                    <Textarea
                      placeholder="例如：生成#1主变转冷备用操作票"
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
                    className="w-full bg-blue-600 hover:bg-blue-700"
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
                        onClick={() => setQuery('生成#1主变转冷备用操作票')}
                      >
                        主变转冷备用
                      </Button>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-xs"
                        onClick={() => setQuery('生成110kV母线I母转II母操作票')}
                      >
                        母线倒闸操作
                      </Button>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-xs"
                        onClick={() => setQuery('生成#2主变投运送电操作票')}
                      >
                        主变投运送电
                      </Button>
                    </div>
                  </div>
                  <Separator />
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">操作规范</h3>
                    <div className="text-xs text-muted-foreground space-y-1">
                      <p>✓ 五防检查</p>
                      <p>✓ 步骤顺序正确</p>
                      <p>✓ 符合安规要求</p>
                      <p>✓ 包含安全措施</p>
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
