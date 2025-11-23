'use client';

import {
  Activity,
  BookOpen,
  Bot,
  Eye,
  Globe,
  GraduationCap,
  Library,
  Share2,
  Zap,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';

export function MenuMain() {
  const pathname = usePathname();
  const translate = useTranslations('sidebar_workspace');
  const t = (key: string) => translate(key as any);

  const isActive = (path: string) =>
    pathname === path || pathname.startsWith(`${path}/`);
  const isAgentActive = (agentId: string) =>
    typeof window !== 'undefined' &&
    window.location.search.includes(`agent=${agentId}`);

  return (
    <>
      <SidebarGroup>
        <SidebarGroupLabel>{t('knowledge_base')}</SidebarGroupLabel>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={isActive('/marketplace')}>
              <Link href="/marketplace">
                <Globe className="size-4" />
                <span>{t('public_collections')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              isActive={
                isActive('/workspace/collections') &&
                !isActive('/workspace/collections/all/graph')
              }
            >
              <Link href="/workspace/collections">
                <BookOpen className="size-4" />
                <span>{t('my_collections')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              isActive={isActive('/workspace/collections/all/graph')}
            >
              <Link href="/workspace/collections/all/graph">
                <Share2 className="size-4" />
                <span>{t('global_graph')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroup>

      <SidebarGroup>
        <SidebarGroupLabel>{t('agents')}</SidebarGroupLabel>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={isActive('/workspace/agents')}>
              <Link href="/workspace/agents">
                <Bot className="size-4" />
                <span>{t('digital_engineer_team')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={isAgentActive('supervisor')}>
              <Link href="/workspace/chat?agent=supervisor">
                <Zap className="size-4 text-yellow-500" />
                <span>{t('agent_supervisor')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={isAgentActive('sentinel')}>
              <Link href="/workspace/chat?agent=sentinel">
                <Eye className="size-4 text-slate-500" />
                <span>{t('agent_sentinel')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={isAgentActive('archivist')}>
              <Link href="/workspace/chat?agent=archivist">
                <Library className="size-4 text-amber-500" />
                <span>{t('agent_archivist')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={isAgentActive('instructor')}>
              <Link href="/workspace/chat?agent=instructor">
                <GraduationCap className="size-4 text-indigo-500" />
                <span>{t('agent_instructor')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              isActive={isAgentActive('diagnostician')}
            >
              <Link href="/workspace/chat?agent=diagnostician">
                <Activity className="size-4 text-red-600" />
                <span>{t('agent_diagnostician')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroup>

      {/* 会话入口保留顶部默认入口,因此此处不再重复 */}
    </>
  );
}
