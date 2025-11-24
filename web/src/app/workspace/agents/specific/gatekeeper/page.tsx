'use client';

import {
  PageContainer,
  PageContent,
  PageHeader,
} from '@/components/page-container';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  FileCheck,
  Layers,
  MessageSquare,
  Search,
  ShieldCheck,
  ThumbsUp,
} from 'lucide-react';
import { useTranslations } from 'next-intl';

export default function GatekeeperWorkspacePage() {
  const t = useTranslations('sidebar_workspace');

  const handleStartTask = () => {
    alert('任务已提交给 The Gatekeeper (调用 Agent API)');
  };

  // Mock Pending Approvals
  const pendingApprovals = [
    {
      id: 'OT-20240524-01',
      type: '操作票',
      content: '#1主变转冷备用',
      user: '张工',
      time: '10分钟前',
      status: 'pending',
    },
    {
      id: 'WP-20240524-03',
      type: '工作票',
      content: '10kV开关柜检修',
      user: '李工',
      time: '30分钟前',
      status: 'pending',
    },
  ];

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: '安监卫士 工作台' },
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Header Section */}
          <div className="to-background relative overflow-hidden rounded-xl border border-blue-500/20 bg-gradient-to-r from-blue-600/10 via-blue-500/5 p-8">
            <div className="relative z-10 flex items-start justify-between">
              <div className="flex items-center space-x-4">
                <div className="rounded-xl bg-blue-500/20 p-4 backdrop-blur-sm">
                  <ShieldCheck className="h-10 w-10 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">
                    安监卫士 The Gatekeeper
                  </h1>
                  <p className="text-muted-foreground mt-2 max-w-xl">
                    安全规程守护者。基于海量安规知识库进行五防逻辑校验、两票审查与风险预控。
                  </p>
                  <div className="mt-4 flex gap-4">
                    <div className="text-muted-foreground flex items-center text-sm">
                      <CheckCircle className="mr-1 h-4 w-4 text-green-500" />
                      <span className="text-foreground mr-1 font-medium">
                        1,240
                      </span>{' '}
                      天安全运行
                    </div>
                    <div className="text-muted-foreground flex items-center text-sm">
                      <ThumbsUp className="mr-1 h-4 w-4 text-blue-500" />
                      <span className="text-foreground mr-1 font-medium">
                        99.8%
                      </span>{' '}
                      规程执行率
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Left Column: Approvals & Tasks */}
            <div className="space-y-6 lg:col-span-2">
              {/* Pending Approvals */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between text-lg">
                    <div className="flex items-center">
                      <FileCheck className="mr-2 h-5 w-5 text-blue-500" />
                      待办审批 (Pending Approvals)
                    </div>
                    <Badge
                      variant="secondary"
                      className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                    >
                      2 待处理
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {pendingApprovals.map((item) => (
                    <div
                      key={item.id}
                      className="bg-card flex items-center justify-between rounded-lg border p-4 transition-shadow hover:shadow-sm"
                    >
                      <div className="flex items-center gap-4">
                        <div
                          className={`rounded-lg p-2 ${item.type === '操作票' ? 'bg-teal-100 text-teal-700' : 'bg-purple-100 text-purple-700'}`}
                        >
                          <FileCheck className="h-5 w-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 font-medium">
                            {item.content}
                            <Badge variant="outline" className="text-[10px]">
                              {item.id}
                            </Badge>
                          </div>
                          <div className="text-muted-foreground mt-1 text-xs">
                            申请人: {item.user} • {item.time}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => alert(`查看 ${item.id}`)}
                        >
                          查看
                        </Button>
                        <Button
                          size="sm"
                          className="bg-blue-600 text-white hover:bg-blue-700"
                          onClick={() => alert(`通过 ${item.id}`)}
                        >
                          通过
                        </Button>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Main Task Input */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-lg">
                    <MessageSquare className="mr-2 h-5 w-5 text-blue-500" />
                    安全咨询与校验 (Safety Query)
                  </CardTitle>
                  <CardDescription>
                    输入操作指令、工作票内容或现场情况，进行安规合规性检查。
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Textarea
                    placeholder="例如：请审核以下操作步骤是否符合五防要求：1. 断开101开关；2. 合上101-1地刀..."
                    className="min-h-[120px] resize-none text-base focus-visible:ring-blue-500"
                  />
                  <div className="flex justify-end gap-2">
                    <Button variant="ghost">上传票据图片</Button>
                    <Button
                      onClick={handleStartTask}
                      className="bg-blue-600 text-white hover:bg-blue-700"
                    >
                      开始校验
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Right Column: Risk & Rules */}
            <div className="space-y-6">
              {/* Current Risk Level */}
              <Card className="border-red-100 bg-red-50 dark:border-red-900/20 dark:bg-red-900/10">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center text-base text-red-700 dark:text-red-400">
                    <AlertTriangle className="mr-2 h-4 w-4" />
                    当前风险等级 (Risk Level)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="mb-2 flex items-end gap-2">
                    <span className="text-3xl font-bold text-red-600">
                      三级
                    </span>
                    <span className="text-muted-foreground mb-1 text-sm">
                      黄色预警
                    </span>
                  </div>
                  <Progress
                    value={30}
                    className="h-2 bg-red-200 dark:bg-red-900/30"
                  />
                  <p className="text-muted-foreground mt-3 text-xs">
                    今日有 2 项二级风险作业正在进行，请重点关注 10kV
                    开关室区域。
                  </p>
                </CardContent>
              </Card>

              {/* Quick Tools */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-lg">
                    <Layers className="text-primary mr-2 h-5 w-5" />
                    安规工具箱
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <Button
                    variant="ghost"
                    className="h-9 w-full justify-start text-sm"
                  >
                    <Search className="mr-2 h-4 w-4 text-blue-500" />
                    查阅《安规》条款
                  </Button>
                  <Button
                    variant="ghost"
                    className="h-9 w-full justify-start text-sm"
                  >
                    <Clock className="mr-2 h-4 w-4 text-orange-500" />
                    违章记录查询
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </PageContent>
    </PageContainer>
  );
}
