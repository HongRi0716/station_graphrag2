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
import {
    ClipboardCheck,
    FileText,
    PenTool,
    Wand2,
} from 'lucide-react';
import { useTranslations } from 'next-intl';

export default function ScribeWorkspacePage() {
    const t = useTranslations('sidebar_workspace');
    const [inputContent, setInputContent] = useState('');
    const [generatedDoc, setGeneratedDoc] = useState<string | null>(null);

    const handleGenerate = () => {
        if (!inputContent.trim()) return;

        let doc = '';
        if (inputContent.includes('缺陷')) {
            doc = `【缺陷单】\n设备：2号主变\n现象：${inputContent}\n等级：一般\n处理建议：建议停电检修。`;
        } else {
            doc = `【巡视记录】\n时间：${new Date().toLocaleString()}\n内容：${inputContent}\n结论：正常`;
        }
        setGeneratedDoc(doc);
    };

    return (
        <PageContainer>
            <PageHeader
                breadcrumbs={[
                    { title: t('agents'), href: '/workspace/agents' },
                    { title: '文书专员 (Scribe) 工作台' },
                ]}
            />
            <PageContent>
                <div className="space-y-6">
                    <div className="flex items-center space-x-4">
                        <div className="rounded-full bg-purple-500/10 p-3">
                            <PenTool className="h-8 w-8 text-purple-500" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">
                                文书专员 (Scribe) 工作台
                            </h1>
                            <p className="text-muted-foreground mt-1">
                                负责将自然语言整理为标准化的运维记录、工作票或缺陷单。
                            </p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center space-x-2 text-lg">
                                    <ClipboardCheck className="h-5 w-5" />
                                    <span>原始记录输入</span>
                                </CardTitle>
                                <CardDescription>
                                    输入口语化的巡视情况或缺陷描述。
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="input">内容描述</Label>
                                    <Textarea
                                        id="input"
                                        placeholder="例如：2号主变风冷系统有异响..."
                                        className="min-h-[200px]"
                                        value={inputContent}
                                        onChange={(e) => setInputContent(e.target.value)}
                                    />
                                </div>
                            </CardContent>
                            <CardFooter>
                                <Button
                                    className="w-full bg-purple-600 hover:bg-purple-700"
                                    onClick={handleGenerate}
                                    disabled={!inputContent.trim()}
                                >
                                    <Wand2 className="mr-2 h-4 w-4" />
                                    生成标准化文档
                                </Button>
                            </CardFooter>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center space-x-2 text-lg">
                                    <FileText className="h-5 w-5" />
                                    <span>生成结果</span>
                                </CardTitle>
                                <CardDescription>
                                    标准化格式文档预览。
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {!generatedDoc ? (
                                    <div className="flex h-[200px] items-center justify-center rounded-md border border-dashed bg-muted/30">
                                        <p className="text-muted-foreground text-sm">
                                            等待生成...
                                        </p>
                                    </div>
                                ) : (
                                    <div className="rounded-md border bg-muted/30 p-4 font-mono text-sm whitespace-pre-wrap">
                                        {generatedDoc}
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
