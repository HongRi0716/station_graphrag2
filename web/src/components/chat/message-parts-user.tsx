import { ChatMessage, Collection } from '@/api';
import { Markdown } from '@/components/markdown';
import { useBotContext } from '@/components/providers/bot-provider';
import { UserRound } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useMemo } from 'react';
import { MessageTimestamp } from './message-timestamp';

export const MessagePartsUser = ({ parts }: { parts: ChatMessage[] }) => {
  const { collections } = useBotContext();
  const page_chat = useTranslations('page_chat');

  // Process message content to replace collection IDs with names
  const processedContent = useMemo(() => {
    const content = parts?.map((part) => part.data || '').join('') || '';

    let processed = content;

    // Replace @__GLOBAL__ with friendly name (handle various formats)
    const globalName =
      page_chat('global_knowledge_base' as any) || '全局知识库';
    processed = processed.replace(/@__GLOBAL__/g, `@${globalName}`);
    // Also handle if stored without @ prefix (though unlikely)
    processed = processed.replace(/\b__GLOBAL__\b/g, globalName);

    // Replace other collection IDs with their names
    // Sort by ID length (longest first) to avoid partial matches
    const sortedCollections = [...(collections || [])].sort(
      (a, b) => (b.id?.length || 0) - (a.id?.length || 0),
    );

    sortedCollections.forEach((collection: Collection) => {
      if (collection.id && collection.title) {
        // Match @collection_id pattern, escape special regex characters
        const escapedId = collection.id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        // Match @collection_id followed by non-alphanumeric character or end of string
        // This ensures we match the full ID and not a partial match
        const regex = new RegExp(`@${escapedId}(?![a-zA-Z0-9])`, 'g');
        processed = processed.replace(regex, `@${collection.title}`);
      }
    });

    return processed;
  }, [parts, collections, page_chat]);

  return (
    <div className="ml-auto flex w-max flex-row gap-4">
      <div className="flex max-w-sm flex-col gap-2 sm:max-w-lg md:max-w-2xl lg:max-w-3xl xl:max-w-4xl">
        <div className="bg-primary text-primary-foreground rounded-lg p-4 text-sm">
          <Markdown>{processedContent}</Markdown>
        </div>
        <MessageTimestamp parts={parts} />
      </div>
      <div>
        <div className="bg-muted text-muted-foreground flex size-12 flex-col justify-center rounded-full">
          <UserRound className="size-5 self-center" />
        </div>
      </div>
    </div>
  );
};
