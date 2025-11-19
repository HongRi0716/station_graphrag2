'use client';

import { PageContainer } from '@/components/page-container';

export default function GlobalGraphPage() {
  return (
    <PageContainer>
      <div className="flex h-[80vh] flex-col items-center justify-center space-y-4 text-center">
        <h1 className="text-2xl font-bold">
          全局知识图谱 (Global Knowledge Graph)
        </h1>
        <p className="text-muted-foreground max-w-md">
          正在构建跨知识库的实体关联网络。此功能将聚合您所有“我的知识库”中的实体与关系。
        </p>
        <div className="bg-muted/50 rounded-lg border p-4 font-mono text-sm">
          Feature under construction: Federation Layer
        </div>
      </div>
    </PageContainer>
  );
}
