'use client';

import { DocumentPreview } from '@/api';
import { cn } from '@/lib/utils';
import {
    BookOpen,
    ChevronLeft,
    ChevronRight,
    Columns2,
    File,
    FileText,
    List,
    Maximize2,
    Minimize2,
    Moon,
    Search,
    Sun,
    X,
} from 'lucide-react';
import dynamic from 'next/dynamic';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Input } from '../ui/input';
import { ScrollArea } from '../ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from '../ui/tooltip';
import { DocumentOutline, OutlineItem } from './document-outline';
import { HighlightedMarkdown } from './highlighted-markdown';
import { SourceFileReader } from './source-file-reader';

// 动态导入PDF组件
const PDFDocument = dynamic(() => import('react-pdf').then((r) => r.Document), {
    ssr: false,
});
const PDFPage = dynamic(() => import('react-pdf').then((r) => r.Page), {
    ssr: false,
});

// 阅览模式
type ViewMode = 'single' | 'split' | 'focus';
// 主题模式
type ThemeMode = 'light' | 'dark' | 'sepia';
// 内容类型
type ContentType = 'parsed' | 'source';

interface DocumentViewerProps {
    documentPreview: DocumentPreview;
    collectionId: string;
    documentId: string;
    className?: string;
}

export const DocumentViewer = ({
    documentPreview,
    collectionId,
    documentId,
    className,
}: DocumentViewerProps) => {
    // 状态管理
    const [viewMode, setViewMode] = useState<ViewMode>('single');
    const [themeMode, setThemeMode] = useState<ThemeMode>('light');
    const [contentType, setContentType] = useState<ContentType>('parsed');
    const [searchQuery, setSearchQuery] = useState('');
    const [searchOpen, setSearchOpen] = useState(false);
    const [outlineOpen, setOutlineOpen] = useState(true);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [numPages, setNumPages] = useState<number>(0);
    const [currentPage, setCurrentPage] = useState(1);

    // refs
    const containerRef = useRef<HTMLDivElement>(null);
    const markdownRef = useRef<HTMLDivElement>(null);
    const pdfRef = useRef<HTMLDivElement>(null);

    // 判断是否为PDF
    const isPdf = useMemo(() => {
        return Boolean(documentPreview.doc_filename?.match(/\.pdf$/i));
    }, [documentPreview.doc_filename]);

    // 是否有源文件可供阅读
    const hasSourceFile = useMemo(() => {
        return Boolean(documentPreview.source_object_path || documentPreview.doc_object_path);
    }, [documentPreview.source_object_path, documentPreview.doc_object_path]);

    // 源文件URL
    const sourceFileUrl = useMemo(() => {
        const path = documentPreview.source_object_path || documentPreview.doc_object_path;
        if (!path) return null;
        return `${process.env.NEXT_PUBLIC_BASE_PATH || ''}/api/v1/collections/${collectionId}/documents/${documentId}/object?path=${path}`;
    }, [collectionId, documentId, documentPreview.source_object_path, documentPreview.doc_object_path]);

    // 源文件类型
    const sourceFileType = useMemo(() => {
        // 优先使用后端返回的类型
        if (documentPreview.source_file_type) {
            return documentPreview.source_file_type;
        }
        // 从文件名提取
        const fileName = documentPreview.doc_filename;
        if (fileName && fileName.includes('.')) {
            return fileName.split('.').pop()?.toLowerCase();
        }
        return undefined;
    }, [documentPreview.source_file_type, documentPreview.doc_filename]);

    // 从Markdown提取大纲
    const outline = useMemo((): OutlineItem[] => {
        if (!documentPreview.markdown_content) return [];

        const headingRegex = /^(#{1,6})\s+(.+)$/gm;
        const items: OutlineItem[] = [];
        let match;
        let index = 0;

        while ((match = headingRegex.exec(documentPreview.markdown_content)) !== null) {
            const level = match[1].length;
            const text = match[2].trim();
            const id = `heading-${index}`;
            items.push({ id, level, text });
            index++;
        }

        return items;
    }, [documentPreview.markdown_content]);

    // 加载PDF worker
    useEffect(() => {
        const loadPDF = async () => {
            const { pdfjs } = await import('react-pdf');
            pdfjs.GlobalWorkerOptions.workerSrc = new URL(
                'pdfjs-dist/build/pdf.worker.min.mjs',
                import.meta.url,
            ).toString();
        };
        loadPDF();
    }, []);

    // 全屏切换
    const toggleFullscreen = useCallback(() => {
        if (!containerRef.current) return;

        if (!isFullscreen) {
            containerRef.current.requestFullscreen?.();
        } else {
            document.exitFullscreen?.();
        }
        setIsFullscreen(!isFullscreen);
    }, [isFullscreen]);

    // 监听全屏变化
    useEffect(() => {
        const handleFullscreenChange = () => {
            setIsFullscreen(!!document.fullscreenElement);
        };
        document.addEventListener('fullscreenchange', handleFullscreenChange);
        return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
    }, []);

    // 大纲点击滚动
    const handleOutlineClick = useCallback((item: OutlineItem) => {
        const element = document.getElementById(item.id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, []);

    // 搜索高亮数量
    const highlightCount = useMemo(() => {
        if (!searchQuery || !documentPreview.markdown_content) return 0;
        const regex = new RegExp(searchQuery, 'gi');
        const matches = documentPreview.markdown_content.match(regex);
        return matches?.length || 0;
    }, [searchQuery, documentPreview.markdown_content]);

    // 主题样式
    const themeStyles = useMemo(() => {
        switch (themeMode) {
            case 'dark':
                return 'bg-gray-900 text-gray-100';
            case 'sepia':
                return 'bg-amber-50 text-amber-900';
            default:
                return 'bg-white text-gray-900';
        }
    }, [themeMode]);

    // PDF路径
    const pdfUrl = useMemo(() => {
        if (!documentPreview.converted_pdf_object_path) return null;
        return `${process.env.NEXT_PUBLIC_BASE_PATH || ''}/api/v1/collections/${collectionId}/documents/${documentId}/object?path=${documentPreview.converted_pdf_object_path}`;
    }, [collectionId, documentId, documentPreview.converted_pdf_object_path]);

    return (
        <div
            ref={containerRef}
            className={cn(
                'relative flex h-full flex-col overflow-hidden rounded-lg border',
                themeStyles,
                isFullscreen && 'fixed inset-0 z-50',
                className,
            )}
        >
            {/* 工具栏 */}
            <div className="flex items-center justify-between border-b px-4 py-2">
                <div className="flex items-center gap-4">
                    {/* 内容类型切换 - 源文件/解析内容 */}
                    {hasSourceFile && (
                        <Tabs value={contentType} onValueChange={(v) => setContentType(v as ContentType)}>
                            <TabsList className="h-8">
                                <TabsTrigger value="source" className="h-7 gap-1 px-3 text-xs">
                                    <File className="h-3 w-3" />
                                    源文件
                                </TabsTrigger>
                                <TabsTrigger value="parsed" className="h-7 gap-1 px-3 text-xs">
                                    <FileText className="h-3 w-3" />
                                    解析内容
                                </TabsTrigger>
                            </TabsList>
                        </Tabs>
                    )}

                    {/* 解析内容模式下的工具 */}
                    {contentType === 'parsed' && (
                        <>
                            {/* 大纲切换 */}
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button
                                        variant={outlineOpen ? 'secondary' : 'ghost'}
                                        size="icon"
                                        className="h-8 w-8"
                                        onClick={() => setOutlineOpen(!outlineOpen)}
                                    >
                                        <List className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>目录大纲</TooltipContent>
                            </Tooltip>

                            {/* 视图模式 */}
                            <div className="flex items-center rounded-md border">
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Button
                                            variant={viewMode === 'single' ? 'secondary' : 'ghost'}
                                            size="icon"
                                            className="h-7 w-7 rounded-r-none"
                                            onClick={() => setViewMode('single')}
                                        >
                                            <FileText className="h-3.5 w-3.5" />
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>单栏视图</TooltipContent>
                                </Tooltip>

                                {isPdf && (
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <Button
                                                variant={viewMode === 'split' ? 'secondary' : 'ghost'}
                                                size="icon"
                                                className="h-7 w-7 rounded-none border-x"
                                                onClick={() => setViewMode('split')}
                                            >
                                                <Columns2 className="h-3.5 w-3.5" />
                                            </Button>
                                        </TooltipTrigger>
                                        <TooltipContent>分屏视图</TooltipContent>
                                    </Tooltip>
                                )}

                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Button
                                            variant={viewMode === 'focus' ? 'secondary' : 'ghost'}
                                            size="icon"
                                            className="h-7 w-7 rounded-l-none"
                                            onClick={() => setViewMode('focus')}
                                        >
                                            <BookOpen className="h-3.5 w-3.5" />
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>专注阅读</TooltipContent>
                                </Tooltip>
                            </div>
                        </>
                    )}
                </div>

                {/* 搜索 - 仅在解析内容模式下显示 */}
                {contentType === 'parsed' && (
                    <div className="flex items-center gap-2">
                        {searchOpen ? (
                            <div className="flex items-center gap-2">
                                <div className="relative">
                                    <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                    <Input
                                        placeholder="搜索内容..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="h-8 w-48 pl-8 pr-8"
                                        autoFocus
                                    />
                                    {searchQuery && (
                                        <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                                            {highlightCount} 处
                                        </span>
                                    )}
                                </div>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={() => {
                                        setSearchOpen(false);
                                        setSearchQuery('');
                                    }}
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>
                        ) : (
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8"
                                        onClick={() => setSearchOpen(true)}
                                    >
                                        <Search className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>搜索</TooltipContent>
                            </Tooltip>
                        )}
                    </div>
                )}

                {/* 右侧工具 */}
                <div className="flex items-center gap-2">
                    {/* 主题切换 */}
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => {
                                    const modes: ThemeMode[] = ['light', 'sepia', 'dark'];
                                    const currentIndex = modes.indexOf(themeMode);
                                    setThemeMode(modes[(currentIndex + 1) % modes.length]);
                                }}
                            >
                                {themeMode === 'dark' ? (
                                    <Moon className="h-4 w-4" />
                                ) : themeMode === 'sepia' ? (
                                    <BookOpen className="h-4 w-4 text-amber-600" />
                                ) : (
                                    <Sun className="h-4 w-4" />
                                )}
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                            {themeMode === 'light' ? '浅色' : themeMode === 'sepia' ? '护眼' : '深色'}
                        </TooltipContent>
                    </Tooltip>

                    {/* 全屏 */}
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={toggleFullscreen}
                            >
                                {isFullscreen ? (
                                    <Minimize2 className="h-4 w-4" />
                                ) : (
                                    <Maximize2 className="h-4 w-4" />
                                )}
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>{isFullscreen ? '退出全屏' : '全屏'}</TooltipContent>
                    </Tooltip>
                </div>
            </div>

            {/* 主内容区 */}
            <div className="flex flex-1 overflow-hidden">
                {/* 源文件阅读模式 */}
                {contentType === 'source' && sourceFileUrl && (
                    <SourceFileReader
                        sourceUrl={sourceFileUrl}
                        fileType={sourceFileType}
                        fileName={documentPreview.doc_filename || undefined}
                        className="flex-1"
                        convertedPdfUrl={pdfUrl || undefined}
                    />
                )}

                {/* 解析内容阅读模式 */}
                {contentType === 'parsed' && (
                    <>
                        {/* 大纲侧边栏 */}
                        {outlineOpen && outline.length > 0 && (
                            <div className="w-64 border-r">
                                <DocumentOutline
                                    items={outline}
                                    onItemClick={handleOutlineClick}
                                    className="h-full"
                                />
                            </div>
                        )}

                        {/* 内容区域 */}
                        <div className="flex flex-1 overflow-hidden">
                            {/* 单栏或专注模式 */}
                            {(viewMode === 'single' || viewMode === 'focus') && (
                                <ScrollArea className="flex-1">
                                    <div
                                        ref={markdownRef}
                                        className={cn(
                                            'p-6',
                                            viewMode === 'focus' && 'mx-auto max-w-3xl',
                                        )}
                                    >
                                        <HighlightedMarkdown
                                            content={documentPreview.markdown_content || ''}
                                            searchQuery={searchQuery}
                                            themeMode={themeMode}
                                        />
                                    </div>
                                </ScrollArea>
                            )}

                            {/* 分屏模式 */}
                            {viewMode === 'split' && isPdf && pdfUrl && (
                                <>
                                    {/* PDF侧 */}
                                    <div className="flex w-1/2 flex-col border-r">
                                        <div className="flex items-center justify-center gap-2 border-b px-4 py-2">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                disabled={currentPage <= 1}
                                                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                                            >
                                                <ChevronLeft className="h-4 w-4" />
                                            </Button>
                                            <span className="text-sm">
                                                {currentPage} / {numPages}
                                            </span>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                disabled={currentPage >= numPages}
                                                onClick={() => setCurrentPage((p) => Math.min(numPages, p + 1))}
                                            >
                                                <ChevronRight className="h-4 w-4" />
                                            </Button>
                                        </div>
                                        <ScrollArea className="flex-1" ref={pdfRef}>
                                            <div className="flex justify-center p-4">
                                                <PDFDocument
                                                    file={pdfUrl}
                                                    onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                                                    loading={
                                                        <Card>
                                                            <CardContent className="flex items-center justify-center py-8">
                                                                <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary" />
                                                            </CardContent>
                                                        </Card>
                                                    }
                                                >
                                                    <PDFPage
                                                        pageNumber={currentPage}
                                                        className="shadow-lg"
                                                        width={450}
                                                    />
                                                </PDFDocument>
                                            </div>
                                        </ScrollArea>
                                    </div>

                                    {/* Markdown侧 */}
                                    <ScrollArea className="w-1/2">
                                        <div ref={markdownRef} className="p-6">
                                            <HighlightedMarkdown
                                                content={documentPreview.markdown_content || ''}
                                                searchQuery={searchQuery}
                                                themeMode={themeMode}
                                            />
                                        </div>
                                    </ScrollArea>
                                </>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default DocumentViewer;
