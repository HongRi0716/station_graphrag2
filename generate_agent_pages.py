
import os

AGENTS = [
    {
        "id": "supervisor",
        "title": "The Supervisor",
        "title_zh": "总控大脑",
        "description": "变电站总控大脑。负责意图识别、任务拆解、指挥其他专家协同工作。",
        "icon_import": "Zap",
        "color": "text-yellow-500",
        "bg": "bg-yellow-500/10",
        "features": [
            {"title": "任务编排 (Task Orchestration)", "desc": "将复杂的运维任务拆解为子任务，并分发给相应的专家智能体。"},
            {"title": "综合研判 (Comprehensive Analysis)", "desc": "汇总各方信息，提供全局视角的决策建议。"},
            {"title": "SOP生成 (SOP Generation)", "desc": "根据当前场景自动生成标准作业程序 (SOP)。"}
        ],
        "input_placeholder": "例如：请制定一份针对主变压器油温过高的应急处理方案，并指挥相关人员进行检查。"
    },
    {
        "id": "sentinel",
        "title": "The Sentinel",
        "title_zh": "巡视哨兵",
        "description": "实时视频监控分析。负责表计读数、安全帽佩戴检测、异物入侵报警。",
        "icon_import": "Eye",
        "color": "text-slate-500",
        "bg": "bg-slate-500/10",
        "features": [
            {"title": "实时监控 (Real-time Monitoring)", "desc": "接入视频流，实时检测异常情况。"},
            {"title": "表计识别 (Meter Reading)", "desc": "自动识别各类仪表读数，并记录归档。"},
            {"title": "安防检测 (Security Detection)", "desc": "检测人员穿戴合规性、非法入侵等安全隐患。"}
        ],
        "input_placeholder": "例如：检查 2 号主变区域的监控视频，确认是否有人员未佩戴安全帽。"
    },
    {
        "id": "archivist",
        "title": "The Archivist",
        "title_zh": "图谱专家",
        "description": "全局知识检索官。跨库搜索设备台账、历史缺陷、检修报告。",
        "icon_import": "Library",
        "color": "text-amber-500",
        "bg": "bg-amber-500/10",
        "features": [
            {"title": "跨库搜索 (Federated Search)", "desc": "同时检索文档库、数据库和知识图谱。"},
            {"title": "实体溯源 (Entity Traceability)", "desc": "追溯设备的全生命周期数据。"},
            {"title": "档案查询 (Archive Query)", "desc": "快速查找历史检修记录和技术档案。"}
        ],
        "input_placeholder": "例如：查询 110kV 隔离开关近三年的检修记录和缺陷报告。"
    },
    {
        "id": "instructor",
        "title": "The Instructor",
        "title_zh": "培训教官",
        "description": "技能培训与考核系统。模拟倒闸操作演练，进行苏格拉底式教学。",
        "icon_import": "GraduationCap",
        "color": "text-indigo-500",
        "bg": "bg-indigo-500/10",
        "features": [
            {"title": "模拟演练 (Simulation Drills)", "desc": "提供虚拟环境进行倒闸操作演练。"},
            {"title": "智能评分 (AI Grading)", "desc": "根据操作规范自动评估学员表现。"},
            {"title": "安规问答 (Safety Q&A)", "desc": "解答关于安全规程的疑问，进行互动式教学。"}
        ],
        "input_placeholder": "例如：我想进行一次 110kV 线路停电操作的模拟演练。"
    },
    {
        "id": "diagnostician",
        "title": "The Diagnostician",
        "title_zh": "故障诊断师",
        "description": "深度故障分析专家。解析录波文件与SOE日志，推演事故因果链。",
        "icon_import": "Activity",
        "color": "text-red-600",
        "bg": "bg-red-600/10",
        "features": [
            {"title": "录波分析 (Waveform Analysis)", "desc": "解析故障录波文件，分析电气量变化。"},
            {"title": "SOE推理 (SOE Reasoning)", "desc": "基于 SOE 记录推断事故发生顺序和原因。"},
            {"title": "事故报告 (Accident Report)", "desc": "自动生成详细的事故分析报告。"}
        ],
        "input_placeholder": "例如：分析上传的录波文件，判断故障类型和故障点位置。"
    },
    {
        "id": "prophet",
        "title": "The Prophet",
        "title_zh": "趋势预言家",
        "description": "时序数据分析师。接入在线监测数据，预测潜在故障趋势。",
        "icon_import": "TrendingUp",
        "color": "text-green-500",
        "bg": "bg-green-500/10",
        "features": [
            {"title": "趋势预测 (Trend Prediction)", "desc": "基于历史数据预测设备状态发展趋势。"},
            {"title": "异常检测 (Anomaly Detection)", "desc": "识别数据中的异常模式，提前预警。"},
            {"title": "数值分析 (Numerical Analysis)", "desc": "对监测数据进行深度统计分析。"}
        ],
        "input_placeholder": "例如：预测 1 号主变油中溶解气体含量的未来一周趋势。"
    },
    {
        "id": "calculator",
        "title": "The Calculator",
        "title_zh": "整定计算师",
        "description": "电气参数计算专家。精确核算继电保护定值、变比与负荷率。",
        "icon_import": "Calculator",
        "color": "text-orange-500",
        "bg": "bg-orange-500/10",
        "features": [
            {"title": "定值计算 (Setting Calculation)", "desc": "计算继电保护装置的整定值。"},
            {"title": "公式推导 (Formula Derivation)", "desc": "展示计算过程和依据的公式。"},
            {"title": "参数核算 (Parameter Verification)", "desc": "校验现有定值是否满足灵敏度要求。"}
        ],
        "input_placeholder": "例如：计算 10kV 线路过流保护的整定值，已知线路参数如下..."
    },
    {
        "id": "gatekeeper",
        "title": "The Gatekeeper",
        "title_zh": "安监卫士",
        "description": "安全规程守护者。基于安规知识库进行五防逻辑校验、两票审查。",
        "icon_import": "ShieldCheck",
        "color": "text-blue-500",
        "bg": "bg-blue-500/10",
        "features": [
            {"title": "安规校验 (Safety Regulation Check)", "desc": "检查操作步骤是否符合安全规程。"},
            {"title": "操作票生成 (Operation Ticket)", "desc": "自动生成标准化的倒闸操作票。"},
            {"title": "风险评估 (Risk Assessment)", "desc": "评估作业现场的安全风险并提出预控措施。"}
        ],
        "input_placeholder": "例如：审核这张工作票的安全措施是否完善。"
    },
    {
        "id": "scribe",
        "title": "The Scribe",
        "title_zh": "文书专员",
        "description": "自动化填报助手。将语音或非结构化文本转化为标准巡视记录单。",
        "icon_import": "PenTool",
        "color": "text-cyan-500",
        "bg": "bg-cyan-500/10",
        "features": [
            {"title": "语音转录 (Voice Transcription)", "desc": "将巡检语音记录转录为文字。"},
            {"title": "表单填充 (Form Filling)", "desc": "自动提取信息并填充到标准表格中。"},
            {"title": "文档生成 (Document Generation)", "desc": "生成巡检日报、周报等文档。"}
        ],
        "input_placeholder": "例如：根据这段语音记录，生成今天的巡检日志。"
    },
    {
        "id": "guardian",
        "title": "The Guardian",
        "title_zh": "电网安全卫士",
        "description": "电网安全守护者。负责保电方案制定、应急预案生成、安全风险评估。",
        "icon_import": "Shield",
        "color": "text-emerald-500",
        "bg": "bg-emerald-500/10",
        "features": [
            {"title": "保电方案 (Power Protection Plan)", "desc": "制定重要活动的保电方案。"},
            {"title": "应急预案 (Emergency Plan)", "desc": "生成针对特定突发事件的应急预案。"},
            {"title": "风险评估 (Risk Assessment)", "desc": "评估电网运行的安全风险。"}
        ],
        "input_placeholder": "例如：为即将到来的台风天气制定一份防汛抗台应急预案。"
    },
    {
        "id": "auditor",
        "title": "The Auditor",
        "title_zh": "合规审计师",
        "description": "文档合规性审查。批量检查检修报告是否符合最新行业标准。",
        "icon_import": "ClipboardList",
        "color": "text-rose-500",
        "bg": "bg-rose-500/10",
        "features": [
            {"title": "合规性检查 (Compliance Check)", "desc": "检查文档是否符合最新的行业标准和规范。"},
            {"title": "报告生成 (Report Generation)", "desc": "生成审计报告，指出不合规项。"},
            {"title": "自动纠错 (Auto Correction)", "desc": "对文档中的格式或内容错误提出修改建议。"}
        ],
        "input_placeholder": "例如：检查这份检修报告是否符合 Q/GDW 11372-2015 标准。"
    }
]

TEMPLATE = """
"use client";

import { PageContainer, PageHeader, PageContent } from "@/components/page-container";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { __ICON_IMPORT__, Search, Layers, Zap, MessageSquare } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { useTranslations } from "next-intl";

export default function __COMPONENT_NAME__Page() {
  const t = useTranslations("sidebar_workspace"); 

  const handleStartTask = () => {
    alert("任务已提交给 __TITLE__ (调用 Agent API)"); 
  };

  return (
    <PageContainer>
      <PageHeader 
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: "__TITLE_ZH__ 工作台" }
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          {/* Header Section */}
          <div className="flex items-center space-x-4 mb-8">
              <div className="p-3 rounded-full __BG__">
                  <__ICON_IMPORT__ className="w-8 h-8 __COLOR__" />
              </div>
              <div>
                  <h1 className="text-3xl font-bold tracking-tight">__TITLE_ZH__ 工作台</h1>
                  <p className="text-muted-foreground mt-1">
                    __DESCRIPTION__
                  </p>
              </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Task Area */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <Zap className="w-5 h-5 __COLOR__" />
                  <span>核心能力 (Core Capabilities)</span>
                </CardTitle>
                <CardDescription>选择一项能力开始任务，或直接在下方输入指令。</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  __FEATURES_JSX__
                </div>
                <Separator />
                <div className="space-y-2">
                    <h3 className="text-sm font-medium">任务指令</h3>
                    <Textarea 
                        placeholder="__INPUT_PLACEHOLDER__"
                        rows={4}
                    />
                </div>
                <Button 
                    onClick={handleStartTask} 
                    className="w-full"
                >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    发送指令
                </Button>
              </CardContent>
            </Card>

            {/* Side Panel: Quick Tools / Context */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-lg flex items-center space-x-2">
                  <Layers className="w-5 h-5 text-primary" />
                  <span>快捷工具</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">上下文检索</h3>
                  <Button variant="outline" className="w-full justify-start">
                    <Search className="w-4 h-4 mr-2" />
                    搜索相关文档
                  </Button>
                </div>
                <Separator />
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">历史记录</h3>
                  <div className="text-sm text-muted-foreground text-center py-4">
                    暂无最近任务记录
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </PageContent>
    </PageContainer>
  );
}
"""

def generate_pages():
    base_path = r"e:\我的口袋\科创\python\创意一_基于视觉语言大模型基座和模型蒸馏演化的全时空巡检天眼系统\model_zoo\ApeRAGv2\web\src\app\workspace\agents\specific"
    
    for agent in AGENTS:
        dir_path = os.path.join(base_path, agent["id"])
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        file_path = os.path.join(dir_path, "page.tsx")
        
        # Generate features JSX
        features_jsx = ""
        for feature in agent["features"]:
            features_jsx += f"""
                  <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors">
                    <h4 className="font-medium text-sm mb-1">{feature["title"]}</h4>
                    <p className="text-xs text-muted-foreground">{feature["desc"]}</p>
                  </div>"""
        
        component_name = agent["id"].capitalize() + "Workspace"
        
        content = TEMPLATE.replace("__COMPONENT_NAME__", component_name) \
                          .replace("__TITLE__", agent["title"]) \
                          .replace("__TITLE_ZH__", agent["title_zh"]) \
                          .replace("__DESCRIPTION__", agent["description"]) \
                          .replace("__ICON_IMPORT__", agent["icon_import"]) \
                          .replace("__COLOR__", agent["color"]) \
                          .replace("__BG__", agent["bg"]) \
                          .replace("__FEATURES_JSX__", features_jsx) \
                          .replace("__INPUT_PLACEHOLDER__", agent["input_placeholder"])
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        
        print(f"Generated {file_path}")

if __name__ == "__main__":
    generate_pages()
