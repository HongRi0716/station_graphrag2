'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import * as d3 from 'd3';
import _ from 'lodash';
import { Loader2, Search } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import dynamic from 'next/dynamic';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

const ForceGraph2D = dynamic(
    () => import('react-force-graph-2d').then((r) => r),
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
    const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphEdge[] }>({ nodes: [], links: [] });
    const [hasSearched, setHasSearched] = useState(false);
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
    const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
    const containerRef = useRef<HTMLDivElement>(null);
    const graphRef = useRef<any>(null);

    // Color scales
    const workspaceColorScale = useMemo(() => d3.scaleOrdinal(d3.schemeCategory10), []);
    const nodeTypeColors = useMemo(() => ({
        collection: '#3b82f6',  // blue
        document: '#10b981',     // green
        entity: '#f59e0b',       // orange
    }), []);

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
        handleResize();
        return () => window.removeEventListener('resize', handleResize);
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
                        query: "",
                        top_k: 50,
                    }),
                });

                if (response.ok) {
                    const data = await response.json();
                    const nodes = data.nodes || [];
                    const links = data.edges || [];

                    // Calculate node values
                    nodes.forEach((node: any) => {
                        const degree = links.filter((l: any) => l.source === node.id || l.target === node.id).length;
                        node.val = Math.max(degree, 5);
                    });

                    setGraphData({ nodes, links });

                    // Auto-expand collections by default
                    const collectionIds = nodes.filter((n: any) => n.type === 'collection').map((n: any) => n.id);
                    setExpandedNodes(new Set(collectionIds));

                    setTimeout(() => {
                        if (graphRef.current) {
                            graphRef.current.zoomToFit(400);
                        }
                    }, 500);
                } else {
                    console.error('Auto-load failed');
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
                    query: query || "",
                    top_k: 50,
                }),
            });

            if (response.ok) {
                const data = await response.json();

                if (hierarchicalView) {
                    // Hierarchical data
                    const nodes = data.nodes || [];
                    const links = data.edges || [];

                    // Calculate node values
                    nodes.forEach((node: any) => {
                        const degree = links.filter((l: any) => l.source === node.id || l.target === node.id).length;
                        node.val = Math.max(degree, 5);
                    });

                    setGraphData({ nodes, links });

                    // Auto-expand collections by default
                    const collectionIds = nodes.filter((n: any) => n.type === 'collection').map((n: any) => n.id);
                    setExpandedNodes(new Set(collectionIds));
                } else {
                    // Flat entity view
                    const nodes = data.nodes || [];
                    const links = data.edges || [];

                    nodes.forEach((node: any) => {
                        const degree = links.filter((l: any) => l.source === node.id || l.target === node.id).length;
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
                console.error('Search failed');
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
        if (hierarchicalView && (node.type === 'collection' || node.type === 'document')) {
            // Toggle expand/collapse
            setExpandedNodes(prev => {
                const newSet = new Set(prev);
                if (newSet.has(node.id)) {
                    newSet.delete(node.id);
                } else {
                    newSet.add(node.id);
                }
                return newSet;
            });
        } else {
            // Zoom to node
            graphRef.current?.centerAt(node.x, node.y, 1000);
            graphRef.current?.zoom(8, 2000);
        }
    };

    // Filter nodes and links based on expanded state
    const filteredGraphData = useMemo(() => {
        if (!hierarchicalView) return graphData;

        const { nodes, links } = graphData;
        const visibleNodes = new Set<string>();
        const visibleLinks: GraphEdge[] = [];

        // Always show collections
        nodes.filter(n => n.type === 'collection').forEach(n => visibleNodes.add(n.id));

        // Show documents if their collection is expanded
        nodes.filter(n => n.type === 'document').forEach(doc => {
            const parentLink = links.find(l => l.target === doc.id && l.type === 'CONTAINS');
            if (parentLink && expandedNodes.has(parentLink.source)) {
                visibleNodes.add(doc.id);
            }
        });

        // Show entities if their document is expanded
        nodes.filter(n => n.type === 'entity').forEach(ent => {
            const parentLink = links.find(l => l.target === ent.id && l.type === 'EXTRACTED_FROM');
            if (parentLink && expandedNodes.has(parentLink.source)) {
                visibleNodes.add(ent.id);
            }
        });

        // Filter links to only show those between visible nodes
        links.forEach(link => {
            const sourceId = typeof link.source === 'object' ? (link.source as any).id : link.source;
            const targetId = typeof link.target === 'object' ? (link.target as any).id : link.target;
            if (visibleNodes.has(sourceId) && visibleNodes.has(targetId)) {
                visibleLinks.push(link);
            }
        });

        return {
            nodes: nodes.filter(n => visibleNodes.has(n.id)),
            links: visibleLinks
        };
    }, [graphData, hierarchicalView, expandedNodes]);

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
        <div className="flex h-full flex-col gap-4 p-4 relative">
            {/* Controls */}
            <div className="absolute top-4 left-4 z-10 flex flex-col gap-2 w-full max-w-md">
                <Card className="flex w-full flex-row p-2 shadow-lg items-center gap-2">
                    <Input
                        type="text"
                        placeholder={t('search_placeholder') || "Search global entities..."}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="flex-1 border-none focus-visible:ring-0"
                        disabled={hierarchicalView}
                    />
                    <Button onClick={handleSearch} disabled={loading} size="sm">
                        {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                        {hierarchicalView ? 'Load' : (t('search') || "Search")}
                    </Button>
                </Card>

                <Card className="flex flex-row items-center gap-2 p-3 shadow-lg">
                    <Switch
                        id="hierarchical-mode"
                        checked={hierarchicalView}
                        onCheckedChange={(checked) => {
                            setHierarchicalView(checked);
                            setGraphData({ nodes: [], links: [] });
                            setHasSearched(false);
                        }}
                    />
                    <Label htmlFor="hierarchical-mode" className="cursor-pointer">
                        Hierarchical View (Collection → Document → Entity)
                    </Label>
                </Card>
            </div>

            {/* Legend */}
            {hasSearched && filteredGraphData.nodes.length > 0 && (
                <div className="absolute top-32 left-4 z-10">
                    <Card className="p-2 shadow-md bg-background/80 backdrop-blur-sm max-w-xs">
                        {hierarchicalView ? (
                            <>
                                <div className="text-xs font-semibold mb-2 text-muted-foreground">Node Types</div>
                                <div className="flex flex-col gap-1">
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3" style={{ backgroundColor: nodeTypeColors.collection }}></div>
                                        <span className="text-xs">Collection (click to expand)</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3" style={{ backgroundColor: nodeTypeColors.document }}></div>
                                        <span className="text-xs">Document (click to expand)</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: nodeTypeColors.entity }}></div>
                                        <span className="text-xs">Entity</span>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <>
                                <div className="text-xs font-semibold mb-2 text-muted-foreground">Workspaces</div>
                                <div className="flex flex-col gap-1">
                                    {_.uniq(filteredGraphData.nodes.map(n => n.workspace)).filter(Boolean).map(ws => (
                                        <div key={ws} className="flex items-center gap-2">
                                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: workspaceColorScale(ws!) }}></div>
                                            <span className="text-xs">{ws}</span>
                                        </div>
                                    ))}
                                </div>
                                <div className="border-t my-2"></div>
                                <div className="flex items-center gap-2">
                                    <div className="w-8 h-0 border-t-2 border-dashed border-gray-400"></div>
                                    <span className="text-xs">Federation (Same As)</span>
                                </div>
                            </>
                        )}
                    </Card>
                </div>
            )}

            {/* Graph Container */}
            <div ref={containerRef} className="flex-1 overflow-hidden rounded-lg border bg-card">
                {hasSearched && filteredGraphData.nodes.length === 0 && !loading ? (
                    <div className="flex h-full items-center justify-center text-muted-foreground">
                        {hierarchicalView ? 'Click "Load" to view hierarchy' : 'No entities found.'}
                    </div>
                ) : (
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
                        linkLineDash={(link: any) => link.type === 'federation' ? [4, 2] : null}
                        linkWidth={(link: any) => link.type === 'federation' ? 2 : 1}
                        linkDirectionalParticles={(link: any) => link.type === 'federation' ? 2 : 0}
                        linkDirectionalParticleSpeed={0.005}
                        backgroundColor={resolvedTheme === 'dark' ? '#020817' : '#ffffff'}
                        onNodeClick={handleNodeClick}
                        nodeCanvasObject={(node: any, ctx, globalScale) => {
                            const label = node.name || node.entity_name;
                            const fontSize = 12 / globalScale;
                            ctx.font = `${fontSize}px Sans-Serif`;

                            const size = hierarchicalView ? (node.type === 'collection' ? 8 : node.type === 'document' ? 6 : 5) : 5;

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
                            if (hierarchicalView && (node.type === 'collection' || node.type === 'document')) {
                                const isExpanded = expandedNodes.has(node.id);
                                ctx.fillStyle = '#fff';
                                ctx.font = `bold ${fontSize * 1.2}px Sans-Serif`;
                                ctx.fillText(isExpanded ? '−' : '+', node.x, node.y);
                            }
                        }}
                    />
                )}
            </div>
        </div>
    );
}
