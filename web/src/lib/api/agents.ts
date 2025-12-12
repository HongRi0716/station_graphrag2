import { request } from './client';

// ========== 基础类型定义 ==========

/**
 * 思考步骤 - 用于展示智能体的思维过程
 */
export interface ThinkingStep {
    step_type: string;
    description: string;
    detail?: any;
    timestamp?: string;
}

/**
 * 智能体请求基类
 */
export interface BaseAgentRequest {
    query: string;       // 前端统一使用 query
    user_id: string;
    chat_id?: string;
}

/**
 * 智能体响应基类
 */
export interface BaseAgentResponse {
    success: boolean;
    message: string;
    answer?: string;     // 统一使用 answer 字段
    thinking_stream?: ThinkingStep[];
}

// ========== Archivist (图谱专家) 类型定义 ==========

export interface ArchivistRequest extends BaseAgentRequest {
    search_type?: 'vector' | 'graph' | 'hybrid';
    top_k?: number;
    collection_ids?: string[];
}

export interface ArchivistResponse extends BaseAgentResponse {
    documents?: any[];
    count: number;
}

// ========== Accident Deduction (事故预想) 类型定义 ==========

export interface AccidentDeductionRequest extends BaseAgentRequest {
    equipment?: string;
    scenario?: string;
    model_provider?: string;
    model_name?: string;
    enable_rag?: boolean;
    enable_llm?: boolean;
}

export interface AccidentDeductionResponse extends BaseAgentResponse {
    data?: any;           // 后端的 data 字段
    report?: string;      // 向后兼容：后端原始字段
    deduction?: {
        title?: string;
        equipment?: string;
        accident_type?: string;
        possible_causes?: Array<{
            cause: string;
            probability: string;
            description: string;
        }>;
        consequences?: Array<{
            consequence: string;
            severity: string;
        }>;
        immediate_actions?: Array<{
            action: string;
            priority: string;
        }>;
        emergency_plan?: string;
    };
}

// ========== Power Guarantee (保电方案) 类型定义 ==========

export interface PowerGuaranteeRequest extends BaseAgentRequest {
    event_name?: string;
    event_level?: string;
    start_date?: string;
    end_date?: string;
}

export interface PowerGuaranteeResponse extends BaseAgentResponse {
    plan?: {
        plan_no?: string;
        plan_name?: string;
        event_info?: any;
        organization?: any;
        risk_assessment?: any;
        measures?: Array<{
            category: string;
            items: string[];
        }>;
        inspection_plan?: any;
        emergency_scenarios?: Array<{
            scenario: string;
            response: string;
        }>;
        resource_preparation?: any;
    };
}

// ========== Operation Ticket (操作票) 类型定义 ==========

export interface OperationTicketRequest extends BaseAgentRequest {
    equipment?: string;
    operation_type?: string;
    target_state?: string;
    ticket_no?: string;
    ticket_content?: string;
    enable_rag?: boolean;
    enable_llm?: boolean;
}

export interface OperationTicketResponse extends BaseAgentResponse {
    report?: string;     // 向后兼容
    ticket?: {
        ticket_no?: string;
        title?: string;
        equipment?: string;
        voltage_level?: string;
        operation_date?: string;
        estimated_time?: string;
        operator?: string;
        supervisor?: string;
        prerequisites?: string[];
        steps?: Array<{
            seq: number;
            action: string;
            detail: string;
            safety_note?: string;
        }>;
        safety_check?: {
            five_prevention_check?: string;
            sequence_check?: string;
            completeness_check?: string;
            regulation_compliance?: string;
            warnings?: string[];
            suggestions?: string[];
        };
    };
}

// ========== Work Permit (工作票) 类型定义 ==========

export interface WorkPermitRequest extends BaseAgentRequest {
    equipment?: string;
    work_content?: string;
    ticket_no?: string;
    ticket_content?: string;
}

export interface WorkPermitResponse extends BaseAgentResponse {
    report?: string;     // 向后兼容
    ticket?: {
        permit_no?: string;
        ticket_no?: string;  // 别名，向后兼容
        permit_type?: string;
        work_location?: string;
        equipment?: string;
        voltage_level?: string;
        work_content?: string;
        planned_start?: string;
        planned_end?: string;
        work_duration?: string;
        safety_measures?: Array<{
            category: string;
            content: string;
            responsible?: string;
            mandatory?: boolean;
        }>;
    };
    hazards?: Array<{
        id: string;
        type: string;
        description: string;
        severity: string;
        location: string;
    }>;
    review_result?: any;
}

// ========== 兼容类型别名 ==========

// 保持向后兼容，使用旧的类型名称
export type TicketRequest = OperationTicketRequest;
export type TicketResponse = OperationTicketResponse;

// ========== 工具函数 ==========

/**
 * 将前端请求格式转换为后端期望的格式
 * 主要是将 query 映射为 task
 */
function mapRequestToBackend<T extends BaseAgentRequest>(req: T): any {
    const { query, ...rest } = req;
    return {
        task: query,  // 后端使用 task 字段
        ...rest
    };
}

/**
 * 将后端响应格式转换为前端期望的格式
 * 主要是将 report 映射为 answer
 */
function mapResponseToFrontend<T extends BaseAgentResponse>(data: any): T {
    return {
        ...data,
        answer: data.answer || data.report  // 优先使用 answer，向后兼容 report
    } as T;
}

// ========== API 客户端 ==========

export const agentAPI = {
    // ========== Archivist API ==========

    async searchKnowledge(req: ArchivistRequest): Promise<ArchivistResponse> {
        const response = await request.post('/agents/archivist/search', req);
        return mapResponseToFrontend<ArchivistResponse>(response.data);
    },

    async graphTraversal(req: ArchivistRequest): Promise<ArchivistResponse> {
        const response = await request.post('/agents/archivist/graph-traversal', req);
        return mapResponseToFrontend<ArchivistResponse>(response.data);
    },

    async historicalSearch(req: ArchivistRequest): Promise<ArchivistResponse> {
        const response = await request.post('/agents/archivist/historical-search', req);
        return mapResponseToFrontend<ArchivistResponse>(response.data);
    },

    async checkArchivistHealth(): Promise<any> {
        const response = await request.get('/agents/archivist/health');
        return response.data;
    },

    // ========== Accident Deduction API ==========

    async generateAccidentDeduction(req: AccidentDeductionRequest): Promise<AccidentDeductionResponse> {
        const response = await request.post('/agents/accident-deduction/deduction',
            mapRequestToBackend(req)
        );
        const data = response.data;
        return {
            success: data.success,
            message: data.message,
            answer: data.answer || data.report,
            deduction: data.data,  // 后端的 data 映射到前端的 deduction
            thinking_stream: data.thinking_stream
        };
    },

    async generateEmergencyPlan(req: AccidentDeductionRequest): Promise<AccidentDeductionResponse> {
        const response = await request.post('/agents/accident-deduction/emergency-plan',
            mapRequestToBackend(req)
        );
        const data = response.data;
        return {
            success: data.success,
            message: data.message,
            answer: data.answer || data.report,
            deduction: data.data,
            thinking_stream: data.thinking_stream
        };
    },

    async generateDrillDesign(req: AccidentDeductionRequest): Promise<AccidentDeductionResponse> {
        const response = await request.post('/agents/accident-deduction/drill-design',
            mapRequestToBackend(req)
        );
        const data = response.data;
        return {
            success: data.success,
            message: data.message,
            answer: data.answer || data.report,
            deduction: data.data,
            thinking_stream: data.thinking_stream
        };
    },

    // ========== Power Guarantee API ==========

    async generatePowerGuaranteePlan(req: PowerGuaranteeRequest): Promise<PowerGuaranteeResponse> {
        const response = await request.post('/agents/power-guarantee/plan',
            mapRequestToBackend(req)
        );
        return mapResponseToFrontend<PowerGuaranteeResponse>(response.data);
    },

    async generateInspectionPlan(req: PowerGuaranteeRequest): Promise<PowerGuaranteeResponse> {
        const response = await request.post('/agents/power-guarantee/inspection',
            mapRequestToBackend(req)
        );
        return mapResponseToFrontend<PowerGuaranteeResponse>(response.data);
    },

    async prepareResources(req: PowerGuaranteeRequest): Promise<PowerGuaranteeResponse> {
        const response = await request.post('/agents/power-guarantee/resources',
            mapRequestToBackend(req)
        );
        return mapResponseToFrontend<PowerGuaranteeResponse>(response.data);
    },

    // ========== Operation Ticket API ==========

    async generateOperationTicket(req: OperationTicketRequest): Promise<OperationTicketResponse> {
        const response = await request.post('/agents/operation-ticket/generate',
            mapRequestToBackend(req)
        );
        return mapResponseToFrontend<OperationTicketResponse>(response.data);
    },

    async reviewOperationTicket(req: OperationTicketRequest): Promise<OperationTicketResponse> {
        const response = await request.post('/agents/operation-ticket/review',
            mapRequestToBackend(req)
        );
        return mapResponseToFrontend<OperationTicketResponse>(response.data);
    },

    // ========== Work Permit API ==========

    async generateWorkPermit(req: WorkPermitRequest): Promise<WorkPermitResponse> {
        const response = await request.post('/agents/work-permit/generate',
            mapRequestToBackend(req)
        );
        const data = response.data;
        // 确保 ticket 中同时有 permit_no 和 ticket_no（向后兼容）
        if (data.ticket && data.ticket.permit_no && !data.ticket.ticket_no) {
            data.ticket.ticket_no = data.ticket.permit_no;
        }
        return mapResponseToFrontend<WorkPermitResponse>(data);
    },

    async identifyHazards(req: WorkPermitRequest): Promise<WorkPermitResponse> {
        const response = await request.post('/agents/work-permit/hazards',
            mapRequestToBackend(req)
        );
        const data = response.data;
        if (data.ticket && data.ticket.permit_no && !data.ticket.ticket_no) {
            data.ticket.ticket_no = data.ticket.permit_no;
        }
        return mapResponseToFrontend<WorkPermitResponse>(data);
    },

    async reviewWorkPermit(req: WorkPermitRequest): Promise<WorkPermitResponse> {
        const response = await request.post('/agents/work-permit/review',
            mapRequestToBackend(req)
        );
        return mapResponseToFrontend<WorkPermitResponse>(response.data);
    },

    // ========== Supervisor API ==========

    async dispatchTask(req: SupervisorRequest): Promise<SupervisorResponse> {
        const response = await request.post('/agents/supervisor/dispatch',
            mapRequestToBackend(req)
        );
        return mapResponseToFrontend<SupervisorResponse>(response.data);
    },

    async getStationStatus(userId: string): Promise<any> {
        const response = await request.get(`/agents/supervisor/status?user_id=${userId}`);
        return response.data;
    },

    // ========== 通用智能体 API ==========

    /**
     * 通用智能体执行方法
     * 用于调用缺少专用 API 的智能体
     */
    async executeGenericAgent(agentType: string, req: BaseAgentRequest): Promise<BaseAgentResponse> {
        const response = await request.post(`/agents/${agentType}/execute`,
            mapRequestToBackend(req)
        );
        return mapResponseToFrontend<BaseAgentResponse>(response.data);
    },

    // ========== 健康检查 API ==========

    async checkHealth(agentType: string): Promise<any> {
        const response = await request.get(`/agents/${agentType}/health`);
        return response.data;
    }
};

export interface SupervisorRequest extends BaseAgentRequest {
    priority?: 'urgent' | 'high' | 'normal';
}

export interface SupervisorResponse extends BaseAgentResponse {
    data?: any;
    task_analysis?: {
        task_type?: string;
        assigned_agents?: string[];
        priority?: string;
    };
}

// ========== Agent Config (智能体配置) 类型定义 ==========

export interface CollectionBinding {
    collection_id: string;
    collection_name?: string;
    is_default?: boolean;
}

export interface AgentConfig {
    role: string;
    name: string;
    description: string;
    collections: CollectionBinding[];
    capabilities: string[];
    system_prompt?: string;
    priority: number;
}

export interface AgentConfigResponse {
    success: boolean;
    data?: AgentConfig;
    message?: string;
}

export interface AgentListResponse {
    success: boolean;
    agents: AgentConfig[];
}

export interface RecommendedCollection {
    category: string;
    keywords: string[];
}

// ========== 智能体配置 API ==========

export const agentConfigAPI = {
    /**
     * 获取所有智能体配置
     */
    async listAgentConfigs(): Promise<AgentListResponse> {
        const response = await request.get('/agents/agent-config/list');
        return response.data;
    },

    /**
     * 获取单个智能体配置
     */
    async getAgentConfig(role: string): Promise<AgentConfigResponse> {
        const response = await request.get(`/agents/agent-config/${role}`);
        return response.data;
    },

    /**
     * 更新智能体的知识库绑定
     */
    async updateAgentCollections(role: string, collectionIds: string[]): Promise<AgentConfigResponse> {
        const response = await request.put(`/agents/agent-config/${role}/collections`, {
            collection_ids: collectionIds
        });
        return response.data;
    },

    /**
     * 获取推荐的知识库
     */
    async getRecommendedCollections(role: string): Promise<{
        success: boolean;
        role: string;
        recommendations: RecommendedCollection[];
    }> {
        const response = await request.get(`/agents/agent-config/${role}/recommended-collections`);
        return response.data;
    },

    /**
     * 获取所有可用知识库列表（从数据库读取）
     */
    async getAvailableCollections(): Promise<{
        success: boolean;
        collections: Array<{
            id: string;
            title: string;
            description?: string;
            type?: string;
            doc_count?: number;
        }>;
        total: number;
    }> {
        const response = await request.get('/agents/agent-config/collections/available');
        return response.data;
    }
};

