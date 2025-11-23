import { getTranslations } from 'next-intl/server';

import {
    PageContainer,
    PageContent,
    PageHeader,
} from '@/components/page-container';

export default async function GatekeeperAgentPage() {
    const t = await getTranslations('sidebar_workspace');

    return (
        <PageContainer>
            <PageHeader
                breadcrumbs={[
                    { title: t('agents'), href: '/workspace/agents' },
                    { title: t('agent_gatekeeper') },
                ]}
            />
            <PageContent>
                <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
                    <div className="text-6xl">🚪</div>
                    <h2 className="text-2xl font-bold">{t('agent_gatekeeper')}</h2>
                    <p className="text-muted-foreground max-w-md">
                        Gatekeeper Agent - Controls access and validates requests to ensure security and compliance before processing.
                    </p>
                    <p className="text-muted-foreground text-sm">
                        守门员智能体 - 控制访问并验证请求,确保安全性和合规性。
                    </p>
                </div>
            </PageContent>
        </PageContainer>
    );
}
