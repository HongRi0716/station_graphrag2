'use client';

import { useState } from 'react';

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
    CardFooter,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { BrainCircuit, FileWarning, Sparkles } from 'lucide-react';
import { useTranslations } from 'next-intl';

export default function ProphetWorkspacePage() {
    const t = useTranslations('sidebar_workspace');
    const [inputContent, setInputContent] = useState('');
    const [generatedReport, setGeneratedReport] = useState<string | null>(null);

    const handleGenerate = () => {
        if (!inputContent.trim()) return;

        // Mock generation logic
        const report = `【事故预想报告】
场景描述：${inputContent}
风险等级：高
可能后果：
1. 导致主变过载跳闸。
2. 造成下游用户停电。
应对措施：
1. 密切监视负荷变化。
2. 检查备用电源自投装置状态。
3. 做好负荷转供准备。`;
        setGeneratedReport(report);
    };

    return (
        <PageContainer>
            <PageHeader
                breadcrumbs={[
                    { title: t('agents'), href: '/workspace/agents' },
                    { title: '预言家 (Prophet) 工作台' },
                ]}
            />
            <PageContent>
                <div className="space-y-6">
                    <div className="flex items-center space-x-4">
                        <div className="rounded-full bg-indigo-500/10 p-3">
                            <BrainCircuit className="h-8 w-8 text-indigo-500" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">
                                预言家 (Prophet) 工作台
                            </h1>
                            <p className="text-muted-foreground mt-1">
                                基于当前运行方式和设备状态，生成事故预想报告和风险分析。
                            </p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center space-x-2 text-lg">
                                    <FileWarning className="h-5 w-5" />
                                    <span>运行场景输入</span>
                                </CardTitle>
                                <CardDescription>
                                    描述当前的电网运行方式、检修计划或异常信号。
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="input">场景描述</Label>
                                    <Textarea
                                        id="input"
                                        placeholder="例如：2号主变计划检修，1号主变带全站负荷运行..."
                                        className="min-h-[200px]"
                                        value={inputContent}
                                        onChange={(e) => setInputContent(e.target.value)}
                                    />
                                </div>
                            </CardContent>
                            <CardFooter>
                                <Button
                                    className="w-full bg-indigo-600 hover:bg-indigo-700"
                                    onClick={handleGenerate}
                                    disabled={!inputContent.trim()}
                                >
                                    <Sparkles className="mr-2 h-4 w-4" />
                                    生成预想报告
                                </Button>
                            </CardFooter>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center space-x-2 text-lg">
                                    <BrainCircuit className="h-5 w-5" />
                                    <span>分析结果</span>
                                </CardTitle>
                                <CardDescription>
                                    AI 生成的事故预想与风险管控措施。
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {!generatedReport ? (
                                    <div className="flex h-[200px] items-center justify-center rounded-md border border-dashed bg-muted/30">
                                        <p className="text-muted-foreground text-sm">
                                            等待分析...
                                        </p>
                                    </div>
                                ) : (
                                    <div className="rounded-md border bg-muted/30 p-4 font-mono text-sm whitespace-pre-wrap">
                                        {generatedReport}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </PageContent>
        </PageContainer>
    );
}
