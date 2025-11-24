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
import {
  ClipboardCheck,
  Layers,
  MessageSquare,
  Search,
  Zap,
} from 'lucide-react';
import { useTranslations } from 'next-intl';

export default function OperationTicketWorkspacePage() {
  const t = useTranslations('sidebar_workspace');

  const handleStartTask = () => {
    alert('任务已提交给 Operation Ticket Agent (调用 Agent API)');
  };

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: '操作票专家 工作台' },
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Header Section */}
          <div className="mb-8 flex items-center space-x-4">
            <div className="rounded-full bg-teal-500/10 p-3">
              <ClipboardCheck className="h-8 w-8 text-teal-500" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                操作票专家 工作台
              </h1>
              <p className="text-muted-foreground mt-1">
                操作票生成与逻辑校验。确保倒闸操作流程安全无误。
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Main Task Area */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <Zap className="h-5 w-5 text-teal-500" />
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
                      操作票生成 (Ticket Generation)
                    </h4>
                    <p className="text-muted-foreground text-xs">
                      根据操作任务自动生成标准操作票。
                    </p>
                  </div>
                  <div className="hover:bg-muted/50 cursor-pointer rounded-lg border p-4 transition-colors">
                    <h4 className="mb-1 text-sm font-medium">
                      逻辑校验 (Logic Verification)
                    </h4>
                    <p className="text-muted-foreground text-xs">
                      检查操作票是否存在五防逻辑错误。
                    </p>
                  </div>
                  <div className="hover:bg-muted/50 cursor-pointer rounded-lg border p-4 transition-colors">
                    <h4 className="mb-1 text-sm font-medium">
                      风险预警 (Risk Alert)
                    </h4>
                    <p className="text-muted-foreground text-xs">
                      识别操作过程中可能存在的安全风险。
                    </p>
                  </div>
                </div>
                <Separator />
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">任务指令</h3>
                  <Textarea
                    placeholder="例如：生成一张将 #1主变 由运行转冷备用的操作票。"
                    rows={4}
                  />
                </div>
                <Button onClick={handleStartTask} className="w-full">
                  <MessageSquare className="mr-2 h-4 w-4" />
                  发送指令
                </Button>
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
