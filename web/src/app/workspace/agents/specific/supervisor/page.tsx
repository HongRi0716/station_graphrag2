'use client';

import {
  PageContainer,
  PageContent,
  PageHeader,
} from '@/components/page-container';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Layers, MessageSquare, Search, Zap, Loader2 } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useState } from 'react';

export default function SupervisorWorkspacePage() {
  const t = useTranslations('sidebar_workspace');
  const [task, setTask] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleStartTask = async () => {
    if (!task.trim()) {
      alert('请输入任务指令');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await fetch('/api/v1/agents/supervisor/dispatch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          task: task.trim(),
          user_id: 'current_user',
          priority: 'normal'
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage =
          (typeof errorData === 'object' && errorData !== null
            ? errorData.message || errorData.detail
            : undefined) || `HTTP ${response.status}`;
        throw new Error(errorMessage);
      }

      const data = await response.json();

      let resultText = `✅ 任务已成功提交\n\n`;
      resultText += `📋 任务: ${task}\n\n`;

      if (data.task_analysis) {
        resultText += `📊 分析结果:\n`;
        resultText += `- 任务类型: ${data.task_analysis.task_type || '未识别'}\n`;
        resultText += `- 复杂度: ${data.task_analysis.complexity || '中等'}\n`;
        if (data.task_analysis.required_agents) {
          resultText += `- 需要智能体: ${data.task_analysis.required_agents.join(', ')}\n`;
        }
      }

      if (data.data) {
        resultText += `\n🎯 执行结果:\n`;
        if (data.data.assigned_agent) {
          resultText += `- 分配给: ${data.data.assigned_agent}\n`;
        }
        if (data.data.task_id) {
          resultText += `- 任务ID: ${data.data.task_id}\n`;
        }
        if (data.data.estimated_time) {
          resultText += `- 预计完成: ${data.data.estimated_time}\n`;
        }
      }

      if (data.message) {
        resultText += `\n💬 ${data.message}`;
      }

      setResult(resultText);
    } catch (error) {
      console.error('任务提交失败:', error);
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      setResult(`❌ 任务提交失败\n\n错误信息: ${errorMessage}\n\n请检查:\n1. 后端服务是否正常运行\n2. 是否已登录\n3. 网络连接是否正常`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: '值班长 (Supervisor)' },
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Header Section */}
          <div className="mb-8 flex items-center space-x-4">
            <div className="rounded-full bg-yellow-500/10 p-3">
              <Zap className="h-8 w-8 text-yellow-500" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                值班长工作台 (Supervisor Dashboard)
              </h1>
              <p className="text-muted-foreground mt-1">
                变电站总控大脑。负责意图识别、任务拆解、指挥其他专家协同工作。
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Main Task Area */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <Zap className="h-5 w-5 text-yellow-500" />
                  <span>核心能力 (Core Capabilities)</span>
                </CardTitle>
                <CardDescription>
                  选择一项能力开始任务，或直接在下方输入指令。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <div className="hover:bg-muted/50 cursor-pointer rounded-lg border p-4 transition-colors">
                    <h4 className="mb-1 text-sm font-medium">
                      任务编排 (Task Orchestration)
                    </h4>
                    <p className="text-muted-foreground text-xs">
                      将复杂的运维任务拆解为子任务，并分发给相应的专家智能体。
                    </p>
                  </div>
                  <div className="hover:bg-muted/50 cursor-pointer rounded-lg border p-4 transition-colors">
                    <h4 className="mb-1 text-sm font-medium">
                      综合研判 (Comprehensive Analysis)
                    </h4>
                    <p className="text-muted-foreground text-xs">
                      汇总各方信息，提供全局视角的决策建议。
                    </p>
                  </div>
                  <div className="hover:bg-muted/50 cursor-pointer rounded-lg border p-4 transition-colors">
                    <h4 className="mb-1 text-sm font-medium">
                      SOP生成 (SOP Generation)
                    </h4>
                    <p className="text-muted-foreground text-xs">
                      根据当前场景自动生成标准作业程序 (SOP)。
                    </p>
                  </div>
                </div>
                <Separator />
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">任务指令</h3>
                  <Textarea
                    placeholder="例如：请制定一份针对主变压器油温过高的应急处理方案，并指挥相关人员进行检查。"
                    rows={4}
                    value={task}
                    onChange={(e) => setTask(e.target.value)}
                    disabled={loading}
                  />
                </div>
                <Button
                  onClick={handleStartTask}
                  className="w-full"
                  disabled={loading || !task.trim()}
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      处理中...
                    </>
                  ) : (
                    <>
                      <MessageSquare className="mr-2 h-4 w-4" />
                      发送指令
                    </>
                  )}
                </Button>

                {/* Result Display */}
                {result && (
                  <div className="mt-4 rounded-lg border bg-muted/50 p-4">
                    <h4 className="mb-2 flex items-center gap-2 text-sm font-medium">
                      <Badge variant="default">执行结果</Badge>
                    </h4>
                    <pre className="text-sm whitespace-pre-wrap">{result}</pre>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Side Panel: Quick Tools / Context */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <Layers className="text-primary h-5 w-5" />
                  <span>快捷工具</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">上下文检索</h3>
                  <Button variant="outline" className="w-full justify-start">
                    <Search className="mr-2 h-4 w-4" />
                    搜索相关文档
                  </Button>
                </div>
                <Separator />
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">历史记录</h3>
                  <div className="text-muted-foreground py-4 text-center text-sm">
                    暂无最近任务记录
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </PageContent>
    </PageContainer>
  );
}
