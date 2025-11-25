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
import * as d3 from 'd3';
import {
  ExternalLink,
  FileText,
  Folder,
  Loader2,
  Network,
  RotateCcw,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

const ForceGraph2D = dynamic(
  () => import('react-force-graph-2d').then((mod) => mod.default || mod),
  {
    ssr: false,
  },
);

type NodeMetadata = {
  collection_id?: string | number;
  document_id?: string | number;
  description?: string;
  [key: string]: unknown;
};

interface GraphNode {
  id: string;
  type: 'collection' | 'document' | 'entity';
  name: string;
  description?: string;
  metadata?: NodeMetadata;
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

const getNodeId = (nodeRef: string | { id: string }) => {
  return typeof nodeRef === 'object' ? nodeRef.id : nodeRef;
};

const getMetadataValue = (node: GraphNode, key: keyof NodeMetadata) => {
  const value = node.metadata?.[key];
  if (value === undefined || value === null) {
    return undefined;
  }
  return String(value);
};

export function GlobalGraphExplorer() {
  const t = useTranslations('page_graph');
  const { resolvedTheme } = useTheme();
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState<{
    nodes: GraphNode[];
    links: GraphEdge[];
  }>({ nodes: [], links: [] });
  const [hasSearched, setHasSearched] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [nodeDetailOpen, setNodeDetailOpen] = useState(false);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [highlightNodes, setHighlightNodes] = useState(new Set<string>());
  const [highlightLinks, setHighlightLinks] = useState(new Set<string>());
  const [lastClickTime, setLastClickTime] = useState(0);
  const [lastClickedNode, setLastClickedNode] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null);
  const hierarchicalView = true;

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
  const fetchHierarchyData = useCallback(async (searchTerm = '') => {
    setLoading(true);
    setHasSearched(true);

    try {
      const response = await fetch('/api/v1/graphs/hierarchy/global', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchTerm.trim(),
          top_k: 100,
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

        // Calculate node values and reset coordinates for DAG layout
        nodes.forEach((node: GraphNode) => {
          if (!node.type) node.type = 'entity';
          if (!node.description && node.metadata?.description) {
            node.description = String(node.metadata.description);
          }

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

        const collectionIds = nodes
          .filter((n: GraphNode) => n.type === 'collection')
          .map((n: GraphNode) => n.id);
        setExpandedNodes(new Set(collectionIds));
        console.log(`✓ Auto-expanded ${collectionIds.length} collections`);

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
    fetchHierarchyData();
  }, [fetchHierarchyData]);

  const handleSearch = async () => {
    await fetchHierarchyData(query);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // Helper function to navigate to knowledge graph
  const navigateToGraph = (node: GraphNode) => {
    if (node.type === 'collection') {
      const metadataId = getMetadataValue(node, 'collection_id');
      const fallback = node.id.replace(/^col_/, '');
      const collectionId = metadataId || fallback;
      if (collectionId) {
        router.push(`/workspace/collections/${collectionId}/graph`);
      }
      return;
    }

    if (node.type === 'document') {
      const collectionId = getMetadataValue(node, 'collection_id');
      const documentId = getMetadataValue(node, 'document_id');
      if (collectionId) {
        const targetUrl = documentId
          ? `/workspace/collections/${collectionId}/graph?doc=${documentId}`
          : `/workspace/collections/${collectionId}/graph`;
        router.push(targetUrl);
      }
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleNodeClick = (node: any) => {
    const currentTime = Date.now();
    const isDoubleClick =
      lastClickedNode === node.id && currentTime - lastClickTime < 500;

    setLastClickTime(currentTime);
    setLastClickedNode(node.id);

    if (isDoubleClick) {
      if (node.type === 'collection' || node.type === 'document') {
        navigateToGraph(node);
        return;
      }
    }

    if (node.type === 'collection' || node.type === 'document') {
      setExpandedNodes((prev) => {
        const updated = new Set(prev);
        if (updated.has(node.id)) {
          updated.delete(node.id);
        } else {
          updated.add(node.id);
        }
        return updated;
      });
    }

    setSelectedNode(node);
    setNodeDetailOpen(true);
    const targetX = node.x ?? 0;
    const targetY = node.y ?? 0;
    graphRef.current?.centerAt(targetX, targetY, 800);
    graphRef.current?.zoom(5, 1000);
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleNodeHover = (node: any) => {
    if (node) {
      setHoveredNode(node);
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

  const filteredGraphData = useMemo(() => {
    const { nodes, links } = graphData;
    const visibleNodes = new Set<string>();
    const visibleLinks: GraphEdge[] = [];

    nodes
      .filter((n) => n.type === 'collection')
      .forEach((n) => visibleNodes.add(n.id));

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
  }, [graphData, expandedNodes]);

  useEffect(() => {
    if (!graphRef.current) return;

    const chargeForce = graphRef.current.d3Force?.('charge') as
      | d3.ForceManyBody<GraphNode>
      | undefined;
    if (chargeForce) {
      chargeForce.strength(-320);
    }

    const linkForce = graphRef.current.d3Force?.('link') as
      | d3.ForceLink<GraphNode, GraphEdge>
      | undefined;
    if (linkForce) {
      linkForce.distance((link) =>
        link.type === 'CONTAINS' ? 80 : link.type === 'EXTRACTED_FROM' ? 60 : 40,
      );
    }

    graphRef.current.d3ReheatSimulation?.();
  }, [filteredGraphData.nodes.length, filteredGraphData.links.length]);

  const metadataDescription =
    typeof selectedNode?.metadata?.description === 'string'
      ? (selectedNode?.metadata?.description as string)
      : undefined;
  const selectedDescription =
    selectedNode?.description || metadataDescription;

  const selectedMetadataEntries =
    selectedNode?.metadata
      ? Object.entries(selectedNode.metadata).filter(
        ([, value]) =>
          ['string', 'number', 'boolean'].includes(typeof value),
      )
      : [];

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getNodeColor = (node: any) => {
    return nodeTypeColors[node.type as keyof typeof nodeTypeColors] || '#999';
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
                t('search_placeholder') ||
                'Filter collections, documents or entities...'
              }
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1"
            />
            <Button
              onClick={handleSearch}
              disabled={loading}
              size="sm"
              variant="secondary"
              title="Refresh directory view"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RotateCcw className="h-4 w-4" />
              )}
              <span className="ml-1">Reload</span>
            </Button>
          </div>

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
      </div>



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
                No Data to Display
              </div>
              <div className="text-sm">
                Please create collections and upload documents with knowledge
                graph enabled.
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
              <div className="text-sm">Loading hierarchy...</div>
            </div>
          </div>
        ) : dimensions.width > 0 && dimensions.height > 0 ? (
          <ForceGraph2D
            key="hierarchical-layout"
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
              const baseSize =
                node.type === 'collection'
                  ? 14
                  : node.type === 'document'
                    ? 10
                    : 6;
              return hoveredNode?.id === node.id ? baseSize * 1.3 : baseSize;
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
            dagLevelDistance={hierarchicalView ? 120 : undefined}
            cooldownTicks={100}
            d3AlphaDecay={0.01}
            d3VelocityDecay={0.3}
            warmupTicks={50}
            nodeCanvasObject={(node: any, ctx: any, globalScale: number) => {
              // eslint-disable-line @typescript-eslint/no-explicit-any
              const label = node.name || node.entity_name || '';
              const x = node.x ?? 0;
              const y = node.y ?? 0;
              const nodeType = (node.type || 'entity') as GraphNode['type'];
              const isHovered = hoveredNode?.id === node.id;
              const isHighlighted = highlightNodes.has(node.id);
              const isDimmed = hoveredNode && !isHighlighted;

              const baseSize =
                nodeType === 'collection'
                  ? 16
                  : nodeType === 'document'
                    ? 12
                    : 7;
              const size = isHovered ? baseSize * 1.2 : baseSize;
              const fillColor = isDimmed
                ? resolvedTheme === 'dark'
                  ? '#2f3542'
                  : '#d4d4d4'
                : getNodeColor(node);

              ctx.save();
              ctx.translate(x, y);
              ctx.fillStyle = fillColor;
              ctx.strokeStyle =
                resolvedTheme === 'dark' ? 'rgba(255,255,255,0.15)' : '#ffffff';
              ctx.lineWidth = isHovered ? 2 : 1;

              ctx.beginPath();
              if (nodeType === 'collection') {
                ctx.rect(-size * 0.8, -size * 0.8, size * 1.6, size * 1.6);
                ctx.fill();
                ctx.stroke();
              } else if (nodeType === 'document') {
                ctx.moveTo(0, -size);
                ctx.lineTo(size, size);
                ctx.lineTo(-size, size);
                ctx.closePath();
                ctx.fill();
              } else {
                ctx.arc(0, 0, size * 0.6, 0, 2 * Math.PI);
                ctx.fill();
              }
              ctx.restore();

              const shouldShowLabel =
                nodeType === 'collection' || isHovered || globalScale > 1.2;
              const fontSize = Math.max(12 / globalScale, 3);

              if (shouldShowLabel && label) {
                ctx.font = `${isHovered ? 'bold ' : ''}${fontSize}px Sans-Serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';

                const textWidth = ctx.measureText(label).width;
                const padding = 4;
                const labelY = y + size + 6;

                ctx.fillStyle =
                  resolvedTheme === 'dark'
                    ? 'rgba(0,0,0,0.75)'
                    : 'rgba(255,255,255,0.9)';
                ctx.fillRect(
                  x - textWidth / 2 - padding,
                  labelY - 2,
                  textWidth + padding * 2,
                  fontSize + 6,
                );

                ctx.fillStyle = resolvedTheme === 'dark' ? '#fff' : '#000';
                ctx.fillText(label, x, labelY);
              }

              if (nodeType === 'collection' || nodeType === 'document') {
                const indicatorRadius = Math.max(6 / globalScale, 3);
                const indicatorX = x;
                const indicatorY = y - size - indicatorRadius - 2;
                const isExpanded = expandedNodes.has(node.id);

                ctx.beginPath();
                ctx.fillStyle =
                  resolvedTheme === 'dark' ? '#0f172a' : 'rgba(255,255,255,0.95)';
                ctx.strokeStyle = fillColor;
                ctx.lineWidth = 1;
                ctx.arc(indicatorX, indicatorY, indicatorRadius, 0, 2 * Math.PI);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = fillColor;
                ctx.font = `bold ${Math.max(10 / globalScale, 3)}px Sans-Serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(isExpanded ? '−' : '+', indicatorX, indicatorY);
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
            <DialogTitle className="flex items-center gap-2 text-lg">
              {selectedNode?.type === 'collection' && (
                <Folder className="h-5 w-5 text-blue-500" />
              )}
              {selectedNode?.type === 'document' && (
                <FileText className="h-5 w-5 text-emerald-500" />
              )}
              {selectedNode?.type === 'entity' && (
                <Network className="h-5 w-5 text-amber-500" />
              )}
              <span>{selectedNode?.name || selectedNode?.entity_name}</span>
            </DialogTitle>
            <DialogDescription>
              {selectedNode?.type && (
                <Badge variant="secondary" className="mt-2 capitalize">
                  {selectedNode.type}
                </Badge>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {(selectedNode?.type === 'collection' ||
              selectedNode?.type === 'document') && (
                <div className="border-primary/20 bg-primary/5 rounded-lg border p-4">
                  <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-primary">
                    🚀 Quick Navigation
                  </div>
                  <Button
                    onClick={() => selectedNode && navigateToGraph(selectedNode)}
                    className="w-full gap-2"
                    size="default"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Enter{' '}
                    {selectedNode.type === 'collection'
                      ? 'Collection'
                      : 'Document'}{' '}
                    Graph
                  </Button>
                  <p className="text-muted-foreground mt-3 text-xs">
                    {selectedNode.type === 'collection'
                      ? 'Explore every entity and relationship inside this knowledge base.'
                      : 'Jump directly into the graph generated from this document.'}
                  </p>
                </div>
              )}

            {selectedDescription && (
              <div>
                <div className="mb-1 text-sm font-semibold">Description</div>
                <p className="text-muted-foreground text-sm">
                  {selectedDescription}
                </p>
              </div>
            )}

            {selectedMetadataEntries.length > 0 && (
              <div>
                <div className="mb-1 text-sm font-semibold">Metadata</div>
                <div className="grid gap-1 rounded-md border p-2 text-xs">
                  {selectedMetadataEntries.map(([key, value]) => (
                    <div
                      key={key}
                      className="flex items-center justify-between gap-2"
                    >
                      <span className="text-muted-foreground capitalize">
                        {key.replace(/_/g, ' ')}
                      </span>
                      <span className="font-medium">{String(value)}</span>
                    </div>
                  ))}
                </div>
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
