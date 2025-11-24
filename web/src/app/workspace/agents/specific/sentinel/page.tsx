"use client";

import { PageContainer, PageHeader, PageContent } from "@/components/page-container";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Eye, Search, Layers, Zap, MessageSquare } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { useTranslations } from "next-intl";

export default function SentinelWorkspacePage() {
  const t = useTranslations("sidebar_workspace"); 

  const handleStartTask = () => {
    alert("任务已提交给 The Sentinel (调用 Agent API)"); 
  };

  return (
    <PageContainer>
      <PageHeader 
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: "巡视哨兵 工作台" }
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Header Section */}
          <div className="flex items-center space-x-4 mb-8">
              <div className="p-3 rounded-full bg-slate-500/10">
                  <Eye className="w-8 h-8 text-slate-500" />
              </div>
              <div>
                  <h1 className="text-3xl font-bold tracking-tight">巡视哨兵 工作台</h1>
                  <p className="text-muted-foreground mt-1">
                    实时视频监控分析。负责表计读数、安全帽佩戴检测、异物入侵报警。
                  </p>
              </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Task Area */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <Zap className="w-5 h-5 text-slate-500" />
                  <span>核心能力 (Core Capabilities)</span>
                </CardTitle>
                <CardDescription>选择一项能力开始任务，或直接在下方输入指令。</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  
                  <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors">
                    <h4 className="font-medium text-sm mb-1">实时监控 (Real-time Monitoring)</h4>
                    <p className="text-xs text-muted-foreground">接入视频流，实时检测异常情况。</p>
                  </div>
                  <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors">
                    <h4 className="font-medium text-sm mb-1">表计识别 (Meter Reading)</h4>
                    <p className="text-xs text-muted-foreground">自动识别各类仪表读数，并记录归档。</p>
                  </div>
                  <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors">
                    <h4 className="font-medium text-sm mb-1">安防检测 (Security Detection)</h4>
                    <p className="text-xs text-muted-foreground">检测人员穿戴合规性、非法入侵等安全隐患。</p>
                  </div>
                </div>
                <Separator />
                <div className="space-y-2">
                    <h3 className="text-sm font-medium">任务指令</h3>
                    <Textarea 
                        placeholder="例如：检查 2 号主变区域的监控视频，确认是否有人员未佩戴安全帽。"
                        rows={4}
                    />
                </div>
                <Button 
                    onClick={handleStartTask} 
                    className="w-full"
                >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    发送指令
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
                  <h3 className="text-sm font-medium">上下文检索</h3>
                  <Button variant="outline" className="w-full justify-start">
                    <Search className="w-4 h-4 mr-2" />
                    搜索相关文档
                  </Button>
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
        </div>
      </PageContent>
    </PageContainer>
  );
}