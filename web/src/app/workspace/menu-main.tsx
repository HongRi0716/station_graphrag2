'use client';

import {
  BookOpen,
  Bot,
  Calculator,
  Database,
  Eye,
  Globe,
  GraduationCap,
  LayoutGrid,
  Library,
  PenTool,
  Settings,
  Share2,
  ShieldCheck,
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
                <span>{t('agents')}</span>
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
            <SidebarMenuButton asChild isActive={isAgentActive('detective')}>
              <Link href="/workspace/chat?agent=detective">
                <BookOpen className="size-4 text-purple-500" />
                <span>{t('agent_detective')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={isAgentActive('gatekeeper')}>
              <Link href="/workspace/chat?agent=gatekeeper">
                <ShieldCheck className="size-4 text-blue-500" />
                <span>{t('agent_gatekeeper')}</span>
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
            <SidebarMenuButton asChild isActive={isActive('/workspace/agents/specific/calculator')}>
              <Link href="/workspace/agents/specific/calculator">
                <Calculator className="size-4 text-orange-500" />
                <span>{t('agent_calculator')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={isActive('/workspace/agents/specific/sentinel')}>
              <Link href="/workspace/agents/specific/sentinel">
                <Eye className="size-4 text-slate-500" />
                <span>{t('agent_sentinel')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={isActive('/workspace/agents/specific/instructor')}>
              <Link href="/workspace/agents/specific/instructor">
                <GraduationCap className="size-4 text-blue-500" />
                <span>{t('agent_instructor')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={isActive('/workspace/agents/specific/scribe')}>
              <Link href="/workspace/agents/specific/scribe">
                <PenTool className="size-4 text-purple-500" />
                <span>{t('agent_scribe')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={isActive('/workspace/agents/specific/prophet')}>
              <Link href="/workspace/agents/specific/prophet">
                <Bot className="size-4 text-indigo-500" />
                <span>{t('agent_prophet')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={isActive('/workspace/agents/specific/guardian')}>
              <Link href="/workspace/agents/specific/guardian">
                <ShieldCheck className="size-4 text-emerald-500" />
                <span>{t('agent_guardian')}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroup>

      {/* 会话入口保留顶部默认入口,因此此处不再重复 */}
    </>
  );
}
