"use client";

import { PageContainer, PageHeader, PageContent } from "@/components/page-container";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GraduationCap, Search, Layers, Zap, MessageSquare } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { useTranslations } from "next-intl";

export default function InstructorWorkspacePage() {
  const t = useTranslations("sidebar_workspace"); 

  const handleStartTask = () => {
    alert("任务已提交给 The Instructor (调用 Agent API)"); 
  };

  return (
    <PageContainer>
      <PageHeader 
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: "培训教官 工作台" }
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Header Section */}
          <div className="flex items-center space-x-4 mb-8">
              <div className="p-3 rounded-full bg-indigo-500/10">
                  <GraduationCap className="w-8 h-8 text-indigo-500" />
              </div>
              <div>
                  <h1 className="text-3xl font-bold tracking-tight">培训教官 工作台</h1>
                  <p className="text-muted-foreground mt-1">
                    技能培训与考核系统。模拟倒闸操作演练，进行苏格拉底式教学。
                  </p>
              </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Task Area */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <Zap className="w-5 h-5 text-indigo-500" />
                  <span>核心能力 (Core Capabilities)</span>
                </CardTitle>
                <CardDescription>选择一项能力开始任务，或直接在下方输入指令。</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  
                  <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors">
                    <h4 className="font-medium text-sm mb-1">模拟演练 (Simulation Drills)</h4>
                    <p className="text-xs text-muted-foreground">提供虚拟环境进行倒闸操作演练。</p>
                  </div>
                  <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors">
                    <h4 className="font-medium text-sm mb-1">智能评分 (AI Grading)</h4>
                    <p className="text-xs text-muted-foreground">根据操作规范自动评估学员表现。</p>
                  </div>
                  <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors">
                    <h4 className="font-medium text-sm mb-1">安规问答 (Safety Q&A)</h4>
                    <p className="text-xs text-muted-foreground">解答关于安全规程的疑问，进行互动式教学。</p>
                  </div>
                </div>
                <Separator />
                <div className="space-y-2">
                    <h3 className="text-sm font-medium">任务指令</h3>
                    <Textarea 
                        placeholder="例如：我想进行一次 110kV 线路停电操作的模拟演练。"
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