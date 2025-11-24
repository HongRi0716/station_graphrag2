import {
  Activity,
  BookOpen,
  Bot,
  Calculator,
  ClipboardCheck,
  ClipboardList,
  Eye,
  FileSearch,
  Globe,
  GraduationCap,
  Library,
  PenTool,
  Share2,
  Shield,
  ShieldCheck,
  TrendingUp,
  Zap,
  LucideIcon,
} from 'lucide-react';

export interface NavItem {
  titleKey: string;
  href: string;
  icon: LucideIcon;
  iconClassName?: string; // For coloring
  agentId?: string;
  // Custom matching logic identifier
  matchType?: 'default' | 'exact' | 'collections' | 'agent';
}

export interface NavGroup {
  labelKey: string;
  items: NavItem[];
}

export const NAV_CONFIG: NavGroup[] = [
  {
    labelKey: 'knowledge_base',
    items: [
      {
        titleKey: 'public_collections',
        href: '/marketplace',
        icon: Globe,
        matchType: 'default',
      },
      {
        titleKey: 'my_collections',
        href: '/workspace/collections',
        icon: BookOpen,
        matchType: 'collections',
      },
      {
        titleKey: 'global_graph',
        href: '/workspace/collections/all/graph',
        icon: Share2,
        matchType: 'default',
      },
    ],
  },
  {
    labelKey: 'agents',
    items: [
      {
        titleKey: 'digital_engineer_team',
        href: '/workspace/agents',
        icon: Bot,
        matchType: 'default',
      },
      {
        titleKey: 'agent_supervisor',
        href: '/workspace/agents/specific/supervisor',
        icon: Zap,
        iconClassName: 'text-yellow-500',
        agentId: 'supervisor',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_detective',
        href: '/workspace/agents/specific/detective',
        icon: FileSearch,
        iconClassName: 'text-purple-500',
        agentId: 'detective',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_sentinel',
        href: '/workspace/agents/specific/sentinel',
        icon: Eye,
        iconClassName: 'text-slate-500',
        agentId: 'sentinel',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_archivist',
        href: '/workspace/agents/specific/archivist',
        icon: Library,
        iconClassName: 'text-amber-500',
        agentId: 'archivist',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_gatekeeper',
        href: '/workspace/agents/specific/gatekeeper',
        icon: ShieldCheck,
        iconClassName: 'text-blue-500',
        agentId: 'gatekeeper',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_diagnostician',
        href: '/workspace/agents/specific/diagnostician',
        icon: Activity,
        iconClassName: 'text-red-600',
        agentId: 'diagnostician',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_prophet',
        href: '/workspace/agents/specific/prophet',
        icon: TrendingUp,
        iconClassName: 'text-green-500',
        agentId: 'prophet',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_instructor',
        href: '/workspace/agents/specific/instructor',
        icon: GraduationCap,
        iconClassName: 'text-indigo-500',
        agentId: 'instructor',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_calculator',
        href: '/workspace/agents/specific/calculator',
        icon: Calculator,
        iconClassName: 'text-orange-500',
        agentId: 'calculator',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_scribe',
        href: '/workspace/agents/specific/scribe',
        icon: PenTool,
        iconClassName: 'text-cyan-500',
        agentId: 'scribe',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_auditor',
        href: '/workspace/agents/specific/auditor',
        icon: ClipboardList,
        iconClassName: 'text-rose-500',
        agentId: 'auditor',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_operation_ticket',
        href: '/workspace/agents/specific/operation_ticket',
        icon: ClipboardCheck,
        iconClassName: 'text-teal-500',
        agentId: 'operation_ticket',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_work_permit',
        href: '/workspace/agents/specific/work_permit',
        icon: FileSearch,
        iconClassName: 'text-violet-500',
        agentId: 'work_permit',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_accident_deduction',
        href: '/workspace/agents/specific/accident_deduction',
        icon: Activity,
        iconClassName: 'text-pink-600',
        agentId: 'accident_deduction',
        matchType: 'agent',
      },
      {
        titleKey: 'agent_power_guarantee',
        href: '/workspace/agents/specific/guardian',
        icon: Shield,
        iconClassName: 'text-emerald-500',
        agentId: 'guardian',
        matchType: 'agent',
      },
    ],
  },
];

