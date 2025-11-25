// 智能体API TypeScript客户端
// 提供完整的类型定义和API调用方法

// ========== 类型定义 ==========

export interface SupervisorRequest {
    task: string;
    user_id: string;
    chat_id?: string;
    priority?: 'urgent' | 'high' | 'normal';
}

export interface SupervisorResponse {
    success: boolean;
    message: string;
    data?: any;
    task_analysis?: {
        task_type: string;
        complexity: string;
        requires_collaboration: boolean;
        priority: string;
        involved_agents: string[];
    };
    thinking_stream?: ThinkingStep[];
}

export interface StationStatusResponse {
    success: boolean;
    status: {
        timestamp: string;
        overall_status: string;
        equipment_count: number;
        alarm_count: number;
        equipment_status: any[];
        recent_alarms: any[];
    };
}

export interface ArchivistRequest {
    query: string;
    user_id: string;
    chat_id?: string;
    search_type?: 'vector' | 'graph' | 'hybrid';
    top_k?: number;
}

export interface ArchivistResponse {
    success: boolean;
    message: string;
    answer?: string;
    documents?: any[];
    count: number;
    thinking_stream?: ThinkingStep[];
}

export interface AccidentDeductionRequest {
    task: string;
    equipment?: string;
    scenario?: string;
    user_id: string;
    chat_id?: string;
    model_provider?: string;
    model_name?: string;
    enable_rag?: boolean;
    enable_llm?: boolean;
}

export interface AccidentDeductionResponse {
    success: boolean;
    message: string;
    data?: any;
    report?: string;
    thinking_stream?: ThinkingStep[];
}

export interface ThinkingStep {
    step_type: string;
    description: string;
    detail?: any;
    timestamp?: string;
}

// ========== API客户端 ==========

// API基础URL配置
// 在生产环境中，可以通过环境变量或构建时配置来设置
// 例如：在 Next.js 中使用 NEXT_PUBLIC_API_URL
const API_BASE_URL = (typeof window !== 'undefined' && (window as any).ENV?.API_URL)
    || 'http://localhost:8000';

class AgentAPIClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    // ========== Supervisor API ==========

    async dispatchTask(request: SupervisorRequest): Promise<SupervisorResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agents/supervisor/dispatch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async getStationStatus(userId: string): Promise<StationStatusResponse> {
        const response = await fetch(
            `${this.baseUrl}/api/v1/agents/supervisor/status?user_id=${userId}`
        );

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    // WebSocket for real-time dispatch
    createSupervisorWebSocket(
        onMessage: (data: any) => void,
        onError?: (error: Event) => void
    ): WebSocket {
        const ws = new WebSocket(`ws://localhost:8000/api/v1/agents/supervisor/ws/dispatch`);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage(data);
        };

        if (onError) {
            ws.onerror = onError;
        }

        return ws;
    }

    // ========== Archivist API ==========

    async searchKnowledge(request: ArchivistRequest): Promise<ArchivistResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agents/archivist/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async graphTraversal(request: ArchivistRequest): Promise<ArchivistResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agents/archivist/graph-traversal`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async historicalSearch(request: ArchivistRequest): Promise<ArchivistResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agents/archivist/historical-search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    // ========== Accident Deduction API ==========

    async generateAccidentDeduction(
        request: AccidentDeductionRequest
    ): Promise<AccidentDeductionResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agents/accident-deduction/deduction`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async generateEmergencyPlan(task: string, userId: string): Promise<AccidentDeductionResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agents/accident-deduction/emergency-plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                task,
                user_id: userId,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async designDrill(task: string, userId: string): Promise<AccidentDeductionResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/agents/accident-deduction/drill-design`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                task,
                user_id: userId,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async getAccidentTemplates(): Promise<any> {
        const response = await fetch(`${this.baseUrl}/api/v1/agents/accident-deduction/templates`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    // ========== Health Checks ==========

    async checkSupervisorHealth(): Promise<any> {
        const response = await fetch(`${this.baseUrl}/api/v1/agents/supervisor/health`);
        return await response.json();
    }

    async checkArchivistHealth(): Promise<any> {
        const response = await fetch(`${this.baseUrl}/api/v1/agents/archivist/health`);
        return await response.json();
    }

    async checkAccidentDeductionHealth(): Promise<any> {
        const response = await fetch(`${this.baseUrl}/api/v1/agents/accident-deduction/health`);
        return await response.json();
    }
}

// 导出单例
export const agentAPI = new AgentAPIClient();

// 导出类以便自定义实例
export default AgentAPIClient;
