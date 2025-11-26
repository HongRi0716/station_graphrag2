// React组件 - Archivist知识检索界面
import { useState, KeyboardEvent, ChangeEvent } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { agentAPI, ArchivistResponse, ThinkingStep } from '../../lib/api/agents';

type SearchMode = 'knowledge' | 'graph' | 'history';

export function ArchivistSearch({ userId }: { userId: string }) {
    const [query, setQuery] = useState('');
    const [searchMode, setSearchMode] = useState<SearchMode>('knowledge');
    const [searchType, setSearchType] = useState<'vector' | 'graph' | 'hybrid'>('hybrid');
    const [result, setResult] = useState<ArchivistResponse | null>(null);
    const [loading, setLoading] = useState(false);

    const handleSearch = async () => {
        if (!query.trim()) return;

        setLoading(true);
        try {
            let response: ArchivistResponse;

            switch (searchMode) {
                case 'knowledge':
                    response = await agentAPI.searchKnowledge({
                        query,
                        user_id: userId,
                        search_type: searchType,
                        top_k: 10,
                    });
                    break;

                case 'graph':
                    response = await agentAPI.graphTraversal({
                        query,
                        user_id: userId,
                    });
                    break;

                case 'history':
                    response = await agentAPI.historicalSearch({
                        query,
                        user_id: userId,
                        top_k: 20,
                    });
                    break;
            }

            setResult(response);
        } catch (error) {
            console.error('Search failed:', error);
            alert('检索失败');
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e: KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSearch();
        }
    };

    return (
        <div className="archivist-search p-6 space-y-6">
            <h1 className="text-3xl font-bold">图谱专家 - 知识检索</h1>

            {/* 搜索控制 */}
            <div className="search-controls bg-white rounded-lg shadow p-6 space-y-4">
                <h2 className="text-xl font-semibold">检索设置</h2>

                {/* 检索模式选择 */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        检索模式
                    </label>
                    <div className="flex space-x-4">
                        <button
                            onClick={() => setSearchMode('knowledge')}
                            className={`px-4 py-2 rounded-lg ${searchMode === 'knowledge'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                }`}
                        >
                            知识检索
                        </button>
                        <button
                            onClick={() => setSearchMode('graph')}
                            className={`px-4 py-2 rounded-lg ${searchMode === 'graph'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                }`}
                        >
                            图谱遍历
                        </button>
                        <button
                            onClick={() => setSearchMode('history')}
                            className={`px-4 py-2 rounded-lg ${searchMode === 'history'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                }`}
                        >
                            历史查询
                        </button>
                    </div>
                </div>

                {/* 知识检索类型选择 */}
                {searchMode === 'knowledge' && (
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            检索类型
                        </label>
                        <select
                            value={searchType}
                            onChange={(e: ChangeEvent<HTMLSelectElement>) => setSearchType(e.target.value as any)}
                            className="w-full p-2 border rounded-lg"
                        >
                            <option value="hybrid">混合检索</option>
                            <option value="vector">向量检索</option>
                            <option value="graph">图谱检索</option>
                        </select>
                    </div>
                )}

                {/* 查询输入 */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        查询内容
                    </label>
                    <div className="flex space-x-2">
                        <input
                            type="text"
                            value={query}
                            onChange={(e: ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder={
                                searchMode === 'knowledge'
                                    ? '输入查询内容，如：查询主变操作规程'
                                    : searchMode === 'graph'
                                        ? '输入关系查询，如：#1主变与哪些设备有连接关系'
                                        : '输入历史查询，如：查询2024年的主变检修记录'
                            }
                            className="flex-1 p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                            onClick={handleSearch}
                            disabled={loading || !query.trim()}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                        >
                            {loading ? '检索中...' : '搜索'}
                        </button>
                    </div>
                </div>

                {/* 快捷查询示例 */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        快捷查询
                    </label>
                    <div className="flex flex-wrap gap-2">
                        {searchMode === 'knowledge' && (
                            <>
                                <button
                                    onClick={() => setQuery('查询主变操作规程')}
                                    className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                                >
                                    主变操作规程
                                </button>
                                <button
                                    onClick={() => setQuery('查询变电安全规程')}
                                    className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                                >
                                    安全规程
                                </button>
                                <button
                                    onClick={() => setQuery('查询设备台账')}
                                    className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                                >
                                    设备台账
                                </button>
                            </>
                        )}
                        {searchMode === 'graph' && (
                            <>
                                <button
                                    onClick={() => setQuery('#1主变与哪些设备有连接关系')}
                                    className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                                >
                                    主变连接关系
                                </button>
                                <button
                                    onClick={() => setQuery('110kV母线供电路径')}
                                    className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                                >
                                    供电路径
                                </button>
                            </>
                        )}
                        {searchMode === 'history' && (
                            <>
                                <button
                                    onClick={() => setQuery('查询2024年的主变检修记录')}
                                    className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                                >
                                    2024年检修记录
                                </button>
                                <button
                                    onClick={() => setQuery('查询历史事故案例')}
                                    className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
                                >
                                    历史事故案例
                                </button>
                            </>
                        )}
                    </div>
                </div>
            </div>

            {/* 检索结果 */}
            {result && (
                <div className="search-results bg-white rounded-lg shadow p-6 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-semibold">检索结果</h2>
                        <span className="text-sm text-gray-500">
                            找到 {result.count} 条结果
                        </span>
                    </div>

                    {/* 思维链 */}
                    {result.thinking_stream && result.thinking_stream.length > 0 && (
                        <div className="thinking-stream bg-gray-50 rounded p-4">
                            <h3 className="font-semibold mb-2 text-sm text-gray-700">推理过程</h3>
                            <div className="space-y-1">
                                {result.thinking_stream.map((step: ThinkingStep, index: number) => (
                                    <div key={index} className="flex items-start space-x-2 text-sm">
                                        <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">
                                            {step.step_type}
                                        </span>
                                        <span className="flex-1 text-gray-600">{step.description}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* 答案展示 */}
                    {result.answer && (
                        <div className="answer prose max-w-none">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                className="markdown-content [&>*]:mb-3"
                            >
                                {result.answer}
                            </ReactMarkdown>
                        </div>
                    )}

                    {/* 图谱数据可视化 (新功能) */}
                    {(result as any).graph_data && (result as any).graph_data.nodes && (result as any).graph_data.nodes.length > 0 && (
                        <div className="graph-visualization mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                            <h3 className="font-semibold mb-2 text-gray-700">图谱结构数据</h3>
                            <div className="text-xs font-mono bg-white p-2 rounded border overflow-auto max-h-40">
                                <pre>{JSON.stringify((result as any).graph_data, null, 2)}</pre>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                                * 此处未来将渲染交互式知识图谱 (Nodes: {(result as any).graph_data.nodes.length}, Edges: {(result as any).graph_data.edges.length})
                            </p>
                        </div>
                    )}

                    {/* 文档列表 */}
                    {result.documents && result.documents.length > 0 && (
                        <div className="documents space-y-3">
                            <h3 className="font-semibold">相关文档</h3>
                            {result.documents.map((doc: any, index: number) => (
                                <div
                                    key={index}
                                    className="document-card border rounded-lg p-4 hover:shadow-md transition-shadow"
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <h4 className="font-medium text-lg mb-1">
                                                {doc.title || '未知文档'}
                                            </h4>
                                            {doc.source && (
                                                <span className="text-xs text-gray-500 mb-2 inline-block">
                                                    来源: {doc.source}
                                                </span>
                                            )}
                                            <p className="text-gray-700 text-sm">
                                                {doc.content?.substring(0, 200)}
                                                {doc.content?.length > 200 && '...'}
                                            </p>
                                        </div>
                                        {(doc.timestamp || doc.date) && (
                                            <span className="text-xs text-gray-400 ml-4">
                                                {doc.timestamp || doc.date}
                                            </span>
                                        )}
                                    </div>
                                    {doc.type && (
                                        <div className="mt-2">
                                            <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                                                {doc.type}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* 使用提示 */}
            {!result && (
                <div className="usage-tips bg-blue-50 rounded-lg p-6">
                    <h3 className="font-semibold mb-3">使用提示</h3>
                    <div className="space-y-2 text-sm text-gray-700">
                        <p>
                            <strong>知识检索:</strong> 从知识库中检索相关文档，支持向量、图谱、混合三种检索模式
                        </p>
                        <p>
                            <strong>图谱遍历:</strong> 查询设备之间的关系和连接路径
                        </p>
                        <p>
                            <strong>历史查询:</strong> 检索历史记录和案例，按时间排序
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}
