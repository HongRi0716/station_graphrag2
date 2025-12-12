'use client';

import { cn } from '@/lib/utils';
import _ from 'lodash';
import {
    ChevronLeft,
    ChevronRight,
    Download,
    FileAudio,
    FileImage,
    FileSpreadsheet,
    FileText,
    FileType,
    LoaderCircle,
    ZoomIn,
    ZoomOut,
} from 'lucide-react';
import dynamic from 'next/dynamic';
import { useCallback, useEffect, useMemo, useState } from 'react';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { ScrollArea } from '../ui/scroll-area';
import { Tooltip, TooltipContent, TooltipTrigger } from '../ui/tooltip';

// 动态导入PDF组件
const PDFDocument = dynamic(() => import('react-pdf').then((r) => r.Document), {
    ssr: false,
});
const PDFPage = dynamic(() => import('react-pdf').then((r) => r.Page), {
    ssr: false,
});

// 支持的文件类型分类
const FILE_TYPE_CATEGORIES = {
    pdf: ['pdf'],
    image: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'tiff', 'tif'],
    office: ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'],
    text: ['txt', 'text', 'md', 'markdown', 'html', 'htm', 'css', 'js', 'ts', 'json', 'xml', 'yaml', 'yml'],
    audio: ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac'],
    video: ['mp4', 'webm', 'mpeg', 'mov', 'avi'],
};

interface SourceFileReaderProps {
    sourceUrl: string;
    fileType?: string;
    fileName?: string;
    className?: string;
    /** 转换后的PDF URL，用于Office文档预览 */
    convertedPdfUrl?: string;
}

// 获取文件类型分类
const getFileCategory = (fileType?: string): string => {
    if (!fileType) return 'unknown';
    const ext = fileType.toLowerCase();

    for (const [category, extensions] of Object.entries(FILE_TYPE_CATEGORIES)) {
        if (extensions.includes(ext)) {
            return category;
        }
    }
    return 'unknown';
};

// 获取文件类型图标
const getFileIcon = (category: string) => {
    switch (category) {
        case 'pdf':
            return FileType;
        case 'image':
            return FileImage;
        case 'office':
            return FileSpreadsheet;
        case 'text':
            return FileText;
        case 'audio':
        case 'video':
            return FileAudio;
        default:
            return FileText;
    }
};

export const SourceFileReader = ({
    sourceUrl,
    fileType,
    fileName,
    className,
    convertedPdfUrl,
}: SourceFileReaderProps) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [numPages, setNumPages] = useState(0);
    const [currentPage, setCurrentPage] = useState(1);
    const [scale, setScale] = useState(1.0);
    const [textContent, setTextContent] = useState<string>('');

    const category = useMemo(() => getFileCategory(fileType), [fileType]);
    const FileIcon = useMemo(() => getFileIcon(category), [category]);

    // 根据文件类型设置初始加载状态
    useEffect(() => {
        // 对于不需要全局加载状态的类型，直接设置为false
        // 这些类型的加载状态会在各自的渲染器内部处理
        if (category === 'unknown' || category === 'office' ||
            category === 'image' || category === 'audio' || category === 'video') {
            setLoading(false);
        }
        // 对于PDF，由 onLoadSuccess 事件处理
        // 对于文本，由 fetch 完成后处理
    }, [category]);

    // 加载PDF worker
    useEffect(() => {
        if (category === 'pdf') {
            const loadPDF = async () => {
                const { pdfjs } = await import('react-pdf');
                pdfjs.GlobalWorkerOptions.workerSrc = new URL(
                    'pdfjs-dist/build/pdf.worker.min.mjs',
                    import.meta.url,
                ).toString();
            };
            loadPDF();
        }
    }, [category]);

    // 加载文本内容
    useEffect(() => {
        if (category === 'text' && sourceUrl) {
            setLoading(true);
            setError(null);
            fetch(sourceUrl)
                .then((res) => {
                    if (!res.ok) throw new Error('加载失败');
                    return res.text();
                })
                .then((text) => {
                    setTextContent(text);
                    setLoading(false);
                })
                .catch((err) => {
                    setError(err.message);
                    setLoading(false);
                });
        }
    }, [category, sourceUrl]);

    // 缩放控制
    const handleZoomIn = useCallback(() => {
        setScale((s) => Math.min(s + 0.25, 3.0));
    }, []);

    const handleZoomOut = useCallback(() => {
        setScale((s) => Math.max(s - 0.25, 0.5));
    }, []);

    // 下载文件
    const handleDownload = useCallback(() => {
        const link = document.createElement('a');
        link.href = sourceUrl;
        link.download = fileName || 'document';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }, [sourceUrl, fileName]);

    // PDF阅读器
    const renderPDFReader = () => (
        <div className="flex h-full flex-col">
            {/* PDF工具栏 */}
            <div className="flex items-center justify-between border-b bg-muted/50 px-4 py-2">
                <div className="flex items-center gap-2">
                    <Button
                        variant="ghost"
                        size="icon"
                        disabled={currentPage <= 1}
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="min-w-20 text-center text-sm">
                        第 {currentPage} / {numPages} 页
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

                <div className="flex items-center gap-2">
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button variant="ghost" size="icon" onClick={handleZoomOut}>
                                <ZoomOut className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>缩小</TooltipContent>
                    </Tooltip>
                    <span className="min-w-12 text-center text-sm">{Math.round(scale * 100)}%</span>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button variant="ghost" size="icon" onClick={handleZoomIn}>
                                <ZoomIn className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>放大</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button variant="ghost" size="icon" onClick={handleDownload}>
                                <Download className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>下载</TooltipContent>
                    </Tooltip>
                </div>
            </div>

            {/* PDF内容 */}
            <ScrollArea className="flex-1 bg-gray-100 dark:bg-gray-800">
                <div className="flex min-h-full justify-center p-4">
                    <PDFDocument
                        file={sourceUrl}
                        onLoadSuccess={({ numPages }) => {
                            setNumPages(numPages);
                            setLoading(false);
                        }}
                        onLoadError={(err) => {
                            setError(err.message);
                            setLoading(false);
                        }}
                        loading={
                            <div className="flex flex-col items-center justify-center py-12">
                                <LoaderCircle className="h-8 w-8 animate-spin text-primary" />
                                <span className="mt-2 text-sm text-muted-foreground">加载文档中...</span>
                            </div>
                        }
                    >
                        {_.times(numPages).map((index) => (
                            <Card key={index} className="mb-4 overflow-hidden">
                                <PDFPage
                                    pageNumber={index + 1}
                                    scale={scale}
                                    className="bg-white"
                                    renderTextLayer={true}
                                    renderAnnotationLayer={true}
                                />
                            </Card>
                        ))}
                    </PDFDocument>
                </div>
            </ScrollArea>
        </div>
    );

    // 图片阅读器
    const renderImageReader = () => (
        <div className="flex h-full flex-col">
            {/* 图片工具栏 */}
            <div className="flex items-center justify-end border-b bg-muted/50 px-4 py-2">
                <div className="flex items-center gap-2">
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button variant="ghost" size="icon" onClick={handleZoomOut}>
                                <ZoomOut className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>缩小</TooltipContent>
                    </Tooltip>
                    <span className="min-w-12 text-center text-sm">{Math.round(scale * 100)}%</span>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button variant="ghost" size="icon" onClick={handleZoomIn}>
                                <ZoomIn className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>放大</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button variant="ghost" size="icon" onClick={handleDownload}>
                                <Download className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>下载</TooltipContent>
                    </Tooltip>
                </div>
            </div>

            {/* 图片内容 */}
            <ScrollArea className="flex-1 bg-gray-100 dark:bg-gray-800">
                <div className="flex min-h-full items-center justify-center p-4">
                    <img
                        src={sourceUrl}
                        alt={fileName || 'Document image'}
                        style={{ transform: `scale(${scale})`, transformOrigin: 'center' }}
                        className="max-w-full rounded-lg shadow-lg transition-transform"
                        onLoad={() => setLoading(false)}
                        onError={() => {
                            setError('无法加载图片');
                            setLoading(false);
                        }}
                    />
                </div>
            </ScrollArea>
        </div>
    );

    // 文本阅读器
    const renderTextReader = () => (
        <div className="flex h-full flex-col">
            {/* 文本工具栏 */}
            <div className="flex items-center justify-end border-b bg-muted/50 px-4 py-2">
                <div className="flex items-center gap-2">
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <Button variant="ghost" size="icon" onClick={handleDownload}>
                                <Download className="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>下载</TooltipContent>
                    </Tooltip>
                </div>
            </div>

            {/* 文本内容 */}
            <ScrollArea className="flex-1">
                <pre className="whitespace-pre-wrap break-words p-6 font-mono text-sm">
                    {textContent}
                </pre>
            </ScrollArea>
        </div>
    );

    // 音频/视频阅读器
    const renderMediaReader = () => (
        <div className="flex h-full flex-col">
            {/* 媒体工具栏 */}
            <div className="flex items-center justify-end border-b bg-muted/50 px-4 py-2">
                <Tooltip>
                    <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" onClick={handleDownload}>
                            <Download className="h-4 w-4" />
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>下载</TooltipContent>
                </Tooltip>
            </div>

            {/* 媒体内容 */}
            <div className="flex flex-1 items-center justify-center p-8">
                {category === 'audio' ? (
                    <audio
                        controls
                        src={sourceUrl}
                        className="w-full max-w-xl"
                        onLoadedData={() => setLoading(false)}
                        onError={() => {
                            setError('无法加载音频');
                            setLoading(false);
                        }}
                    />
                ) : (
                    <video
                        controls
                        src={sourceUrl}
                        className="max-h-full max-w-full rounded-lg shadow-lg"
                        onLoadedData={() => setLoading(false)}
                        onError={() => {
                            setError('无法加载视频');
                            setLoading(false);
                        }}
                    />
                )}
            </div>
        </div>
    );

    // Office文档阅读器 (使用转换后的PDF)
    const renderOfficeReader = () => {
        // 如果有转换后的PDF，直接使用PDF阅读器
        if (convertedPdfUrl) {
            return (
                <div className="flex h-full flex-col">
                    {/* Office工具栏 */}
                    <div className="flex items-center justify-between border-b bg-muted/50 px-4 py-2">
                        <div className="flex items-center gap-2">
                            <Button
                                variant="ghost"
                                size="icon"
                                disabled={currentPage <= 1}
                                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                            >
                                <ChevronLeft className="h-4 w-4" />
                            </Button>
                            <span className="min-w-20 text-center text-sm">
                                第 {currentPage} / {numPages} 页
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

                        <div className="flex items-center gap-2">
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button variant="ghost" size="icon" onClick={handleZoomOut}>
                                        <ZoomOut className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>缩小</TooltipContent>
                            </Tooltip>
                            <span className="min-w-12 text-center text-sm">{Math.round(scale * 100)}%</span>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button variant="ghost" size="icon" onClick={handleZoomIn}>
                                        <ZoomIn className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>放大</TooltipContent>
                            </Tooltip>
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button variant="ghost" size="icon" onClick={handleDownload}>
                                        <Download className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>下载原文件</TooltipContent>
                            </Tooltip>
                        </div>
                    </div>

                    {/* PDF内容 */}
                    <ScrollArea className="flex-1 bg-gray-100 dark:bg-gray-800">
                        <div className="flex min-h-full justify-center p-4">
                            <PDFDocument
                                file={convertedPdfUrl}
                                onLoadSuccess={({ numPages }) => {
                                    setNumPages(numPages);
                                    setLoading(false);
                                }}
                                onLoadError={(err) => {
                                    setError(err.message);
                                    setLoading(false);
                                }}
                                loading={
                                    <div className="flex flex-col items-center justify-center py-12">
                                        <LoaderCircle className="h-8 w-8 animate-spin text-primary" />
                                        <span className="mt-2 text-sm text-muted-foreground">加载文档中...</span>
                                    </div>
                                }
                            >
                                {_.times(numPages).map((index) => (
                                    <Card key={index} className="mb-4 overflow-hidden">
                                        <PDFPage
                                            pageNumber={index + 1}
                                            scale={scale}
                                            className="bg-white"
                                            renderTextLayer={true}
                                            renderAnnotationLayer={true}
                                        />
                                    </Card>
                                ))}
                            </PDFDocument>
                        </div>
                    </ScrollArea>
                </div>
            );
        }

        // 没有PDF转换，显示提示并提供下载
        return (
            <div className="flex h-full flex-col items-center justify-center gap-4 p-8">
                <FileIcon className="h-16 w-16 text-muted-foreground" />
                <div className="text-center">
                    <h3 className="text-lg font-medium">Office文档无法在线阅读</h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                        文档尚未转换为可预览格式，请下载后使用本地软件查看
                    </p>
                </div>
                <Button onClick={handleDownload} className="mt-4">
                    <Download className="mr-2 h-4 w-4" />
                    下载文件
                </Button>
            </div>
        );
    };

    // 不支持的文件类型
    const renderUnsupportedType = () => (
        <div className="flex h-full flex-col items-center justify-center gap-4 p-8">
            <FileIcon className="h-16 w-16 text-muted-foreground" />
            <div className="text-center">
                <h3 className="text-lg font-medium">无法在线阅读此文件类型</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                    文件类型: {fileType?.toUpperCase() || '未知'}
                </p>
            </div>
            <Button onClick={handleDownload} className="mt-4">
                <Download className="mr-2 h-4 w-4" />
                下载文件
            </Button>
        </div>
    );

    // 错误状态
    if (error) {
        return (
            <div className={cn('flex h-full flex-col items-center justify-center gap-4', className)}>
                <FileIcon className="h-16 w-16 text-destructive" />
                <div className="text-center">
                    <h3 className="text-lg font-medium text-destructive">加载失败</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{error}</p>
                </div>
                <Button onClick={handleDownload} variant="outline">
                    <Download className="mr-2 h-4 w-4" />
                    下载文件
                </Button>
            </div>
        );
    }

    // 加载状态
    if (loading && category !== 'pdf') {
        return (
            <div className={cn('flex h-full flex-col items-center justify-center gap-4', className)}>
                <LoaderCircle className="h-12 w-12 animate-spin text-primary" />
                <span className="text-sm text-muted-foreground">加载文档中...</span>
            </div>
        );
    }

    // 根据文件类型渲染对应的阅读器
    return (
        <div className={cn('h-full overflow-hidden', className)}>
            {category === 'pdf' && renderPDFReader()}
            {category === 'image' && renderImageReader()}
            {category === 'text' && renderTextReader()}
            {(category === 'audio' || category === 'video') && renderMediaReader()}
            {category === 'office' && renderOfficeReader()}
            {category === 'unknown' && renderUnsupportedType()}
        </div>
    );
};

export default SourceFileReader;
