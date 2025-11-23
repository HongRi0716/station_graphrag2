'use client';

import type { ComponentType } from 'react';

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import {
  AlertTriangle,
  Eye,
  Loader2,
  MapPin,
  Thermometer,
  Video,
} from 'lucide-react';
import { useTranslations } from 'next-intl';

const MockCameraFeed = () => (
  <div className="relative flex h-96 w-full items-center justify-center rounded-lg bg-black p-4 text-white shadow-xl">
    <Video className="text-muted-foreground/50 h-16 w-16" />
    <span className="absolute top-2 left-2 font-mono text-xs text-white/80">
      CAM_101 / #1 主变本体
    </span>
    <div className="absolute top-1/4 left-1/4 flex h-1/2 w-1/2 items-center justify-center rounded-sm border-2 border-red-500/80 text-sm font-bold text-red-500/80">
      目标框选 (Violation Detected)
    </div>
  </div>
);

const AnalysisResultCard = ({
  title,
  icon: Icon,
  value,
  colorClass,
}: {
  title: string;
  icon: ComponentType<{ className?: string }>;
  value: string;
  colorClass: string;
}) => (
  <Card className="flex h-full flex-col justify-between p-4">
    <div className="flex items-center space-x-3">
      <Icon className={`h-6 w-6 ${colorClass}`} />
      <span className="text-muted-foreground text-sm font-medium">{title}</span>
    </div>
    <p className={`mt-2 text-2xl font-bold ${colorClass}`}>{value}</p>
  </Card>
);

export default function SentinelWorkspacePage() {
  const translate = useTranslations('sidebar_workspace');
  const t = (key: string) => translate(key as any);

  const handleSnapshotAnalysis = () => {
    alert('执行 AI 画面分析指令... (调用 Sentinel Agent API)');
  };

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: `${t('agent_sentinel')} 工作台` },
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          <div className="flex items-center space-x-4">
            <div className="rounded-full bg-slate-500/10 p-3">
              <Eye className="h-8 w-8 text-slate-500" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                {t('agent_sentinel')} 工作台
              </h1>
              <p className="text-muted-foreground mt-1">
                专用工作区，用于实时视频监控、安全违规检测和远程仪表读数识别。
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
            <Card className="lg:col-span-3">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <MapPin className="h-5 w-5" />
                  <span>现场实时监控与控制</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <h3 className="mb-1 text-sm font-medium">选择摄像头</h3>
                    <Select defaultValue="CAM_101">
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="选择监控点" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="CAM_101">#1 主变本体</SelectItem>
                        <SelectItem value="CAM_205">10kV 开关室</SelectItem>
                        <SelectItem value="CAM_302">GIS 隔离开关</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <h3 className="mb-1 text-sm font-medium">分析模式</h3>
                    <Select defaultValue="safety_check">
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="选择分析任务" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="safety_check">
                          安全帽/工服检测
                        </SelectItem>
                        <SelectItem value="meter_read">远程仪表读数</SelectItem>
                        <SelectItem value="anomaly">异常行为检测</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <MockCameraFeed />
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">定制指令</h3>
                  <Textarea
                    placeholder="例如：请确认画面中是否有未佩戴安全帽的人员。"
                    rows={2}
                  />
                  <Button
                    className="w-full bg-slate-600 hover:bg-slate-700"
                    onClick={handleSnapshotAnalysis}
                  >
                    <Loader2 className="mr-2 h-4 w-4" />
                    执行 AI 快照分析
                  </Button>
                </div>
              </CardContent>
            </Card>

            <div className="space-y-6 lg:col-span-1">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">关键指标与告警</CardTitle>
                  <CardDescription>AI 最新识别的结果摘要。</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <AnalysisResultCard
                    title="安全违规告警"
                    icon={AlertTriangle}
                    value="发现 1 处违规"
                    colorClass="text-red-500"
                  />
                  <AnalysisResultCard
                    title="主变油温读数"
                    icon={Thermometer}
                    value="55.8 °C"
                    colorClass="text-blue-500"
                  />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">历史记录</CardTitle>
                </CardHeader>
                <CardContent className="text-muted-foreground text-sm">
                  2025/11/19 10:30: 发现未戴安全帽。
                  <br />
                  2025/11/19 09:00: 自动巡视完成，正常。
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </PageContent>
    </PageContainer>
  );
}
