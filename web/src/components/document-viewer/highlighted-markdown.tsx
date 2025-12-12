'use client';

import { cn } from '@/lib/utils';
import { useMemo } from 'react';
import { Markdown } from '../markdown';

interface HighlightedMarkdownProps {
    content: string;
    searchQuery?: string;
    themeMode?: 'light' | 'dark' | 'sepia';
    className?: string;
}

export const HighlightedMarkdown = ({
    content,
    searchQuery,
    themeMode = 'light',
    className,
}: HighlightedMarkdownProps) => {
    // 处理搜索高亮
    const processedContent = useMemo(() => {
        if (!searchQuery || !content) return content;

        // 使用HTML mark标签高亮搜索词
        // 注意：这是简化处理，实际项目中可能需要更复杂的处理
        try {
            const escapedQuery = searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regex = new RegExp(`(${escapedQuery})`, 'gi');
            return content.replace(regex, '<mark class="search-highlight">$1</mark>');
        } catch {
            return content;
        }
    }, [content, searchQuery]);

    // 为标题添加ID，便于大纲导航
    const contentWithIds = useMemo(() => {
        let index = 0;
        return processedContent.replace(
            /^(#{1,6})\s+(.+)$/gm,
            (match, hashes, text) => {
                const id = `heading-${index}`;
                index++;
                // 使用HTML属性语法添加ID
                return `${hashes} ${text} {#${id}}`;
            },
        );
    }, [processedContent]);

    // 主题相关样式
    const themeStyles = useMemo(() => {
        switch (themeMode) {
            case 'dark':
                return 'prose-invert prose-p:text-gray-300 prose-headings:text-gray-100';
            case 'sepia':
                return 'prose-amber prose-p:text-amber-900 prose-headings:text-amber-800';
            default:
                return '';
        }
    }, [themeMode]);

    return (
        <div
            className={cn(
                'prose prose-sm max-w-none dark:prose-invert',
                themeStyles,
                className,
            )}
        >
            <style jsx global>{`
        .search-highlight {
          background-color: #fef08a;
          color: #1f2937;
          padding: 0 2px;
          border-radius: 2px;
        }
        
        .prose-invert .search-highlight {
          background-color: #fbbf24;
          color: #1f2937;
        }
        
        .prose-amber .search-highlight {
          background-color: #fcd34d;
          color: #78350f;
        }
      `}</style>
            <Markdown>{contentWithIds}</Markdown>
        </div>
    );
};

export default HighlightedMarkdown;
