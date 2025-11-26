"""
联邦图谱搜索功能测试脚本

用途: 验证全局图谱搜索 API 是否正常工作

使用方法:
    python test_federated_graph_search.py

前提条件:
    1. API 服务器正在运行
    2. 用户已登录并有有效的 token
    3. 至少有一个启用知识图谱的 Collection
"""

import asyncio
import json
import sys
from typing import Dict, Any

try:
    import httpx
except ImportError:
    print("❌ 需要安装 httpx: pip install httpx")
    sys.exit(1)


class FederatedGraphSearchTester:
    """联邦图谱搜索测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def test_global_search(self, query: str, top_k: int = 20) -> Dict[str, Any]:
        """
        测试全局图谱搜索
        
        Args:
            query: 搜索查询词
            top_k: 返回的最大节点数
            
        Returns:
            API 响应数据
        """
        url = f"{self.base_url}/api/v1/graphs/search/global"
        
        payload = {
            "query": query,
            "top_k": top_k
        }
        
        print(f"\n🔍 测试全局图谱搜索")
        print(f"   查询词: {query}")
        print(f"   Top K: {top_k}")
        print(f"   URL: {url}")
        
        try:
            response = await self.client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"\n📊 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self._print_results(data)
                return data
            else:
                print(f"❌ 请求失败: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return {}
    
    def _print_results(self, data: Dict[str, Any]):
        """打印搜索结果"""
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        print(f"\n✅ 搜索成功!")
        print(f"   节点数: {len(nodes)}")
        print(f"   边数: {len(edges)}")
        
        if nodes:
            print(f"\n📌 节点示例 (前 5 个):")
            for i, node in enumerate(nodes[:5], 1):
                node_id = node.get("id", "N/A")
                node_type = node.get("type", "N/A")
                label = node.get("label", node.get("name", "N/A"))
                sources = node.get("source_collections", [])
                
                print(f"   {i}. [{node_type}] {label}")
                print(f"      ID: {node_id}")
                if sources:
                    print(f"      来源: {', '.join(sources)}")
                else:
                    workspace = node.get("metadata", {}).get("workspace", "N/A")
                    print(f"      工作区: {workspace}")
        
        if edges:
            print(f"\n🔗 边示例 (前 5 个):")
            for i, edge in enumerate(edges[:5], 1):
                source = edge.get("source", "N/A")
                target = edge.get("target", "N/A")
                label = edge.get("label", "N/A")
                workspace = edge.get("workspace", "N/A")
                
                print(f"   {i}. {source} --[{label}]--> {target}")
                print(f"      工作区: {workspace}")
    
    async def test_hierarchy(self, query: str = "", top_k: int = 100) -> Dict[str, Any]:
        """
        测试层级图谱视图
        
        Args:
            query: 可选的过滤查询
            top_k: 返回的最大节点数
            
        Returns:
            API 响应数据
        """
        url = f"{self.base_url}/api/v1/graphs/hierarchy/global"
        
        payload = {
            "query": query,
            "top_k": top_k
        }
        
        print(f"\n🏗️ 测试层级图谱视图")
        print(f"   过滤词: {query or '(无)'}")
        print(f"   URL: {url}")
        
        try:
            response = await self.client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"\n📊 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                nodes = data.get("nodes", [])
                edges = data.get("edges", [])
                
                print(f"\n✅ 查询成功!")
                print(f"   节点数: {len(nodes)}")
                print(f"   边数: {len(edges)}")
                
                # 统计节点类型
                node_types = {}
                for node in nodes:
                    node_type = node.get("type", "unknown")
                    node_types[node_type] = node_types.get(node_type, 0) + 1
                
                print(f"\n📊 节点类型分布:")
                for node_type, count in node_types.items():
                    print(f"   {node_type}: {count}")
                
                return data
            else:
                print(f"❌ 请求失败: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return {}
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 联邦图谱搜索功能测试")
    print("=" * 60)
    
    # 创建测试器
    tester = FederatedGraphSearchTester()
    
    try:
        # 测试 1: 全局图谱搜索
        print("\n" + "=" * 60)
        print("测试 1: 全局实体搜索")
        print("=" * 60)
        
        # 这里使用一个通用的测试查询词
        # 在实际使用中，应该替换为您的知识库中存在的实体
        test_queries = ["变压器", "设备", "运维", "巡检"]
        
        for query in test_queries:
            result = await tester.test_global_search(query, top_k=10)
            if result.get("nodes"):
                print(f"\n✅ 查询 '{query}' 成功找到结果")
                break
        else:
            print(f"\n⚠️ 所有测试查询都未找到结果")
            print(f"   这可能是因为:")
            print(f"   1. 没有启用知识图谱的 Collections")
            print(f"   2. 知识库中没有这些实体")
            print(f"   3. API 服务器未运行或需要认证")
        
        # 测试 2: 层级视图
        print("\n" + "=" * 60)
        print("测试 2: 层级图谱视图")
        print("=" * 60)
        
        await tester.test_hierarchy(query="", top_k=50)
        
        print("\n" + "=" * 60)
        print("✅ 测试完成!")
        print("=" * 60)
        
        print("\n💡 提示:")
        print("   1. 如果看到认证错误，请确保已登录")
        print("   2. 如果返回空结果，请检查是否有启用 KG 的 Collections")
        print("   3. 查看完整文档: FEDERATED_GRAPH_SEARCH_SUMMARY.md")
        
    finally:
        await tester.close()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
