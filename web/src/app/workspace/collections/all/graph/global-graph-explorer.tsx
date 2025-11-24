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
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import * as d3 from 'd3';
import _ from 'lodash';
import {
  ExternalLink,
  Filter,
  Loader2,
  RotateCcw,
  Search,
  X,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import type { ReactNode } from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

const ForceGraph2D = dynamic(
  () => import('react-force-graph-2d').then((mod) => mod.default || mod),
  {
    ssr: false,
  },
);

interface GraphNode {
  id: string;
  type: 'collection' | 'document' | 'entity';
  name: string;
  description?: string;
  metadata?: Record<string, unknown>;
  workspace?: string;
  entity_name?: string;
  val?: number;
  x?: number;
  y?: number;
  [key: string]: unknown; // Allow additional properties for D3/ForceGraph
}

interface GraphEdge extends d3.SimulationLinkDatum<GraphNode> {
  source: string | GraphNode;
  target: string | GraphNode;
  label: string;
  type: string;
  workspace?: string;
  [key: string]: unknown; // Allow additional properties for D3/ForceGraph
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface ForceGraphMethods {
  zoom: (scale?: number, duration?: number) => number | void;
  zoomToFit: (duration?: number) => void;
  centerAt: (x?: number, y?: number, duration?: number) => void;
}

const getNodeId = (nodeRef: string | { id: string }) => {
  return typeof nodeRef === 'object' ? nodeRef.id : nodeRef;
};

export function GlobalGraphExplorer() {
  const t = useTranslations('page_graph');
  const { resolvedTheme } = useTheme();
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [hierarchicalView, setHierarchicalView] = useState(false);
  const [graphData, setGraphData] = useState<{
    nodes: GraphNode[];
    links: GraphEdge[];
  }>({ nodes: [], links: [] });
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
  const [lastClickTime, setLastClickTime] = useState(0);
  const [lastClickedNode, setLastClickedNode] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null);

  // Type guard for string description
  const isStringDescription = (desc: unknown): desc is string => {
    return typeof desc === 'string';
  };

  // Color scales
  const workspaceColorScale = useMemo(
    () => d3.scaleOrdinal(d3.schemeCategory10),
    [],
  );
  const nodeTypeColors = useMemo(
    () => ({
      collection: '#3b82f6', // blue
      document: '#10b981', // green
      entity: '#f59e0b', // orange
    }),
    [],
  );

  const handleResize = useCallback(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.offsetWidth,
        height: containerRef.current.offsetHeight,
      });
    }
  }, []);

  useEffect(() => {
    window.addEventListener('resize', handleResize);
    // Use setTimeout to ensure container is rendered
    const timer = setTimeout(() => {
      handleResize();
    }, 100);
    return () => {
      window.removeEventListener('resize', handleResize);
      clearTimeout(timer);
    };
  }, [handleResize]);

  // Define data loading function for reuse
  const fetchHierarchyData = useCallback(async () => {
    setLoading(true);
    setHasSearched(true);

    try {
      const response = await fetch('/api/v1/graphs/hierarchy/global', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: '',
          top_k: 50,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Auto-load graph data:', {
          nodeCount: data.nodes?.length || 0,
          edgeCount: data.edges?.length || 0,
          statistics: data.statistics,
        });
        const nodes = data.nodes || [];
        const links = data.edges || [];

        // Calculate node values and RESET coordinates for DAG layout
        nodes.forEach((node: GraphNode) => {
          if (!node.type) node.type = 'entity';

          // Reset coordinates to force DAG layout to re-calculate
          delete node.x;
          delete node.y;
          delete node.vx;
          delete node.vy;
          delete node.fx;
          delete node.fy;

          const degree = links.filter((l: GraphEdge) => {
            const sourceId =
              typeof l.source === 'object' ? l.source.id : l.source;
            const targetId =
              typeof l.target === 'object' ? l.target.id : l.target;
            return sourceId === node.id || targetId === node.id;
          }).length;
          node.val = Math.max(degree, 5);
        });

        setGraphData({ nodes, links });

        // Auto-expand ALL collections AND documents
        const expandableIds = nodes
          .filter(
            (n: GraphNode) => n.type === 'collection' || n.type === 'document',
          )
          .map((n: GraphNode) => n.id);
        setExpandedNodes(new Set(expandableIds));
        console.log(`✓ Auto-expanded ${expandableIds.length} nodes`);

        // Force engine restart for DAG layout
        if (graphRef.current) {
          graphRef.current.d3ReheatSimulation();
          setTimeout(() => {
            graphRef.current.zoomToFit(400, 50);
          }, 500);
        }
      } else {
        console.error('Auto-load failed:', response.status);
      }
    } catch (error) {
      console.error('Auto-load error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-load graph on mount
  useEffect(() => {
    setHierarchicalView(true);
    fetchHierarchyData();
  }, [fetchHierarchyData]);

  const handleSearch = async () => {
    if (!hierarchicalView && !query.trim()) return;

    setLoading(true);
    setHasSearched(true);

    try {
      const endpoint = hierarchicalView
        ? '/api/v1/graphs/hierarchy/global'
        : '/api/v1/graphs/search/global';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query || '',
          top_k: 50,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Graph data received:', {
          nodeCount: data.nodes?.length || 0,
          edgeCount: data.edges?.length || 0,
          statistics: data.statistics,
        });

        if (hierarchicalView) {
          // Hierarchical data
          const nodes = data.nodes || [];
          const links = data.edges || [];

          // Ensure all nodes have a type
          nodes.forEach((node: GraphNode) => {
            if (!node.type) {
              console.warn('Node without type in hierarchy:', node);
              node.type = 'entity';
            }
          });

          // Calculate node values
          nodes.forEach((node: GraphNode) => {
            const degree = links.filter((l: GraphEdge) => {
              const sourceId =
                typeof l.source === 'object' ? l.source.id : l.source;
              const targetId =
                typeof l.target === 'object' ? l.target.id : l.target;
              return sourceId === node.id || targetId === node.id;
            }).length;
            node.val = Math.max(degree, 5);
          });

          setGraphData({ nodes, links });

          // Auto-expand collections by default
          const collectionIds = nodes
            .filter((n: GraphNode) => n.type === 'collection')
            .map((n: GraphNode) => n.id);
          setExpandedNodes(new Set(collectionIds));
        } else {
          // Flat entity view
          const nodes = data.nodes || [];
          const links = data.edges || [];

          // Ensure all nodes have a type
          nodes.forEach((node: GraphNode) => {
            if (!node.type) {
              console.warn('Node without type in search:', node);
              node.type = 'entity';
            }
          });

          nodes.forEach((node: GraphNode) => {
            const degree = links.filter((l: GraphEdge) => {
              const sourceId =
                typeof l.source === 'object' ? l.source.id : l.source;
              const targetId =
                typeof l.target === 'object' ? l.target.id : l.target;
              return sourceId === node.id || targetId === node.id;
            }).length;
            node.val = Math.max(degree, 5);
          });

          setGraphData({ nodes, links });
        }

        setTimeout(() => {
          if (graphRef.current) {
            graphRef.current.zoomToFit(400);
          }
        }, 500);
      } else {
        const errorText = await response.text();
        console.error('Search failed:', response.status, errorText);
        setGraphData({ nodes: [], links: [] });
      }
    } catch (error) {
      console.error('Search error:', error);
      setGraphData({ nodes: [], links: [] });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // Helper function to navigate to knowledge graph
  const navigateToGraph = (node: any) => {
    if (node.type === 'collection') {
      // Extract collection ID from node.id (format: "col_<id>")
      const collectionId =
        node.metadata?.collection_id || node.id.replace('col_', '');
      router.push(`/workspace/collections/${collectionId}/graph`);
    } else if (node.type === 'document') {
      // Extract collection and document IDs
      const collectionId = node.metadata?.collection_id;
      const documentId = node.metadata?.document_id;
      if (collectionId && documentId) {
        // Navigate to collection graph with document filter
        router.push(
          `/workspace/collections/${collectionId}/graph?doc=${documentId}`,
        );
      }
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleNodeClick = (node: any) => {
    const currentTime = Date.now();
    const isDoubleClick =
      lastClickedNode === node.id && currentTime - lastClickTime < 300; // 300ms for double click

    setLastClickTime(currentTime);
    setLastClickedNode(node.id);

    if (isDoubleClick) {
      // Double click: navigate to graph
      if (node.type === 'collection' || node.type === 'document') {
        navigateToGraph(node);
        return;
      }
    }

    // Single click behavior
    if (
      hierarchicalView &&
      (node.type === 'collection' || node.type === 'document')
    ) {
      // Toggle expand/collapse
      setExpandedNodes((prev) => {
        const newSet = new Set(prev);
        if (newSet.has(node.id)) {
          newSet.delete(node.id);
        } else {
          newSet.add(node.id);
        }
        return newSet;
      });
    } else {
      // Show node details
      setSelectedNode(node);
      setNodeDetailOpen(true);
      // Zoom to node
      graphRef.current?.centerAt(node.x, node.y, 1000);
      graphRef.current?.zoom(8, 2000);
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleNodeHover = (node: any) => {
    if (node) {
      setHoveredNode(node);
      // Highlight connected nodes and links
      const connectedNodeIds = new Set<string>();
      const connectedLinkIds = new Set<string>();

      filteredGraphData.links.forEach((link) => {
        const sourceId =
          typeof link.source === 'object' ? link.source.id : link.source;
        const targetId =
          typeof link.target === 'object' ? link.target.id : link.target;

        if (sourceId === node.id || targetId === node.id) {
          connectedNodeIds.add(sourceId);
          connectedNodeIds.add(targetId);
          connectedLinkIds.add(`${sourceId}-${targetId}`);
        }
      });

      setHighlightNodes(connectedNodeIds);
      setHighlightLinks(connectedLinkIds);
    } else {
      setHoveredNode(null);
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    }
  };

  const handleZoomIn = () => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom() || 1;
      graphRef.current.zoom(currentZoom * 1.5, 500);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom() || 1;
      graphRef.current.zoom(currentZoom / 1.5, 500);
    }
  };

  const handleResetView = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
    }
  };

  // Filter nodes and links based on expanded state and type filter
  const filteredGraphData = useMemo(() => {
    let { nodes, links } = graphData;

    // Apply type filter
    if (nodeTypeFilter !== 'all') {
      nodes = nodes.filter((n) => n.type === nodeTypeFilter);
    }

    if (!hierarchicalView) {
      // Filter links to only include those between visible nodes
      const nodeIds = new Set(nodes.map((n) => n.id));
      links = links.filter((link) => {
        const sourceId =
          typeof link.source === 'object'
            ? (link.source as { id: string }).id
            : link.source;
        const targetId =
          typeof link.target === 'object'
            ? (link.target as { id: string }).id
            : link.target;
        return nodeIds.has(sourceId) && nodeIds.has(targetId);
      });
      return { nodes, links };
    }

    // Hierarchical filtering
    const visibleNodes = new Set<string>();
    const visibleLinks: GraphEdge[] = [];

    // Always show collections
    nodes
      .filter((n) => n.type === 'collection')
      .forEach((n) => visibleNodes.add(n.id));

    // Show documents if their collection is expanded
    nodes
      .filter((n) => n.type === 'document')
      .forEach((doc) => {
        const parentLink = links.find((l) => {
          const targetId = getNodeId(l.target);
          return targetId === doc.id && l.type === 'CONTAINS';
        });
        const parentSource = parentLink ? getNodeId(parentLink.source) : null;
        if (parentLink && parentSource && expandedNodes.has(parentSource)) {
          visibleNodes.add(doc.id);
        }
      });

    // Show entities if their document is expanded
    nodes
      .filter((n) => n.type === 'entity')
      .forEach((ent) => {
        const parentLink = links.find((l) => {
          const targetId = getNodeId(l.target);
          return targetId === ent.id && l.type === 'EXTRACTED_FROM';
        });
        const parentSource = parentLink ? getNodeId(parentLink.source) : null;
        if (parentLink && parentSource && expandedNodes.has(parentSource)) {
          visibleNodes.add(ent.id);
        }
      });

    // Filter links to only show those between visible nodes
    links.forEach((link) => {
      const sourceId =
        typeof link.source === 'object'
          ? (link.source as { id: string }).id
          : link.source;
      const targetId =
        typeof link.target === 'object'
          ? (link.target as { id: string }).id
          : link.target;
      if (visibleNodes.has(sourceId) && visibleNodes.has(targetId)) {
        visibleLinks.push(link);
      }
    });

    return {
      nodes: nodes.filter((n) => visibleNodes.has(n.id)),
      links: visibleLinks,
    };
  }, [graphData, hierarchicalView, expandedNodes, nodeTypeFilter]);

  useEffect(() => {
    if (!graphRef.current || !hierarchicalView) return;

    const chargeForce = graphRef.current.d3Force?.('charge') as
      | d3.ForceManyBody<GraphNode>
      | undefined;
    if (chargeForce) {
      chargeForce.strength(-500);
    }

    const linkForce = graphRef.current.d3Force?.('link') as
      | d3.ForceLink<GraphNode, GraphEdge>
      | undefined;
    if (linkForce) {
      linkForce.distance(50);
    }

    graphRef.current.d3ReheatSimulation?.();
  }, [
    hierarchicalView,
    filteredGraphData.nodes.length,
    filteredGraphData.links.length,
  ]);

  // Calculate statistics
  const stats = useMemo(() => {
    const { nodes, links } = filteredGraphData;
    const typeCounts = nodes.reduce(
      (acc, node) => {
        acc[node.type] = (acc[node.type] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    const linkTypeCounts = links.reduce(
      (acc, link) => {
        acc[link.type] = (acc[link.type] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    return {
      totalNodes: nodes.length,
      totalLinks: links.length,
      typeCounts,
      linkTypeCounts,
    };
  }, [filteredGraphData]);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getNodeColor = (node: any) => {
    if (hierarchicalView) {
      return nodeTypeColors[node.type as keyof typeof nodeTypeColors] || '#999';
    } else {
      return workspaceColorScale(node.workspace || '');
    }
  };

  const getNodeShape = (node: any) => {
    if (node.type === 'collection') return 'square';
    if (node.type === 'document') return 'triangle';
    return 'circle';
  };

  return (
    <div className="relative flex h-full flex-col gap-4 p-4">
      {/* Controls */}
      <div className="absolute top-4 left-4 z-10 flex w-full max-w-md flex-col gap-2">
        <Card className="flex w-full flex-col gap-2 p-3 shadow-lg">
          <div className="flex items-center gap-2">
            <Input
              type="text"
              placeholder={
                t('search_placeholder') || 'Search global entities...'
              }
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1"
              disabled={hierarchicalView}
            />
            <Button onClick={handleSearch} disabled={loading} size="sm">
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              <span className="ml-1">
                {hierarchicalView ? 'Load' : 'Search'}
              </span>
            </Button>
          </div>
          {hierarchicalView && hasSearched && (
            <div className="text-muted-foreground flex flex-col gap-1 text-xs">
              <div className="flex items-start gap-1">
                <span>💡</span>
                <span>
                  <strong>Tree Layout:</strong> Collection (□) → Document (△) →
                  Entity (●)
                </span>
              </div>
              <div className="pl-5 text-xs">
                • Single click: expand/collapse nodes
              </div>
              <div className="pl-5 text-xs">
                • Double click: open detailed knowledge graph
              </div>
              <div className="pl-5 text-xs">• Hover: highlight connections</div>
            </div>
          )}
          {hasSearched && filteredGraphData.nodes.length > 200 && (
            <div className="flex items-start gap-1 text-xs text-yellow-600 dark:text-yellow-500">
              <span>⚠️</span>
              <span>
                Large graph ({filteredGraphData.nodes.length} nodes).
                Performance may be affected.
              </span>
            </div>
          )}
        </Card>

        <Card className="flex flex-col gap-2 p-3 shadow-lg">
          <div className="flex flex-row items-center gap-2">
            <Switch
              id="hierarchical-mode"
              checked={hierarchicalView}
              onCheckedChange={(checked) => {
                setHierarchicalView(checked);
                setGraphData({ nodes: [], links: [] });
                setHasSearched(false);
                if (checked) {
                  // Auto-load hierarchy when enabling
                  setTimeout(() => fetchHierarchyData(), 100);
                }
              }}
            />
            <Label
              htmlFor="hierarchical-mode"
              className="flex-1 cursor-pointer"
            >
              Hierarchical View (Collection → Document → Entity)
            </Label>
          </div>
          {!hierarchicalView && (
            <div className="flex items-center gap-2">
              <Filter className="text-muted-foreground h-4 w-4" />
              <Select value={nodeTypeFilter} onValueChange={setNodeTypeFilter}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Filter by type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="collection">Collections</SelectItem>
                  <SelectItem value="document">Documents</SelectItem>
                  <SelectItem value="entity">Entities</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </Card>

        {/* Zoom Controls */}
        {hasSearched && filteredGraphData.nodes.length > 0 && (
          <Card className="flex flex-col gap-2 p-2 shadow-lg">
            <div className="flex flex-row items-center gap-2">
              <Button
                onClick={handleZoomIn}
                size="sm"
                variant="outline"
                title="Zoom In"
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button
                onClick={handleZoomOut}
                size="sm"
                variant="outline"
                title="Zoom Out"
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button
                onClick={handleResetView}
                size="sm"
                variant="outline"
                title="Reset View"
              >
                <RotateCcw className="h-4 w-4" />
              </Button>
            </div>
            {hierarchicalView && (
              <div className="flex flex-row items-center gap-2">
                <Button
                  onClick={() => {
                    // Expand all collections and documents
                    const allExpandableIds = graphData.nodes
                      .filter(
                        (n) => n.type === 'collection' || n.type === 'document',
                      )
                      .map((n) => n.id);
                    setExpandedNodes(new Set(allExpandableIds));
                  }}
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  title="Expand All"
                >
                  Expand All
                </Button>
                <Button
                  onClick={() => {
                    // Collapse all
                    setExpandedNodes(new Set());
                  }}
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  title="Collapse All"
                >
                  Collapse All
                </Button>
              </div>
            )}
          </Card>
        )}
      </div>

      {/* Legend and Stats */}
      {hasSearched && filteredGraphData.nodes.length > 0 && (
        <div className="absolute top-32 left-4 z-10 flex flex-col gap-2">
          <Card className="bg-background/95 max-w-xs p-3 shadow-lg backdrop-blur-sm">
            {hierarchicalView ? (
              <>
                <div className="text-muted-foreground mb-2 text-xs font-bold tracking-wide uppercase">
                  Node Types
                </div>
                <div className="flex flex-col gap-2">
                  <div className="hover:bg-muted/50 flex items-center gap-2 rounded p-1">
                    <div
                      className="h-4 w-4 rounded-sm border border-gray-300"
                      style={{ backgroundColor: nodeTypeColors.collection }}
                    ></div>
                    <span className="text-xs font-medium">Collection</span>
                    <span className="text-muted-foreground ml-auto text-xs">
                      □
                    </span>
                  </div>
                  <div className="hover:bg-muted/50 flex items-center gap-2 rounded p-1">
                    <div
                      className="h-4 w-4 border border-gray-300"
                      style={{
                        backgroundColor: nodeTypeColors.document,
                        clipPath: 'polygon(50% 0%, 100% 100%, 0% 100%)',
                      }}
                    ></div>
                    <span className="text-xs font-medium">Document</span>
                    <span className="text-muted-foreground ml-auto text-xs">
                      △
                    </span>
                  </div>
                  <div className="hover:bg-muted/50 flex items-center gap-2 rounded p-1">
                    <div
                      className="h-4 w-4 rounded-full border border-gray-300"
                      style={{ backgroundColor: nodeTypeColors.entity }}
                    ></div>
                    <span className="text-xs font-medium">Entity</span>
                    <span className="text-muted-foreground ml-auto text-xs">
                      ●
                    </span>
                  </div>
                </div>
                <div className="text-muted-foreground mt-2 space-y-1 text-xs">
                  <div>
                    📍 <strong>Tree structure showing hierarchy</strong>
                  </div>
                  <div>• Click: expand/collapse child nodes</div>
                  <div>• Double-click: view detailed graph</div>
                </div>
              </>
            ) : (
              <>
                <div className="text-muted-foreground mb-2 text-xs font-bold tracking-wide uppercase">
                  Collections
                </div>
                <div className="flex max-h-32 flex-col gap-1 overflow-y-auto">
                  {_.uniq(
                    filteredGraphData.nodes
                      .filter((n) => n.type === 'collection')
                      .map((n) => ({ id: n.id, name: n.name })),
                  )
                    .filter((col) => col.id && col.name)
                    .map((col) => (
                      <div
                        key={col.id}
                        className="hover:bg-muted/30 flex items-center gap-2 rounded p-1"
                      >
                        <div
                          className="h-3 w-3 rounded-sm"
                          style={{
                            backgroundColor: workspaceColorScale(col.id),
                          }}
                        ></div>
                        <span className="truncate text-xs" title={col.name}>
                          {col.name}
                        </span>
                      </div>
                    ))}
                  {filteredGraphData.nodes.filter(
                    (n) => n.type === 'collection',
                  ).length === 0 && (
                    <div className="text-muted-foreground text-xs italic">
                      No collections in view
                    </div>
                  )}
                </div>
                <div className="my-2 border-t"></div>
                <div className="text-muted-foreground flex items-center gap-2">
                  <div className="h-0 w-6 border-t-2 border-dashed"></div>
                  <span className="text-xs">Cross-Collection Links</span>
                </div>
              </>
            )}
          </Card>

          {/* Statistics */}
          {showStats && (
            <Card className="bg-background/95 max-w-xs p-3 shadow-lg backdrop-blur-sm">
              <div className="mb-2 flex items-center justify-between">
                <div className="text-muted-foreground text-xs font-bold tracking-wide uppercase">
                  Statistics
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="hover:bg-destructive/10 h-6 w-6 p-0"
                  onClick={() => setShowStats(false)}
                  title="Hide statistics"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex flex-col gap-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Total Nodes:</span>
                  <span className="font-bold">{stats.totalNodes}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Total Links:</span>
                  <span className="font-bold">{stats.totalLinks}</span>
                </div>

                {stats.totalNodes > 0 && (
                  <>
                    <div className="my-1 border-t"></div>
                    <div className="text-muted-foreground mb-1 text-xs font-semibold">
                      Node Types:
                    </div>
                    {Object.entries(stats.typeCounts)
                      .filter(
                        ([type]) => type !== 'undefined' && type !== 'unknown',
                      )
                      .map(([type, count]) => (
                        <div
                          key={type}
                          className="flex items-center justify-between gap-2 pl-2"
                        >
                          <div className="flex items-center gap-2">
                            <div
                              className="h-3 w-3 rounded-sm"
                              style={{
                                backgroundColor:
                                  nodeTypeColors[
                                    type as keyof typeof nodeTypeColors
                                  ] || '#999',
                              }}
                            ></div>
                            <span className="capitalize">
                              {type === 'collection'
                                ? 'Collections'
                                : type === 'document'
                                  ? 'Documents'
                                  : type === 'entity'
                                    ? 'Entities'
                                    : type}
                            </span>
                          </div>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                  </>
                )}

                {hoveredNode && (
                  <>
                    <div className="my-2 border-t"></div>
                    <div className="bg-primary/10 rounded p-2">
                      <div className="mb-1 text-xs font-bold">
                        Selected Node:
                      </div>
                      <div
                        className="mb-1 truncate font-medium"
                        title={hoveredNode.name || hoveredNode.entity_name}
                      >
                        {hoveredNode.name || hoveredNode.entity_name}
                      </div>
                      <div className="text-muted-foreground flex items-center justify-between">
                        <span>Type:</span>
                        <span className="capitalize">{hoveredNode.type}</span>
                      </div>
                      {/* Show description for collections or preview for entities */}
                      {(() => {
                        const desc = hoveredNode.description;
                        if (isStringDescription(desc)) {
                          return (
                            <div className="text-muted-foreground mt-1 line-clamp-2 text-[10px] italic">
                              {desc}
                            </div>
                          ) as ReactNode;
                        }
                        return null as ReactNode;
                      })()}
                      {(() => {
                        const metadataContent = hoveredNode.metadata?.content;
                        if (
                          hoveredNode.type === 'entity' &&
                          typeof metadataContent === 'string'
                        ) {
                          return (
                            <div className="text-muted-foreground mt-1 line-clamp-2 text-[10px]">
                              {metadataContent.substring(0, 100)}...
                            </div>
                          );
                        }
                        return null;
                      })()}
                      <div className="text-muted-foreground mt-1 flex items-center justify-between border-t pt-1">
                        <span>Connections:</span>
                        <span className="font-medium">
                          {highlightNodes.size - 1}
                        </span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Graph Container */}
      <div
        ref={containerRef}
        className="bg-card flex-1 overflow-hidden rounded-lg border"
        style={{ minHeight: '400px' }}
      >
        {loading ? (
          <div className="text-muted-foreground flex h-full items-center justify-center">
            <Loader2 className="mr-2 h-6 w-6 animate-spin" />
            Loading graph...
          </div>
        ) : hasSearched && filteredGraphData.nodes.length === 0 ? (
          <div className="text-muted-foreground flex h-full flex-col items-center justify-center gap-4">
            <div className="text-6xl opacity-20">🔍</div>
            <div className="text-center">
              <div className="mb-2 text-lg font-semibold">
                {hierarchicalView ? 'No Data to Display' : 'No Entities Found'}
              </div>
              <div className="text-sm">
                {hierarchicalView
                  ? 'Please create collections and upload documents with knowledge graph enabled.'
                  : 'Try a different search term or enable hierarchical view to see all data.'}
              </div>
            </div>
          </div>
        ) : !hasSearched ? (
          <div className="text-muted-foreground flex h-full flex-col items-center justify-center gap-4">
            <div className="text-6xl opacity-20">📊</div>
            <div className="text-center">
              <div className="mb-2 text-lg font-semibold">
                Global Knowledge Graph
              </div>
              <div className="text-sm">
                {hierarchicalView
                  ? 'Click "Load" to view the hierarchical structure of your knowledge base.'
                  : 'Enter a search term to find entities across all collections.'}
              </div>
            </div>
          </div>
        ) : dimensions.width > 0 && dimensions.height > 0 ? (
          <ForceGraph2D
            key={hierarchicalView ? 'hierarchical-layout' : 'standard-layout'}
            ref={graphRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={filteredGraphData}
            nodeLabel={(node: any) => node.name || node.entity_name} // eslint-disable-line @typescript-eslint/no-explicit-any
            nodeColor={(node: any) => {
              // eslint-disable-line @typescript-eslint/no-explicit-any
              if (hoveredNode) {
                return highlightNodes.has(node.id)
                  ? getNodeColor(node)
                  : resolvedTheme === 'dark'
                    ? '#333'
                    : '#ddd';
              }
              return getNodeColor(node);
            }}
            nodeRelSize={8}
            nodeVal={(node: any) => {
              // eslint-disable-line @typescript-eslint/no-explicit-any
              const baseSize = hierarchicalView
                ? node.type === 'collection'
                  ? 12
                  : node.type === 'document'
                    ? 8
                    : 6
                : 6;
              return hoveredNode?.id === node.id ? baseSize * 1.5 : baseSize;
            }}
            linkColor={(link: any) => {
              // eslint-disable-line @typescript-eslint/no-explicit-any
              const sourceId =
                typeof link.source === 'object' ? link.source.id : link.source;
              const targetId =
                typeof link.target === 'object' ? link.target.id : link.target;
              const linkId = `${sourceId}-${targetId}`;

              if (hoveredNode && !highlightLinks.has(linkId)) {
                return resolvedTheme === 'dark' ? '#222' : '#eee';
              }

              if (link.type === 'federation') return '#FFA500';
              if (link.type === 'CONTAINS') return '#3b82f6';
              if (link.type === 'EXTRACTED_FROM') return '#10b981';
              return resolvedTheme === 'dark' ? '#555' : '#999';
            }}
            linkLineDash={(
              link: any, // eslint-disable-line @typescript-eslint/no-explicit-any
            ) => (link.type === 'federation' ? [4, 2] : null)}
            linkWidth={(link: any) => {
              // eslint-disable-line @typescript-eslint/no-explicit-any
              const sourceId =
                typeof link.source === 'object' ? link.source.id : link.source;
              const targetId =
                typeof link.target === 'object' ? link.target.id : link.target;
              const linkId = `${sourceId}-${targetId}`;
              const baseWidth = link.type === 'federation' ? 2 : 1;
              return hoveredNode && highlightLinks.has(linkId)
                ? baseWidth * 2
                : baseWidth;
            }}
            linkDirectionalParticles={(
              link: any, // eslint-disable-line @typescript-eslint/no-explicit-any
            ) => (link.type === 'federation' ? 2 : 0)}
            linkDirectionalParticleSpeed={0.005}
            linkDirectionalParticleWidth={(link: any) => {
              // eslint-disable-line @typescript-eslint/no-explicit-any
              const sourceId =
                typeof link.source === 'object' ? link.source.id : link.source;
              const targetId =
                typeof link.target === 'object' ? link.target.id : link.target;
              const linkId = `${sourceId}-${targetId}`;
              return hoveredNode && highlightLinks.has(linkId) ? 4 : 2;
            }}
            backgroundColor={resolvedTheme === 'dark' ? '#020817' : '#ffffff'}
            onNodeClick={handleNodeClick}
            onNodeHover={handleNodeHover}
            dagMode={hierarchicalView ? 'td' : undefined}
            dagLevelDistance={hierarchicalView ? 200 : undefined}
            cooldownTicks={hierarchicalView ? 100 : 100}
            d3AlphaDecay={hierarchicalView ? 0.01 : 0.02}
            d3VelocityDecay={hierarchicalView ? 0.3 : 0.3}
            warmupTicks={hierarchicalView ? 50 : 50}
            nodeCanvasObject={(node: any, ctx: any, globalScale: number) => {
              // eslint-disable-line @typescript-eslint/no-explicit-any
              const label = node.name || node.entity_name || '';
              const fontSize = Math.max(10, 14 / globalScale);
              const x = node.x ?? 0;
              const y = node.y ?? 0;

              const isHovered = hoveredNode?.id === node.id;
              const isHighlighted = highlightNodes.has(node.id);
              const isDimmed = hoveredNode && !isHighlighted;

              const baseSize = hierarchicalView
                ? node.type === 'collection'
                  ? 10
                  : node.type === 'document'
                    ? 7
                    : 5
                : 5;
              const size = isHovered ? baseSize * 1.4 : baseSize;

              // Draw glow for hovered node
              if (isHovered) {
                ctx.shadowBlur = 20;
                ctx.shadowColor = getNodeColor(node);
              } else {
                ctx.shadowBlur = 0;
              }

              // Draw node shape with outline
              ctx.fillStyle = isDimmed
                ? resolvedTheme === 'dark'
                  ? '#333'
                  : '#ddd'
                : getNodeColor(node);
              ctx.strokeStyle =
                isHovered || isHighlighted
                  ? resolvedTheme === 'dark'
                    ? '#fff'
                    : '#000'
                  : 'rgba(0,0,0,0.2)';
              ctx.lineWidth = isHovered ? 3 : isHighlighted ? 2 : 1;
              ctx.beginPath();

              if (node.type === 'collection') {
                // Rounded square
                const radius = size * 0.2;
                ctx.moveTo(x - size + radius, y - size);
                ctx.lineTo(x + size - radius, y - size);
                ctx.quadraticCurveTo(
                  x + size,
                  y - size,
                  x + size,
                  y - size + radius,
                );
                ctx.lineTo(x + size, y + size - radius);
                ctx.quadraticCurveTo(
                  x + size,
                  y + size,
                  x + size - radius,
                  y + size,
                );
                ctx.lineTo(x - size + radius, y + size);
                ctx.quadraticCurveTo(
                  x - size,
                  y + size,
                  x - size,
                  y + size - radius,
                );
                ctx.lineTo(x - size, y - size + radius);
                ctx.quadraticCurveTo(
                  x - size,
                  y - size,
                  x - size + radius,
                  y - size,
                );
                ctx.closePath();
              } else if (node.type === 'document') {
                // Triangle
                ctx.moveTo(x, y - size);
                ctx.lineTo(x + size * 0.866, y + size * 0.5);
                ctx.lineTo(x - size * 0.866, y + size * 0.5);
                ctx.closePath();
              } else {
                // Circle
                ctx.arc(x, y, size, 0, 2 * Math.PI, false);
              }
              ctx.fill();
              ctx.stroke();
              ctx.shadowBlur = 0;

              // Draw label (only if zoomed in enough or hovered)
              if (globalScale > 0.8 || isHovered) {
                ctx.font = `${isHovered ? 'bold ' : ''}${fontSize}px Sans-Serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';

                // Draw label background for better readability
                const textWidth = ctx.measureText(label).width;
                const padding = 4;
                const labelY = y + size + 4;

                ctx.fillStyle =
                  resolvedTheme === 'dark'
                    ? 'rgba(0,0,0,0.7)'
                    : 'rgba(255,255,255,0.9)';
                ctx.fillRect(
                  x - textWidth / 2 - padding,
                  labelY - 2,
                  textWidth + padding * 2,
                  fontSize + 4,
                );

                ctx.fillStyle = isDimmed
                  ? resolvedTheme === 'dark'
                    ? '#666'
                    : '#999'
                  : resolvedTheme === 'dark'
                    ? '#fff'
                    : '#000';
                ctx.fillText(label, x, labelY);
              }

              // Draw expand indicator for collections and documents
              if (
                hierarchicalView &&
                (node.type === 'collection' || node.type === 'document')
              ) {
                const isExpanded = expandedNodes.has(node.id);
                const indicatorSize = size * 0.4;

                // Draw circle background for indicator
                ctx.fillStyle = resolvedTheme === 'dark' ? '#1a1a1a' : '#fff';
                ctx.strokeStyle = getNodeColor(node);
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(x, y, indicatorSize, 0, 2 * Math.PI, false);
                ctx.fill();
                ctx.stroke();

                // Draw +/- symbol
                ctx.fillStyle = getNodeColor(node);
                ctx.font = `bold ${fontSize * 1.1}px Sans-Serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(isExpanded ? '−' : '+', x, y);
              }
            }}
          />
        ) : (
          <div className="text-muted-foreground flex h-full items-center justify-center">
            Initializing graph...
          </div>
        )}
      </div>

      {/* Node Detail Dialog */}
      <Dialog open={nodeDetailOpen} onOpenChange={setNodeDetailOpen}>
        <DialogContent className="max-h-[80vh] max-w-2xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedNode?.name || selectedNode?.entity_name}
              {(selectedNode?.type === 'collection' ||
                selectedNode?.type === 'document') && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 gap-1 text-xs"
                  onClick={() => selectedNode && navigateToGraph(selectedNode)}
                  title="View Knowledge Graph"
                >
                  <ExternalLink className="h-3 w-3" />
                  View Graph
                </Button>
              )}
            </DialogTitle>
            <DialogDescription>
              {selectedNode?.type && (
                <Badge variant="secondary" className="mt-2">
                  {selectedNode.type}
                </Badge>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {(selectedNode?.type === 'collection' ||
              selectedNode?.type === 'document') && (
              <div className="border-primary/20 bg-primary/5 rounded-lg border p-3">
                <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                  <ExternalLink className="h-4 w-4" />
                  Quick Actions
                </div>
                <Button
                  onClick={() => selectedNode && navigateToGraph(selectedNode)}
                  className="w-full"
                  size="sm"
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Open{' '}
                  {selectedNode?.type === 'collection'
                    ? 'Collection'
                    : 'Document'}{' '}
                  Knowledge Graph
                </Button>
                <p className="text-muted-foreground mt-2 text-xs">
                  {selectedNode?.type === 'collection'
                    ? 'View all entities and relationships in this collection'
                    : 'View entities extracted from this document'}
                </p>
              </div>
            )}

            {selectedNode?.description && (
              <div>
                <div className="mb-1 text-sm font-semibold">Description</div>
                <div className="text-muted-foreground text-sm">
                  {selectedNode.description}
                </div>
              </div>
            )}

            {selectedNode?.metadata && (
              <div>
                <div className="mb-1 text-sm font-semibold">Metadata</div>
                <pre className="bg-muted overflow-auto rounded p-2 text-xs">
                  {JSON.stringify(selectedNode.metadata, null, 2)}
                </pre>
              </div>
            )}

            {selectedNode?.workspace && (
              <div>
                <div className="mb-1 text-sm font-semibold">Workspace</div>
                <div className="text-muted-foreground text-sm">
                  {selectedNode.workspace}
                </div>
              </div>
            )}

            <div>
              <div className="mb-1 text-sm font-semibold">Connections</div>
              <div className="text-muted-foreground text-sm">
                {
                  filteredGraphData.links.filter((link) => {
                    const sourceId =
                      typeof link.source === 'object'
                        ? (link.source as { id: string }).id
                        : link.source;
                    const targetId =
                      typeof link.target === 'object'
                        ? (link.target as { id: string }).id
                        : link.target;
                    return (
                      sourceId === selectedNode?.id ||
                      targetId === selectedNode?.id
                    );
                  }).length
                }{' '}
                connections
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
