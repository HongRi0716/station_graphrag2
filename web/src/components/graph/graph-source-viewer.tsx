import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { apiClient } from '@/lib/api/client';
import { cn } from '@/lib/utils';
import { FileText, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

interface GraphSourceViewerProps {
    collectionId: string;
    documentId: string;
    documentName?: string;
    highlightText?: string; // The snippet to highlight (grounding)
    onClose: () => void;
    className?: string;
}

export function GraphSourceViewer({
    collectionId,
    documentId,
    documentName,
    highlightText,
    onClose,
    className,
}: GraphSourceViewerProps) {
    const [content, setContent] = useState<string>('');
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const highlightRef = useRef<HTMLSpanElement>(null);

    // Fetch document content
    useEffect(() => {
        if (!collectionId || !documentId) return;

        const fetchContent = async () => {
            setLoading(true);
            try {
                // Fetch document details/content using defaultApi
                const res = await apiClient.defaultApi.collectionsCollectionIdDocumentsDocumentIdGet({
                    collectionId,
                    documentId,
                });

                const docData = res.data as any;
                // Assuming content is in content or text field
                setContent(docData.content || docData.text || 'No text content available for preview.');

            } catch (error) {
                console.error('Failed to fetch document content', error);
                toast.error('Failed to load document content');
                setContent('Error loading content.');
            } finally {
                setLoading(false);
            }
        };

        fetchContent();
    }, [collectionId, documentId]);

    // Auto-scroll to highlight
    useEffect(() => {
        if (!loading && highlightText && highlightRef.current) {
            highlightRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, [loading, highlightText, content]);

    // Helper for lodash-like escape
    const _ = {
        escapeRegExp: (string: string) => string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    };

    // Text Renderer with Highlighting
    const renderContent = () => {
        if (!content) return null;
        if (!highlightText) return <div className="whitespace-pre-wrap text-sm">{content}</div>;

        // Simple string splitting for highlighting
        const parts = content.split(new RegExp(`(${_.escapeRegExp(highlightText)})`, 'gi'));

        return (
            <div className="whitespace-pre-wrap text-sm">
                {parts.map((part, i) =>
                    part.toLowerCase() === highlightText.toLowerCase() ? (
                        <span
                            key={i}
                            ref={highlightRef}
                            className="bg-yellow-200 dark:bg-yellow-900/50 text-foreground font-medium px-1 rounded animate-pulse"
                        >
                            {part}
                        </span>
                    ) : (
                        <span key={i}>{part}</span>
                    )
                )}
            </div>
        );
    };

    return (
        <Card className={cn("flex flex-col h-full border-l shadow-xl rounded-none w-[400px] bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60", className)}>
            <CardHeader className="p-4 border-b flex flex-row items-center justify-between space-y-0">
                <div className="flex flex-col gap-1 overflow-hidden">
                    <CardTitle className="text-base font-medium flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <span className="truncate" title={documentName}>{documentName || 'Document Source'}</span>
                    </CardTitle>
                    {highlightText && (
                        <Badge variant="outline" className="w-fit text-[10px] px-1 py-0 h-5 text-muted-foreground font-normal">
                            Source Grounding Active
                        </Badge>
                    )}
                </div>
                <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
                    <X className="h-4 w-4" />
                </Button>
            </CardHeader>
            <CardContent className="flex-1 p-0 overflow-hidden relative">
                {loading ? (
                    <div className="p-4 space-y-2">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-[90%]" />
                        <Skeleton className="h-4 w-[95%]" />
                        <Skeleton className="h-4 w-[80%]" />
                    </div>
                ) : (
                    <ScrollArea className="h-full p-4" ref={scrollRef}>
                        {renderContent()}
                    </ScrollArea>
                )}
            </CardContent>
        </Card>
    );
}
