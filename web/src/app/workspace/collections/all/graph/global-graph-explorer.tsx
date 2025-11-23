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
  metadata?: any;
  workspace?: string;
  entity_name?: string;
  [key: string]: any;
}

interface GraphEdge {
  source: string;
  target: string;
  label: string;
  type: string;
  workspace?: string;
  [key: string]: any;
}

export function GlobalGraphExplorer() {
  const t = useTranslations('page_graph');
  const { resolvedTheme } = useTheme();
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
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);

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

  // Auto-load graph on mount
  useEffect(() => {
    // Auto-load hierarchical view on initial mount
    const autoLoad = async () => {
      setHierarchicalView(true);
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
          });
          const nodes = data.nodes || [];
          const links = data.edges || [];

          // Calculate node values
          nodes.forEach((node: any) => {
            const degree = links.filter((l: any) => {
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
            .filter((n: any) => n.type === 'collection')
            .map((n: any) => n.id);
          setExpandedNodes(new Set(collectionIds));

          setTimeout(() => {
            if (graphRef.current) {
              graphRef.current.zoomToFit(400);
            }
          }, 500);
        } else {
          const errorText = await response.text();
          console.error('Auto-load failed:', response.status, errorText);
        }
      } catch (error) {
        console.error('Auto-load error:', error);
      } finally {
        setLoading(false);
      }
    };

    autoLoad();
  }, []); // Empty dependency array = run once on mount

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
          data,
        });

        if (hierarchicalView) {
          // Hierarchical data
          const nodes = data.nodes || [];
          const links = data.edges || [];

          // Calculate node values
          nodes.forEach((node: any) => {
            const degree = links.filter((l: any) => {
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
            .filter((n: any) => n.type === 'collection')
            .map((n: any) => n.id);
          setExpandedNodes(new Set(collectionIds));
        } else {
          // Flat entity view
          const nodes = data.nodes || [];
          const links = data.edges || [];

          nodes.forEach((node: any) => {
            const degree = links.filter((l: any) => {
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

  const handleNodeClick = (node: any) => {
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
            ? (link.source as any).id
            : link.source;
        const targetId =
          typeof link.target === 'object'
            ? (link.target as any).id
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
        const parentLink = links.find(
          (l) => l.target === doc.id && l.type === 'CONTAINS',
        );
        if (parentLink && expandedNodes.has(parentLink.source)) {
          visibleNodes.add(doc.id);
        }
      });

    // Show entities if their document is expanded
    nodes
      .filter((n) => n.type === 'entity')
      .forEach((ent) => {
        const parentLink = links.find(
          (l) => l.target === ent.id && l.type === 'EXTRACTED_FROM',
        );
        if (parentLink && expandedNodes.has(parentLink.source)) {
          visibleNodes.add(ent.id);
        }
      });

    // Filter links to only show those between visible nodes
    links.forEach((link) => {
      const sourceId =
        typeof link.source === 'object' ? (link.source as any).id : link.source;
      const targetId =
        typeof link.target === 'object' ? (link.target as any).id : link.target;
      if (visibleNodes.has(sourceId) && visibleNodes.has(targetId)) {
        visibleLinks.push(link);
      }
    });

    return {
      nodes: nodes.filter((n) => visibleNodes.has(n.id)),
      links: visibleLinks,
    };
  }, [graphData, hierarchicalView, expandedNodes, nodeTypeFilter]);

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

  const getNodeColor = (node: any) => {
    if (hierarchicalView) {
      return nodeTypeColors[node.type as keyof typeof nodeTypeColors] || '#999';
    } else {
      return workspaceColorScale(node.workspace);
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
        <Card className="flex w-full flex-row items-center gap-2 p-2 shadow-lg">
          <Input
            type="text"
            placeholder={t('search_placeholder') || 'Search global entities...'}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 border-none focus-visible:ring-0"
            disabled={hierarchicalView}
          />
          <Button onClick={handleSearch} disabled={loading} size="sm">
            {loading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Search className="mr-2 h-4 w-4" />
            )}
            {hierarchicalView ? 'Load' : t('search') || 'Search'}
          </Button>
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
          <Card className="flex flex-row items-center gap-2 p-2 shadow-lg">
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
          </Card>
        )}
      </div>

      {/* Legend and Stats */}
      {hasSearched && filteredGraphData.nodes.length > 0 && (
        <div className="absolute top-32 left-4 z-10 flex flex-col gap-2">
          <Card className="bg-background/80 max-w-xs p-2 shadow-md backdrop-blur-sm">
            {hierarchicalView ? (
              <>
                <div className="text-muted-foreground mb-2 text-xs font-semibold">
                  Node Types
                </div>
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <div
                      className="h-3 w-3"
                      style={{ backgroundColor: nodeTypeColors.collection }}
                    ></div>
                    <span className="text-xs">
                      Collection (click to expand)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className="h-3 w-3"
                      style={{ backgroundColor: nodeTypeColors.document }}
                    ></div>
                    <span className="text-xs">Document (click to expand)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: nodeTypeColors.entity }}
                    ></div>
                    <span className="text-xs">Entity</span>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="text-muted-foreground mb-2 text-xs font-semibold">
                  Workspaces
                </div>
                <div className="flex max-h-32 flex-col gap-1 overflow-y-auto">
                  {_.uniq(filteredGraphData.nodes.map((n) => n.workspace))
                    .filter(Boolean)
                    .map((ws) => (
                      <div key={ws} className="flex items-center gap-2">
                        <div
                          className="h-3 w-3 rounded-full"
                          style={{ backgroundColor: workspaceColorScale(ws!) }}
                        ></div>
                        <span className="text-xs">{ws}</span>
                      </div>
                    ))}
                </div>
                <div className="my-2 border-t"></div>
                <div className="flex items-center gap-2">
                  <div className="h-0 w-8 border-t-2 border-dashed border-gray-400"></div>
                  <span className="text-xs">Federation (Same As)</span>
                </div>
              </>
            )}
          </Card>

          {/* Statistics */}
          {showStats && (
            <Card className="bg-background/80 max-w-xs p-2 shadow-md backdrop-blur-sm">
              <div className="mb-2 flex items-center justify-between">
                <div className="text-muted-foreground text-xs font-semibold">
                  Statistics
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-4 w-4 p-0"
                  onClick={() => setShowStats(false)}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
              <div className="flex flex-col gap-1 text-xs">
                <div>Nodes: {stats.totalNodes}</div>
                <div>Links: {stats.totalLinks}</div>
                {Object.entries(stats.typeCounts).map(([type, count]) => (
                  <div key={type} className="flex items-center gap-2">
                    <div
                      className="h-2 w-2 rounded-full"
                      style={{
                        backgroundColor:
                          nodeTypeColors[type as keyof typeof nodeTypeColors] ||
                          '#999',
                      }}
                    ></div>
                    <span className="capitalize">
                      {type}: {count}
                    </span>
                  </div>
                ))}
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
          <div className="text-muted-foreground flex h-full items-center justify-center">
            {hierarchicalView
              ? 'Click "Load" to view hierarchy'
              : 'No entities found.'}
          </div>
        ) : dimensions.width > 0 && dimensions.height > 0 ? (
          <ForceGraph2D
            ref={graphRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={filteredGraphData}
            nodeLabel={(node: any) => node.name || node.entity_name}
            nodeColor={getNodeColor}
            nodeRelSize={6}
            linkColor={(link: any) => {
              if (link.type === 'federation') return '#FFA500';
              if (link.type === 'CONTAINS') return '#3b82f6';
              if (link.type === 'EXTRACTED_FROM') return '#10b981';
              return resolvedTheme === 'dark' ? '#555' : '#999';
            }}
            linkLineDash={(link: any) =>
              link.type === 'federation' ? [4, 2] : null
            }
            linkWidth={(link: any) => (link.type === 'federation' ? 2 : 1)}
            linkDirectionalParticles={(link: any) =>
              link.type === 'federation' ? 2 : 0
            }
            linkDirectionalParticleSpeed={0.005}
            backgroundColor={resolvedTheme === 'dark' ? '#020817' : '#ffffff'}
            onNodeClick={handleNodeClick}
            nodeCanvasObject={(node: any, ctx, globalScale) => {
              const label = node.name || node.entity_name;
              const fontSize = 12 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;

              const size = hierarchicalView
                ? node.type === 'collection'
                  ? 8
                  : node.type === 'document'
                    ? 6
                    : 5
                : 5;

              // Draw node shape
              ctx.fillStyle = getNodeColor(node);
              ctx.beginPath();

              if (node.type === 'collection') {
                // Square
                ctx.rect(node.x - size, node.y - size, size * 2, size * 2);
              } else if (node.type === 'document') {
                // Triangle
                ctx.moveTo(node.x, node.y - size);
                ctx.lineTo(node.x + size, node.y + size);
                ctx.lineTo(node.x - size, node.y + size);
                ctx.closePath();
              } else {
                // Circle
                ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);
              }
              ctx.fill();

              // Draw label
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillStyle = resolvedTheme === 'dark' ? '#fff' : '#000';
              ctx.fillText(label, node.x, node.y + size + 8);

              // Draw expand indicator for collections and documents
              if (
                hierarchicalView &&
                (node.type === 'collection' || node.type === 'document')
              ) {
                const isExpanded = expandedNodes.has(node.id);
                ctx.fillStyle = '#fff';
                ctx.font = `bold ${fontSize * 1.2}px Sans-Serif`;
                ctx.fillText(isExpanded ? '−' : '+', node.x, node.y);
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
            <DialogTitle>
              {selectedNode?.name || selectedNode?.entity_name}
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
                        ? (link.source as any).id
                        : link.source;
                    const targetId =
                      typeof link.target === 'object'
                        ? (link.target as any).id
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
