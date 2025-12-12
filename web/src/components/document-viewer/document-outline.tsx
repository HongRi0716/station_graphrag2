'use client';

import { cn } from '@/lib/utils';
import { ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { ScrollArea } from '../ui/scroll-area';

export interface OutlineItem {
    id: string;
    level: number;
    text: string;
    children?: OutlineItem[];
}

interface DocumentOutlineProps {
    items: OutlineItem[];
    onItemClick: (item: OutlineItem) => void;
    className?: string;
}

// 单个大纲项
const OutlineItemComponent = ({
    item,
    onItemClick,
    activeId,
}: {
    item: OutlineItem;
    onItemClick: (item: OutlineItem) => void;
    activeId?: string;
}) => {
    const [expanded, setExpanded] = useState(true);
    const hasChildren = item.children && item.children.length > 0;
    const isActive = activeId === item.id;

    return (
        <div>
            <div
                className={cn(
                    'group flex cursor-pointer items-center gap-1 rounded-md px-2 py-1.5 text-sm transition-colors',
                    'hover:bg-accent hover:text-accent-foreground',
                    isActive && 'bg-accent text-accent-foreground font-medium',
                )}
                style={{ paddingLeft: `${(item.level - 1) * 12 + 8}px` }}
                onClick={() => onItemClick(item)}
            >
                {hasChildren && (
                    <ChevronRight
                        className={cn(
                            'h-3 w-3 shrink-0 transition-transform',
                            expanded && 'rotate-90',
                        )}
                        onClick={(e) => {
                            e.stopPropagation();
                            setExpanded(!expanded);
                        }}
                    />
                )}
                <span className="truncate">{item.text}</span>
            </div>

            {hasChildren && expanded && (
                <div>
                    {item.children!.map((child) => (
                        <OutlineItemComponent
                            key={child.id}
                            item={child}
                            onItemClick={onItemClick}
                            activeId={activeId}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

export const DocumentOutline = ({
    items,
    onItemClick,
    className,
}: DocumentOutlineProps) => {
    const [activeId, setActiveId] = useState<string>();

    const handleItemClick = (item: OutlineItem) => {
        setActiveId(item.id);
        onItemClick(item);
    };

    if (items.length === 0) {
        return (
            <div className={cn('p-4 text-center text-sm text-muted-foreground', className)}>
                暂无目录
            </div>
        );
    }

    return (
        <ScrollArea className={className}>
            <div className="p-2">
                <div className="mb-2 px-2 text-xs font-semibold uppercase text-muted-foreground">
                    目录大纲
                </div>
                {items.map((item) => (
                    <OutlineItemComponent
                        key={item.id}
                        item={item}
                        onItemClick={handleItemClick}
                        activeId={activeId}
                    />
                ))}
            </div>
        </ScrollArea>
    );
};

export default DocumentOutline;
