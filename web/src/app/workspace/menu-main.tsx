'use client';

import {
  Activity,
  BookOpen,
  Bot,
  ChevronRight,
  Eye,
  Globe,
  GraduationCap,
  Library,
  MessageSquare,
  Share2,
  ShieldCheck,
  Users,
  Zap,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from '@/components/ui/sidebar';

export function MenuMain() {
  const pathname = usePathname();
  const translate = useTranslations();
  const t = (key: string) => translate(key as any, {});

  const isActive = (path: string) =>
    pathname === path || pathname.startsWith(`${path}/`);

  const containsAgent = (agentId: string) =>
    typeof window !== 'undefined' &&
    window.location.search.includes(`agent=${agentId}`);

  return (
    <SidebarGroup>
      <SidebarGroupLabel>Platform</SidebarGroupLabel>
      <SidebarMenu>
        <Collapsible
          asChild
          defaultOpen={
            isActive('/workspace/collections') ||
            isActive('/workspace/marketplace')
          }
        >
          <SidebarMenuItem>
            <CollapsibleTrigger asChild>
              <SidebarMenuButton
                tooltip={t('sidebar_workspace.knowledge_base')}
              >
                <Library className="size-4" />
                <span>{t('sidebar_workspace.knowledge_base')}</span>
                <ChevronRight className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-90" />
              </SidebarMenuButton>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <SidebarMenuSub>
                <SidebarMenuSubItem>
                  <SidebarMenuSubButton
                    asChild
                    isActive={isActive('/workspace/marketplace')}
                  >
                    <Link href="/workspace/marketplace">
                      <Globe className="mr-2 size-4" />
                      <span>{t('sidebar_workspace.shared_collections')}</span>
                    </Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>

                <SidebarMenuSubItem>
                  <div className="flex flex-col gap-1">
                    <SidebarMenuSubButton
                      asChild
                      isActive={
                        isActive('/workspace/collections') &&
                        !isActive('/workspace/collections/all/graph')
                      }
                    >
                      <Link href="/workspace/collections">
                        <BookOpen className="mr-2 size-4" />
                        <span>{t('sidebar_workspace.my_collections')}</span>
                      </Link>
                    </SidebarMenuSubButton>

                    <SidebarMenuSubButton
                      asChild
                      className="text-muted-foreground h-8 pl-9 text-xs"
                      isActive={isActive('/workspace/collections/all/graph')}
                    >
                      <Link href="/workspace/collections/all/graph">
                        <Share2 className="mr-2 size-3" />
                        <span>{t('sidebar_workspace.global_graph')}</span>
                      </Link>
                    </SidebarMenuSubButton>
                  </div>
                </SidebarMenuSubItem>
              </SidebarMenuSub>
            </CollapsibleContent>
          </SidebarMenuItem>
        </Collapsible>

        <Collapsible
          asChild
          defaultOpen={
            isActive('/workspace/agents') || pathname.includes('?agent=')
          }
        >
          <SidebarMenuItem>
            <CollapsibleTrigger asChild>
              <SidebarMenuButton tooltip={t('sidebar_workspace.agents')}>
                <Bot className="size-4" />
                <span>{t('sidebar_workspace.agents')}</span>
                <ChevronRight className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-90" />
              </SidebarMenuButton>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <SidebarMenuSub>
                <SidebarMenuSubItem>
                  <SidebarMenuSubButton
                    asChild
                    isActive={containsAgent('supervisor')}
                  >
                    <Link href="/workspace/chat?agent=supervisor">
                      <Zap className="mr-2 size-4 text-yellow-500" />
                      <span>{t('sidebar_workspace.agent_supervisor')}</span>
                    </Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>

                <SidebarMenuSubItem>
                  <SidebarMenuSubButton
                    asChild
                    isActive={containsAgent('archivist')}
                  >
                    <Link href="/workspace/chat?agent=archivist">
                      <Library className="mr-2 size-4 text-amber-500" />
                      <span>{t('sidebar_workspace.agent_archivist')}</span>
                    </Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>

                <SidebarMenuSubItem>
                  <SidebarMenuSubButton
                    asChild
                    isActive={containsAgent('sentinel')}
                  >
                    <Link href="/workspace/chat?agent=sentinel">
                      <Eye className="mr-2 size-4 text-slate-500" />
                      <span>{t('sidebar_workspace.agent_sentinel')}</span>
                    </Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>

                <SidebarMenuSubItem>
                  <SidebarMenuSubButton
                    asChild
                    isActive={containsAgent('diagnostician')}
                  >
                    <Link href="/workspace/chat?agent=diagnostician">
                      <Activity className="mr-2 size-4 text-red-600" />
                      <span>{t('sidebar_workspace.agent_diagnostician')}</span>
                    </Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>

                <SidebarMenuSubItem>
                  <SidebarMenuSubButton
                    asChild
                    isActive={containsAgent('gatekeeper')}
                  >
                    <Link href="/workspace/chat?agent=gatekeeper">
                      <ShieldCheck className="mr-2 size-4 text-blue-500" />
                      <span>{t('sidebar_workspace.agent_gatekeeper')}</span>
                    </Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>

                <SidebarMenuSubItem>
                  <SidebarMenuSubButton
                    asChild
                    isActive={containsAgent('instructor')}
                  >
                    <Link href="/workspace/chat?agent=instructor">
                      <GraduationCap className="mr-2 size-4 text-indigo-500" />
                      <span>{t('sidebar_workspace.agent_instructor')}</span>
                    </Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>

                <SidebarMenuSubItem>
                  <SidebarMenuSubButton
                    asChild
                    isActive={isActive('/workspace/agents')}
                  >
                    <Link href="/workspace/agents">
                      <Users className="mr-2 size-4" />
                      <span>{t('sidebar_workspace.view_all_agents')}</span>
                    </Link>
                  </SidebarMenuSubButton>
                </SidebarMenuSubItem>
              </SidebarMenuSub>
            </CollapsibleContent>
          </SidebarMenuItem>
        </Collapsible>

        <SidebarMenuItem>
          <SidebarMenuButton
            asChild
            isActive={
              isActive('/workspace/chat') && !pathname.includes('agent=')
            }
            tooltip={t('sidebar_workspace.chat')}
          >
            <Link href="/workspace/chat">
              <MessageSquare className="size-4" />
              <span>{t('sidebar_workspace.chat')}</span>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarGroup>
  );
}
