import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { BaseAgentResponse } from '@/lib/api/agents';

/**
 * 通用智能体请求 Hook
 * 
 * 提供统一的加载状态管理、错误处理和结果管理
 * 
 * @param apiMethod - API 调用方法
 * @param options - 可选配置
 */
export function useAgent<TRequest, TResponse extends BaseAgentResponse>(
    apiMethod: (req: TRequest) => Promise<TResponse>,
    options: {
        successMessage?: string;
        errorMessage?: string;
        onSuccess?: (response: TResponse) => void;
        onError?: (error: Error) => void;
    } = {}
) {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<TResponse | null>(null);
    const [error, setError] = useState<Error | null>(null);

    const {
        successMessage = '任务执行成功',
        errorMessage = '任务执行失败，请稍后重试',
        onSuccess,
        onError
    } = options;

    const execute = useCallback(async (request: TRequest): Promise<TResponse | null> => {
        setLoading(true);
        setResult(null);
        setError(null);

        try {
            const response = await apiMethod(request);
            setResult(response);

            if (response.success) {
                toast.success(successMessage);
            }

            onSuccess?.(response);
            return response;
        } catch (e) {
            const err = e as Error;
            setError(err);
            console.error('Agent task failed:', err);
            toast.error(errorMessage);
            onError?.(err);
            return null;
        } finally {
            setLoading(false);
        }
    }, [apiMethod, successMessage, errorMessage, onSuccess, onError]);

    const reset = useCallback(() => {
        setResult(null);
        setError(null);
    }, []);

    return {
        loading,
        result,
        error,
        execute,
        reset,
        setResult
    };
}

/**
 * 带有查询状态管理的智能体 Hook
 * 
 * 扩展了 useAgent，添加了查询字符串的状态管理
 */
export function useAgentWithQuery<TRequest extends { query: string; user_id: string }, TResponse extends BaseAgentResponse>(
    apiMethod: (req: TRequest) => Promise<TResponse>,
    userId: string | undefined,
    options: {
        successMessage?: string;
        errorMessage?: string;
        onSuccess?: (response: TResponse) => void;
        onError?: (error: Error) => void;
    } = {}
) {
    const [query, setQuery] = useState('');
    const { loading, result, error, execute, reset, setResult } = useAgent(apiMethod, options);

    const handleStartTask = useCallback(async (overrideQuery?: string) => {
        const taskQuery = overrideQuery ?? query;
        if (!taskQuery.trim()) {
            toast.error('请输入任务指令');
            return null;
        }

        return execute({
            query: taskQuery,
            user_id: userId || 'user-1',
        } as TRequest);
    }, [query, userId, execute]);

    const handleQuickTask = useCallback(async (taskQuery: string, extraParams?: Partial<TRequest>) => {
        setQuery(taskQuery);
        return execute({
            query: taskQuery,
            user_id: userId || 'user-1',
            ...extraParams
        } as TRequest);
    }, [userId, execute]);

    return {
        query,
        setQuery,
        loading,
        result,
        error,
        execute,
        reset,
        setResult,
        handleStartTask,
        handleQuickTask
    };
}
