'use client';
import {
  GraphEdge,
  GraphNode,
  KnowledgeGraph,
  MergeSuggestionsResponse,
} from '@/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { apiClient } from '@/lib/api/client';
import { cn } from '@/lib/utils';

import { Badge } from '@/components/ui/badge';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import { Input } from '@/components/ui/input';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Tooltip, TooltipContent } from '@/components/ui/tooltip';
import { TooltipTrigger } from '@radix-ui/react-tooltip';
import * as d3 from 'd3';
import _ from 'lodash';
import {
  AlertTriangle,
  ArrowLeft,
  ChevronDown,
  Database,
  FileText,
  FolderOpen,
  LoaderCircle,
  Maximize,
  Minimize,
  Search,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import dynamic from 'next/dynamic';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'sonner';
import { CollectionGraphNodeDetail } from './collection-graph-node-detail';
import { CollectionGraphNodeMerge } from './collection-graph-node-merge';
import { GraphContextMenu } from '@/components/graph/graph-context-menu';
import { GraphSourceViewer } from '@/components/graph/graph-source-viewer';

const ForceGraph2D = dynamic(
  () => import('react-force-graph-2d').then((r) => r),
  {
    ssr: false,
  },
);

// --- Types ---

type ViewMode = 'hierarchy' | 'graph';

type ProcessedNode = GraphNode & {
  sourceCollections: Set<string>;
  isBridge: boolean;
  isDocument: boolean;
  isCollectionRoot?: boolean;
  collectionId?: string;
  docId?: string;
  degree: number;
  value: number;
  label: string;
};

type ProcessedEdge = GraphEdge & {
  sourceCollectionId?: string;
};

export const CollectionGraph = ({
  marketplace = false,
  mode = 'contextual',
  collectionId,
}: {
  marketplace: boolean;
  mode?: 'contextual' | 'global';
  collectionId?: string;
}) => {
  const params = useParams();
  const router = useRouter();
  const currentCollectionId = collectionId || (params.collectionId as string);

  // --- State ---
  const [viewMode, setViewMode] = useState<ViewMode>(
    mode === 'global' ? 'hierarchy' : 'graph',
  );
  const [targetContext, setTargetContext] = useState<{
    collectionId: string;
    documentId?: string;
  } | null>(null);

  const [fullscreen, setFullscreen] = useState<boolean>(false);
  const { resolvedTheme } = useTheme();
  const page_graph = useTranslations('page_graph');

  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [graphData, setGraphData] = useState<{
    nodes: ProcessedNode[];
    links: ProcessedEdge[];
  }>();
  const [prunedCount, setPrunedCount] = useState(0);
  const [mergeSuggestion, setMergeSuggestion] =
    useState<MergeSuggestionsResponse>();
  const [mergeSuggestionOpen, setMergeSuggestionOpen] =
    useState<boolean>(false);

  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  const [allEntities, setAllEntities] = useState<{
    [key in string]: ProcessedNode[];
  }>({});
  const [activeEntities, setActiveEntities] = useState<string[]>([]);

  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());
  const [hoverNode, setHoverNode] = useState<ProcessedNode>();
  const [activeNode, setActiveNode] = useState<ProcessedNode>();

  // New State for Context Menu & Source Viewer
  const [sourceViewerState, setSourceViewerState] = useState<{
    open: boolean;
    collectionId?: string;
    docId?: string;
    docName?: string;
    highlight?: string;
  }>({ open: false });

  const [contextMenu, setContextMenu] = useState<{
    open: boolean;
    x: number;
    y: number;
    node: any;
  }>({ open: false, x: 0, y: 0, node: null });

  const [globalSearchQuery, setGlobalSearchQuery] = useState('');
  const color = useMemo(() => d3.scaleOrdinal(d3.schemeCategory10), []);

  const { NODE_MIN, NODE_MAX, SAFE_NODE_LIMIT } = useMemo(
    () => ({
      NODE_MIN: 6,
      NODE_MAX: 24,
      LINK_MIN: 1,
      LINK_MAX: 4,
      SAFE_NODE_LIMIT: 2000,
    }),
    [],
  );

  // --- Helper: Safe Round Rect for Canvas ---
  const drawRoundRect = useCallback(
    (
      ctx: CanvasRenderingContext2D,
      x: number,
      y: number,
      w: number,
      h: number,
      r: number,
    ) => {
      if (ctx.roundRect) {
        // Use native roundRect if available (Chrome 99+, Safari 16+)
        ctx.roundRect(x, y, w, h, r);
      } else {
        // Fallback for older browsers using arcTo
        if (w < 2 * r) r = w / 2;
        if (h < 2 * r) r = h / 2;
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.arcTo(x + w, y, x + w, y + h, r);
        ctx.arcTo(x + w, y + h, x, y + h, r);
        ctx.arcTo(x, y + h, x, y, r);
        ctx.arcTo(x, y, x + w, y, r);
        ctx.closePath();
      }
    },
    [],
  );

  // --- Data Processing: Hierarchy (Collections -> Docs -> Entities) ---
  const fetchHierarchyData = useCallback(async () => {
    setLoading(true);
    setGraphData(undefined); // Clear previous data to avoid ghosting
    try {
      // Call global hierarchy API
      const res = await apiClient.graphApi.graphsHierarchyGlobalPost({
        graphsHierarchyGlobalPostRequest: { query: '', top_k: 100 },
      });
      const data = res.data as any;

      const nodes = data.nodes || [];
      const edges = data.edges || [];

      // Convert API response to ProcessedNode format for visualization
      const processedNodes: ProcessedNode[] = nodes.map((node: any) => {
        const isCollection = node.type === 'collection';
        const isDocument = node.type === 'document';
        const isEntity = node.type === 'entity';

        return {
          id: node.id,
          label: node.name || node.id,
          value: isCollection ? 20 : isDocument ? 10 : 8,
          degree: 1,
          isCollectionRoot: isCollection,
          collectionId: node.metadata?.collection_id,
          docId: node.metadata?.document_id,
          isDocument: isDocument,
          isBridge: false,
          sourceCollections: new Set(
            node.metadata?.collection_id ? [node.metadata.collection_id] : [],
          ),
          properties: { entity_type: node.type?.toUpperCase() || 'UNKNOWN' },
          labels: [],
        };
      });

      // Convert edges to ProcessedEdge format
      const processedEdges: ProcessedEdge[] = edges.map((edge: any) => ({
        source: edge.source,
        target: edge.target,
        id: `E-${edge.source}-${edge.target}`,
        type: edge.type || 'DIRECTED',
        properties: { label: edge.label },
      }));

      setGraphData({ nodes: processedNodes, links: processedEdges });

      // Set entity types for legend
      const entityTypes = _.groupBy(
        processedNodes,
        (n) => n.properties?.entity_type || 'UNKNOWN',
      );
      setAllEntities(entityTypes);
      setActiveEntities(Object.keys(entityTypes));
      setPrunedCount(0); // Reset pruned count for hierarchy
    } catch (e) {
      console.error(e);
      toast.error('Failed to load global overview');
    } finally {
      setLoading(false);
    }
  }, []);

  // --- Data Processing: Entity Graph (Pruning & Filtering) ---
  const processAndPruneGraph = useCallback(
    (rawNodes: GraphNode[], rawEdges: GraphEdge[], filterDocId?: string) => {
      const nodeMap = new Map<string, ProcessedNode>();

      // 1. Initialize
      rawNodes.forEach((n) => {
        const isDoc =
          n.properties?.entity_type === 'DOCUMENT' ||
          n.labels?.includes('Document');
        // Generate label from labels array or use id
        const label =
          n.labels && n.labels.length > 0 ? n.labels[0] : String(n.id);
        nodeMap.set(n.id, {
          ...n,
          label,
          sourceCollections: new Set(),
          isBridge: false,
          isDocument: isDoc,
          degree: 0,
          value: NODE_MIN,
        });
      });

      // 2. Analyze Edges
      rawEdges.forEach((edge) => {
        // @ts-expect-error dynamic props
        const collId = edge.properties?.collection_id || edge.collection_id;
        const sourceId =
          typeof edge.source === 'object'
            ? (edge.source as any).id
            : edge.source;
        const targetId =
          typeof edge.target === 'object'
            ? (edge.target as any).id
            : edge.target;

        const sNode = nodeMap.get(sourceId);
        const tNode = nodeMap.get(targetId);

        if (sNode && tNode) {
          sNode.degree++;
          tNode.degree++;
          if (collId) {
            sNode.sourceCollections.add(collId);
            tNode.sourceCollections.add(collId);
          }
        }
      });

      // 3. Filter by Document (if requested)
      // Ego-Graph Strategy:
      // 1. Find nodes that represent the document (either by ID matching or property)
      // 2. Find all edges connected to those nodes
      // 3. Find all neighbors connected by those edges
      let finalNodes = Array.from(nodeMap.values());
      let finalEdges = rawEdges;

      if (filterDocId) {
        const relatedNodeIds = new Set<string>();

        // Find the node that IS the document
        const documentNode = finalNodes.find(
          (n) => n.id === filterDocId || n.id.includes(filterDocId),
        );

        if (documentNode) relatedNodeIds.add(documentNode.id);

        // Filter edges that reference this document
        const relevantEdges = rawEdges.filter((e) => {
          const s =
            typeof e.source === 'object' ? (e.source as any).id : e.source;
          const t =
            typeof e.target === 'object' ? (e.target as any).id : e.target;

          // Condition 1: Explicit source metadata
          const isSource =
            e.properties?.source_doc_id === filterDocId ||
            (e as any).source_doc_id === filterDocId;

          // Condition 2: Connected to the document node found above
          const isConnected =
            documentNode && (s === documentNode.id || t === documentNode.id);

          return isSource || isConnected;
        });

        if (relevantEdges.length > 0) {
          relevantEdges.forEach((e) => {
            relatedNodeIds.add(
              typeof e.source === 'object' ? (e.source as any).id : e.source,
            );
            relatedNodeIds.add(
              typeof e.target === 'object' ? (e.target as any).id : e.target,
            );
          });
          finalEdges = relevantEdges;
          finalNodes = finalNodes.filter((n) => relatedNodeIds.has(n.id));
        }
      }

      // 4. Styling & Bridges
      finalNodes.forEach((node) => {
        if (node.sourceCollections.size > 1) {
          node.isBridge = true;
          node.value = NODE_MAX;
        } else if (node.isDocument) {
          node.value = NODE_MAX * 0.8;
        } else {
          node.value = Math.min(
            NODE_MAX,
            Math.max(NODE_MIN, NODE_MIN + Math.log2(node.degree + 1) * 2),
          );
        }
      });

      // 5. Safety Pruning
      let pruned = 0;
      if (!filterDocId && finalNodes.length > SAFE_NODE_LIMIT) {
        finalNodes.sort((a, b) => {
          if (a.isBridge !== b.isBridge) return a.isBridge ? -1 : 1;
          if (a.isDocument !== b.isDocument) return a.isDocument ? -1 : 1;
          return b.degree - a.degree;
        });
        const keptSet = new Set(
          finalNodes.slice(0, SAFE_NODE_LIMIT).map((n) => n.id),
        );
        pruned = finalNodes.length - SAFE_NODE_LIMIT;
        finalNodes = finalNodes.slice(0, SAFE_NODE_LIMIT);
        finalEdges = finalEdges.filter((e) => {
          const s =
            typeof e.source === 'object' ? (e.source as any).id : e.source;
          const t =
            typeof e.target === 'object' ? (e.target as any).id : e.target;
          return keptSet.has(s) && keptSet.has(t);
        });
      }

      setPrunedCount(pruned);
      return { nodes: finalNodes, links: finalEdges };
    },
    [NODE_MIN, NODE_MAX, SAFE_NODE_LIMIT],
  );

  // --- API Call: Entity Graph ---
  const fetchEntityGraph = useCallback(
    async (cId: string, dId?: string, query?: string) => {
      setLoading(true);
      setGraphData(undefined); // Clear previous to show loading state clearly
      try {
        // Check if we're in global mode with search query
        if (cId === 'all' && query) {
          // Call global graph search API
          const res = await apiClient.graphApi.graphsSearchGlobalPost({
            graphsSearchGlobalPostRequest: { query, top_k: 100 },
          });
          const data = res.data as any;

          // Process global search results
          const nodes = data.nodes || [];
          const edges = data.edges || [];

          setGraphData({ nodes, links: edges });
          setAllEntities(
            _.groupBy(nodes, (n: any) => n.properties?.entity_type || 'ENTITY'),
          );
          setActiveEntities(
            Object.keys(
              _.groupBy(
                nodes,
                (n: any) => n.properties?.entity_type || 'ENTITY',
              ),
            ),
          );
        } else if (cId !== 'all') {
          // Normal collection graph
          const res = await apiClient.graphApi.collectionsCollectionIdGraphsGet(
            { collectionId: cId },
            { timeout: 60000 },
          );
          const data = res.data as KnowledgeGraph;

          // Process with Document ID filter if present
          const processed = processAndPruneGraph(
            data.nodes || [],
            data.edges || [],
            dId,
          );

          setGraphData(processed);
          setAllEntities(
            _.groupBy(processed.nodes, (n) => n.properties?.entity_type || ''),
          );
          setActiveEntities(
            Object.keys(
              _.groupBy(
                processed.nodes,
                (n) => n.properties?.entity_type || '',
              ),
            ),
          );
        }
      } catch (e) {
        console.error(e);
        toast.error('Failed to load graph');
      } finally {
        setLoading(false);
      }
    },
    [processAndPruneGraph],
  );

  // --- Handlers ---

  const handleCloseDetail = useCallback(() => {
    setActiveNode(undefined);
    setHoverNode(undefined);
    // Only clear highlights if source viewer is NOT open
    if (!sourceViewerState.open) {
      highlightNodes.clear();
      highlightLinks.clear();
    }
  }, [highlightLinks, highlightNodes, sourceViewerState.open]);

  const handleNodeClick = useCallback(
    (node: any) => {
      // Convert to ProcessedNode - ForceGraph2D passes a generic node object
      const processedNode = node as ProcessedNode;
      setContextMenu(prev => ({ ...prev, open: false })); // Close context menu on left click

      if (viewMode === 'hierarchy') {
        // Drill down logic
        if (processedNode.isCollectionRoot && processedNode.collectionId) {
          // Enter Collection Graph
          setViewMode('graph');
          setTargetContext({ collectionId: processedNode.collectionId });
          fetchEntityGraph(processedNode.collectionId);
          toast.info(`Loading graph for collection: ${processedNode.label}`);
        } else if (
          processedNode.isDocument &&
          processedNode.collectionId &&
          processedNode.docId
        ) {
          // Enter Document Graph (Filtered)
          setViewMode('graph');
          setTargetContext({
            collectionId: processedNode.collectionId,
            documentId: processedNode.docId,
          });
          fetchEntityGraph(processedNode.collectionId, processedNode.docId);
          toast.info(`Loading graph for document: ${processedNode.label}`);
        }
      } else {
        // Normal graph interaction (show details)
        if (activeNode?.id === processedNode.id) handleCloseDetail();
        else setActiveNode(processedNode);
      }
    },
    [viewMode, activeNode, fetchEntityGraph, handleCloseDetail],
  );

  const handleBackToHierarchy = useCallback(() => {
    setViewMode('hierarchy');
    setTargetContext(null);
    setHighlightNodes(new Set()); // Clear highlighting
    setHighlightLinks(new Set()); // Clear link highlighting
    setActiveNode(undefined); // Clear active node
    setHoverNode(undefined); // Clear hover node
    setSourceViewerState({ open: false }); // Close source viewer
    fetchHierarchyData(); // Reload hierarchy
  }, [fetchHierarchyData]);

  const handleNodeRightClick = useCallback((node: any, event: any) => {
    // Determine coordinates (ForceGraph passes event with clientX/Y or x/y depending on version, usually standard MouseEvent structure in event)
    // react-force-graph-2d passes (node, event) where event is the DOM event
    setContextMenu({
      open: true,
      x: event.clientX,
      y: event.clientY,
      node: node,
    });
  }, []);

  const handleLinkClick = useCallback((link: any) => {
    // Check if link has source info
    const props = link.properties || {};
    // Try to find source doc id from various possible property names
    const docId = props.source_doc_id || (link as any).source_doc_id || props.document_id;
    const text = props.source_text || props.context || (link as any).context || props.text;

    if (docId) {
      const docNode = graphData?.nodes.find(n => n.id === docId);
      const docName = docNode?.label || 'Document';

      setSourceViewerState({
        open: true,
        collectionId: currentCollectionId === 'all' ? (link.sourceCollectionId || props.collection_id) : currentCollectionId,
        docId,
        docName,
        highlight: text
      });

      // Highlight this link and connected nodes
      highlightLinks.clear();
      highlightNodes.clear();
      highlightLinks.add(link);

      const sId = typeof link.source === 'object' ? link.source.id : link.source;
      const tId = typeof link.target === 'object' ? link.target.id : link.target;
      const sNode = graphData?.nodes.find(n => n.id === sId);
      const tNode = graphData?.nodes.find(n => n.id === tId);
      if (sNode) highlightNodes.add(sNode);
      if (tNode) highlightNodes.add(tNode);

      setHighlightNodes(new Set(highlightNodes));
      setHighlightLinks(new Set(highlightLinks));

      // Close detail if open to avoid clutter
      setActiveNode(undefined);
    } else {
      toast.info("No source document linked to this relationship.");
    }
  }, [graphData, currentCollectionId, highlightLinks, highlightNodes]);

  const handleContextMenuAction = useCallback((action: string, node: any) => {
    setContextMenu(prev => ({ ...prev, open: false }));
    switch (action) {
      case 'focus':
        if (node.x && node.y) {
          graphRef.current?.centerAt(node.x, node.y, 1000);
          graphRef.current?.zoom(6, 1000);
        }
        break;
      case 'chat':
        // Navigate to chat with preset query
        router.push(`/workspace/chat?q=Explain entity "${node.label}"`);
        break;
      case 'source':
        if (node.isDocument && node.docId) {
          setSourceViewerState({
            open: true,
            collectionId: node.collectionId || currentCollectionId,
            docId: node.docId,
            docName: node.label
          });
        } else {
          toast.info("Source viewing for raw entities requires edge traversal (Coming Soon)");
        }
        break;
      case 'expand':
        if (node.isCollectionRoot && node.collectionId) {
          setViewMode('graph');
          fetchEntityGraph(node.collectionId);
        }
        break;
      case 'search':
        setGlobalSearchQuery(node.label);
        if (viewMode === 'graph') {
          fetchEntityGraph(targetContext?.collectionId || 'all', undefined, node.label);
        } else {
          setViewMode('graph');
          setTargetContext({ collectionId: 'all' });
          fetchEntityGraph('all', undefined, node.label);
        }
        break;
    }
  }, [currentCollectionId, viewMode, targetContext, fetchEntityGraph, router]);

  const getGraphData = useCallback(
    async (query?: string) => {
      if (typeof currentCollectionId !== 'string') return;
      if (mode === 'contextual') {
        fetchEntityGraph(currentCollectionId);
        return;
      }
      // For global mode with query, use fetchEntityGraph
      if (mode === 'global' && query) {
        fetchEntityGraph('all', undefined, query);
      }
    },
    [currentCollectionId, mode, fetchEntityGraph],
  );

  const getMergeSuggestions = useCallback(async () => {
    if (
      typeof currentCollectionId !== 'string' ||
      marketplace ||
      mode === 'global'
    )
      return;
    try {
      const suggestionRes =
        await apiClient.graphApi.collectionsCollectionIdGraphsMergeSuggestionsPost(
          {
            collectionId: currentCollectionId,
          },
          {
            timeout: 1000 * 20,
          },
        );
      setMergeSuggestion(suggestionRes.data);
    } catch (e) {
      console.error(e);
    }
  }, [marketplace, currentCollectionId, mode]);

  const handleResizeContainer = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    const width = container.offsetWidth || 0;
    const height = container.offsetHeight || 0;
    setDimensions({
      width: width - 2,
      height: height - 2,
    });
  }, []);

  useEffect(() => {
    if (activeEntities.length) return;
    setActiveEntities(Object.keys(allEntities));
  }, [activeEntities.length, allEntities]);

  useEffect(() => handleResizeContainer(), [handleResizeContainer]);
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    handleResizeContainer();
    window.addEventListener('resize', handleResizeContainer);
    return () => window.removeEventListener('resize', handleResizeContainer);
  }, [handleResizeContainer, fullscreen]);

  // [MOD] Spotlight Effect logic in useEffect
  useEffect(() => {
    highlightNodes.clear();
    highlightLinks.clear();

    if (activeNode || hoverNode) {
      const target = activeNode || hoverNode;
      if (!target) return;

      const nodeLinks = graphData?.links.filter((link) => {
        const sourceId = typeof link.source === 'object' ? (link.source as any).id : link.source;
        const targetId = typeof link.target === 'object' ? (link.target as any).id : link.target;
        return sourceId === target.id || targetId === target.id;
      });

      nodeLinks?.forEach((link: ProcessedEdge) => {
        highlightLinks.add(link);
        const sourceId = typeof link.source === 'object' ? (link.source as any).id : link.source;
        const targetId = typeof link.target === 'object' ? (link.target as any).id : link.target;
        const sNode = graphData?.nodes.find((n) => n.id === sourceId);
        const tNode = graphData?.nodes.find((n) => n.id === targetId);
        if (sNode) highlightNodes.add(sNode);
        if (tNode) highlightNodes.add(tNode);
      });
      highlightNodes.add(target);

      // Auto-center only on activeNode change, not hover
      if (activeNode && target === activeNode) {
        // @ts-expect-error node.x node.y
        graphRef.current?.centerAt(activeNode.x, activeNode.y, 400);
        graphRef.current?.zoom(3, 600);
      }
    } else {
      // Reset view only if explicitly cleared (optional, maybe distracting)
      // graphRef.current?.centerAt(0, 0, 400);
      // graphRef.current?.zoom(1.5, 600);
    }
    setHighlightNodes(new Set(highlightNodes));
    setHighlightLinks(new Set(highlightLinks));
  }, [activeNode, hoverNode, graphData]);

  // Initial Load Router
  useEffect(() => {
    if (mode === 'global') {
      if (viewMode === 'hierarchy') {
        fetchHierarchyData();
      }
    } else {
      // Contextual mode (single collection)
      fetchEntityGraph(currentCollectionId);
      getMergeSuggestions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, viewMode]); // Only run on mode mount or if manually triggered

  const handleGlobalSearchSubmit = useCallback(() => {
    if (!globalSearchQuery.trim()) return;
    // If searching in hierarchy mode, switch to graph mode and search all
    if (viewMode === 'graph') {
      fetchEntityGraph(
        targetContext?.collectionId || 'all',
        undefined,
        globalSearchQuery,
      );
    } else {
      // In hierarchy, switch to graph mode and search global entities
      setViewMode('graph');
      setTargetContext({ collectionId: 'all' });
      fetchEntityGraph('all', undefined, globalSearchQuery);
    }
  }, [globalSearchQuery, viewMode, targetContext, fetchEntityGraph]);

  return (
    <div
      className={cn('top-0 right-0 bottom-0 left-0 flex flex-1 flex-col', {
        fixed: fullscreen,
        'bg-background': fullscreen,
        'z-49': fullscreen,
      })}
    >
      {/* Header Bar */}
      <div
        className={cn('mb-2 flex flex-row items-center justify-between gap-2', {
          'px-2': fullscreen,
          'pt-2': fullscreen,
        })}
      >
        {/* Left: Indicators / Back Button */}
        <div className="flex items-center gap-2">
          {mode === 'global' && viewMode === 'graph' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleBackToHierarchy}
              className="gap-1 pl-0"
            >
              <ArrowLeft size={16} />
              Back to Overview
            </Button>
          )}

          {mode === 'global' && viewMode === 'hierarchy' && (
            <Badge
              variant="outline"
              className="border-primary/50 text-primary gap-1 text-sm font-normal"
            >
              <FolderOpen size={14} /> Global Overview
            </Badge>
          )}

          {mode === 'contextual' && (
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="w-40 justify-between">
                  {page_graph('node_search')}
                  <ChevronDown />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-[200px] p-0" align="start">
                <Command>
                  <CommandInput placeholder="Search node..." className="h-9" />
                  <CommandList className="max-h-60">
                    <CommandEmpty>No node found.</CommandEmpty>
                    <CommandGroup>
                      {graphData?.nodes.slice(0, 50).map((node) => (
                        <CommandItem
                          key={node.id}
                          value={node.id}
                          onSelect={() => setActiveNode(node)}
                        >
                          <div className="truncate">{node.label}</div>
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          )}

          {/* Global Search Input */}
          {mode === 'global' && (
            <div className="relative w-60">
              <Search className="text-muted-foreground absolute top-2.5 left-2 h-4 w-4" />
              <Input
                placeholder="Search entities..."
                className="h-9 pl-8"
                value={globalSearchQuery}
                onChange={(e) => setGlobalSearchQuery(e.target.value)}
                onKeyDown={(e) =>
                  e.key === 'Enter' && handleGlobalSearchSubmit()
                }
              />
            </div>
          )}
        </div>

        {/* Right: Tools */}
        <div className="flex flex-row items-center gap-2">
          {prunedCount > 0 && (
            <Badge variant="destructive" className="flex gap-1">
              <AlertTriangle size={12} /> {prunedCount} Hidden
            </Badge>
          )}
          {!marketplace &&
            mode !== 'global' &&
            !_.isEmpty(mergeSuggestion?.suggestions) && (
              <Tooltip>
                <TooltipTrigger>
                  <Badge
                    variant="destructive"
                    className="mr-4 h-5 min-w-5 cursor-pointer rounded-full px-1 font-mono tabular-nums"
                    onClick={() => setMergeSuggestionOpen(true)}
                  >
                    {mergeSuggestion?.suggestions?.length &&
                      mergeSuggestion?.suggestions?.length > 10
                      ? '10+'
                      : mergeSuggestion?.suggestions?.length}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  {page_graph('merge_infomation', {
                    count: String(mergeSuggestion?.pending_count || 0),
                  })}
                </TooltipContent>
              </Tooltip>
            )}

          <Button
            size="icon"
            variant="outline"
            onClick={() => {
              if (viewMode === 'hierarchy') fetchHierarchyData();
              else
                fetchEntityGraph(
                  targetContext?.collectionId || currentCollectionId,
                  targetContext?.documentId,
                );
            }}
          >
            <LoaderCircle className={loading ? 'animate-spin' : ''} />
          </Button>

          <Button
            size="icon"
            variant="outline"
            className="cursor-pointer"
            onClick={() => {
              setFullscreen(!fullscreen);
            }}
          >
            {fullscreen ? <Minimize /> : <Maximize />}
          </Button>
        </div>
      </div>

      <Card
        ref={containerRef}
        className="bg-card/0 relative flex flex-1 gap-0 overflow-hidden py-0"
      >
        {mode === 'global' &&
          (!graphData?.nodes || graphData.nodes.length === 0) &&
          !loading && (
            <div className="bg-background/50 absolute inset-0 z-20 flex flex-col items-center justify-center p-6 backdrop-blur-sm">
              <div className="flex w-full max-w-2xl flex-col items-center gap-4 text-center">
                <h2 className="text-3xl font-bold tracking-tight">
                  {page_graph('global_explorer_title')}
                </h2>
                <p className="text-muted-foreground mb-4">
                  {page_graph('global_explorer_description')}
                </p>
                <div className="flex w-full max-w-md items-center space-x-2">
                  <Input
                    className="h-12 text-lg shadow-lg"
                    placeholder={page_graph('global_search_placeholder')}
                    value={globalSearchQuery}
                    onChange={(e) => setGlobalSearchQuery(e.target.value)}
                    onKeyDown={(e) =>
                      e.key === 'Enter' && handleGlobalSearchSubmit()
                    }
                  />
                  <Button
                    size="lg"
                    className="h-12 px-6 shadow-lg"
                    onClick={handleGlobalSearchSubmit}
                  >
                    <Search className="mr-2 h-5 w-5" /> {page_graph('search')}
                  </Button>
                </div>
              </div>
            </div>
          )}

        {loading && (
          <div className="absolute top-4/12 left-1/2 z-30 -translate-x-1/2">
            <div className="flex flex-row gap-2 py-2">
              <div className="bg-primary size-3 animate-bounce rounded-full delay-0"></div>
              <div className="bg-primary size-3 animate-bounce rounded-full delay-150"></div>
              <div className="bg-primary size-3 animate-bounce rounded-full delay-300"></div>
            </div>
          </div>
        )}

        {graphData !== undefined &&
          _.isEmpty(graphData?.nodes) &&
          !loading &&
          mode !== 'global' && (
            <div className="absolute top-4/12 w-full">
              <div className="text-muted-foreground text-center">
                {page_graph('no_nodes_found')}
              </div>
            </div>
          )}

        {/* Legends */}
        <div className="bg-background pointer-events-none absolute top-0 right-0 left-0 z-10 flex flex-row flex-wrap gap-1 rounded-xl p-2">
          {_.map(allEntities, (item, key) => {
            const isActive = activeEntities.includes(key);
            return (
              <Badge
                key={key}
                className={cn(
                  'pointer-events-auto flex cursor-pointer gap-1 capitalize',
                  !activeEntities.includes(key) && 'opacity-50',
                )}
                style={{
                  backgroundColor: activeEntities.includes(key)
                    ? color(key)
                    : undefined,
                }}
                onClick={() =>
                  setActiveEntities((prev) =>
                    prev.includes(key)
                      ? prev.filter((k) => k !== key)
                      : [...prev, key],
                  )
                }
              >
                {key === 'COLLECTION' && <Database size={10} />}
                {key === 'DOCUMENT' && <FileText size={10} />}
                {key} ({item.length})
              </Badge>
            );
          })}
        </div>

        <ForceGraph2D
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          nodeLabel="label"
          warmupTicks={100}
          cooldownTicks={50}
          ref={graphRef}
          nodeVisibility={(node) => {
            const nodeType =
              (node as ProcessedNode).properties?.entity_type ||
              (node as any).type ||
              'UNKNOWN';
            return activeEntities.includes(nodeType);
          }}
          onNodeClick={handleNodeClick}
          onNodeRightClick={handleNodeRightClick}
          onLinkClick={handleLinkClick}
          onNodeHover={(node) => setHoverNode(node as ProcessedNode)}

          // Rendering Props
          nodeCanvasObject={(node: any, ctx, globalScale) => {
            const x = node.x || 0;
            const y = node.y || 0;
            const size = node.value || 5;

            // [MOD] Spotlight Logic: Opacity
            const isHighlighted = highlightNodes.has(node);
            const hasSelection = highlightNodes.size > 0;
            // Dim if selection exists AND this node is not highlighted
            const opacity = hasSelection && !isHighlighted ? 0.1 : 1;

            ctx.globalAlpha = opacity;
            ctx.beginPath();

            // ... (Existing Shape Logic) ...
            const processedNode = node as ProcessedNode;
            if (processedNode.isCollectionRoot) {
              ctx.fillStyle = '#3b82f6';
              drawRoundRect(ctx, x - size, y - size * 0.8, size * 2, size * 1.6, 4);
            } else if (processedNode.isDocument) {
              ctx.fillStyle = '#10b981';
              ctx.rect(x - size * 0.8, y - size, size * 1.6, size * 2);
            } else {
              ctx.fillStyle = color(processedNode.properties?.entity_type || '');
              ctx.arc(x, y, size, 0, 2 * Math.PI);
            }
            ctx.fill();

            // Label Logic (Only show if highlighted or zoomed in)
            if (opacity > 0.5 && (globalScale > 1.2 || isHighlighted)) {
              const label = processedNode.label;
              ctx.font = `${10 / globalScale}px Sans-Serif`; // Scalable font
              ctx.fillStyle = resolvedTheme === 'dark' ? '#fff' : '#000';
              ctx.textAlign = 'center';
              ctx.fillText(label, x, y + size + 4);
            }

            ctx.globalAlpha = 1; // Reset opacity
          }}
          nodePointerAreaPaint={(node: any, color, ctx) => {
            const x = node.x || 0;
            const y = node.y || 0;
            const size = node.value || 5;
            const processedNode = node as ProcessedNode;
            ctx.fillStyle = color;
            ctx.beginPath();

            if (processedNode.isCollectionRoot) {
              // [FIX] Use safe drawer for compatibility
              drawRoundRect(
                ctx,
                x - size,
                y - size * 0.8,
                size * 2,
                size * 1.6,
                4,
              );
            } else if (processedNode.isDocument) {
              ctx.rect(x - size * 0.8, y - size, size * 1.6, size * 2);
            } else {
              ctx.arc(x, y, size, 0, 2 * Math.PI, false);
            }
            ctx.fill();
          }}
          linkLabel="id"
          linkColor={(link) => highlightLinks.has(link) ? (resolvedTheme === 'dark' ? '#fff' : '#000') : (resolvedTheme === 'dark' ? '#555' : '#ccc')}
          linkWidth={(link) => highlightLinks.has(link) ? 2 : 0.5}
          // Hide non-highlighted links when spotlight is active
          linkVisibility={(link) => highlightNodes.size === 0 || highlightLinks.has(link)}
        />

        <CollectionGraphNodeDetail
          open={!mergeSuggestionOpen && Boolean(activeNode)}
          node={activeNode}
          onClose={handleCloseDetail}
        />

        {sourceViewerState.open && sourceViewerState.collectionId && sourceViewerState.docId && (
          <div className="absolute top-0 right-0 bottom-0 z-20 h-full shadow-xl animate-in slide-in-from-right-10">
            <GraphSourceViewer
              collectionId={sourceViewerState.collectionId}
              documentId={sourceViewerState.docId}
              documentName={sourceViewerState.docName}
              highlightText={sourceViewerState.highlight}
              onClose={() => {
                setSourceViewerState(prev => ({ ...prev, open: false }));
                // Clear highlight if we are closing
                highlightNodes.clear();
                highlightLinks.clear();
                setHighlightNodes(new Set());
                setHighlightLinks(new Set());
              }}
            />
          </div>
        )}

        <GraphContextMenu
          open={contextMenu.open}
          position={{ x: contextMenu.x, y: contextMenu.y }}
          node={contextMenu.node}
          onClose={() => setContextMenu(prev => ({ ...prev, open: false }))}
          onAction={handleContextMenuAction}
        />

        {mergeSuggestion && (
          <CollectionGraphNodeMerge
            dataSource={mergeSuggestion}
            open={mergeSuggestionOpen}
            onRefresh={getMergeSuggestions}
            onClose={() => {
              setActiveNode(undefined);
              setMergeSuggestionOpen(false);
            }}
            onSelectNode={(id: string) => {
              const n = graphData?.nodes.find((nod) => nod.id === id);
              if (n) setActiveNode(n);
            }}
          />
        )}
      </Card>
    </div>
  );
};
