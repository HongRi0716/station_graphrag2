// React组件 - Supervisor总控台 (WebSocket版)
import { useState, useEffect, useRef, ChangeEvent } from 'react';
import { agentAPI, SupervisorResponse, StationStatusResponse, ThinkingStep } from '../../lib/api/agents';

export function SupervisorDashboard({ userId }: { userId: string }) {
    const [task, setTask] = useState('');
    const [result, setResult] = useState<SupervisorResponse | null>(null);
    const [status, setStatus] = useState<StationStatusResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [thinkingStream, setThinkingStream] = useState<ThinkingStep[]>([]);
    const [wsConnected, setWsConnected] = useState(false);

    const wsRef = useRef<WebSocket | null>(null);
    const streamEndRef = useRef<HTMLDivElement>(null);

    // 自动滚动思维链
    useEffect(() => {
        streamEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [thinkingStream]);

    // 定期刷新态势
    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const data = await agentAPI.getStationStatus(userId);
                setStatus(data);
            } catch (error) {
                console.error('Failed to fetch status:', error);
            }
        };

        fetchStatus();
        const interval = setInterval(fetchStatus, 30000); // 30秒刷新一次

        return () => clearInterval(interval);
    }, [userId]);

    // 初始化 WebSocket
    useEffect(() => {
        const ws = agentAPI.createSupervisorWebSocket(
            (data: any) => {
                // 处理消息
                switch (data.type) {
                    case 'start':
                        setLoading(true);
                        setThinkingStream([]);
                        setResult(null);
                        break;

                    case 'thinking':
                        setThinkingStream((prev: ThinkingStep[]) => [...prev, {
                            step_type: data.step_type,
                            description: data.description,
                            detail: data.detail,
                            timestamp: new Date().toISOString()
                        }]);
                        break;

                    case 'result':
                        setResult({
                            success: true,
                            message: '任务完成',
                            data: data.data,
                            task_analysis: data.task_analysis,
                            thinking_stream: [] // 结果中不需要重复思维链，因为我们已经实时展示了
                        });
                        setLoading(false);
                        break;

                    case 'complete':
                        setLoading(false);
                        break;

                    case 'error':
                        console.error('WebSocket error message:', data.message);
                        alert(`错误: ${data.message}`);
                        setLoading(false);
                        break;
                }
            },
            (error: Event) => {
                console.error('WebSocket connection error:', error);
                setWsConnected(false);
            }
        );

        ws.onopen = () => {
            console.log('WebSocket connected');
            setWsConnected(true);
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setWsConnected(false);
        };

        wsRef.current = ws;

        return () => {
            ws.close();
        };
    }, [userId]);

    const handleDispatch = () => {
        if (!task.trim()) return;

        if (!wsConnected || !wsRef.current) {
            alert('WebSocket 未连接，正在尝试重连...');
            // 可以在这里尝试重连逻辑，或者降级到 REST API
            return;
        }

        setLoading(true);
        setThinkingStream([]);
        setResult(null);

        // 发送任务
        wsRef.current.send(JSON.stringify({
            task,
            user_id: userId
        }));
    };

    return (
        <div className="supervisor-dashboard p-6 space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold">值班长总控台</h1>
                <div className={`px-3 py-1 rounded-full text-sm ${wsConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                    {wsConnected ? '实时连接正常' : '实时连接断开'}
                </div>
            </div>

            {/* 态势展示 */}
            <div className="status-panel bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">变电站态势</h2>
                {status ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="stat-card">
                            <div className="text-sm text-gray-500">整体状态</div>
                            <div className={`text-2xl font-bold ${status.status.overall_status === '正常' ? 'text-green-600' : 'text-red-600'
                                }`}>
                                {status.status.overall_status}
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="text-sm text-gray-500">设备数量</div>
                            <div className="text-2xl font-bold">{status.status.equipment_count}</div>
                        </div>
                        <div className="stat-card">
                            <div className="text-sm text-gray-500">告警数量</div>
                            <div className={`text-2xl font-bold ${status.status.alarm_count > 0 ? 'text-orange-600' : 'text-gray-600'
                                }`}>
                                {status.status.alarm_count}
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="text-sm text-gray-500">更新时间</div>
                            <div className="text-sm">
                                {new Date(status.status.timestamp).toLocaleTimeString()}
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="text-gray-500">正在获取态势数据...</div>
                )}
            </div>

            {/* 任务分发 */}
            <div className="task-dispatch bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">任务分发</h2>
                <div className="space-y-4">
                    <textarea
                        value={task}
                        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setTask(e.target.value)}
                        placeholder="输入任务描述，如：#1主变跳闸，请组织应急处置"
                        className="w-full h-32 p-3 border rounded-lg resize-none focus:ring-2 focus:ring-blue-500"
                        disabled={loading}
                    />
                    <button
                        onClick={handleDispatch}
                        disabled={loading || !task.trim() || !wsConnected}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                    >
                        {loading ? '正在处理...' : '分发任务'}
                    </button>
                </div>
            </div>

            {/* 实时思维链 */}
            {(thinkingStream.length > 0 || loading) && (
                <div className="thinking-panel bg-gray-50 rounded-lg shadow p-6 border border-blue-100">
                    <h2 className="text-lg font-semibold mb-4 flex items-center">
                        {loading && <span className="animate-spin mr-2">⚙️</span>}
                        智能体思考过程
                    </h2>
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                        {thinkingStream.map((step: ThinkingStep, index: number) => (
                            <div key={index} className="flex items-start space-x-3 text-sm animate-fadeIn">
                                <div className={`flex-shrink-0 w-20 px-2 py-1 rounded text-center text-xs font-medium ${step.step_type === 'thought' ? 'bg-gray-200 text-gray-700' :
                                    step.step_type === 'action' ? 'bg-blue-100 text-blue-800' :
                                        step.step_type === 'observation' ? 'bg-green-100 text-green-800' :
                                            step.step_type === 'correction' ? 'bg-red-100 text-red-800' :
                                                'bg-purple-100 text-purple-800' // plan
                                    }`}>
                                    {step.step_type.toUpperCase()}
                                </div>
                                <div className="flex-1 bg-white p-2 rounded border border-gray-100 shadow-sm">
                                    {step.description}
                                    {step.detail && (
                                        <pre className="mt-1 text-xs bg-gray-50 p-1 rounded overflow-x-auto">
                                            {JSON.stringify(step.detail, null, 2)}
                                        </pre>
                                    )}
                                </div>
                                <div className="text-xs text-gray-400 w-16 text-right">
                                    {step.timestamp ? new Date(step.timestamp).toLocaleTimeString().split(' ')[0] : ''}
                                </div>
                            </div>
                        ))}
                        <div ref={streamEndRef} />
                    </div>
                </div>
            )}

            {/* 处理结果 */}
            {result && (
                <div className="result bg-white rounded-lg shadow p-6 border-t-4 border-green-500 animate-slideUp">
                    <h2 className="text-xl font-semibold mb-4">处理结果</h2>

                    {/* 任务分析摘要 */}
                    {result.task_analysis && (
                        <div className="flex flex-wrap gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
                            <div className="flex items-center">
                                <span className="text-gray-500 mr-2">任务类型:</span>
                                <span className="font-medium px-2 py-0.5 bg-blue-50 text-blue-700 rounded">
                                    {result.task_analysis.task_type}
                                </span>
                            </div>
                            <div className="flex items-center">
                                <span className="text-gray-500 mr-2">优先级:</span>
                                <span className={`font-medium px-2 py-0.5 rounded ${result.task_analysis.priority === 'urgent' ? 'bg-red-50 text-red-700' :
                                    result.task_analysis.priority === 'high' ? 'bg-orange-50 text-orange-700' :
                                        'bg-green-50 text-green-700'
                                    }`}>
                                    {result.task_analysis.priority}
                                </span>
                            </div>
                            {result.task_analysis.involved_agents?.length > 0 && (
                                <div className="flex items-center">
                                    <span className="text-gray-500 mr-2">协作智能体:</span>
                                    <span className="font-medium text-gray-700">
                                        {result.task_analysis.involved_agents.join(', ')}
                                    </span>
                                </div>
                            )}
                        </div>
                    )}

                    {/* 最终答案 */}
                    <div className="answer prose max-w-none bg-white p-4 rounded border border-gray-100">
                        <div dangerouslySetInnerHTML={{ __html: result.data?.answer || result.message || '' }} />
                    </div>
                </div>
            )}
        </div>
    );
}
