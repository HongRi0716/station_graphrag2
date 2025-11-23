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
import Color from 'color';
import * as d3 from 'd3';
import _ from 'lodash';
import {
  Check,
  ChevronDown,
  LoaderCircle,
  Maximize,
  Minimize,
  Search,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import dynamic from 'next/dynamic';
import { useParams } from 'next/navigation';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'sonner';
import { CollectionGraphNodeDetail } from './collection-graph-node-detail';
import { CollectionGraphNodeMerge } from './collection-graph-node-merge';

const ForceGraph2D = dynamic(
  () => import('react-force-graph-2d').then((r) => r),
  {
    ssr: false,
  },
);

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
  const currentCollectionId = collectionId || (params.collectionId as string);
  const [fullscreen, setFullscreen] = useState<boolean>(false);
  const { resolvedTheme } = useTheme();
  const page_graph = useTranslations('page_graph');

  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [graphData, setGraphData] = useState<{
    nodes: GraphNode[];
    links: GraphEdge[];
  }>();
  const [mergeSuggestion, setMergeSuggestion] =
    useState<MergeSuggestionsResponse>();
  const [mergeSuggestionOpen, setMergeSuggestionOpen] =
    useState<boolean>(false);

  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  const [allEntities, setAllEntities] = useState<{
    [key in string]: GraphNode[];
  }>({});
  const [activeEntities, setActiveEntities] = useState<string[]>([]);

  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());
  const [hoverNode, setHoverNode] = useState<GraphNode>();
  const [activeNode, setActiveNode] = useState<GraphNode>();
  const [globalSearchQuery, setGlobalSearchQuery] = useState('');
  const color = useMemo(() => d3.scaleOrdinal(d3.schemeCategory10), []);

  const { NODE_MIN, NODE_MAX } = useMemo(
    () => ({
      NODE_MIN: 7,
      NODE_MAX: 24,
      LINK_MIN: 18,
      LINK_MAX: 36,
    }),
    [],
  );

  const getGraphData = useCallback(
    async (query?: string) => {
      if (typeof currentCollectionId !== 'string') return;
      setLoading(true);

      try {
        let data: KnowledgeGraph;

        if (!marketplace) {
          if (mode === 'global') {
            if (!query) {
              setLoading(false);
              return;
            }
            const res =
              await apiClient.graphApi.collectionsCollectionIdGraphsGet(
                {
                  collectionId: 'all',
                },
                { timeout: 1000 * 30 },
              );
            data = res.data;
          } else {
            const res =
              await apiClient.graphApi.collectionsCollectionIdGraphsGet(
                {
                  collectionId: currentCollectionId,
                },
                {
                  timeout: 1000 * 20,
                },
              );
            data = res.data;
          }
        } else {
          const res =
            await apiClient.defaultApi.marketplaceCollectionsCollectionIdGraphGet(
              {
                collectionId: currentCollectionId,
              },
              {
                timeout: 1000 * 20,
              },
            );
          data = res.data as KnowledgeGraph;
        }

        const nodes =
          data.nodes?.map((n) => {
            const targetCount = data.edges.filter(
              (edg) => edg.target === n.id,
            ).length;
            const sourceCount = data.edges.filter(
              (edg) => edg.source === n.id,
            ).length;
            return {
              ...n,
              value: Math.max(targetCount, sourceCount, NODE_MIN),
            };
          }) || [];
        const links = data.edges || [];

        setGraphData({ nodes, links });
        setAllEntities(_.groupBy(nodes, (n) => n.properties.entity_type));
      } catch (e) {
        console.error(e);
        toast.error('Failed to load graph data');
      } finally {
        setLoading(false);
      }
    },
    [NODE_MIN, marketplace, currentCollectionId, mode],
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

  const handleCloseDetail = useCallback(() => {
    setActiveNode(undefined);
    setHoverNode(undefined);
    highlightNodes.clear();
    highlightLinks.clear();
  }, [highlightLinks, highlightNodes]);

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

  useEffect(() => {
    highlightNodes.clear();
    highlightLinks.clear();

    if (activeNode) {
      const nodeLinks = graphData?.links.filter((link) => {
        return (
          // @ts-expect-error link.source.id link.target.id
          link.source.id === activeNode.id || link.target.id === activeNode.id
        );
      });
      nodeLinks?.forEach((link: GraphEdge) => {
        highlightLinks.add(link);
        highlightNodes.add(link.source);
        highlightNodes.add(link.target);
      });
      highlightNodes.add(activeNode);
      // @ts-expect-error node.x node.y
      graphRef.current?.centerAt(activeNode.x, activeNode.y, 400);
      graphRef.current?.zoom(3, 600);
    } else {
      graphRef.current?.centerAt(0, 0, 400);
      graphRef.current?.zoom(1.5, 600);
    }
    setHighlightNodes(highlightNodes);
    setHighlightLinks(highlightLinks);
  }, [activeNode, graphData?.links, highlightLinks, highlightNodes]);

  useEffect(() => {
    if (mode === 'contextual') {
      getGraphData();
      getMergeSuggestions();
    }
  }, [getGraphData, getMergeSuggestions, mode]);

  const handleGlobalSearchSubmit = useCallback(() => {
    if (!globalSearchQuery.trim()) return;
    getGraphData(globalSearchQuery);
  }, [globalSearchQuery, getGraphData]);

  return (
    <div
      className={cn('top-0 right-0 bottom-0 left-0 flex flex-1 flex-col', {
        fixed: fullscreen,
        'bg-background': fullscreen,
        'z-49': fullscreen,
      })}
    >
      <div
        className={cn('mb-2 flex flex-row items-center justify-between gap-2', {
          'px-2': fullscreen,
          'pt-2': fullscreen,
        })}
      >
        {mode === 'contextual' ? (
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
                    {_.map(graphData?.nodes, (node, key) => {
                      const isActive = activeNode?.id === node.id;
                      return (
                        <CommandItem
                          key={key}
                          className={cn('capitalize')}
                          value={node.id}
                          onSelect={() => {
                            setActiveNode(isActive ? undefined : node);
                          }}
                        >
                          <div className="truncate">{node.id}</div>
                          <Check
                            className={cn(
                              'ml-auto',
                              isActive ? 'opacity-100' : 'opacity-0',
                            )}
                          />
                        </CommandItem>
                      );
                    })}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        ) : (
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-sm font-normal">
              {page_graph('global_view')}
            </Badge>
          </div>
        )}
        <div className="flex flex-row items-center gap-2">
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
            className="cursor-pointer"
            onClick={() => {
              if (mode === 'global') {
                handleGlobalSearchSubmit();
              } else {
                getGraphData();
                getMergeSuggestions();
              }
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

        <div className="bg-background pointer-events-none absolute top-0 right-0 left-0 z-10 flex flex-row flex-wrap gap-1 rounded-xl p-2">
          {_.map(allEntities, (item, key) => {
            const isActive = activeEntities.includes(key);
            //@ts-expect-error entity error
            const title = page_graph(`entity_${key}`);
            return (
              <Badge
                key={key}
                className={cn(
                  'pointer-events-auto cursor-pointer capitalize',
                  isActive ? '' : 'border-transparent',
                )}
                style={{
                  backgroundColor: color(key),
                  opacity: isActive ? 1 : 0.7,
                }}
                onClick={() =>
                  setActiveEntities((items) => {
                    if (isActive) {
                      return _.reject(items, (item) => item === key);
                    } else {
                      return _.uniq(items.concat(key));
                    }
                  })
                }
              >
                {title} ({item.length})
              </Badge>
            );
          })}
        </div>

        <ForceGraph2D
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          nodeLabel={(nod) => String(nod.id)}
          ref={graphRef}
          nodeVisibility={(node) => {
            return (
              !node.properties.entity_type ||
              activeEntities.includes(node.properties.entity_type)
            );
          }}
          onNodeClick={(node) => {
            if (activeNode?.id === node.id) {
              handleCloseDetail();
              return;
            }
            setActiveNode(node as GraphNode);
          }}
          onNodeHover={(node) => {
            if (activeNode) return;
            highlightNodes.clear();
            highlightLinks.clear();
            if (node) {
              const nodeLinks = graphData?.links.filter((link) => {
                //@ts-expect-error link.source.id link.target.id
                return link.source.id === node.id || link.target.id === node.id;
              });
              nodeLinks?.forEach((link: GraphEdge) => {
                highlightLinks.add(link);
              });
            }
            setHoverNode(
              node
                ? {
                    ...node,
                    id: String(node.id),
                    labels: [],
                    properties: {},
                  }
                : undefined,
            );
            setHighlightNodes(highlightNodes);
            setHighlightLinks(highlightLinks);
          }}
          onLinkHover={(link) => {
            if (activeNode) return;
            highlightNodes.clear();
            highlightLinks.clear();
            if (link) {
              highlightLinks.add(link);
            }
            setHighlightNodes(highlightNodes);
            setHighlightLinks(highlightLinks);
          }}
          nodeCanvasObject={(node, ctx) => {
            const x = node.x || 0;
            const y = node.y || 0;

            let size = Math.min(node.value, NODE_MAX);
            if (node === hoverNode) size += 1;
            ctx.beginPath();
            ctx.arc(x, y, size, 0, 2 * Math.PI, false);

            const colorNormal = color(node.properties.entity_type || '');
            const colorSecondary =
              resolvedTheme === 'dark'
                ? Color(colorNormal).grayscale().darken(0.3)
                : Color(colorNormal).grayscale().lighten(0.6);
            ctx.fillStyle =
              highlightNodes.size === 0 || highlightNodes.has(node)
                ? colorNormal
                : colorSecondary.string();
            ctx.fill();

            // node circle
            ctx.beginPath();
            ctx.arc(x, y, size, 0, 2 * Math.PI, false);
            ctx.lineWidth = 0.5;
            ctx.strokeStyle = highlightNodes.has(node)
              ? Color('#FFF').grayscale().string()
              : '#FFF';
            ctx.stroke();

            // node label
            let fontSize = 16;
            const offset = 2;
            ctx.font = `${fontSize}px Arial`;
            let textWidth = ctx.measureText(String(node.id)).width - offset;
            do {
              fontSize -= 1;
              ctx.font = `${fontSize}px Arial`;
              textWidth = ctx.measureText(String(node.id)).width - offset;
            } while (textWidth > size && fontSize > 0);
            ctx.fillStyle = '#fff';
            if (fontSize <= 0) {
              fontSize = 1;
              ctx.font = `${fontSize}px Arial`;
              textWidth = ctx.measureText(String(node.id)).width - offset;
            }
            ctx.fillText(
              String(node.id),
              x - (textWidth + offset) / 2,
              y + fontSize / 2,
            );
          }}
          nodePointerAreaPaint={(node, color, ctx) => {
            const x = node.x || 0;
            const y = node.y || 0;
            const size = Math.min(node.value, NODE_MAX);
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(x, y, size, 0, 2 * Math.PI, false);
            ctx.fill();
          }}
          linkLabel="id"
          linkColor={(link) => {
            if (resolvedTheme === 'dark') {
              return highlightLinks.has(link) ? '#585858' : '#383838';
            } else {
              return highlightLinks.has(link) ? '#BBB' : '#DDD';
            }
          }}
          linkWidth={(link) => {
            return highlightLinks.has(link) ? 2 : 1;
          }}
          linkDirectionalParticleWidth={(link) => {
            return highlightLinks.has(link) ? 3 : 0;
          }}
          linkDirectionalParticles={2}
          linkVisibility={(link) => {
            // @ts-expect-error link.source.properties
            const sourceEntityType = link.source?.properties?.entity_type || '';

            // @ts-expect-error link.source.properties
            const tatgetEntityType = link.target?.properties?.entity_type || '';
            return (
              activeEntities.includes(sourceEntityType) &&
              activeEntities.includes(tatgetEntityType)
            );
          }}
        />

        <CollectionGraphNodeDetail
          open={!mergeSuggestionOpen && Boolean(activeNode)}
          node={activeNode}
          onClose={handleCloseDetail}
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
