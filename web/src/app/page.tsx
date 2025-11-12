import { AppTopbar } from '@/components/app-topbar';
import { PageContainer, PageContent } from '@/components/page-container';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';

const painPoints = [
  {
    title: '资料分散，难以共用',
    description: '图纸、规程、报告散落在不同系统，关键时刻找不到、找不全。',
  },
  {
    title: '经验断层，响应迟缓',
    description: '专家经验随人流转，新人成长慢，重复问题占据大量时间。',
  },
  {
    title: '图纸版本，隐患难控',
    description: '新旧版本混用，现场施工与检修容易埋下安全风险。',
  },
  {
    title: '数据沉睡，无法预警',
    description: '在线监测、巡视记录难以联动，难以支撑预测性维护决策。',
  },
];

const features = [
  {
    title: '全景档案一体化管理',
    description:
      '汇聚一次设计、保护定值、巡视与检修记录等资料，按主设备与回路自动建档，实时呈现生命周期状态。',
  },
  {
    title: '图谱驱动的精准检索',
    description:
      '基于设备拓扑与知识图谱，支持按间隔、告警、工单多维检索，快速定位关联文档与处置措施。',
  },
  {
    title: '多源数据智能解析',
    description:
      '自动识别红外测温、无人机影像、监控视频与报告等复杂格式，沉淀结构化知识节点。',
  },
  {
    title: '安全合规运营中心',
    description:
      '提供操作留痕、权限分级、审计追踪与数据水印，支撑主责部门闭环化治理与风险追溯。',
  },
  {
    title: '巡检作业协同闭环',
    description:
      '跨站点共享点检路线、缺陷票与备品状态，自动生成复核提醒与班组交接记录。',
  },
  {
    title: '弹性部署与生态对接',
    description:
      '兼容局端、本地及云边协同部署，快速对接调度 SCADA、EMS、DMS 与智能巡检终端。',
  },
];

export default function Home() {
  return (
    <>
      <AppTopbar />
      <PageContainer className="relative px-6">
        <div
          aria-hidden="true"
          className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80"
        >
          <div
            style={{
              clipPath:
                'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)',
            }}
            className="relative left-[calc(50%-11rem)] aspect-1155/678 w-144.5 -translate-x-1/2 rotate-30 bg-linear-to-tr from-[#ff80b5] to-[#9089fc] opacity-30 sm:left-[calc(50%-30rem)] sm:w-288.75"
          ></div>
        </div>
        <PageContent className="mx-auto max-w-300 py-32">
          <div className="mx-auto flex max-w-6xl flex-col items-center gap-8 text-center">
            <div className="inline-flex items-center justify-center gap-3 rounded-full border border-sky-400/40 bg-sky-400/10 px-6 py-2 text-sm font-semibold tracking-[0.35em] text-sky-600 uppercase dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-300">
              变电站全时空感知
              <span className="inline-flex h-2 w-2 rounded-full bg-amber-400" />
              数据驱动安全运维
            </div>
            <div className="relative">
              <div className="absolute -inset-6 rounded-[40px] bg-gradient-to-br from-sky-500/30 via-amber-300/20 to-transparent blur-3xl" />
              <div className="relative flex h-32 w-32 items-center justify-center rounded-[36px] bg-white/90 shadow-2xl ring-1 ring-sky-500/30 backdrop-blur dark:bg-slate-900/90 dark:ring-sky-500/40">
                <Image
                  src="/logo-intelligent-graph.svg"
                  alt="变电站智能数字图书馆标识"
                  width={110}
                  height={110}
                  priority
                  className="drop-shadow-[0_0_18px_rgba(66,153,225,0.45)]"
                />
              </div>
            </div>
            <h1 className="max-w-4xl text-4xl leading-tight font-semibold tracking-tight text-pretty sm:text-5xl lg:text-6xl">
              变电站智慧大脑：激活知识资产，赋能电网未来
            </h1>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-center">
              <Button size="lg" asChild className="h-12 px-8 text-base">
                <Link href="/workspace/collections">立即体验</Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                asChild
                className="h-12 border-sky-500/50 px-8 text-base hover:bg-sky-500/10"
              >
                <Link href="/marketplace">
                  探索智能工具
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </PageContent>
        <div
          aria-hidden="true"
          className="absolute inset-x-0 top-[calc(100%-30rem)] -z-10 transform-gpu overflow-hidden blur-3xl sm:top-[calc(100%-40rem)]"
        >
          <div
            style={{
              clipPath:
                'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)',
            }}
            className="relative left-[calc(50%+3rem)] aspect-1155/678 w-144.5 -translate-x-1/2 bg-linear-to-tr from-[#ff80b5] to-[#9089fc] opacity-30 sm:left-[calc(50%+36rem)] sm:w-288.75"
          ></div>
        </div>

        <PageContent className="py-12">
          <div className="text-center">
            <p className="text-sm font-medium tracking-[0.3em] text-sky-500 uppercase">
              核心能力
            </p>
            <h2 className="mt-3 text-3xl font-semibold text-slate-900 dark:text-slate-100">
              打造全生命周期的变电站数字资产基座
            </h2>
            <p className="text-muted-foreground mt-4 text-base">
              从数据接入、档案治理、知识构建到业务协同，全方位支撑变电站数字化升级与智慧运维。
            </p>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {features.map((feature, index) => (
              <div
                key={feature.title}
                className="group relative overflow-hidden rounded-3xl border border-slate-200/80 bg-white/80 p-8 shadow-lg shadow-slate-950/5 backdrop-blur transition-transform duration-300 hover:-translate-y-1 hover:border-sky-400/60 hover:shadow-sky-500/20 dark:border-slate-700/60 dark:bg-slate-900/70"
              >
                <span className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-full bg-sky-500/10 text-sm font-semibold text-sky-600 dark:text-sky-300">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <h3 className="mb-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">
                  {feature.title}
                </h3>
                <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </PageContent>
      </PageContainer>
    </>
  );
}
