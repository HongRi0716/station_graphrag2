import { getTranslations } from "next-intl/server";
import Link from "next/link";

import {
  PageContainer,
  PageContent,
  PageHeader,
} from "@/components/page-container";

import { redirect } from "next/navigation";

const SPECIAL_AGENT_ROUTES: Record<string, string> = {
  detective: '/workspace/agents/specific/detective',
  diagnostician: '/workspace/agents/specific/diagnostician',
  calculator: '/workspace/agents/specific/calculator',
  supervisor: '/workspace/agents/specific/supervisor',
  archivist: '/workspace/agents/specific/archivist',
  gatekeeper: '/workspace/agents/specific/gatekeeper',
  sentinel: '/workspace/agents/specific/sentinel',
  prophet: '/workspace/agents/specific/prophet',
  scribe: '/workspace/agents/specific/scribe',
  instructor: '/workspace/agents/specific/instructor',
  guardian: '/workspace/agents/specific/guardian',
};

export default async function WorkspaceChatPage(
  props: Readonly<{ searchParams: Promise<Record<string, string | undefined>> }>,
) {
  const searchParams = await props.searchParams;
  const agent = searchParams?.agent;

  if (agent && SPECIAL_AGENT_ROUTES[agent]) {
    redirect(SPECIAL_AGENT_ROUTES[agent]);
  }

  const displayAgent = agent || "supervisor";
  const t = await getTranslations("sidebar_workspace");

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          { title: t("agents"), href: "/workspace/agents" },
          {
            title: `${t("agent_supervisor")} / ${t("chat")}`,
          },
        ]}
      />
      <PageContent>
        <div className="rounded-lg border bg-muted/40 p-6 text-sm text-muted-foreground">
          <p className="mb-4">
            找不到专用的会话页面。请从下方入口进入智能体作战台或创建 Bot：
          </p>
          <div className="flex flex-col gap-2">
            <Link
              className="text-primary underline underline-offset-4"
              href={`/workspace/agents?agent=${displayAgent}`}
            >
              {`前往 ${t("agents")}`}
            </Link>
            <Link
              className="text-primary underline underline-offset-4"
              href="/workspace/bots"
            >
              创建新的 Bot
            </Link>
          </div>
        </div>
      </PageContent>
    </PageContainer>
  );
}
