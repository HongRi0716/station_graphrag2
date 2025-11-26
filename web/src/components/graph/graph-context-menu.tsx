import {
    Command,
    CommandGroup,
    CommandItem,
    CommandList,
    CommandSeparator,
} from '@/components/ui/command';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import {
    Bot,
    Crosshair,
    Expand,
    FileText,
    MessageSquare,
    MoreHorizontal,
    Search,
    ZoomIn,
} from 'lucide-react';
import { useEffect, useRef } from 'react';

export interface GraphContextMenuProps {
    open: boolean;
    position: { x: number; y: number } | null;
    node: any; // Using any for flexibility with ForceGraph node types
    onClose: () => void;
    onAction: (action: 'chat' | 'focus' | 'expand' | 'source' | 'search', node: any) => void;
}

export function GraphContextMenu({
    open,
    position,
    node,
    onClose,
    onAction,
}: GraphContextMenuProps) {
    const menuRef = useRef<HTMLDivElement>(null);

    // Close on click outside
    useEffect(() => {
        const handleClick = (e: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
                onClose();
            }
        };
        if (open) {
            document.addEventListener('click', handleClick);
            document.addEventListener('contextmenu', handleClick); // Close on new right click elsewhere
        }
        return () => {
            document.removeEventListener('click', handleClick);
            document.removeEventListener('contextmenu', handleClick);
        };
    }, [open, onClose]);

    if (!open || !position || !node) return null;

    const isCollection = node.type === 'collection' || node.isCollectionRoot;
    const isDocument = node.type === 'document' || node.isDocument;
    const isEntity = !isCollection && !isDocument;

    return (
        <div
            ref={menuRef}
            className="fixed z-50 min-w-[180px] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95"
            style={{
                left: position.x,
                top: position.y,
            }}
        >
            <Command className="w-full">
                <div className="px-2 py-1.5 text-xs font-medium text-muted-foreground bg-muted/50 border-b">
                    {node.label || node.name || 'Unknown Node'}
                </div>
                <CommandList>
                    <CommandGroup>
                        <CommandItem onSelect={() => onAction('focus', node)}>
                            <Crosshair className="mr-2 h-4 w-4" />
                            <span>Focus Node</span>
                        </CommandItem>

                        {!isCollection && (
                            <CommandItem onSelect={() => onAction('chat', node)}>
                                <Bot className="mr-2 h-4 w-4" />
                                <span>Ask AI Agent</span>
                            </CommandItem>
                        )}

                        {isEntity && (
                            <CommandItem onSelect={() => onAction('search', node)}>
                                <Search className="mr-2 h-4 w-4" />
                                <span>Search Similar</span>
                            </CommandItem>
                        )}
                    </CommandGroup>

                    <CommandSeparator />

                    <CommandGroup>
                        {(isDocument || isEntity) && (
                            <CommandItem onSelect={() => onAction('source', node)}>
                                <FileText className="mr-2 h-4 w-4" />
                                <span>View Source</span>
                            </CommandItem>
                        )}

                        {isCollection && (
                            <CommandItem onSelect={() => onAction('expand', node)}>
                                <Expand className="mr-2 h-4 w-4" />
                                <span>Expand Collection</span>
                            </CommandItem>
                        )}
                    </CommandGroup>
                </CommandList>
            </Command>
        </div>
    );
}
