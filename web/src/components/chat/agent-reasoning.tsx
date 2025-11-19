import {
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Loader2,
  UserCog,
} from 'lucide-react';
import { useState } from 'react';

import { cn } from '@/lib/utils';

export interface ThinkingStep {
  id: string;
  agentName: string;
  action: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  content?: string;
  timestamp: number;
}

interface AgentReasoningProps {
  steps: ThinkingStep[];
  isFinished: boolean;
  className?: string;
}

export function AgentReasoning({
  steps,
  isFinished,
  className,
}: AgentReasoningProps) {
  const [isOpen, setIsOpen] = useState(!isFinished);

  if (!steps || !steps.length) {
    return null;
  }

  return (
    <div
      className={cn(
        'bg-muted/40 my-4 overflow-hidden rounded-lg border text-sm',
        className,
      )}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-muted/60 hover:bg-muted flex w-full items-center justify-between p-3 transition-colors"
      >
        <div className="text-foreground flex items-center gap-2 font-medium">
          {isFinished ? (
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          ) : (
            <BrainCircuit className="text-primary h-4 w-4 animate-pulse" />
          )}
          <span>智能体团队协同中 ({steps.length} 步骤)</span>
        </div>
        <div className="text-muted-foreground flex items-center gap-2">
          <span className="text-xs">{isFinished ? '完成' : '执行中...'}</span>
          {isOpen ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </div>
      </button>

      {isOpen && (
        <div className="bg-background/50 space-y-5 p-4">
          {steps.map((step, index) => (
            <div key={step.id} className="relative pl-8 last:pb-0">
              {index !== steps.length - 1 && (
                <div className="bg-border absolute top-6 bottom-0 left-[11px] w-0.5" />
              )}

              <div
                className={cn(
                  'bg-background absolute top-1 left-0 z-10 flex h-6 w-6 items-center justify-center rounded-full border',
                  step.status === 'running'
                    ? 'border-primary text-primary shadow-[0_0_8px_rgba(var(--primary),0.5)]'
                    : step.status === 'completed'
                      ? 'border-green-500 bg-green-500/10 text-green-500'
                      : 'border-muted-foreground/30 text-muted-foreground',
                )}
              >
                {step.status === 'running' ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : step.status === 'completed' ? (
                  <CheckCircle2 className="h-3 w-3" />
                ) : (
                  <div className="bg-muted-foreground/30 h-2 w-2 rounded-full" />
                )}
              </div>

              <div className="flex flex-col gap-1.5">
                <div className="flex items-center gap-2">
                  <div className="bg-primary/10 text-primary border-primary/20 flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-bold">
                    <UserCog className="h-3 w-3" />
                    {step.agentName}
                  </div>
                  <span className="text-muted-foreground text-xs">
                    {new Date(step.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                <p className="text-sm leading-none font-medium">
                  {step.action}
                </p>

                {step.content && (
                  <div className="bg-muted/50 text-muted-foreground mt-2 overflow-x-auto rounded-md border p-3 font-mono text-xs whitespace-pre-wrap">
                    {step.content}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
