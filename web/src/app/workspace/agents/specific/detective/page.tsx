"use client";

import { PageContainer, PageHeader, PageContent } from "@/components/page-container";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileUp, Search, Layers, Diff, Zap, FileSearch } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { useTranslations } from "next-intl";

// Mock Component for File Upload/Display
const DrawingUploadSlot = ({ version, fileName }: { version: string, fileName?: string }) => (
  <div className="flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-lg h-40 bg-background/50 hover:bg-muted/30 transition-colors">
    <FileUp className="w-8 h-8 text-muted-foreground mb-2" />
    <p className="text-sm font-medium text-muted-foreground">{version}</p>
    {fileName ? (
      <span className="text-xs text-primary font-mono mt-1">{fileName}</span>
    ) : (
      <span className="text-xs text-muted-foreground mt-1">点击上传图纸文件</span>
    )}
  </div>
);


export default function DetectiveWorkspacePage() {
  const t = useTranslations("sidebar_workspace"); 

  const handleStartAnalysis = () => {
    // 实际逻辑：收集文件和指令，调用 Detective Agent 的专用 API
    alert("开始图纸对比分析... (调用 Detective Agent API)"); 
  };

  return (
    <PageContainer>
      <PageHeader 
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: `${t('agent_detective')} 工作台` }
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Header Section (Visual Title) */}
          <div className="flex items-center space-x-4 mb-8">
              <div className="p-3 rounded-full bg-purple-500/10">
                  <FileSearch className="w-8 h-8 text-purple-500" />
              </div>
              <div>
                  <h1 className="text-3xl font-bold tracking-tight">{t('agent_detective')} 工作台</h1>
                  <p className="text-muted-foreground mt-1">
                    专用工作区，用于执行图纸识别、拓扑提取和多版本对比任务。
                  </p>
              </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Column 1 & 2: Drawing Comparison View */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <Diff className="w-5 h-5 text-purple-500" />
                  <span>图纸版本对比 (Diff Analysis)</span>
                </CardTitle>
                <CardDescription>上传两份图纸（例如：设计稿 vs 竣工稿）进行结构化差异分析。</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <DrawingUploadSlot version="图纸 A (基准版本)" fileName="B5391S_V1.0.pdf" />
                  <DrawingUploadSlot version="图纸 B (待对比版本)" fileName="B5391S_V2.1.pdf" />
                </div>
                <Separator />
                <div className="space-y-2">
                    <h3 className="text-sm font-medium">任务指令</h3>
                    <Textarea 
                        placeholder="例如：请对比两张图纸中，110kV 侧隔离开关的数量是否有变化，并提取拓扑差异。"
                        rows={4}
                    />
                </div>
                <Button 
                    onClick={handleStartAnalysis} 
                    className="w-full bg-purple-600 hover:bg-purple-700"
                >
                    <Search className="w-4 h-4 mr-2" />
                    开始结构化对比
                </Button>
              </CardContent>
            </Card>

            {/* Column 3: Quick Tools/Chat Integration */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-lg flex items-center space-x-2">
                  <Layers className="w-5 h-5 text-primary" />
                  <span>快速工具与问答</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">拓扑查询</h3>
                  <Input placeholder="输入设备 ID (如 L101) 查找连接关系..." />
                  <Button variant="secondary" className="w-full">
                    查询拓扑信息
                  </Button>
                </div>
                <Separator />
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">图像问答 (VQA)</h3>
                  <Textarea 
                    placeholder="针对上传的图纸提问 (例如：图中变压器的型号是什么?)"
                    rows={3}
                  />
                  <Button variant="outline" className="w-full">
                    <Zap className="w-4 h-4 mr-2" />
                    提交 VQA 任务
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </PageContent>
    </PageContainer>
  );
}
