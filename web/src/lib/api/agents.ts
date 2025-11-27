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

// ========== 事故预想智能体类型定义 ==========

export interface AccidentDeductionRequest {
    query: string;
    user_id: string;
    chat_id?: string;
    equipment?: string;
    scenario?: string;
}

export interface AccidentDeductionResponse {
    success: boolean;
    message: string;
    answer?: string;  // 从后端的 report 字段映射
    data?: any;       // 从后端的 data 字段映射
    report?: string;  // 后端原始字段
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
    thinking_stream?: ThinkingStep[];
}

// ========== 保电方案智能体类型定义 ==========

export interface PowerGuaranteeRequest {
    query: string;
    user_id: string;
    chat_id?: string;
    event_name?: string;
    event_level?: string;
}

export interface PowerGuaranteeResponse {
    success: boolean;
    message: string;
    answer?: string;
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
    thinking_stream?: ThinkingStep[];
}

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

    // ========== Accident Deduction API ==========

    async generateAccidentDeduction(req: AccidentDeductionRequest): Promise<AccidentDeductionResponse> {
        const response = await request.post('/api/v1/agents/accident-deduction/deduction', {
            task: req.query,
            user_id: req.user_id,
            chat_id: req.chat_id,
            equipment: req.equipment,
            scenario: req.scenario
        });
        // 映射后端响应到前端期望的格式
        const backendData = response.data;
        return {
            success: backendData.success,
            message: backendData.message,
            answer: backendData.report,  // 后端的report映射到answer
            deduction: backendData.data,  // 后端的data映射到deduction
            thinking_stream: backendData.thinking_stream
        };
    },

    async generateEmergencyPlan(req: AccidentDeductionRequest): Promise<AccidentDeductionResponse> {
        const response = await request.post('/api/v1/agents/accident-deduction/emergency-plan', {
            task: req.query,
            user_id: req.user_id,
            chat_id: req.chat_id
        });
        const backendData = response.data;
        return {
            success: backendData.success,
            message: backendData.message,
            answer: backendData.report,
            deduction: backendData.data,
            thinking_stream: backendData.thinking_stream
        };
    },

    async generateDrillDesign(req: AccidentDeductionRequest): Promise<AccidentDeductionResponse> {
        const response = await request.post('/api/v1/agents/accident-deduction/drill-design', {
            task: req.query,
            user_id: req.user_id,
            chat_id: req.chat_id
        });
        const backendData = response.data;
        return {
            success: backendData.success,
            message: backendData.message,
            answer: backendData.report,
            deduction: backendData.data,
            thinking_stream: backendData.thinking_stream
        };
    },

    // ========== Power Guarantee API ==========

    async generatePowerGuaranteePlan(req: PowerGuaranteeRequest): Promise<PowerGuaranteeResponse> {
        const response = await request.post('/agents/power-guarantee/plan', req);
        return response.data;
    },

    async generateInspectionPlan(req: PowerGuaranteeRequest): Promise<PowerGuaranteeResponse> {
        const response = await request.post('/agents/power-guarantee/inspection', req);
        return response.data;
    },

    async prepareResources(req: PowerGuaranteeRequest): Promise<PowerGuaranteeResponse> {
        const response = await request.post('/agents/power-guarantee/resources', req);
        return response.data;
    },

    // ========== Operation Ticket API ==========

    async generateOperationTicket(req: TicketRequest): Promise<TicketResponse> {
        const response = await request.post('/agents/operation-ticket/generate', req);
        return response.data;
    },

    async reviewOperationTicket(req: TicketRequest): Promise<TicketResponse> {
        const response = await request.post('/agents/operation-ticket/review', req);
        return response.data;
    },

    // ========== Work Permit API ==========

    async generateWorkPermit(req: TicketRequest): Promise<TicketResponse> {
        const response = await request.post('/agents/work-permit/generate', req);
        return response.data;
    },

    async identifyHazards(req: TicketRequest): Promise<TicketResponse> {
        const response = await request.post('/agents/work-permit/hazards', req);
        return response.data;
    },
};

// ========== 两票智能体类型定义 ==========

export interface TicketRequest {
    query: string;
    user_id: string;
    chat_id?: string;
    operation_type?: string;
    equipment?: string;
    work_content?: string;
}

export interface TicketResponse {
    success: boolean;
    message: string;
    answer?: string;
    ticket?: {
        ticket_no?: string;
        ticket_type?: string;
        operation_steps?: Array<{
            step_no: number;
            operation: string;
            executor: string;
            supervisor: string;
        }>;
        safety_measures?: Array<{
            measure: string;
            responsible: string;
        }>;
        hazard_points?: Array<{
            hazard: string;
            level: string;
            control_measure: string;
        }>;
        approvals?: Array<{
            role: string;
            name: string;
            signature: string;
        }>;
    };
    thinking_stream?: ThinkingStep[];
}
