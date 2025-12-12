"use client";

import React from 'react';
import { PageContainer, PageHeader, PageContent } from "@/components/page-container";
import { LucideIcon } from 'lucide-react';

interface AgentWorkspaceLayoutProps {
    /** 面包屑导航 */
    breadcrumbs: Array<{ title: string; href?: string }>;
    /** 智能体标题 */
    title: string;
    /** 智能体描述 */
    description: string;
    /** 图标组件 */
    icon: LucideIcon;
    /** 主题颜色 (violet, pink, blue, amber, green, etc.) */
    color: string;
    /** 子内容 */
    children: React.ReactNode;
}

/**
 * 智能体工作区布局组件
 * 
 * 提供统一的页面结构，包括面包屑导航和带有渐变背景的标题区域
 */
export function AgentWorkspaceLayout({
    breadcrumbs,
    title,
    description,
    icon: Icon,
    color,
    children
}: AgentWorkspaceLayoutProps) {
    // 根据颜色生成对应的 CSS 类
    const colorClasses = {
        border: `border-${color}-500/20`,
        bg: `from-${color}-500/10 via-${color}-500/5`,
        iconBg: `bg-${color}-500/20`,
        iconColor: `text-${color}-500`
    };

    return (
        <PageContainer>
            <PageHeader breadcrumbs={breadcrumbs} />
            <PageContent>
                <div className="space-y-6">
                    {/* Header Section */}
                    <div className={`relative overflow-hidden rounded-xl border ${colorClasses.border} bg-gradient-to-br ${colorClasses.bg} to-background p-8`}>
                        <div className="relative z-10">
                            <div className="flex items-center space-x-4 mb-6">
                                <div className={`p-3 rounded-full ${colorClasses.iconBg} backdrop-blur-sm`}>
                                    <Icon className={`w-8 h-8 ${colorClasses.iconColor}`} />
                                </div>
                                <div>
                                    <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
                                    <p className="text-muted-foreground mt-1">{description}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Main Content */}
                    {children}
                </div>
            </PageContent>
        </PageContainer>
    );
}

export default AgentWorkspaceLayout;
