'use client';

import { useState } from 'react';

import {
  PageContainer,
  PageContent,
  PageHeader,
} from '@/components/page-container';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { BookOpen, GraduationCap, MessageSquare, Play } from 'lucide-react';
import { useTranslations } from 'next-intl';

export default function InstructorWorkspacePage() {
  const t = useTranslations('sidebar_workspace');
  const [scenario, setScenario] = useState<string | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [feedback, setFeedback] = useState<string | null>(null);

  const startTraining = () => {
    setScenario(
      '模拟场景：110kV I母、II母并列运行，现需将 #1主变 110kV侧 101开关 由 I母倒至 II母运行。请口述第一步操作。',
    );
    setFeedback(null);
    setUserAnswer('');
  };

  const submitAnswer = () => {
    if (!userAnswer.trim()) return;
    // Mock feedback
    if (userAnswer.includes('压板') || userAnswer.includes('互联')) {
      setFeedback('✅ 回答正确！关键点：投入母差保护互联压板。');
    } else {
      setFeedback('❌ 回答不完整。提示：考虑母差保护的运行方式。');
    }
  };

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: '培训教官 (Instructor) 工作台' },
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          <div className="flex items-center space-x-4">
            <div className="rounded-full bg-blue-500/10 p-3">
              <GraduationCap className="h-8 w-8 text-blue-500" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                培训教官 (Instructor) 工作台
              </h1>
              <p className="text-muted-foreground mt-1">
                负责变电站运维人员的技能培训与考核，模拟故障处置场景。
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card className="flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <BookOpen className="h-5 w-5" />
                  <span>演练场景</span>
                </CardTitle>
                <CardDescription>
                  点击开始生成随机演练题目。
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 space-y-4">
                {!scenario ? (
                  <div className="flex h-40 items-center justify-center rounded-md border border-dashed">
                    <p className="text-muted-foreground text-sm">
                      暂无进行中的演练
                    </p>
                  </div>
                ) : (
                  <div className="bg-muted/30 rounded-md p-4">
                    <p className="font-medium">{scenario}</p>
                  </div>
                )}
              </CardContent>
              <CardFooter>
                <Button
                  className="w-full"
                  onClick={startTraining}
                  disabled={!!scenario && !feedback}
                >
                  <Play className="mr-2 h-4 w-4" />
                  {scenario ? '切换下一题' : '开始演练'}
                </Button>
              </CardFooter>
            </Card>

            <Card className="flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <MessageSquare className="h-5 w-5" />
                  <span>学员作答</span>
                </CardTitle>
                <CardDescription>
                  输入您的操作步骤或回答。
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="answer">您的回答</Label>
                  <Textarea
                    id="answer"
                    placeholder="在此输入..."
                    className="min-h-[120px]"
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    disabled={!scenario || !!feedback}
                  />
                </div>
                {feedback && (
                  <div
                    className={`rounded-md p-3 text-sm font-medium ${
                      feedback.startsWith('✅')
                        ? 'bg-green-500/10 text-green-600'
                        : 'bg-red-500/10 text-red-600'
                    }`}
                  >
                    {feedback}
                  </div>
                )}
              </CardContent>
              <CardFooter>
                <Button
                  className="w-full"
                  onClick={submitAnswer}
                  disabled={!scenario || !!feedback || !userAnswer.trim()}
                >
                  提交回答
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
      </PageContent>
    </PageContainer>
  );
}
