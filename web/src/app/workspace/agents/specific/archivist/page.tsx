import { getTranslations } from 'next-intl/server';

import {
    PageContainer,
    PageContent,
    PageHeader,
} from '@/components/page-container';

export default async function ArchivistAgentPage() {
    const t = await getTranslations('sidebar_workspace');

    return (
        <PageContainer>
            <PageHeader
                breadcrumbs={[
                    { title: t('agents'), href: '/workspace/agents' },
                    { title: t('agent_archivist') },
                ]}
            />
            <PageContent>
                <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
                    <div className="text-6xl">📚</div>
                    <h2 className="text-2xl font-bold">{t('agent_archivist')}</h2>
                    <p className="text-muted-foreground max-w-md">
                        Archivist Agent - Manages and organizes knowledge, documents, and historical data for efficient retrieval and preservation.
                    </p>
                    <p className="text-muted-foreground text-sm">
                        档案员智能体 - 管理和组织知识、文档和历史数据,实现高效检索和保存。
                    </p>
                </div>
            </PageContent>
        </PageContainer>
    );
}
