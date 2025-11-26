import { request } from './client';

// ========== 类型定义 ==========

export interface ArchivistRequest {
    query: string;
    user_id: string;
    chat_id?: string;
    search_type?: 'vector' | 'graph' | 'hybrid';
    top_k?: number;
    collection_ids?: string[];
}

export interface ThinkingStep {
    step_type: string;
    description: string;
    detail?: any;
    timestamp?: string;
}

export interface ArchivistResponse {
    success: boolean;
    message: string;
    answer?: string;
    documents?: any[];
    count: number;
    thinking_stream?: ThinkingStep[];
}

// ========== API客户端 ==========

export const agentAPI = {
    // ========== Archivist API ==========

    async searchKnowledge(req: ArchivistRequest): Promise<ArchivistResponse> {
        const response = await request.post('/agents/archivist/search', req);
        return response.data;
    },

    async graphTraversal(req: ArchivistRequest): Promise<ArchivistResponse> {
        const response = await request.post('/agents/archivist/graph-traversal', req);
        return response.data;
    },

    async historicalSearch(req: ArchivistRequest): Promise<ArchivistResponse> {
        const response = await request.post('/agents/archivist/historical-search', req);
        return response.data;
    },

    async checkArchivistHealth(): Promise<any> {
        const response = await request.get('/agents/archivist/health');
        return response.data;
    },
};
