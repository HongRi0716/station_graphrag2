'use client';

import {
  Activity,
  Bot,
  Calculator as CalculatorIcon,
  ClipboardList,
  Eye,
  FileSearch,
  GraduationCap,
  Library,
  PenTool,
  ShieldCheck,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { useRouter } from 'next/navigation';

import { PageContainer } from '@/components/page-container';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

const SPECIALIST_AGENTS = [
  {
    id: 'supervisor',
    title: 'The Supervisor (值长)',
    description:
      '变电站总控大脑。负责意图识别、任务拆解、指挥其他专家协同工作。',
    icon: Zap,
    color: 'text-yellow-500',
    bg: 'bg-yellow-500/10',
    capabilities: ['任务编排', '综合研判', 'SOP生成'],
  },
  {
    id: 'archivist',
    title: 'The Archivist (图谱专家)',
    description: '全局知识检索官。跨库搜索设备台账、历史缺陷、检修报告。',
    icon: Library,
    color: 'text-amber-500',
    bg: 'bg-amber-500/10',
    capabilities: ['跨库联邦搜索', '实体溯源', '档案查询'],
  },
  {
    id: 'detective',
    title: 'The Detective (图纸侦探)',
    description: '电气图纸与视觉专家。擅长OCR识别、拓扑关系提取、图纸比对。',
    icon: FileSearch,
    color: 'text-purple-500',
    bg: 'bg-purple-500/10',
    capabilities: ['视觉问答', '拓扑分析', '图纸比对'],
  },
  {
    id: 'sentinel',
    title: 'The Sentinel (巡视哨兵)',
    description:
      '实时视频监控分析。负责表计读数、安全帽佩戴检测、异物入侵报警。',
    icon: Eye,
    color: 'text-slate-500',
    bg: 'bg-slate-500/10',
    capabilities: ['实时监控', '表计识别', '安防检测'],
  },
  {
    id: 'diagnostician',
    title: 'The Diagnostician (故障诊断师)',
    description: '深度故障分析专家。解析录波文件与SOE日志，推演事故因果链。',
    icon: Activity,
    color: 'text-red-600',
    bg: 'bg-red-600/10',
    capabilities: ['录波分析', 'SOE推理', '事故报告'],
  },
  {
    id: 'prophet',
    title: 'The Prophet (趋势预言家)',
    description: '时序数据分析师。接入在线监测数据，预测潜在故障趋势。',
    icon: TrendingUp,
    color: 'text-green-500',
    bg: 'bg-green-500/10',
    capabilities: ['趋势预测', '异常检测', '数值分析'],
  },
  {
    id: 'calculator',
    title: 'The Calculator (整定计算师)',
    description: '电气参数计算专家。精确核算继电保护定值、变比与负荷率。',
    icon: CalculatorIcon,
    color: 'text-orange-500',
    bg: 'bg-orange-500/10',
    capabilities: ['定值计算', '代码解释器', '公式推导'],
  },
  {
    id: 'gatekeeper',
    title: 'The Gatekeeper (安监卫士)',
    description: '安全规程守护者。基于安规知识库进行五防逻辑校验、两票审查。',
    icon: ShieldCheck,
    color: 'text-blue-500',
    bg: 'bg-blue-500/10',
    capabilities: ['安规校验', '操作票生成', '风险评估'],
  },
  {
    id: 'scribe',
    title: 'The Scribe (文书专员)',
    description: '自动化填报助手。将语音或非结构化文本转化为标准巡视记录单。',
    icon: PenTool,
    color: 'text-cyan-500',
    bg: 'bg-cyan-500/10',
    capabilities: ['语音转录', '表单填充', '文档生成'],
  },
  {
    id: 'instructor',
    title: 'The Instructor (培训教官)',
    description: '技能培训与考核系统。模拟倒闸操作演练，进行苏格拉底式教学。',
    icon: GraduationCap,
    color: 'text-indigo-500',
    bg: 'bg-indigo-500/10',
    capabilities: ['模拟演练', '智能评分', '安规问答'],
  },
  {
    id: 'auditor',
    title: 'The Auditor (合规审计师)',
    description: '文档合规性审查。批量检查检修报告是否符合最新行业标准。',
    icon: ClipboardList,
    color: 'text-rose-500',
    bg: 'bg-rose-500/10',
    capabilities: ['合规性检查', '报告生成', '自动纠错'],
  },
];

export default function AgentsPage() {
  const router = useRouter();

  const startAgentSession = (agentId: string) => {
    router.push(`/workspace/chat?agent=${agentId}&new_session=true`);
  };

  return (
    <PageContainer>
      <div className="space-y-8 p-4 pt-6 md:p-8">
        <div className="flex flex-col space-y-4">
          <div className="flex items-center space-x-4">
            <div className="bg-primary/10 rounded-full p-3">
              <Bot className="text-primary h-8 w-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                数字工程师团队 (Agent Workbench)
              </h1>
              <p className="text-muted-foreground mt-1">
                选择特定的垂直领域智能体来处理复杂的变电站运维任务。
              </p>
            </div>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {SPECIALIST_AGENTS.map((agent) => (
            <Card
              key={agent.id}
              className="group hover:border-primary/50 flex h-full flex-col border transition-all duration-300 hover:shadow-lg"
            >
              <CardHeader>
                <div className="mb-2 flex items-start justify-between">
                  <div
                    className={`${agent.bg} rounded-xl p-3 ring-1 ring-black/5 ring-inset dark:ring-white/5`}
                  >
                    <agent.icon className={`h-6 w-6 ${agent.color}`} />
                  </div>
                  {agent.id === 'supervisor' && (
                    <Badge
                      variant="default"
                      className="bg-primary/80 hover:bg-primary"
                    >
                      Leader
                    </Badge>
                  )}
                </div>
                <CardTitle className="text-lg font-semibold">
                  {agent.title}
                </CardTitle>
                <CardDescription className="mt-2 line-clamp-3 min-h-[60px] text-xs">
                  {agent.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="flex-grow">
                <div className="flex flex-wrap gap-2">
                  {agent.capabilities.map((cap) => (
                    <Badge
                      key={cap}
                      variant="secondary"
                      className="bg-secondary/50 px-2 py-0.5 text-[10px] font-normal"
                    >
                      {cap}
                    </Badge>
                  ))}
                </div>
              </CardContent>

              <CardFooter className="pt-4">
                <Button
                  className="group-hover:bg-primary group-hover:text-primary-foreground w-full shadow-sm transition-colors"
                  variant="outline"
                  onClick={() => startAgentSession(agent.id)}
                >
                  <Zap className="mr-2 h-4 w-4" />
                  激活智能体
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </PageContainer>
  );
}
