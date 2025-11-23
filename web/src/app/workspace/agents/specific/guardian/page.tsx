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
import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react';
import { useTranslations } from 'next-intl';

export default function GuardianWorkspacePage() {
    const t = useTranslations('sidebar_workspace');
    const [inputContent, setInputContent] = useState('');
    const [generatedPlan, setGeneratedPlan] = useState<string | null>(null);

    const handleGenerate = () => {
        if (!inputContent.trim()) return;

        // Mock generation logic
        const plan = `【保电方案】
任务名称：${inputContent}
保电等级：一级
组织措施：
1. 成立保电领导小组，由站长任组长。
2. 安排双人24小时值班。
技术措施：
1. 提前对全站设备进行红外测温。
2. 检查事故照明及消防设施完好。
3. 停止一切非紧急检修工作。
应急预案：
如遇主变跳闸，立即启用备用变压器，优先保障重要负荷供电。`;
        setGeneratedPlan(plan);
    };

    return (
        <PageContainer>
            <PageHeader
                breadcrumbs={[
                    { title: t('agents'), href: '/workspace/agents' },
                    { title: '守护者 (Guardian) 工作台' },
                ]}
            />
            <PageContent>
                <div className="space-y-6">
                    <div className="flex items-center space-x-4">
                        <div className="rounded-full bg-emerald-500/10 p-3">
                            <Shield className="h-8 w-8 text-emerald-500" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">
                                守护者 (Guardian) 工作台
                            </h1>
                            <p className="text-muted-foreground mt-1">
                                针对重大活动或特殊天气，生成专项保电方案和应急预案。
                            </p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center space-x-2 text-lg">
                                    <ShieldAlert className="h-5 w-5" />
                                    <span>保电任务输入</span>
                                </CardTitle>
                                <CardDescription>
                                    输入保电任务名称、时间、重要程度及特殊要求。
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="input">任务详情</Label>
                                    <Textarea
                                        id="input"
                                        placeholder="例如：2024年国庆节期间保电，重点保障政府机关及医院供电..."
                                        className="min-h-[200px]"
                                        value={inputContent}
                                        onChange={(e) => setInputContent(e.target.value)}
                                    />
                                </div>
                            </CardContent>
                            <CardFooter>
                                <Button
                                    className="w-full bg-emerald-600 hover:bg-emerald-700"
                                    onClick={handleGenerate}
                                    disabled={!inputContent.trim()}
                                >
                                    <ShieldCheck className="mr-2 h-4 w-4" />
                                    生成保电方案
                                </Button>
                            </CardFooter>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center space-x-2 text-lg">
                                    <Shield className="h-5 w-5" />
                                    <span>生成结果</span>
                                </CardTitle>
                                <CardDescription>
                                    AI 生成的标准化保电方案。
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {!generatedPlan ? (
                                    <div className="flex h-[200px] items-center justify-center rounded-md border border-dashed bg-muted/30">
                                        <p className="text-muted-foreground text-sm">
                                            等待生成...
                                        </p>
                                    </div>
                                ) : (
                                    <div className="rounded-md border bg-muted/30 p-4 font-mono text-sm whitespace-pre-wrap">
                                        {generatedPlan}
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
