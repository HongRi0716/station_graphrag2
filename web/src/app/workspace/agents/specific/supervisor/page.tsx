import { getTranslations } from 'next-intl/server';

import {
    PageContainer,
    PageContent,
    PageHeader,
} from '@/components/page-container';

export default async function SupervisorAgentPage() {
    const t = await getTranslations('sidebar_workspace');

    return (
        <PageContainer>
            <PageHeader
                breadcrumbs={[
                    { title: t('agents'), href: '/workspace/agents' },
                    { title: t('agent_supervisor') },
                ]}
            />
            <PageContent>
                <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
                    <div className="text-6xl">🎯</div>
                    <h2 className="text-2xl font-bold">{t('agent_supervisor')}</h2>
                    <p className="text-muted-foreground max-w-md">
                        Supervisor Agent - Orchestrates and coordinates multiple specialized agents to accomplish complex tasks efficiently.
                    </p>
                    <p className="text-muted-foreground text-sm">
                        主管智能体 - 协调和编排多个专业智能体,高效完成复杂任务。
                    </p>
                </div>
            </PageContent>
        </PageContainer>
    );
}
