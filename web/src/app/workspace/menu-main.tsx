'use client';

import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';

import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { NAV_CONFIG, NavItem } from '@/config/navigation-config';
import { cn } from '@/lib/utils';

export function MenuMain() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const translate = useTranslations('sidebar_workspace');
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const t = (key: string) => translate(key as any);

  const isActive = (path: string) =>
    pathname === path || pathname.startsWith(`${path}/`);

  const isAgentActive = (agentId: string) =>
    searchParams.get('agent') === agentId ||
    pathname.includes(`/agents/specific/${agentId}`);

  const isItemActive = (item: NavItem) => {
    if (item.matchType === 'agent' && item.agentId) {
      return isAgentActive(item.agentId);
    }
    if (item.matchType === 'collections') {
      return (
        isActive('/workspace/collections') &&
        !isActive('/workspace/collections/all/graph')
      );
    }
    if (item.matchType === 'exact') {
      return pathname === item.href;
    }
    // default
    return isActive(item.href);
  };

  return (
    <>
      {NAV_CONFIG.map((group) => (
        <SidebarGroup key={group.labelKey}>
          <SidebarGroupLabel>{t(group.labelKey)}</SidebarGroupLabel>
          <SidebarMenu>
            {group.items.map((item) => (
              <SidebarMenuItem key={item.href}>
                <SidebarMenuButton asChild isActive={isItemActive(item)}>
                  <Link href={item.href}>
                    <item.icon className={cn('size-4', item.iconClassName)} />
                    <span>{t(item.titleKey)}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      ))}

      {/* 会话入口保留顶部默认入口,因此此处不再重复 */}
    </>
  );
}
