'use client';

import { useState } from 'react';
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
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  Database,
  FileText,
  Library,
  MessageSquare,
  Search,
  Share2,
  Loader2,
  Brain,
  ChevronRight,
  ChevronDown
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useAppContext } from '@/components/providers/app-provider';
import { agentAPI, ArchivistResponse, ThinkingStep } from '@/lib/api/agents';
import { toast } from 'sonner';

export default function ArchivistWorkspacePage() {
  const t = useTranslations('sidebar_workspace');
  const { user } = useAppContext();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ArchivistResponse | null>(null);
  const [showThinking, setShowThinking] = useState(true);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setResult(null);
    try {
      const response = await agentAPI.searchKnowledge({
        query,
        user_id: user?.id || 'user-1', // Use actual user ID or fallback
        search_type: 'hybrid',
      });
      setResult(response);
    } catch (error) {
      console.error('Search failed:', error);
      toast.error('检索失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // Mock Stats (Keep these for initial view)
  const stats = [
    {
      label: '文档总数',
      value: '12,450',
      icon: FileText,
      color: 'text-blue-500',
    },
    {
      label: '图谱节点',
      value: '89,302',
      icon: Share2,
      color: 'text-purple-500',
    },
    {
      label: '知识条目',
      value: '256,000',
      icon: Database,
      color: 'text-amber-500',
    },
  ];

  // Mock Recent Docs
  const recentDocs = [
    { title: '110kV变电站运行规程 V2.0', type: '规程', date: '2小时前' },
    { title: '#2主变出厂试验报告.pdf', type: '报告', date: '5小时前' },
    { title: '2024年度第一季度检修计划', type: '计划', date: '1天前' },
  ];

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: '图谱专家 知识库' },
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Hero & Search Section */}
          <div className="to-background relative overflow-hidden rounded-xl border border-amber-500/20 bg-gradient-to-br from-amber-500/10 via-amber-500/5 p-8">
            <div className="relative z-10">
              <div className="mb-6 flex items-center space-x-4">
                <div className="rounded-xl bg-amber-500/20 p-3 backdrop-blur-sm">
                  <Library className="h-8 w-8 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">
                    图谱专家 The Archivist
                  </h1>
                  <p className="text-muted-foreground mt-1">
                    全知全能的知识管家。支持跨文档、数据库和知识图谱的深度语义检索。
                  </p>
                </div>
              </div>

              {/* Main Search Bar */}
              <div className="bg-background flex max-w-3xl gap-2 rounded-lg border p-1 shadow-lg">
                <div className="relative flex-1">
                  <Search className="text-muted-foreground absolute top-3 left-3 h-5 w-5" />
                  <Input
                    placeholder="搜索设备台账、历史缺陷、检修方案..."
                    className="h-11 border-0 pl-10 text-base focus-visible:ring-0"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyPress}
                  />
                </div>
                <Button
                  onClick={handleSearch}
                  disabled={loading || !query.trim()}
                  className="h-11 bg-amber-600 px-8 font-medium text-white hover:bg-amber-700"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      搜索中
                    </>
                  ) : (
                    '深度搜索'
                  )}
                </Button>
              </div>
              <div className="text-muted-foreground mt-4 flex gap-4 text-sm">
                <span>热门搜索:</span>
                <span
                  className="cursor-pointer underline underline-offset-4 hover:text-amber-600"
                  onClick={() => setQuery('#1主变油温')}
                >
                  #1主变油温
                </span>
                <span
                  className="cursor-pointer underline underline-offset-4 hover:text-amber-600"
                  onClick={() => setQuery('GIS局放')}
                >
                  GIS局放
                </span>
                <span
                  className="cursor-pointer underline underline-offset-4 hover:text-amber-600"
                  onClick={() => setQuery('倒闸操作票')}
                >
                  倒闸操作票
                </span>
              </div>
            </div>
          </div>

          {/* Results Section */}
          {result && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* Thinking Stream */}
              {result.thinking_stream && result.thinking_stream.length > 0 && (
                <Card className="border-blue-100 bg-blue-50/50 dark:border-blue-900/50 dark:bg-blue-900/10">
                  <CardHeader className="pb-2">
                    <div
                      className="flex items-center justify-between cursor-pointer"
                      onClick={() => setShowThinking(!showThinking)}
                    >
                      <CardTitle className="flex items-center text-base text-blue-700 dark:text-blue-400">
                        <Brain className="mr-2 h-5 w-5" />
                        思考过程
                      </CardTitle>
                      {showThinking ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </div>
                  </CardHeader>
                  {showThinking && (
                    <CardContent className="space-y-3 pt-0">
                      {result.thinking_stream.map((step, index) => (
                        <div key={index} className="flex items-start gap-3 text-sm">
                          <Badge variant="secondary" className="mt-0.5 shrink-0 bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/40 dark:text-blue-300">
                            {step.step_type}
                          </Badge>
                          <span className="text-muted-foreground">{step.description}</span>
                        </div>
                      ))}
                    </CardContent>
                  )}
                </Card>
              )}

              {/* Answer */}
              {result.answer && (
                <Card className="border-amber-200 bg-amber-50/30 dark:border-amber-900/30 dark:bg-amber-900/5">
                  <CardHeader>
                    <CardTitle className="flex items-center text-lg">
                      <MessageSquare className="mr-2 h-5 w-5 text-amber-600" />
                      回答
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div
                      className="prose prose-amber dark:prose-invert max-w-none"
                      dangerouslySetInnerHTML={{ __html: result.answer }}
                    />
                  </CardContent>
                </Card>
              )}

              {/* Documents */}
              {result.documents && result.documents.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold flex items-center">
                    <FileText className="mr-2 h-5 w-5" />
                    参考文档 ({result.documents.length})
                  </h3>
                  <div className="grid gap-4 md:grid-cols-2">
                    {result.documents.map((doc: any, index: number) => (
                      <Card key={index} className="hover:shadow-md transition-shadow">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-base font-medium line-clamp-1" title={doc.title}>
                            {doc.title || '未知文档'}
                          </CardTitle>
                          <CardDescription className="flex items-center justify-between text-xs">
                            <span>{doc.source || '知识库'}</span>
                            <span>{doc.timestamp || doc.date}</span>
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <p className="text-sm text-muted-foreground line-clamp-3">
                            {doc.content}
                          </p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Initial Dashboard (Hide when searching/showing results) */}
          {!result && !loading && (
            <>
              {/* Stats Grid */}
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {stats.map((stat) => (
                  <Card
                    key={stat.label}
                    className="border-amber-100 dark:border-amber-900/50"
                  >
                    <CardContent className="flex items-center justify-between p-6">
                      <div>
                        <p className="text-muted-foreground text-sm font-medium">
                          {stat.label}
                        </p>
                        <p className="mt-1 text-2xl font-bold">{stat.value}</p>
                      </div>
                      <div
                        className={`bg-secondary rounded-full p-3 ${stat.color.replace('text-', 'bg-').replace('500', '100')} dark:bg-secondary`}
                      >
                        <stat.icon className={`h-6 w-6 ${stat.color}`} />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                {/* Left Column: Advanced Query */}
                <div className="space-y-6 lg:col-span-2">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center text-lg">
                        <MessageSquare className="mr-2 h-5 w-5 text-amber-500" />
                        高级咨询 (Advanced Inquiry)
                      </CardTitle>
                      <CardDescription>
                        针对复杂问题进行多跳推理和跨库查询。
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <Textarea
                        placeholder="例如：请列出 110kV 西区变电站所有服役超过 10 年的隔离开关，并汇总它们近三年的缺陷记录。"
                        className="min-h-[120px] resize-none text-base focus-visible:ring-amber-500"
                      />
                      <div className="flex items-center justify-between">
                        <div className="flex gap-2">
                          <Badge
                            variant="outline"
                            className="hover:bg-secondary cursor-pointer"
                          >
                            包含图纸
                          </Badge>
                          <Badge
                            variant="outline"
                            className="hover:bg-secondary cursor-pointer"
                          >
                            包含报告
                          </Badge>
                        </div>
                        <Button
                          onClick={() => toast.info('高级咨询功能即将上线')}
                          variant="outline"
                          className="border-amber-500 text-amber-600 hover:bg-amber-50"
                        >
                          提交咨询
                        </Button>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <Card className="bg-muted/30 border-dashed">
                      <CardContent className="hover:bg-muted/50 flex cursor-pointer flex-col items-center justify-center space-y-2 p-6 text-center transition-colors">
                        <BookOpen className="text-muted-foreground h-8 w-8" />
                        <h3 className="font-medium">知识图谱浏览器</h3>
                        <p className="text-muted-foreground text-xs">
                          可视化查看设备拓扑与关联关系
                        </p>
                      </CardContent>
                    </Card>
                    <Card className="bg-muted/30 border-dashed">
                      <CardContent className="hover:bg-muted/50 flex cursor-pointer flex-col items-center justify-center space-y-2 p-6 text-center transition-colors">
                        <Database className="text-muted-foreground h-8 w-8" />
                        <h3 className="font-medium">数据源管理</h3>
                        <p className="text-muted-foreground text-xs">
                          管理已接入的 12 个数据源
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                </div>

                {/* Right Column: Recent & Context */}
                <div className="space-y-6">
                  {/* Recent Updates */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center text-lg">
                        <Activity className="text-primary mr-2 h-5 w-5" />
                        最近接入 (Recent Ingestions)
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-0 px-0">
                      {recentDocs.map((doc, i) => (
                        <div
                          key={i}
                          className="hover:bg-muted/50 flex cursor-pointer items-center justify-between border-b px-6 py-3 last:border-0"
                        >
                          <div className="flex items-center gap-3 overflow-hidden">
                            <div className="rounded bg-blue-50 p-2 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">
                              <FileText className="h-4 w-4" />
                            </div>
                            <div className="min-w-0">
                              <p className="truncate text-sm font-medium">
                                {doc.title}
                              </p>
                              <p className="text-muted-foreground text-xs">
                                {doc.type}
                              </p>
                            </div>
                          </div>
                          <span className="text-muted-foreground text-xs whitespace-nowrap">
                            {doc.date}
                          </span>
                        </div>
                      ))}
                      <div className="p-4 pt-2">
                        <Button
                          variant="ghost"
                          className="text-muted-foreground w-full text-xs"
                        >
                          查看全部 <ArrowUpRight className="ml-1 h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </>
          )}
        </div>
      </PageContent>
    </PageContainer>
  );
}
