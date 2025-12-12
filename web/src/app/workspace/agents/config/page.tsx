'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { PageContainer, PageHeader, PageContent } from '@/components/page-container';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
    Settings,
    Database,
    Save,
    Loader2,
    Bot,
    Search,
    Plus,
    X,
    ChevronRight,
    ChevronDown,
    Info,
    FileText,
    FolderOpen,
    Folder
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { toast } from 'sonner';
import {
    agentConfigAPI,
    AgentConfig,
    CollectionBinding
} from '@/lib/api/agents';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

// 智能体图标映射
const AGENT_ICONS: Record<string, string> = {
    supervisor: '👨‍✈️',
    archivist: '📚',
    accident_deduction: '⚡',
    operation_ticket: '📋',
    work_permit: '🎫',
    power_guarantee: '🛡️',
    diagnostician: '🔍',
    calculator: '🧮',
    detective: '🔎',
    gatekeeper: '🚪',
    prophet: '🔮',
    auditor: '📝',
    scribe: '✍️',
    instructor: '👨‍🏫'
};

// 智能体颜色映射
const AGENT_COLORS: Record<string, string> = {
    supervisor: 'yellow',
    archivist: 'amber',
    accident_deduction: 'pink',
    operation_ticket: 'blue',
    work_permit: 'green',
    power_guarantee: 'emerald',
    diagnostician: 'purple',
    calculator: 'orange',
    detective: 'cyan',
    gatekeeper: 'red',
    prophet: 'violet',
    auditor: 'gray',
    scribe: 'lime',
    instructor: 'teal'
};

// 树节点类型
interface TreeNode {
    id: string;
    label: string;
    type: 'collection' | 'document';
    children?: TreeNode[];
    description?: string;
}

interface CollectionOption {
    id: string;
    title: string;
    description?: string;
    type?: string;
}

// 树形项组件
const TreeItem = ({
    node,
    level = 0,
    selectedIds,
    onToggle,
    expandedIds,
    toggleExpand,
}: {
    node: TreeNode;
    level?: number;
    selectedIds: Set<string>;
    onToggle: (id: string, type: 'collection' | 'document') => void;
    expandedIds: Set<string>;
    toggleExpand: (id: string) => void;
}) => {
    const isExpanded = expandedIds.has(node.id);
    const isSelected = selectedIds.has(node.id);
    const hasChildren = node.children && node.children.length > 0;

    return (
        <div className="w-full">
            <div
                className={cn(
                    'flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors cursor-pointer',
                    isSelected
                        ? 'bg-primary/10 border border-primary/30'
                        : 'hover:bg-muted/50 border border-transparent'
                )}
                style={{ paddingLeft: `${level * 16 + 8}px` }}
            >
                {/* 展开/折叠按钮 */}
                <div
                    className={cn(
                        'flex h-5 w-5 items-center justify-center rounded hover:bg-black/10 dark:hover:bg-white/10',
                        !hasChildren && 'invisible'
                    )}
                    onClick={(e) => {
                        e.stopPropagation();
                        toggleExpand(node.id);
                    }}
                >
                    {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                    ) : (
                        <ChevronRight className="h-4 w-4" />
                    )}
                </div>

                {/* 复选框 */}
                <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => onToggle(node.id, node.type)}
                    className="h-4 w-4"
                />

                {/* 图标 */}
                {node.type === 'collection' ? (
                    isExpanded ? (
                        <FolderOpen className="h-4 w-4 shrink-0 text-blue-500" />
                    ) : (
                        <Folder className="h-4 w-4 shrink-0 text-blue-500" />
                    )
                ) : (
                    <FileText className="h-4 w-4 shrink-0 text-green-500" />
                )}

                {/* 标签 */}
                <span
                    className="truncate flex-1 cursor-pointer"
                    onClick={() => onToggle(node.id, node.type)}
                >
                    {node.label}
                </span>

                {/* 类型标签 */}
                <Badge variant="outline" className="text-xs shrink-0">
                    {node.type === 'collection' ? '集合' : '文件'}
                </Badge>

                {isSelected && (
                    <Badge variant="default" className="text-xs shrink-0">
                        已选
                    </Badge>
                )}
            </div>

            {/* 子节点 */}
            {isExpanded && hasChildren && (
                <div>
                    {node.children!.map((child) => (
                        <TreeItem
                            key={child.id}
                            node={child}
                            level={level + 1}
                            selectedIds={selectedIds}
                            onToggle={onToggle}
                            expandedIds={expandedIds}
                            toggleExpand={toggleExpand}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

export default function AgentConfigPage() {
    const t = useTranslations('sidebar_workspace');
    const searchParams = useSearchParams();
    const initialAgentId = searchParams.get('agent');

    const [agents, setAgents] = useState<AgentConfig[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<AgentConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [collections, setCollections] = useState<CollectionOption[]>([]);
    const [selectedCollections, setSelectedCollections] = useState<string[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [dialogOpen, setDialogOpen] = useState(false);
    const [collectionsLoading, setCollectionsLoading] = useState(false);

    // 树形结构状态
    const [treeData, setTreeData] = useState<TreeNode[]>([]);
    const [expandedTreeIds, setExpandedTreeIds] = useState<Set<string>>(new Set());
    const [selectedTreeIds, setSelectedTreeIds] = useState<Set<string>>(new Set());

    // 加载智能体列表
    useEffect(() => {
        loadAgents();
        loadTreeData();
    }, []);

    // 当初始智能体ID存在且智能体列表加载完成后，选中对应的智能体
    useEffect(() => {
        if (initialAgentId && agents.length > 0 && !selectedAgent) {
            const targetAgent = agents.find(a => a.role === initialAgentId);
            if (targetAgent) {
                setSelectedAgent(targetAgent);
                setSelectedCollections(targetAgent.collections.map(c => c.collection_id));
                setSelectedTreeIds(new Set(targetAgent.collections.map(c => c.collection_id)));
            }
        }
    }, [initialAgentId, agents]);

    const loadAgents = async () => {
        try {
            setLoading(true);
            const response = await agentConfigAPI.listAgentConfigs();
            if (response.success) {
                setAgents(response.agents);
                if (response.agents.length > 0 && !selectedAgent) {
                    setSelectedAgent(response.agents[0]);
                    setSelectedCollections(
                        response.agents[0].collections.map(c => c.collection_id)
                    );
                    setSelectedTreeIds(new Set(response.agents[0].collections.map(c => c.collection_id)));
                }
            }
        } catch (error) {
            console.error('Failed to load agents:', error);
            toast.error('加载智能体列表失败');
        } finally {
            setLoading(false);
        }
    };

    // 加载树形数据（集合和文档）
    const loadTreeData = async () => {
        try {
            setCollectionsLoading(true);

            // 使用 graphs/hierarchy/global API 获取集合和文档层级
            const response = await fetch('/api/v1/graphs/hierarchy/global', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: '', top_k: 10000, include_entities: false }),
            });

            if (response.ok) {
                const data = await response.json();
                const nodes = data.nodes || [];
                const edges = data.edges || [];

                const collectionNodes = nodes.filter((n: any) => n.type === 'collection');
                const documentNodes = nodes.filter((n: any) => n.type === 'document');

                // 构建树形结构
                const tree: TreeNode[] = collectionNodes.map((col: any) => {
                    const colId = col.id;
                    const childDocs = edges
                        .filter((e: any) => e.source === colId && e.type === 'CONTAINS')
                        .map((e: any) => {
                            const docNode = documentNodes.find((d: any) => d.id === e.target);
                            return docNode ? {
                                id: docNode.id,
                                label: docNode.name || docNode.id,
                                type: 'document' as const,
                                description: docNode.description
                            } : null;
                        })
                        .filter(Boolean) as TreeNode[];

                    return {
                        id: colId,
                        label: col.name || colId,
                        type: 'collection' as const,
                        children: childDocs,
                        description: col.description
                    };
                });

                setTreeData(tree);
                // 默认展开所有集合
                setExpandedTreeIds(new Set(tree.map(t => t.id)));

                // 同时设置 collections 列表（兼容旧的显示方式）
                const collectionOptions: CollectionOption[] = tree.map(col => ({
                    id: col.id,
                    title: col.label,
                    description: col.description,
                    type: 'collection'
                }));
                setCollections(collectionOptions);
            } else {
                // 回退到简单 API
                const simpleResponse = await agentConfigAPI.getAvailableCollections();
                if (simpleResponse.success && simpleResponse.collections) {
                    const tree: TreeNode[] = simpleResponse.collections.map(col => ({
                        id: col.id,
                        label: col.title,
                        type: 'collection' as const,
                        children: [],
                        description: col.description
                    }));
                    setTreeData(tree);
                    setExpandedTreeIds(new Set(tree.map(t => t.id)));
                    setCollections(simpleResponse.collections.map(col => ({
                        id: col.id,
                        title: col.title,
                        description: col.description,
                        type: col.type
                    })));
                }
            }
        } catch (error) {
            console.error('Failed to load tree data:', error);
            setTreeData([]);
            setCollections([]);
        } finally {
            setCollectionsLoading(false);
        }
    };

    // 切换树节点选择
    const handleTreeToggle = useCallback((id: string, type: 'collection' | 'document') => {
        setSelectedTreeIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) {
                next.delete(id);
            } else {
                next.add(id);
            }
            return next;
        });
        // 同步更新 selectedCollections
        setSelectedCollections(prev => {
            if (prev.includes(id)) {
                return prev.filter(x => x !== id);
            } else {
                return [...prev, id];
            }
        });
    }, []);

    // 切换树节点展开
    const toggleTreeExpand = useCallback((id: string) => {
        setExpandedTreeIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) {
                next.delete(id);
            } else {
                next.add(id);
            }
            return next;
        });
    }, []);

    const handleSelectAgent = (agent: AgentConfig) => {
        setSelectedAgent(agent);
        setSelectedCollections(agent.collections.map(c => c.collection_id));
    };

    const handleToggleCollection = (collectionId: string) => {
        setSelectedCollections(prev =>
            prev.includes(collectionId)
                ? prev.filter(id => id !== collectionId)
                : [...prev, collectionId]
        );
    };

    const handleSaveCollections = async () => {
        if (!selectedAgent) return;

        try {
            setSaving(true);
            const response = await agentConfigAPI.updateAgentCollections(
                selectedAgent.role,
                selectedCollections
            );

            if (response.success) {
                toast.success('知识库配置已更新');
                // 更新本地状态
                setAgents(prev => prev.map(a =>
                    a.role === selectedAgent.role
                        ? { ...a, collections: selectedCollections.map(id => ({ collection_id: id })) }
                        : a
                ));
            }
        } catch (error) {
            console.error('Failed to save collections:', error);
            toast.error('保存失败，请重试');
        } finally {
            setSaving(false);
        }
    };

    const filteredCollections = collections.filter(c =>
        c.title.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) {
        return (
            <PageContainer>
                <PageContent>
                    <div className="flex items-center justify-center h-64">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <span className="ml-2">加载中...</span>
                    </div>
                </PageContent>
            </PageContainer>
        );
    }

    return (
        <PageContainer>
            <PageHeader
                breadcrumbs={[
                    { title: t('agents'), href: '/workspace/agents' },
                    { title: '智能体配置' }
                ]}
            />
            <PageContent>
                <div className="space-y-6">
                    {/* Header */}
                    <div className="relative overflow-hidden rounded-xl border border-primary/20 bg-gradient-to-br from-primary/10 via-primary/5 to-background p-8">
                        <div className="relative z-10">
                            <div className="flex items-center space-x-4 mb-4">
                                <div className="p-3 rounded-full bg-primary/20 backdrop-blur-sm">
                                    <Settings className="w-8 h-8 text-primary" />
                                </div>
                                <div>
                                    <h1 className="text-3xl font-bold tracking-tight">智能体配置管理</h1>
                                    <p className="text-muted-foreground mt-1">
                                        为每个智能体配置专属知识库，提升回答的专业性和准确性
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* 左侧：智能体列表 */}
                        <Card className="lg:col-span-1">
                            <CardHeader>
                                <CardTitle className="text-lg flex items-center">
                                    <Bot className="mr-2 h-5 w-5" />
                                    智能体列表
                                </CardTitle>
                                <CardDescription>
                                    选择要配置的智能体
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                {agents.map((agent) => (
                                    <div
                                        key={agent.role}
                                        className={`p-3 rounded-lg border cursor-pointer transition-all ${selectedAgent?.role === agent.role
                                            ? 'border-primary bg-primary/5'
                                            : 'border-transparent hover:border-muted-foreground/30 hover:bg-muted/50'
                                            }`}
                                        onClick={() => handleSelectAgent(agent)}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <span className="text-2xl">
                                                    {AGENT_ICONS[agent.role] || '🤖'}
                                                </span>
                                                <div>
                                                    <h4 className="font-medium text-sm">{agent.name}</h4>
                                                    <p className="text-xs text-muted-foreground truncate max-w-[180px]">
                                                        {agent.description}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Badge variant="secondary" className="text-xs">
                                                    {agent.collections.length} 库
                                                </Badge>
                                                <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </CardContent>
                        </Card>

                        {/* 右侧：知识库配置 */}
                        <Card className="lg:col-span-2">
                            {selectedAgent ? (
                                <>
                                    <CardHeader>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <span className="text-3xl">
                                                    {AGENT_ICONS[selectedAgent.role] || '🤖'}
                                                </span>
                                                <div>
                                                    <CardTitle className="text-lg">{selectedAgent.name}</CardTitle>
                                                    <CardDescription>{selectedAgent.description}</CardDescription>
                                                </div>
                                            </div>
                                            <Button
                                                onClick={handleSaveCollections}
                                                disabled={saving}
                                            >
                                                {saving ? (
                                                    <>
                                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                        保存中...
                                                    </>
                                                ) : (
                                                    <>
                                                        <Save className="mr-2 h-4 w-4" />
                                                        保存配置
                                                    </>
                                                )}
                                            </Button>
                                        </div>
                                    </CardHeader>
                                    <CardContent className="space-y-6">
                                        {/* 能力标签 */}
                                        <div>
                                            <h3 className="text-sm font-medium mb-2">能力标签</h3>
                                            <div className="flex flex-wrap gap-2">
                                                {selectedAgent.capabilities.map((cap) => (
                                                    <Badge key={cap} variant="outline">
                                                        {cap}
                                                    </Badge>
                                                ))}
                                            </div>
                                        </div>

                                        <Separator />

                                        {/* 知识库配置 */}
                                        <div>
                                            <div className="flex items-center justify-between mb-4">
                                                <h3 className="text-sm font-medium flex items-center">
                                                    <Database className="mr-2 h-4 w-4" />
                                                    绑定知识库
                                                    <Badge variant="secondary" className="ml-2">
                                                        已选 {selectedCollections.length} 个
                                                    </Badge>
                                                </h3>
                                                <div className="relative w-64">
                                                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                                    <Input
                                                        placeholder="搜索知识库..."
                                                        value={searchQuery}
                                                        onChange={(e) => setSearchQuery(e.target.value)}
                                                        className="pl-8"
                                                    />
                                                </div>
                                            </div>

                                            {/* 已选知识库 */}
                                            {selectedCollections.length > 0 && (
                                                <div className="mb-4">
                                                    <h4 className="text-xs text-muted-foreground mb-2">已绑定:</h4>
                                                    <div className="flex flex-wrap gap-2">
                                                        {selectedCollections.map(id => {
                                                            const col = collections.find(c => c.id === id);
                                                            return (
                                                                <Badge
                                                                    key={id}
                                                                    variant="default"
                                                                    className="flex items-center gap-1"
                                                                >
                                                                    {col?.title || id}
                                                                    <X
                                                                        className="h-3 w-3 cursor-pointer hover:text-destructive"
                                                                        onClick={() => handleToggleCollection(id)}
                                                                    />
                                                                </Badge>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            )}

                                            {/* 知识库树形列表 */}
                                            <ScrollArea className="h-[400px] border rounded-lg">
                                                <div className="p-2">
                                                    {collectionsLoading ? (
                                                        <div className="flex items-center justify-center py-12">
                                                            <Loader2 className="h-6 w-6 animate-spin text-primary mr-2" />
                                                            <span className="text-muted-foreground">加载知识库列表...</span>
                                                        </div>
                                                    ) : treeData.length > 0 ? (
                                                        <div className="space-y-1">
                                                            {treeData
                                                                .filter(node =>
                                                                    !searchQuery ||
                                                                    node.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
                                                                    node.children?.some(child =>
                                                                        child.label.toLowerCase().includes(searchQuery.toLowerCase())
                                                                    )
                                                                )
                                                                .map(node => (
                                                                    <TreeItem
                                                                        key={node.id}
                                                                        node={node}
                                                                        selectedIds={selectedTreeIds}
                                                                        onToggle={handleTreeToggle}
                                                                        expandedIds={expandedTreeIds}
                                                                        toggleExpand={toggleTreeExpand}
                                                                    />
                                                                ))
                                                            }
                                                        </div>
                                                    ) : (
                                                        <div className="text-center py-12 text-muted-foreground">
                                                            <Database className="h-12 w-12 mx-auto mb-3 opacity-50" />
                                                            <p className="font-medium">暂无知识库</p>
                                                            <p className="text-sm mt-1">请先创建知识库后再进行绑定配置</p>
                                                        </div>
                                                    )}
                                                </div>
                                            </ScrollArea>
                                        </div>

                                        <Separator />

                                        {/* 提示信息 */}
                                        <div className="flex items-start gap-2 p-3 rounded-lg bg-muted/50">
                                            <Info className="h-5 w-5 text-primary mt-0.5" />
                                            <div className="text-sm text-muted-foreground">
                                                <p className="font-medium text-foreground mb-1">配置说明</p>
                                                <ul className="list-disc list-inside space-y-1">
                                                    <li>可以选择绑定整个知识库集合，也可以选择其中的单独文件</li>
                                                    <li>绑定后，智能体将优先从选中的资源中检索相关信息</li>
                                                    <li>建议根据智能体职责选择相关的专业知识库或文件</li>
                                                    <li>展开集合可以查看和选择其中的具体文件</li>
                                                </ul>
                                            </div>
                                        </div>
                                    </CardContent>
                                </>
                            ) : (
                                <CardContent className="flex items-center justify-center h-64">
                                    <div className="text-center text-muted-foreground">
                                        <Bot className="h-12 w-12 mx-auto mb-2 opacity-50" />
                                        <p>请选择一个智能体进行配置</p>
                                    </div>
                                </CardContent>
                            )}
                        </Card>
                    </div>
                </div>
            </PageContent>
        </PageContainer>
    );
}
