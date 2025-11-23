"use client";

import { useState, useEffect } from "react";
import { PageContainer, PageHeader, PageContent } from "@/components/page-container";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useTranslations } from "next-intl";
import { Settings, RefreshCw, Save, CheckCircle2, Pencil, X } from "lucide-react";

// Simple toast notification function
const useToast = () => {
    return {
        toast: ({ title, description, variant }: { title: string; description: string; variant?: string }) => {
            if (variant === "destructive") {
                alert(`❌ ${title}\n${description}`);
            } else {
                alert(`✅ ${title}\n${description}`);
            }
        }
    };
};

interface PresetCollection {
    id: string;
    title_zh: string;
    title_en: string;
    description_zh: string;
    description_en: string;
    category: string;
    tags: string[];
    icon: string;
    recommended_agents: string[];
    auto_create: boolean;
    order: number;
}

interface PresetConfig {
    enabled: boolean;
    auto_create_for_new_users: boolean;
    collections: PresetCollection[];
    categories: Record<string, any>;
}

export default function PresetCollectionsAdminPage() {
    const t = useTranslations("sidebar_workspace");
    const { toast } = useToast();

    const [config, setConfig] = useState<PresetConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [editingCollection, setEditingCollection] = useState<PresetCollection | null>(null);
    const [editDialogOpen, setEditDialogOpen] = useState(false);

    // Load configuration
    const loadConfig = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch("/api/v1/admin/preset-collections/config");
            if (response.ok) {
                const data = await response.json();
                console.log("Loaded config:", data);
                setConfig(data);
            } else {
                const errorText = await response.text();
                console.error("Failed to load config:", response.status, errorText);
                const errMsg = `无法加载预设知识库配置 (${response.status}): ${errorText.substring(0, 100)}`;
                setError(errMsg);
                toast({
                    title: "加载失败",
                    description: errMsg,
                    variant: "destructive",
                });
            }
        } catch (error) {
            console.error("Failed to load config:", error);
            const errMsg = `网络错误: ${error instanceof Error ? error.message : String(error)}`;
            setError(errMsg);
            toast({
                title: "加载失败",
                description: errMsg,
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    // Save configuration
    const saveConfig = async () => {
        if (!config) return;

        setSaving(true);
        try {
            const response = await fetch("/api/v1/admin/preset-collections/config", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(config),
            });

            if (response.ok) {
                toast({
                    title: "保存成功",
                    description: "预设知识库配置已更新",
                });
            } else {
                toast({
                    title: "保存失败",
                    description: "无法保存配置",
                    variant: "destructive",
                });
            }
        } catch (error) {
            console.error("Failed to save config:", error);
            toast({
                title: "保存失败",
                description: "网络错误",
                variant: "destructive",
            });
        } finally {
            setSaving(false);
        }
    };

    // Handle editing a collection
    const handleEditCollection = (collection: PresetCollection) => {
        setEditingCollection({ ...collection }); // Create a copy
        setEditDialogOpen(true);
    };

    // Save edited collection
    const handleSaveEdit = () => {
        if (!editingCollection || !config) return;

        const newCollections = config.collections.map(c =>
            c.id === editingCollection.id ? editingCollection : c
        );
        setConfig({ ...config, collections: newCollections });
        setEditDialogOpen(false);
        setEditingCollection(null);
        toast({
            title: "修改成功",
            description: "预设知识库信息已更新，请点击\"保存配置\"以持久化更改",
        });
    };

    // Update editing collection field
    const updateEditingField = (field: keyof PresetCollection, value: any) => {
        if (!editingCollection) return;
        setEditingCollection({ ...editingCollection, [field]: value });
    };

    // Update tags (comma separated string to array)
    const updateTags = (tagsString: string) => {
        const tags = tagsString.split(',').map(t => t.trim()).filter(t => t.length > 0);
        updateEditingField('tags', tags);
    };

    // Update recommended agents (comma separated string to array)
    const updateRecommendedAgents = (agentsString: string) => {
        const agents = agentsString.split(',').map(a => a.trim()).filter(a => a.length > 0);
        updateEditingField('recommended_agents', agents);
    };

    useEffect(() => {
        loadConfig();
    }, []);

    if (loading) {
        return (
            <PageContainer>
                <PageHeader breadcrumbs={[{ title: "管理后台" }, { title: "预设知识库配置" }]} />
                <PageContent>
                    <div className="flex items-center justify-center h-64">
                        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
                    </div>
                </PageContent>
            </PageContainer>
        );
    }

    if (!config) {
        return (
            <PageContainer>
                <PageHeader breadcrumbs={[{ title: "管理后台" }, { title: "预设知识库配置" }]} />
                <PageContent>
                    <div className="text-center space-y-4">
                        <p className="text-muted-foreground">配置加载失败</p>
                        {error && <p className="text-sm text-destructive">{error}</p>}
                        <Button onClick={loadConfig}>
                            <RefreshCw className="w-4 h-4 mr-2" />
                            重试
                        </Button>
                    </div>
                </PageContent>
            </PageContainer>
        );
    }

    return (
        <PageContainer>
            <PageHeader
                breadcrumbs={[
                    { title: "管理后台", href: "/admin" },
                    { title: "预设知识库配置" }
                ]}
            />
            <PageContent>
                <div className="space-y-6">
                    {/* Header Section */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <div className="p-3 rounded-full bg-primary/10">
                                <Settings className="w-8 h-8 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold tracking-tight">预设知识库配置</h1>
                                <p className="text-muted-foreground mt-1">
                                    管理系统预设的知识库模板,用于变电站巡检系统
                                </p>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={loadConfig} disabled={loading}>
                                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                                刷新
                            </Button>
                            <Button onClick={saveConfig} disabled={saving}>
                                <Save className="w-4 h-4 mr-2" />
                                {saving ? "保存中..." : "保存配置"}
                            </Button>
                        </div>
                    </div>

                    {/* Global Settings */}
                    <Card>
                        <CardHeader>
                            <CardTitle>全局设置</CardTitle>
                            <CardDescription>控制预设知识库功能的全局行为</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="font-medium">启用预设知识库</div>
                                    <div className="text-sm text-muted-foreground">
                                        是否启用预设知识库功能
                                    </div>
                                </div>
                                <Switch
                                    checked={config.enabled}
                                    onCheckedChange={(checked) =>
                                        setConfig({ ...config, enabled: checked })
                                    }
                                />
                            </div>
                            <Separator />
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="font-medium">新用户自动创建</div>
                                    <div className="text-sm text-muted-foreground">
                                        为新注册用户自动创建预设知识库
                                    </div>
                                </div>
                                <Switch
                                    checked={config.auto_create_for_new_users}
                                    onCheckedChange={(checked) =>
                                        setConfig({ ...config, auto_create_for_new_users: checked })
                                    }
                                    disabled={!config.enabled}
                                />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Collections List */}
                    <Card>
                        <CardHeader>
                            <CardTitle>预设知识库列表 ({config.collections.length})</CardTitle>
                            <CardDescription>
                                配置各个预设知识库的启用状态和属性
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {config.collections
                                    .sort((a, b) => a.order - b.order)
                                    .map((collection, index) => (
                                        <div key={collection.id}>
                                            {index > 0 && <Separator className="my-4" />}
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1 space-y-2">
                                                    <div className="flex items-center gap-3">
                                                        <span className="text-2xl">{collection.icon}</span>
                                                        <div>
                                                            <div className="font-semibold text-lg">
                                                                {collection.title_zh}
                                                            </div>
                                                            <div className="text-sm text-muted-foreground">
                                                                {collection.title_en}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="text-sm text-muted-foreground whitespace-pre-line pl-11">
                                                        {collection.description_zh.split('\n')[0]}
                                                    </div>
                                                    <div className="flex flex-wrap gap-2 pl-11">
                                                        <Badge variant="outline">{collection.category}</Badge>
                                                        {collection.tags.map((tag) => (
                                                            <Badge key={tag} variant="secondary">
                                                                {tag}
                                                            </Badge>
                                                        ))}
                                                    </div>
                                                    {collection.recommended_agents.length > 0 && (
                                                        <div className="text-xs text-muted-foreground pl-11">
                                                            推荐智能体: {collection.recommended_agents.join(", ")}
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2 ml-4">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleEditCollection(collection)}
                                                        className="h-8"
                                                    >
                                                        <Pencil className="w-4 h-4 mr-1" />
                                                        编辑
                                                    </Button>
                                                    <div className="text-right">
                                                        <div className="text-xs text-muted-foreground mb-1">
                                                            自动创建
                                                        </div>
                                                        <Switch
                                                            checked={collection.auto_create}
                                                            onCheckedChange={(checked) => {
                                                                const newCollections = [...config.collections];
                                                                const idx = newCollections.findIndex(
                                                                    (c) => c.id === collection.id
                                                                );
                                                                if (idx !== -1) {
                                                                    newCollections[idx] = {
                                                                        ...newCollections[idx],
                                                                        auto_create: checked,
                                                                    };
                                                                    setConfig({ ...config, collections: newCollections });
                                                                }
                                                            }}
                                                            disabled={!config.enabled}
                                                        />
                                                    </div>
                                                    {collection.auto_create && (
                                                        <CheckCircle2 className="w-5 h-5 text-green-500" />
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Statistics */}
                    <Card>
                        <CardHeader>
                            <CardTitle>统计信息</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-3 gap-4">
                                <div className="text-center">
                                    <div className="text-3xl font-bold text-primary">
                                        {config.collections.length}
                                    </div>
                                    <div className="text-sm text-muted-foreground mt-1">
                                        预设知识库总数
                                    </div>
                                </div>
                                <div className="text-center">
                                    <div className="text-3xl font-bold text-green-600">
                                        {config.collections.filter((c) => c.auto_create).length}
                                    </div>
                                    <div className="text-sm text-muted-foreground mt-1">
                                        启用自动创建
                                    </div>
                                </div>
                                <div className="text-center">
                                    <div className="text-3xl font-bold text-blue-600">
                                        {Object.keys(config.categories).length}
                                    </div>
                                    <div className="text-sm text-muted-foreground mt-1">
                                        知识库分类
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Edit Dialog */}
                <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
                    <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                        <DialogHeader>
                            <DialogTitle>编辑预设知识库</DialogTitle>
                            <DialogDescription>
                                修改预设知识库的配置信息
                            </DialogDescription>
                        </DialogHeader>
                        {editingCollection && (
                            <div className="space-y-4 py-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="title_zh">中文标题</Label>
                                        <Input
                                            id="title_zh"
                                            value={editingCollection.title_zh}
                                            onChange={(e) => updateEditingField('title_zh', e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="title_en">英文标题</Label>
                                        <Input
                                            id="title_en"
                                            value={editingCollection.title_en}
                                            onChange={(e) => updateEditingField('title_en', e.target.value)}
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="description_zh">中文描述</Label>
                                    <Textarea
                                        id="description_zh"
                                        value={editingCollection.description_zh}
                                        onChange={(e) => updateEditingField('description_zh', e.target.value)}
                                        rows={4}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="description_en">英文描述</Label>
                                    <Textarea
                                        id="description_en"
                                        value={editingCollection.description_en}
                                        onChange={(e) => updateEditingField('description_en', e.target.value)}
                                        rows={4}
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="icon">图标 (Emoji)</Label>
                                        <Input
                                            id="icon"
                                            value={editingCollection.icon}
                                            onChange={(e) => updateEditingField('icon', e.target.value)}
                                            placeholder="📐"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="category">分类</Label>
                                        <Input
                                            id="category"
                                            value={editingCollection.category}
                                            onChange={(e) => updateEditingField('category', e.target.value)}
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="tags">标签 (逗号分隔)</Label>
                                    <Input
                                        id="tags"
                                        value={editingCollection.tags.join(', ')}
                                        onChange={(e) => updateTags(e.target.value)}
                                        placeholder="drawings, schematics, blueprints"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="agents">推荐智能体 (逗号分隔)</Label>
                                    <Input
                                        id="agents"
                                        value={editingCollection.recommended_agents.join(', ')}
                                        onChange={(e) => updateRecommendedAgents(e.target.value)}
                                        placeholder="detective, archivist"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="order">显示顺序</Label>
                                    <Input
                                        id="order"
                                        type="number"
                                        value={editingCollection.order}
                                        onChange={(e) => updateEditingField('order', parseInt(e.target.value) || 0)}
                                    />
                                </div>
                            </div>
                        )}
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
                                <X className="w-4 h-4 mr-2" />
                                取消
                            </Button>
                            <Button onClick={handleSaveEdit}>
                                <Save className="w-4 h-4 mr-2" />
                                保存修改
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </PageContent>
        </PageContainer>
    );
}
