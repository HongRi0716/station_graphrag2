"use client";

import { PageContainer, PageHeader, PageContent } from "@/components/page-container";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity, Search, Layers, Zap, MessageSquare } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { useTranslations } from "next-intl";

export default function DiagnosticianWorkspacePage() {
  const t = useTranslations("sidebar_workspace"); 

  const handleStartTask = () => {
    alert("任务已提交给 The Diagnostician (调用 Agent API)"); 
  };

  return (
    <PageContainer>
      <PageHeader 
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: "故障诊断师 工作台" }
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Header Section */}
          <div className="flex items-center space-x-4 mb-8">
              <div className="p-3 rounded-full bg-red-600/10">
                  <Activity className="w-8 h-8 text-red-600" />
              </div>
              <div>
                  <h1 className="text-3xl font-bold tracking-tight">故障诊断师 工作台</h1>
                  <p className="text-muted-foreground mt-1">
                    深度故障分析专家。解析录波文件与SOE日志，推演事故因果链。
                  </p>
              </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Task Area */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <Zap className="w-5 h-5 text-red-600" />
                  <span>核心能力 (Core Capabilities)</span>
                </CardTitle>
                <CardDescription>选择一项能力开始任务，或直接在下方输入指令。</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  
                  <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors">
                    <h4 className="font-medium text-sm mb-1">录波分析 (Waveform Analysis)</h4>
                    <p className="text-xs text-muted-foreground">解析故障录波文件，分析电气量变化。</p>
                  </div>
                  <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors">
                    <h4 className="font-medium text-sm mb-1">SOE推理 (SOE Reasoning)</h4>
                    <p className="text-xs text-muted-foreground">基于 SOE 记录推断事故发生顺序和原因。</p>
                  </div>
                  <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors">
                    <h4 className="font-medium text-sm mb-1">事故报告 (Accident Report)</h4>
                    <p className="text-xs text-muted-foreground">自动生成详细的事故分析报告。</p>
                  </div>
                </div>
                <Separator />
                <div className="space-y-2">
                    <h3 className="text-sm font-medium">任务指令</h3>
                    <Textarea 
                        placeholder="例如：分析上传的录波文件，判断故障类型和故障点位置。"
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