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
import { Activity, Code, FileUp, LineChart, Search } from 'lucide-react';
import { useTranslations } from 'next-intl';

const LogUploadSlot = ({ type }: { type: string }) => (
  <div className="bg-background/50 hover:bg-muted/30 flex h-32 flex-col items-center justify-center rounded-lg border-2 border-dashed p-4 transition-colors">
    <FileUp className="text-muted-foreground mb-1 h-6 w-6" />
    <p className="text-muted-foreground text-sm font-medium">
      {type} 文件 (.cfg / .dat / .txt)
    </p>
    <span className="text-muted-foreground mt-1 text-xs">点击上传或拖拽</span>
  </div>
);

const WaveformDisplay = () => (
  <div className="relative flex h-64 items-center justify-center rounded-lg border border-red-800/40 bg-black/90 p-8">
    <LineChart className="h-full w-full text-red-500/40" />
    <span className="absolute font-mono text-sm text-red-400/80">
      波形图生成区域 (Ia, Ib, Ic, Ua, Ub, Uc)
    </span>
  </div>
);

export default function DiagnosticianWorkspacePage() {
  const t = useTranslations('sidebar_workspace');

  const handleStartAnalysis = () => {
    alert('开始事故因果链推理... (调用 Diagnostician Agent API)');
  };

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: `${t('agent_diagnostician')} 工作台` },
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          <div className="flex items-center space-x-4">
            <div className="rounded-full bg-red-600/10 p-3">
              <Activity className="h-8 w-8 text-red-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                {t('agent_diagnostician')} 工作台
              </h1>
              <p className="text-muted-foreground mt-1">
                专用工作区，用于故障录波、SOE (事件顺序记录)
                分析与事故因果链推演。
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card className="flex h-full flex-col lg:col-span-1">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <FileUp className="h-5 w-5" />
                  <span>故障数据上传</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-grow space-y-4">
                <LogUploadSlot type="录波文件 (COMTRADE)" />
                <LogUploadSlot type="SOE 日志文件" />
                <Separator />
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">分析指令</h3>
                  <Textarea
                    placeholder="例如：请判断本次故障是否为区内短路，并估算故障发生距离。"
                    rows={4}
                  />
                </div>
              </CardContent>
              <div className="p-6 pt-0">
                <Button
                  className="w-full bg-red-600 hover:bg-red-700"
                  onClick={handleStartAnalysis}
                >
                  <Search className="mr-2 h-4 w-4" />
                  开始故障诊断
                </Button>
              </div>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <Code className="text-primary h-5 w-5" />
                  <span>诊断报告与波形分析</span>
                </CardTitle>
                <CardDescription>
                  AI 推理出的事故因果链与关键波形数据。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <WaveformDisplay />
                <Separator />
                <div className="space-y-2">
                  <h3 className="flex items-center space-x-2 text-sm font-medium">
                    <Activity className="h-4 w-4" />
                    <span>AI 诊断结论</span>
                  </h3>
                  <div className="bg-muted text-muted-foreground min-h-[120px] rounded-md p-3 text-sm">
                    <p>
                      AI 推理结果：[🔴 结论] A 相短路。保护动作正确，动作时间
                      35ms， 符合要求。故障类型已锁定。
                    </p>
                    <p className="mt-2 text-xs">AI 思考链条可追溯至聊天记录…</p>
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
