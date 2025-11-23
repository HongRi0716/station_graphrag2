import {
  PageContainer,
  PageContent,
  PageHeader,
} from '@/components/page-container';
import { getTranslations } from 'next-intl/server';
import { CollectionHeader } from '../collection-header';
import { CollectionGraph } from './collection-graph';

export default async function Page({
  params,
}: {
  params: { collectionId: string };
}) {
  const { collectionId } = await params;
  const isGlobal = collectionId === 'all';

  const page_collections = await getTranslations('page_collections');
  const page_graph = await getTranslations('page_graph');

  const breadcrumbs = isGlobal
    ? [
        {
          title: page_collections('metadata.title'),
          href: '/workspace/collections',
        },
        {
          title: page_graph('global_title'),
        },
      ]
    : [
        {
          title: page_collections('metadata.title'),
          href: '/workspace/collections',
        },
        {
          title: page_graph('metadata.title'),
        },
      ];

  return (
    <PageContainer>
      <PageHeader breadcrumbs={breadcrumbs} />
      <div className="flex h-[calc(100vh-48px)] flex-col px-0">
        {!isGlobal && <CollectionHeader className="w-full" />}

        {isGlobal && (
          <div className="px-8 pt-6 pb-2">
            <h1 className="text-3xl font-bold">{page_graph('global_title')}</h1>
            <p className="text-muted-foreground mt-1">
              {page_graph('global_description')}
            </p>
          </div>
        )}

        <PageContent className="flex w-full flex-1 flex-col">
          <CollectionGraph
            marketplace={false}
            mode={isGlobal ? 'global' : 'contextual'}
            collectionId={collectionId}
          />
        </PageContent>
      </div>
    </PageContainer>
  );
}
