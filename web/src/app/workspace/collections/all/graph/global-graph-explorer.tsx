'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import * as d3 from 'd3';
import _ from 'lodash';
import {
  ChevronDown,
  ChevronRight,
  Database,
  ExternalLink,
  FileText,
  Filter,
  Focus,
  Layers,
  Loader2,
  MessageSquare,
  RotateCcw,
  Search,
  X,
  ZoomIn,
  ZoomOut,
  Eye,
  Copy,
  Maximize2,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import type { ReactNode } from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

const ForceGraph2D = dynamic(
  () => import('react-force-graph-2d').then((mod) => mod.default || mod),
  {
    ssr: false,
  },
);

// --- Types ---

interface GraphNode {
  id: string;
  type: 'collection' | 'document' | 'entity';
  name: string;
  description?: string;
  metadata?: Record<string, unknown>;
  workspace?: string;
  entity_name?: string;
  source_collections?: string[];  // 实体来源的多个 Collection
  source_documents?: string[];    // 实体来源的多个 Document
  val?: number;
  x?: number;
  y?: number;
  [key: string]: unknown;
}

interface GraphEdge extends d3.SimulationLinkDatum<GraphNode> {
  source: string | GraphNode;
  target: string | GraphNode;
  label: string;
  type: string;
  workspace?: string;
  [key: string]: unknown;
}

interface TreeNode {
  id: string;
  label: string;
  type: 'collection' | 'document';
  children?: TreeNode[];
  metadata?: any;
}

// --- Components ---

const TreeItem = ({
  node,
  level = 0,
  onSelect,
  selectedId,
  expandedIds,
  toggleExpand,
  highlightIds,
}: {
  node: TreeNode;
  level?: number;
  onSelect: (node: TreeNode) => void;
  selectedId?: string | null;
  expandedIds: Set<string>;
  toggleExpand: (id: string) => void;
  highlightIds?: Set<string>;
}) => {
  const isExpanded = expandedIds.has(node.id);
  const isSelected = selectedId === node.id;
  const isHighlighted = highlightIds?.has(node.id);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className="w-full">
      <div
        className={cn(
          'flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm transition-colors',
          isSelected
            ? 'bg-primary text-primary-foreground'
            : 'hover:bg-muted/50',
          isHighlighted && !isSelected && 'bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-400 dark:border-yellow-600',
        )}
        style={{ paddingLeft: `${level * 12 + 8}px` }}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(node);
        }}
      >
        <div
          className={cn(
            'flex h-4 w-4 items-center justify-center rounded-sm hover:bg-black/10 dark:hover:bg-white/10',
            !hasChildren && 'invisible',
          )}
          onClick={(e) => {
            e.stopPropagation();
            toggleExpand(node.id);
          }}
        >
          {isExpanded ? (
            <ChevronDown className="h-3 w-3" />
          ) : (
            <ChevronRight className="h-3 w-3" />
          )}
        </div>

        {node.type === 'collection' ? (
          <Database className="h-4 w-4 shrink-0 text-blue-500" />
        ) : (
          <FileText className="h-4 w-4 shrink-0 text-green-500" />
        )}

        <span className="truncate">{node.label}</span>
      </div>
      {isExpanded && hasChildren && (
        <div>
          {node.children!.map((child) => (
            <TreeItem
              key={child.id}
              node={child}
              level={level + 1}
              onSelect={onSelect}
              selectedId={selectedId}
              expandedIds={expandedIds}
              toggleExpand={toggleExpand}
              highlightIds={highlightIds}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// --- Main Component ---

export function GlobalGraphExplorer() {
  const t = useTranslations('page_graph');
  const { resolvedTheme } = useTheme();
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [treeLoading, setTreeLoading] = useState(false);

  // Graph Data
  const [graphData, setGraphData] = useState<{
    nodes: GraphNode[];
    links: GraphEdge[];
  }>({ nodes: [], links: [] });

  // Directory Tree Data
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [expandedTreeIds, setExpandedTreeIds] = useState<Set<string>>(new Set());
  const [selectedTreeId, setSelectedTreeId] = useState<string | null>(null);
  const [highlightTreeIds, setHighlightTreeIds] = useState<Set<string>>(new Set());

  // View Controls
  const [hierarchicalView, setHierarchicalView] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [nodeDetailOpen, setNodeDetailOpen] = useState(false);
  const [nodeTypeFilter, setNodeTypeFilter] = useState<string>('all');
  const [showStats, setShowStats] = useState(true);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [highlightNodes, setHighlightNodes] = useState(new Set<string>());
  const [highlightLinks, setHighlightLinks] = useState(new Set<string>());
  const [searchMatchedNodes, setSearchMatchedNodes] = useState(new Set<string>());
  const [showAllLabels, setShowAllLabels] = useState(true); // 🔥 默认显示所有标签

  // Context Menu
  const [contextMenuNode, setContextMenuNode] = useState<GraphNode | null>(null);
  const [contextMenuPos, setContextMenuPos] = useState({ x: 0, y: 0 });

  // 🔦 Spotlight Mode
  const [spotlightMode, setSpotlightMode] = useState(false);
  const [spotlightNodes, setSpotlightNodes] = useState(new Set<string>());

  // 📄 Source Viewer Panel
  const [sourceViewerOpen, setSourceViewerOpen] = useState(false);
  const [sourceViewerData, setSourceViewerData] = useState<{
    nodeId: string;
    nodeName: string;
    nodeType: string;
    metadata?: any;
  } | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);

  // Helper: Get one-hop neighbors
  const getNeighbors = useCallback((nodeId: string): string[] => {
    const neighbors: string[] = [];
    graphData.links.forEach(link => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;

      if (sourceId === nodeId) neighbors.push(targetId as string);
      if (targetId === nodeId) neighbors.push(sourceId as string);
    });
    return neighbors;
  }, [graphData.links]);

  // -- 1. Fetch Directory Tree (Collections -> Documents) --
  const fetchDirectoryTree = useCallback(async () => {
    setTreeLoading(true);
    try {
      const response = await fetch('/api/v1/graphs/hierarchy/global', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: '', top_k: 10000, include_entities: false }),
      });

      if (response.ok) {
        const data = await response.json();
        const nodes = data.nodes || [];
        const edges = data.edges || [];

        const collections = nodes.filter((n: any) => n.type === 'collection');
        const documents = nodes.filter((n: any) => n.type === 'document');

        const tree: TreeNode[] = collections.map((col: any) => {
          const colId = col.id;
          const childDocs = edges
            .filter((e: any) => e.source === colId && e.type === 'CONTAINS')
            .map((e: any) => {
              const docNode = documents.find((d: any) => d.id === e.target);
              return docNode ? {
                id: docNode.id,
                label: docNode.name,
                type: 'document' as const,
                metadata: docNode.metadata
              } : null;
            })
            .filter(Boolean) as TreeNode[];

          return {
            id: colId,
            label: col.name,
            type: 'collection' as const,
            children: childDocs,
            metadata: col.metadata
          };
        });

        setTreeData(tree);
        setExpandedTreeIds(new Set(tree.map(t => t.id)));
      }
    } catch (error) {
      console.error('Failed to fetch directory tree:', error);
    } finally {
      setTreeLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDirectoryTree();
    handleSearch(true);
  }, [fetchDirectoryTree]);

  // -- 2. Search & Graph Logic with Entity Deduplication --
  const handleSearch = async (initialLoad = false) => {
    if (!initialLoad && !query.trim()) return;

    setLoading(true);
    setHasSearched(true);
    setSelectedTreeId(null);

    try {
      const endpoint = initialLoad || hierarchicalView
        ? '/api/v1/graphs/hierarchy/global'
        : '/api/v1/graphs/search/global';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query || '',
          top_k: 50,
          include_entities: true
        }),
      });

      if (response.ok) {
        const data = await response.json();
        let nodes = data.nodes || [];
        let links = data.edges || [];

        // 🔥 处理重复实体：合并来自多个文档的同名实体
        const entityMap = new Map<string, GraphNode>();
        const nonEntityNodes: GraphNode[] = [];

        nodes.forEach((node: GraphNode) => {
          if (!node.type) node.type = 'entity';

          if (node.type === 'entity') {
            const entityKey = node.name || node.entity_name || node.id;

            if (entityMap.has(entityKey)) {
              // 实体已存在，合并来源信息
              const existingNode = entityMap.get(entityKey)!;

              // 合并 source_collections
              const existingCollections = existingNode.source_collections || [];
              const newCollections = node.metadata?.workspace ? [node.metadata.workspace as string] : [];
              existingNode.source_collections = Array.from(new Set([...existingCollections, ...newCollections]));

              // 合并 source_documents
              const existingDocs = existingNode.source_documents || [];
              const newDocs = node.metadata?.document_id ? [node.metadata.document_id as string] : [];
              existingNode.source_documents = Array.from(new Set([...existingDocs, ...newDocs]));

              // 增加节点权重（表示重要性）
              existingNode.val = (existingNode.val || 1) + 1;

            } else {
              // 新实体，初始化来源信息
              node.source_collections = node.metadata?.workspace ? [node.metadata.workspace as string] : [];
              node.source_documents = node.metadata?.document_id ? [node.metadata.document_id as string] : [];
              node.val = 1;
              entityMap.set(entityKey, node);
            }
          } else {
            // Collection 和 Document 节点直接添加
            nonEntityNodes.push(node);
          }
        });

        // 合并去重后的节点
        const deduplicatedNodes = [...nonEntityNodes, ...Array.from(entityMap.values())];

        // 计算节点度数
        deduplicatedNodes.forEach((node: GraphNode) => {
          const degree = links.filter((l: GraphEdge) => {
            const s = typeof l.source === 'object' ? l.source.id : l.source;
            const t = typeof l.target === 'object' ? l.target.id : l.target;
            return s === node.id || t === node.id;
          }).length;
          if (node.type !== 'entity') {
            node.val = Math.max(degree, 2);
          }
        });

        setGraphData({ nodes: deduplicatedNodes, links });

        // 🔥 高亮搜索匹配的节点
        if (!initialLoad && query) {
          console.log('🔍 Search query:', query);
          const matchedNodeIds = new Set<string>();
          const matchedDocIds = new Set<string>();
          const matchedColIds = new Set<string>();

          deduplicatedNodes.forEach((n: GraphNode) => {
            // 尝试多个名称字段，确保转换为字符串
            const nodeName = String(n.name || n.entity_name || n.label || n.id || '').toLowerCase();
            const queryLower = query.toLowerCase();

            if (nodeName.includes(queryLower)) {
              console.log('✅ Matched node:', n.id, nodeName);
              matchedNodeIds.add(n.id);

              if (n.type === 'entity') {
                links.forEach((l: GraphEdge) => {
                  const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                  const sourceId = typeof l.source === 'object' ? l.source.id : l.source;

                  if (targetId === n.id && l.type === 'EXTRACTED_FROM') {
                    if (sourceId.startsWith('doc_')) matchedDocIds.add(sourceId);
                  }
                });
              } else if (n.type === 'document') {
                matchedDocIds.add(n.id);
              }
            }
          });

          console.log('🎯 Total matched nodes:', matchedNodeIds.size);
          console.log('📄 Matched documents:', matchedDocIds.size);

          treeData.forEach(col => {
            if (col.children?.some(doc => matchedDocIds.has(doc.id))) {
              matchedColIds.add(col.id);
              setExpandedTreeIds(prev => {
                const next = new Set(prev);
                next.add(col.id);
                return next;
              });
            }
          });

          setHighlightTreeIds(new Set([...matchedDocIds, ...matchedColIds]));
          setSearchMatchedNodes(matchedNodeIds);
          console.log('🌟 Search matched nodes state updated:', matchedNodeIds.size);

          // 🔦 启用聚光灯模式
          if (matchedNodeIds.size > 0) {
            const spotlight = new Set(matchedNodeIds);
            // 添加一跳邻居到聚光灯
            matchedNodeIds.forEach(id => {
              const neighbors = getNeighbors(id);
              neighbors.forEach(n => spotlight.add(n));
            });
            setSpotlightNodes(spotlight);
            setSpotlightMode(true);
            console.log('🔦 Spotlight mode activated. Spotlight nodes:', spotlight.size);
          } else {
            setSpotlightMode(false);
            setSpotlightNodes(new Set());
          }
        } else {
          setHighlightTreeIds(new Set());
          setSearchMatchedNodes(new Set());
          setSpotlightMode(false);
          setSpotlightNodes(new Set());
        }

        setTimeout(() => {
          graphRef.current?.zoomToFit(400);
        }, 500);

      }
    } catch (error) {
      console.error('Search error:', error);
      toast.error('搜索失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // -- 3. Tree Interaction --
  const handleTreeSelect = useCallback((node: TreeNode) => {
    setSelectedTreeId(node.id);

    if (!graphRef.current) return;

    const relatedNodeIds = new Set<string>();
    relatedNodeIds.add(node.id);

    if (node.type === 'collection') {
      node.children?.forEach(child => relatedNodeIds.add(child.id));

      graphData.links.forEach(link => {
        const s = typeof link.source === 'object' ? link.source.id : link.source;
        const t = typeof link.target === 'object' ? link.target.id : link.target;

        if (relatedNodeIds.has(s as string)) relatedNodeIds.add(t as string);
        if (relatedNodeIds.has(t as string)) relatedNodeIds.add(s as string);
      });
    }
    else if (node.type === 'document') {
      graphData.links.forEach(link => {
        const s = typeof link.source === 'object' ? link.source.id : link.source;
        const t = typeof link.target === 'object' ? link.target.id : link.target;
        if (s === node.id) relatedNodeIds.add(t as string);
      });
    }

    setHighlightNodes(relatedNodeIds);

    const graphNode = graphData.nodes.find(n => n.id === node.id);
    if (graphNode && typeof graphNode.x === 'number' && typeof graphNode.y === 'number') {
      graphRef.current.centerAt(graphNode.x, graphNode.y, 1000);
      graphRef.current.zoom(4, 2000);
    }

  }, [graphData, treeData]);

  // -- 4. Context Menu Handlers --
  const handleNodeRightClick = useCallback((node: any, event: MouseEvent) => {
    event.preventDefault();
    setContextMenuNode(node as GraphNode);
    setContextMenuPos({ x: event.clientX, y: event.clientY });
  }, []);

  const handleContextMenuAction = useCallback((action: string) => {
    if (!contextMenuNode) return;

    switch (action) {
      case 'focus':
        if (contextMenuNode.x && contextMenuNode.y) {
          graphRef.current?.centerAt(contextMenuNode.x, contextMenuNode.y, 1000);
          graphRef.current?.zoom(6, 1000);
        }
        break;
      case 'chat':
        router.push(`/workspace/chat?q=解释实体"${contextMenuNode.name || contextMenuNode.entity_name}"`);
        break;
      case 'expand':
        const connectedIds = new Set<string>([contextMenuNode.id]);
        graphData.links.forEach(link => {
          const s = typeof link.source === 'object' ? link.source.id : link.source;
          const t = typeof link.target === 'object' ? link.target.id : link.target;
          if (s === contextMenuNode.id) connectedIds.add(t as string);
          if (t === contextMenuNode.id) connectedIds.add(s as string);
        });
        setHighlightNodes(connectedIds);
        break;
      case 'copy':
        navigator.clipboard.writeText(contextMenuNode.name || contextMenuNode.entity_name || contextMenuNode.id);
        toast.success('已复制到剪贴板');
        break;
      case 'details':
        setSelectedNode(contextMenuNode);
        setNodeDetailOpen(true);
        break;
    }

    setContextMenuNode(null);
  }, [contextMenuNode, graphData, router]);

  // -- Resize Handler --
  const handleResize = useCallback(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.offsetWidth,
        height: containerRef.current.offsetHeight,
      });
    }
  }, []);

  useEffect(() => {
    const observer = new ResizeObserver(() => {
      handleResize();
    });
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    return () => observer.disconnect();
  }, [handleResize]);

  // -- Render --

  const filteredGraphData = useMemo(() => {
    let { nodes, links } = graphData;
    if (nodeTypeFilter !== 'all') {
      nodes = nodes.filter((n) => n.type === nodeTypeFilter);
    }
    return { nodes, links };
  }, [graphData, nodeTypeFilter]);

  // 🎨 优化：根据主题动态调整节点颜色，暗色模式使用更亮的颜色
  const nodeTypeColors = useMemo(() => ({
    collection: resolvedTheme === 'dark' ? '#60a5fa' : '#3b82f6',  // 暗色更亮的蓝
    document: resolvedTheme === 'dark' ? '#34d399' : '#10b981',    // 暗色更亮的绿
    entity: resolvedTheme === 'dark' ? '#fbbf24' : '#f59e0b',      // 暗色更亮的橙
  }), [resolvedTheme]);

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col bg-background">
      {/* Top Bar */}
      <div className="border-b p-4 flex items-center gap-4 bg-card/50 backdrop-blur-sm z-20">
        <div className="flex-1 max-w-2xl flex items-center gap-2 relative">
          <Search className="absolute left-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t('search_placeholder') || "搜索实体、文档或知识库..."}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            className="pl-9 bg-background/80"
          />
          <Button onClick={() => handleSearch()} disabled={loading} size="sm">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "搜索"}
          </Button>
        </div>

        <div className="flex items-center gap-4 ml-auto">
          <div className="flex items-center gap-2">
            <Switch
              id="view-mode"
              checked={hierarchicalView}
              onCheckedChange={v => {
                setHierarchicalView(v);
                handleSearch();
              }}
            />
            <Label htmlFor="view-mode" className="text-xs">层级视图</Label>
          </div>
          <Select value={nodeTypeFilter} onValueChange={setNodeTypeFilter}>
            <SelectTrigger className="w-[120px] h-8 text-xs">
              <SelectValue placeholder="节点类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部类型</SelectItem>
              <SelectItem value="collection">知识库</SelectItem>
              <SelectItem value="document">文档</SelectItem>
              <SelectItem value="entity">实体</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* 🔥 Search Status Banner */}
      {searchMatchedNodes.size > 0 && (
        <div className="bg-orange-500/10 border-b border-orange-500/30 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-orange-500 animate-pulse"></div>
              <span className="text-sm font-semibold text-orange-600 dark:text-orange-400">
                搜索结果激活
              </span>
            </div>
            <Badge variant="secondary" className="bg-orange-500/20 text-orange-700 dark:text-orange-300">
              找到 {searchMatchedNodes.size} 个匹配实体
            </Badge>
            {spotlightMode && (
              <Badge variant="outline" className="text-xs">
                🔦 聚光灯模式
              </Badge>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setQuery('');
              setSearchMatchedNodes(new Set());
              setSpotlightMode(false);
              setSpotlightNodes(new Set());
              setHighlightTreeIds(new Set());
              handleSearch(true);
            }}
            className="text-xs"
          >
            <X className="h-3 w-3 mr-1" />
            清除搜索
          </Button>
        </div>
      )}

      <ResizablePanelGroup direction="horizontal" className="flex-1 overflow-hidden">
        {/* Left Panel: Search Results or Directory Tree */}
        <ResizablePanel defaultSize={20} minSize={15} maxSize={40} className="border-r bg-muted/10">
          <div className="flex flex-col h-full">
            {/* 🔥 Search Results Mode */}
            {searchMatchedNodes.size > 0 ? (
              <>
                <div className="p-3 border-b flex items-center justify-between bg-orange-500/5">
                  <span className="font-semibold text-sm flex items-center gap-2">
                    <Search className="h-4 w-4 text-orange-500" />
                    搜索结果 ({searchMatchedNodes.size})
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => {
                      setQuery('');
                      setSearchMatchedNodes(new Set());
                      setSpotlightMode(false);
                      setSpotlightNodes(new Set());
                      handleSearch(true);
                    }}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
                <ScrollArea className="flex-1 p-2">
                  <div className="space-y-1">
                    {Array.from(searchMatchedNodes).map((nodeId) => {
                      const node = graphData.nodes.find(n => n.id === nodeId);
                      if (!node) return null;

                      const nodeName = node.name || node.entity_name || node.id;
                      const nodeType = node.type || 'entity';
                      const sources = node.source_collections || [];

                      return (
                        <div
                          key={nodeId}
                          className="flex flex-col gap-1 p-2 rounded-sm hover:bg-orange-500/10 cursor-pointer border border-transparent hover:border-orange-500/30 transition-all"
                          onClick={() => {
                            if (graphRef.current && node.x !== undefined && node.y !== undefined) {
                              graphRef.current.centerAt(node.x, node.y, 1000);
                              graphRef.current.zoom(6, 1000);

                              // 临时高亮该节点
                              setHighlightNodes(new Set([nodeId]));
                              setTimeout(() => {
                                setHighlightNodes(new Set());
                              }, 2000);
                            }
                          }}
                        >
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                            <span className="text-sm font-medium truncate flex-1">
                              {nodeName}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 ml-4">
                            <Badge variant="outline" className="text-xs">
                              {nodeType}
                            </Badge>
                            {sources.length > 0 && (
                              <span className="text-xs text-muted-foreground truncate">
                                {sources.length} 个来源
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </ScrollArea>
              </>
            ) : (
              /* Directory Tree Mode */
              <>
                <div className="p-3 border-b flex items-center justify-between">
                  <span className="font-semibold text-sm flex items-center gap-2">
                    <Layers className="h-4 w-4" /> 知识库目录
                  </span>
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={fetchDirectoryTree}>
                    <RotateCcw className="h-3 w-3" />
                  </Button>
                </div>
                <ScrollArea className="flex-1 p-2">
                  {treeLoading ? (
                    <div className="flex justify-center py-8 text-muted-foreground">
                      <Loader2 className="h-6 w-6 animate-spin" />
                    </div>
                  ) : treeData.length === 0 ? (
                    <div className="text-center py-8 text-xs text-muted-foreground">暂无知识库</div>
                  ) : (
                    <div className="space-y-1">
                      {treeData.map(node => (
                        <TreeItem
                          key={node.id}
                          node={node}
                          onSelect={handleTreeSelect}
                          selectedId={selectedTreeId}
                          expandedIds={expandedTreeIds}
                          highlightIds={highlightTreeIds}
                          toggleExpand={(id) => {
                            setExpandedTreeIds(prev => {
                              const next = new Set(prev);
                              if (next.has(id)) next.delete(id);
                              else next.add(id);
                              return next;
                            });
                          }}
                        />
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </>
            )}
          </div>
        </ResizablePanel>

        <ResizableHandle />

        {/* Right Panel: Graph Visualization */}
        <ResizablePanel defaultSize={80}>
          <div className="relative w-full h-full" ref={containerRef}>
            {/* Graph Controls */}
            <div className="absolute bottom-4 right-4 z-10 flex flex-col gap-2">
              <Button size="icon" variant="secondary" onClick={() => graphRef.current?.zoomIn()}>
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button size="icon" variant="secondary" onClick={() => graphRef.current?.zoomOut()}>
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button size="icon" variant="secondary" onClick={() => graphRef.current?.zoomToFit()}>
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>

            {/* 🎯 新增：图例面板 */}
            <div className="absolute top-4 left-4 z-10">
              <Card className="p-3 bg-background/80 backdrop-blur">
                <div className="text-xs font-bold mb-2">图例</div>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#3b82f6' }} />
                    <span className="text-xs text-muted-foreground">知识库</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#10b981' }} />
                    <span className="text-xs text-muted-foreground">文档</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#f59e0b' }} />
                    <span className="text-xs text-muted-foreground">实体</span>
                  </div>
                  {searchMatchedNodes.size > 0 && (
                    <div className="flex items-center gap-2 border-t pt-1.5 mt-1.5">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ff6b35' }} />
                      <span className="text-xs text-orange-600 dark:text-orange-400">搜索匹配</span>
                    </div>
                  )}
                </div>
              </Card>
            </div>

            {/* Stats Overlay */}
            {showStats && (
              <div className="absolute top-4 right-4 z-10">
                <Card className="p-3 w-48 bg-background/80 backdrop-blur">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-bold">图谱统计</span>
                    <X className="h-3 w-3 cursor-pointer hover:text-destructive" onClick={() => setShowStats(false)} />
                  </div>
                  <div className="text-xs space-y-1 text-muted-foreground">
                    <div className="flex justify-between"><span>节点:</span> <span className="font-mono text-foreground">{filteredGraphData.nodes.length}</span></div>
                    <div className="flex justify-between"><span>连接:</span> <span className="font-mono text-foreground">{filteredGraphData.links.length}</span></div>
                    {searchMatchedNodes.size > 0 && (
                      <div className="flex justify-between border-t pt-1 mt-1"><span>匹配:</span> <span className="font-mono text-yellow-600 dark:text-yellow-400">{searchMatchedNodes.size}</span></div>
                    )}
                    {spotlightMode && (
                      <div className="flex justify-between items-center border-t pt-1 mt-1">
                        <span className="flex items-center gap-1">
                          🔦 聚光灯
                        </span>
                        <span className="font-mono text-blue-600 dark:text-blue-400">{spotlightNodes.size}</span>
                      </div>
                    )}
                  </div>
                </Card>
              </div>
            )}

            {dimensions.width > 0 && (
              <ForceGraph2D
                ref={graphRef}
                width={dimensions.width}
                height={dimensions.height}
                graphData={filteredGraphData}
                nodeLabel={(node: any) => {
                  const name = node.name || node.entity_name || '';
                  const sources = node.source_collections?.length > 0
                    ? `\n来源: ${node.source_collections.join(', ')}`
                    : '';
                  return name + sources;
                }}
                nodeColor={(node: any) => {
                  // 搜索匹配的节点高亮显示
                  if (searchMatchedNodes.has(node.id)) {
                    return '#ff6b35'; // 🎨 橙红色高亮
                  }
                  if (highlightNodes.size > 0 && !highlightNodes.has(node.id)) {
                    return resolvedTheme === 'dark' ? '#333' : '#eee';
                  }
                  return nodeTypeColors[node.type as keyof typeof nodeTypeColors] || '#999';
                }}
                nodeRelSize={6}
                linkColor={(link: any) => {
                  const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                  const targetId = typeof link.target === 'object' ? link.target.id : link.target;

                  // 高亮搜索匹配节点的连接
                  if (searchMatchedNodes.has(sourceId) || searchMatchedNodes.has(targetId)) {
                    return '#ff6b35'; // 🎨 橙红色高亮连接
                  }

                  // 🔦 聚光灯模式：淡化非相关连接
                  if (spotlightMode) {
                    return resolvedTheme === 'dark' ? '#ffffff25' : '#00000025';
                  }

                  return resolvedTheme === 'dark' ? '#ffffff20' : '#00000020';
                }}
                linkWidth={(link: any) => {
                  const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                  const targetId = typeof link.target === 'object' ? link.target.id : link.target;

                  // 高亮搜索匹配节点的连接
                  if (searchMatchedNodes.has(sourceId) || searchMatchedNodes.has(targetId)) {
                    return 2;
                  }
                  return 1;
                }}
                // 🎯 新增：连接线方向箭头
                linkDirectionalArrowLength={4}
                linkDirectionalArrowRelPos={0.85}
                // 🎯 新增：连接线弯曲，避免重叠
                linkCurvature={0.15}
                // 🎯 新增：悬停时显示关系标签
                linkLabel={(link: any) => link.label || link.type || ''}
                // 🚀 新增：力导图布局优化参数
                d3AlphaDecay={0.02}        // 减慢稳定速度，让布局更均匀
                d3VelocityDecay={0.3}      // 减少节点漂移
                warmupTicks={100}           // 预热帧数，加速初始布局
                cooldownTime={5000}         // 冷却时间
                backgroundColor={resolvedTheme === 'dark' ? '#020817' : '#ffffff'}
                onNodeClick={(node) => {
                  const graphNode = node as GraphNode;
                  // 打开原文预览面板
                  setSourceViewerData({
                    nodeId: graphNode.id,
                    nodeName: graphNode.name || graphNode.entity_name || graphNode.id,
                    nodeType: graphNode.type,
                    metadata: graphNode.metadata,
                  });
                  setSourceViewerOpen(true);

                  // 同时保留详情对话框功能（可选）
                  // setSelectedNode(graphNode);
                  // setNodeDetailOpen(true);
                }}
                onNodeRightClick={handleNodeRightClick}
                nodeCanvasObject={(node: any, ctx, globalScale) => {
                  // 🔍 尝试多个可能的名称字段
                  const label = node.name ||
                    node.entity_name ||
                    node.label ||
                    node.title ||
                    node.description ||
                    node.id ||
                    'Unknown';

                  // 调试：第一次渲染时打印节点结构
                  if (!(window as any)._nodeLogged && node.id) {
                    console.log('📊 Sample node structure:', {
                      id: node.id,
                      type: node.type,
                      name: node.name,
                      entity_name: node.entity_name,
                      label: node.label,
                      title: node.title,
                      allKeys: Object.keys(node),
                    });
                    (window as any)._nodeLogged = true;
                  }

                  const fontSize = 12 / globalScale;
                  const isHighlighted = highlightNodes.has(node.id);
                  const isSearchMatched = searchMatchedNodes.has(node.id);

                  // 🔦 聚光灯模式透明度控制 - 平衡可见性
                  if (spotlightMode) {
                    const isInSpotlight = spotlightNodes.has(node.id);
                    if (isSearchMatched) {
                      ctx.globalAlpha = 1.0;  // 搜索匹配：完全不透明
                    } else if (isInSpotlight) {
                      ctx.globalAlpha = 0.6;  // 一跳邻居：较明显
                    } else {
                      ctx.globalAlpha = 0.3;  // 其他节点：清晰可见
                    }
                  } else {
                    ctx.globalAlpha = 1.0;
                  }

                  // 节点大小：搜索匹配 > 高亮 > 普通
                  let size = 5;
                  if (isSearchMatched) size = 10; // 🎯 适中大小，突出但不过分
                  else if (isHighlighted) size = 8;
                  else if (node.val) size = Math.min(node.val * 2, 12);

                  // 🎨 绘制适度光晕效果 (仅针对搜索匹配节点)
                  if (isSearchMatched) {
                    // 单层光晕，更简洁
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, size + 6, 0, 2 * Math.PI, false);
                    ctx.fillStyle = 'rgba(255, 107, 53, 0.25)'; // 橙红色光晕
                    ctx.fill();
                  }

                  ctx.beginPath();
                  ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);

                  // 颜色逻辑
                  if (isSearchMatched) {
                    ctx.fillStyle = '#ff6b35'; // 🎨 橙红色，更醒目
                  } else if (highlightNodes.size > 0 && !isHighlighted) {
                    ctx.fillStyle = resolvedTheme === 'dark' ? '#333' : '#e5e7eb';
                  } else {
                    ctx.fillStyle = nodeTypeColors[node.type as keyof typeof nodeTypeColors] || '#999';
                  }

                  ctx.fill();

                  // 边框
                  if (isSearchMatched || isHighlighted) {
                    ctx.strokeStyle = isSearchMatched ? '#e63946' : (resolvedTheme === 'dark' ? '#fff' : '#000');
                    ctx.lineWidth = (isSearchMatched ? 3 : 2) / globalScale;
                    ctx.stroke();
                  }

                  // 🔥 优化标签显示逻辑
                  // 选项1: 强制显示所有标签（调试模式）
                  // 选项2: 智能显示（重要节点 + 搜索匹配 + 高亮 + 缩放）
                  const isImportantNode = node.type === 'collection' || node.type === 'document';
                  const shouldShowLabel = showAllLabels ||
                    isImportantNode ||
                    isSearchMatched ||
                    isHighlighted ||
                    globalScale > 0.3;

                  if (shouldShowLabel && label && label !== 'Unknown') {
                    ctx.font = `${isSearchMatched ? 'bold ' : ''}${fontSize}px Sans-Serif`;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'top';

                    const textWidth = ctx.measureText(label).width;
                    const padding = 4;
                    const labelY = node.y + size + 4;

                    // 文字背景
                    if (isSearchMatched) {
                      ctx.fillStyle = 'rgba(255, 107, 53, 0.9)'; // 🎨 橙红色背景
                    } else {
                      ctx.fillStyle = resolvedTheme === 'dark'
                        ? 'rgba(0,0,0,0.75)'
                        : 'rgba(255,255,255,0.9)';
                    }

                    ctx.fillRect(
                      node.x - textWidth / 2 - padding,
                      labelY - 2,
                      textWidth + padding * 2,
                      fontSize + 6,
                    );

                    // 文字颜色
                    if (isSearchMatched) {
                      ctx.fillStyle = '#ffffff'; // 白色文字
                      ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
                      ctx.shadowBlur = 1;
                    } else {
                      ctx.fillStyle = resolvedTheme === 'dark' ? '#fff' : '#000';
                      ctx.shadowBlur = 0;
                    }

                    ctx.fillText(label, node.x, labelY);
                    ctx.shadowBlur = 0; // 重置阴影

                    // 🔥 显示多来源标记
                    if (node.type === 'entity' && node.source_collections?.length > 1) {
                      const sourceLabel = `${node.source_collections.length} 个来源`;
                      const sourceFontSize = fontSize * 0.75;
                      ctx.font = `italic ${sourceFontSize}px Sans-Serif`;
                      const sourceY = labelY + fontSize + 4;

                      const sourceWidth = ctx.measureText(sourceLabel).width;
                      ctx.fillStyle = resolvedTheme === 'dark'
                        ? 'rgba(0,0,0,0.6)'
                        : 'rgba(255,255,255,0.8)';
                      ctx.fillRect(
                        node.x - sourceWidth / 2 - 2,
                        sourceY - 1,
                        sourceWidth + 4,
                        sourceFontSize + 2
                      );

                      ctx.fillStyle = '#3b82f6'; // 蓝色表示多来源
                      ctx.fillText(sourceLabel, node.x, sourceY);
                    }
                  }

                  // 恢复透明度
                  ctx.globalAlpha = 1.0;
                }}
              />
            )}
          </div>
        </ResizablePanel>

        {/* Right Panel: Source Viewer (Conditional) */}
        {sourceViewerOpen && (
          <>
            <ResizableHandle />
            <ResizablePanel defaultSize={30} minSize={20} maxSize={40} className="border-l bg-muted/5">
              <div className="flex flex-col h-full">
                {/* Header */}
                <div className="p-3 border-b flex items-center justify-between bg-card">
                  <span className="font-semibold text-sm flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    原文预览
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => setSourceViewerOpen(false)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>

                {/* Content */}
                <ScrollArea className="flex-1 p-4">
                  {sourceViewerData ? (
                    <div className="space-y-4">
                      {/* Node Info */}
                      <div>
                        <div className="text-xs text-muted-foreground mb-1">节点信息</div>
                        <Card className="p-3">
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">类型:</span>
                              <Badge variant="outline">{sourceViewerData.nodeType}</Badge>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">名称:</span>
                              <span className="font-medium">{sourceViewerData.nodeName}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">ID:</span>
                              <span className="font-mono text-xs">{sourceViewerData.nodeId}</span>
                            </div>
                          </div>
                        </Card>
                      </div>

                      {/* Metadata */}
                      {sourceViewerData.metadata && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">元数据</div>
                          <Card className="p-3">
                            <pre className="text-xs overflow-auto max-h-60 whitespace-pre-wrap">
                              {JSON.stringify(sourceViewerData.metadata, null, 2)}
                            </pre>
                          </Card>
                        </div>
                      )}

                      {/* Source Document (Placeholder) */}
                      <div>
                        <div className="text-xs text-muted-foreground mb-1">来源文档</div>
                        <Card className="p-3">
                          <div className="text-sm text-muted-foreground">
                            {sourceViewerData.nodeType === 'entity' ? (
                              <div>
                                <p className="mb-2">该实体提取自以下文档：</p>
                                <div className="space-y-1">
                                  {sourceViewerData.metadata?.document_id && (
                                    <div className="flex items-center gap-2 p-2 bg-muted/50 rounded">
                                      <FileText className="h-3 w-3" />
                                      <span className="text-xs font-mono">
                                        {sourceViewerData.metadata.document_id}
                                      </span>
                                    </div>
                                  )}
                                </div>
                                <p className="mt-3 text-xs italic">
                                  💡 提示：点击文档可查看原文内容
                                </p>
                              </div>
                            ) : (
                              <p>选择一个实体节点以查看其来源文档</p>
                            )}
                          </div>
                        </Card>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                      点击节点查看详情
                    </div>
                  )}
                </ScrollArea>
              </div>
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>

      {/* Context Menu */}
      {contextMenuNode && (
        <div
          className="fixed z-50 min-w-[200px] rounded-md border bg-popover p-1 text-popover-foreground shadow-md"
          style={{ left: contextMenuPos.x, top: contextMenuPos.y }}
          onMouseLeave={() => setContextMenuNode(null)}
        >
          <div className="px-2 py-1.5 text-sm font-semibold border-b mb-1">
            {contextMenuNode.name || contextMenuNode.entity_name}
          </div>
          <button
            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
            onClick={() => handleContextMenuAction('focus')}
          >
            <Focus className="h-4 w-4" />
            聚焦节点
          </button>
          <button
            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
            onClick={() => handleContextMenuAction('expand')}
          >
            <Eye className="h-4 w-4" />
            显示关联
          </button>
          <button
            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
            onClick={() => handleContextMenuAction('chat')}
          >
            <MessageSquare className="h-4 w-4" />
            AI 对话
          </button>
          <button
            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
            onClick={() => handleContextMenuAction('copy')}
          >
            <Copy className="h-4 w-4" />
            复制名称
          </button>
          <div className="border-t my-1" />
          <button
            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
            onClick={() => handleContextMenuAction('details')}
          >
            <ExternalLink className="h-4 w-4" />
            查看详情
          </button>
        </div>
      )}

      {/* Node Detail Dialog */}
      <Dialog open={nodeDetailOpen} onOpenChange={setNodeDetailOpen}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedNode?.type === 'collection' && <Database className="h-4 w-4" />}
              {selectedNode?.type === 'document' && <FileText className="h-4 w-4" />}
              {selectedNode?.name || selectedNode?.entity_name}
            </DialogTitle>
            <DialogDescription>
              <Badge variant="outline">{selectedNode?.type}</Badge>
              {selectedNode?.source_collections && selectedNode.source_collections.length > 1 && (
                <Badge variant="secondary" className="ml-2">
                  {selectedNode.source_collections.length} 个来源
                </Badge>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 text-sm mt-2">
            {selectedNode?.description && (
              <div>
                <div className="font-semibold mb-1">描述</div>
                <div className="text-muted-foreground">{selectedNode.description}</div>
              </div>
            )}

            {/* 🔥 显示多来源信息 */}
            {selectedNode?.source_collections && selectedNode.source_collections.length > 0 && (
              <div>
                <div className="font-semibold mb-1">来源知识库</div>
                <div className="flex flex-wrap gap-2">
                  {selectedNode.source_collections.map((col, idx) => (
                    <Badge key={idx} variant="secondary">{col}</Badge>
                  ))}
                </div>
              </div>
            )}

            {selectedNode?.metadata && (
              <div>
                <div className="font-semibold mb-1">元数据</div>
                <pre className="bg-muted p-2 rounded text-xs overflow-auto max-h-40">
                  {JSON.stringify(selectedNode.metadata, null, 2)}
                </pre>
              </div>
            )}

            {selectedNode?.type === 'collection' && (
              <Button className="w-full" variant="outline" onClick={() => router.push(`/workspace/collections/${selectedNode.metadata?.collection_id || selectedNode.id.replace('col_', '')}/graph`)}>
                <ExternalLink className="h-4 w-4 mr-2" /> 打开知识库图谱
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
