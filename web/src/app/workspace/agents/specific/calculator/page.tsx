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
import { Separator } from '@/components/ui/separator';
import { Calculator, PenLine, Sigma, Zap } from 'lucide-react';
import { useTranslations } from 'next-intl';

const CalculationResultDisplay = ({
  formula,
  primary,
  secondary,
}: {
  formula: string;
  primary: string;
  secondary: string;
}) => (
  <Card className="border-primary/20 bg-muted/50 p-4">
    <div className="text-primary mb-3 flex items-center space-x-3 text-sm font-semibold">
      <Sigma className="h-5 w-5" />
      <span>计算结果摘要</span>
    </div>
    <p className="text-muted-foreground mb-3 font-mono text-xs">
      公式: {formula}
    </p>
    <div className="space-y-2">
      <div className="bg-background flex items-center justify-between rounded-md border p-3">
        <span className="font-medium">一次侧动作电流 (I op)</span>
        <span className="text-lg font-bold text-green-600">{primary}</span>
      </div>
      <div className="bg-background flex items-center justify-between rounded-md border p-3">
        <span className="font-medium">二次侧整定值 (I set)</span>
        <span className="text-lg font-bold text-blue-600">{secondary}</span>
      </div>
    </div>
  </Card>
);

export default function CalculatorWorkspacePage() {
  const t = useTranslations('sidebar_workspace');

  const [ctPrimary, setCtPrimary] = useState('600');
  const [ctSecondary, setCtSecondary] = useState('5');
  const [iLoadMax, setILoadMax] = useState('400');
  const [kRel, setKRel] = useState('1.3');

  const handleCalculate = () => {
    const P =
      parseFloat(ctPrimary || '1') / parseFloat(ctSecondary || '1') || 1;
    const I = parseFloat(iLoadMax || '0');
    const K = parseFloat(kRel || '1');

    if ([P, I, K].some((value) => Number.isNaN(value))) {
      alert('输入参数无效，请检查数值。');
      return;
    }

    const i_primary_op = (K * I) / 0.85;
    const i_secondary_op = i_primary_op / P;

    alert(
      `计算完成。一次侧: ${i_primary_op.toFixed(2)}A, 二次侧: ${i_secondary_op.toFixed(
        2,
      )}A. (调用 Calculator Agent)`,
    );
  };

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          { title: t('agents'), href: '/workspace/agents' },
          { title: `${t('agent_calculator')} 工作台` },
        ]}
      />
      <PageContent>
        <div className="space-y-6">
          <div className="flex items-center space-x-4">
            <div className="rounded-full bg-orange-500/10 p-3">
              <Calculator className="h-8 w-8 text-orange-500" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                {t('agent_calculator')} 工作台
              </h1>
              <p className="text-muted-foreground mt-1">
                专用工作区，用于精确的继电保护定值计算和变比核算。
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <PenLine className="h-5 w-5" />
                  <span>输入参数</span>
                </CardTitle>
                <CardDescription>
                  输入关键电气参数和系数，选择计算公式。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="formula">选择计算公式</Label>
                  <Input
                    id="formula"
                    className="bg-muted/30 font-mono"
                    readOnly
                    value="过流保护动作值计算 (I op = (K rel * I load_max) / K ret)"
                  />
                </div>
                <Separator />
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="ct-primary">CT 变比 (一次侧 A)</Label>
                    <Input
                      id="ct-primary"
                      placeholder="例如: 600"
                      value={ctPrimary}
                      onChange={(event) => setCtPrimary(event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ct-secondary">CT 变比 (二次侧 A)</Label>
                    <Input
                      id="ct-secondary"
                      placeholder="例如: 5"
                      value={ctSecondary}
                      onChange={(event) => setCtSecondary(event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="load-max">
                      最大负荷电流 (I load_max A)
                    </Label>
                    <Input
                      id="load-max"
                      placeholder="例如: 400"
                      value={iLoadMax}
                      onChange={(event) => setILoadMax(event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="k-rel">可靠系数 (K rel)</Label>
                    <Input
                      id="k-rel"
                      placeholder="例如: 1.3"
                      value={kRel}
                      onChange={(event) => setKRel(event.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
              <CardFooter>
                <Button
                  className="w-full bg-orange-600 hover:bg-orange-700"
                  onClick={handleCalculate}
                >
                  <Zap className="mr-2 h-4 w-4" />
                  运行精确计算
                </Button>
              </CardFooter>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-lg">
                  <Calculator className="h-5 w-5" />
                  <span>计算结果</span>
                </CardTitle>
                <CardDescription>
                  AI Code Interpreter 运行后的输出结果。
                </CardDescription>
              </CardHeader>
              <CardContent>
                <CalculationResultDisplay
                  formula="I op = (K rel * I load_max) / K ret"
                  primary="611.76 A"
                  secondary="5.10 A"
                />
                <div className="bg-background mt-6 rounded-lg border p-4 text-sm">
                  <h4 className="mb-2 font-semibold">计算详情 (AI 沙箱日志)</h4>
                  <pre className="text-muted-foreground font-mono text-xs">
                    {`>>> Running Python Script in Sandbox...
Variable I_max_sec = 5.10 A
Variable P_ratio = 120
Status: Success. Execution time: 45ms`}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </PageContent>
    </PageContainer>
  );
}
