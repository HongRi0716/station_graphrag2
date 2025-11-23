import { PageContainer, PageHeader } from '@/components/page-container';
import { getTranslations } from 'next-intl/server';
import { GlobalGraphExplorer } from './global-graph-explorer';

export default async function GlobalGraphPage() {
  const t = await getTranslations('sidebar_workspace');

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          {
            title: t('global_graph'),
          },
        ]}
      />
      <div className="flex h-[calc(100vh-48px)] flex-col">
        <GlobalGraphExplorer />
      </div>
    </PageContainer>
  );
}
