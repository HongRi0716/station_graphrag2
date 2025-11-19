#!/usr/bin/env python3
"""
检查 Celery 日志，查找"主接线.png"处理失败的原因
"""

import sys
import os
import subprocess
import json
from datetime import datetime, timezone

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import select, desc
    from aperag.db.models import (
        Document,
        DocumentIndex,
        DocumentIndexType,
        DocumentIndexStatus,
    )
    from aperag.config import get_sync_session
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)


def find_document_by_name(document_name: str):
    """通过文件名查找文档"""
    for session in get_sync_session():
        # 尝试精确匹配
        stmt = select(Document).where(
            Document.name == document_name
        ).order_by(desc(Document.gmt_created))
        result = session.execute(stmt)
        documents = result.scalars().all()

        if not documents:
            # 尝试模糊匹配
            stmt = select(Document).where(
                Document.name.like(f"%{document_name}%")
            ).order_by(desc(Document.gmt_created))
            result = session.execute(stmt)
            documents = result.scalars().all()

        if len(documents) == 0:
            return None
        elif len(documents) == 1:
            return documents[0]
        else:
            print(f"\n⚠️  找到 {len(documents)} 个匹配的文档:")
            for i, doc in enumerate(documents, 1):
                print(
                    f"   {i}. {doc.name} (ID: {doc.id}, 状态: {doc.status}, 创建时间: {doc.gmt_created})")
            print("\n使用最新的文档")
            return documents[0]


def get_document_indexes(document_id: str):
    """获取文档的所有索引信息"""
    for session in get_sync_session():
        indexes = session.execute(
            select(DocumentIndex).where(
                DocumentIndex.document_id == document_id
            )
        ).scalars().all()
        return indexes
    return []


def check_celery_logs_docker(document_id: str, document_name: str):
    """检查 Docker 容器中的 Celery 日志"""
    print("=" * 80)
    print("📋 检查 Celery Worker 日志")
    print("=" * 80)

    container_name = "aperag-celeryworker"

    # 检查容器是否存在
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter",
                f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if container_name not in result.stdout:
            print(f"\n⚠️  容器 {container_name} 未运行")
            print("   请确保 Docker 容器正在运行")
            print_manual_commands(document_id, document_name)
            return
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("\n⚠️  无法访问 Docker，将提供手动检查命令")
        print_manual_commands(document_id, document_name)
        return

    print(f"\n🔍 正在检查容器 {container_name} 的日志...\n")

    # 1. 检查文档相关的所有日志
    print("1️⃣  文档相关日志（最近500行）:")
    print("-" * 80)
    try:
        result = subprocess.run(
            ["docker", "logs", container_name, "--tail", "500"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            relevant_lines = [
                line for line in lines
                if document_id.lower() in line.lower() or
                document_name.lower() in line.lower() or
                "主接线" in line
            ]
            if relevant_lines:
                for line in relevant_lines[-20:]:  # 只显示最后20行相关日志
                    print(f"   {line}")
            else:
                print("   ⚠️  未找到相关日志")
        else:
            print(f"   ❌ 获取日志失败: {result.stderr}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 2. 检查错误日志
    print("\n2️⃣  错误和异常日志（最近500行）:")
    print("-" * 80)
    try:
        result = subprocess.run(
            ["docker", "logs", container_name, "--tail", "500"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            error_lines = [
                line for line in lines
                if any(keyword in line.lower() for keyword in [
                    'error', 'exception', 'failed', 'fail', 'traceback',
                    'timeout', 'connection', 'refused'
                ]) and (
                    document_id.lower() in line.lower() or
                    document_name.lower() in line.lower() or
                    "主接线" in line or
                    "vision" in line.lower() or
                    "graph" in line.lower() or
                    "vector" in line.lower()
                )
            ]
            if error_lines:
                for line in error_lines[-30:]:  # 显示最后30行错误日志
                    print(f"   {line}")
            else:
                print("   ⚠️  未找到相关错误日志")
        else:
            print(f"   ❌ 获取日志失败: {result.stderr}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 3. 检查 Vision 相关日志
    print("\n3️⃣  Vision 索引相关日志（最近500行）:")
    print("-" * 80)
    try:
        result = subprocess.run(
            ["docker", "logs", container_name, "--tail", "500"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            vision_lines = [
                line for line in lines
                if 'vision' in line.lower() and (
                    document_id.lower() in line.lower() or
                    document_name.lower() in line.lower() or
                    "主接线" in line
                )
            ]
            if vision_lines:
                for line in vision_lines[-20:]:
                    print(f"   {line}")
            else:
                print("   ⚠️  未找到 Vision 相关日志")
        else:
            print(f"   ❌ 获取日志失败: {result.stderr}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 4. 检查 Graph 相关日志
    print("\n4️⃣  Graph 索引相关日志（最近500行）:")
    print("-" * 80)
    try:
        result = subprocess.run(
            ["docker", "logs", container_name, "--tail", "500"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            graph_lines = [
                line for line in lines
                if ('graph' in line.lower() or 'knowledge' in line.lower() or 'entity' in line.lower()) and (
                    document_id.lower() in line.lower() or
                    document_name.lower() in line.lower() or
                    "主接线" in line
                )
            ]
            if graph_lines:
                for line in graph_lines[-20:]:
                    print(f"   {line}")
            else:
                print("   ⚠️  未找到 Graph 相关日志")
        else:
            print(f"   ❌ 获取日志失败: {result.stderr}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 5. 检查任务执行日志
    print("\n5️⃣  任务执行日志（最近200行，包含任务ID）:")
    print("-" * 80)
    try:
        result = subprocess.run(
            ["docker", "logs", container_name, "--tail", "200"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            task_lines = [
                line for line in lines
                if any(keyword in line.lower() for keyword in [
                    'task', 'parse_document', 'create_index', 'vision', 'graph'
                ]) and (
                    document_id.lower() in line.lower() or
                    document_name.lower() in line.lower() or
                    "主接线" in line
                )
            ]
            if task_lines:
                for line in task_lines[-20:]:
                    print(f"   {line}")
            else:
                print("   ⚠️  未找到任务执行日志")
        else:
            print(f"   ❌ 获取日志失败: {result.stderr}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")


def print_manual_commands(document_id: str, document_name: str):
    """打印手动检查命令"""
    print("\n" + "=" * 80)
    print("📋 手动检查 Celery 日志的命令")
    print("=" * 80)

    print("\n1. 查看文档相关的所有日志:")
    print(
        f"   docker logs aperag-celeryworker --tail 500 | grep -i '{document_id}'")
    print(
        f"   docker logs aperag-celeryworker --tail 500 | grep -i '{document_name}'")
    print(f"   docker logs aperag-celeryworker --tail 500 | grep '主接线'")

    print("\n2. 查看错误和异常日志:")
    print(
        f"   docker logs aperag-celeryworker --tail 500 | grep -iE 'error|exception|failed|fail' | grep -i '{document_id}'")
    print(f"   docker logs aperag-celeryworker --tail 500 | grep -iE 'error|exception|failed|fail' | grep '主接线'")

    print("\n3. 查看 Vision 相关日志:")
    print(
        f"   docker logs aperag-celeryworker --tail 500 | grep -i vision | grep -i '{document_id}'")
    print(f"   docker logs aperag-celeryworker --tail 500 | grep -i vision | grep '主接线'")
    print(f"   docker logs aperag-celeryworker --tail 500 | grep 'Vision LLM'")

    print("\n4. 查看 Graph 相关日志:")
    print(
        f"   docker logs aperag-celeryworker --tail 500 | grep -iE 'graph|knowledge|entity' | grep -i '{document_id}'")
    print(f"   docker logs aperag-celeryworker --tail 500 | grep -iE 'graph|knowledge|entity' | grep '主接线'")

    print("\n5. 查看任务执行日志:")
    print(
        f"   docker logs aperag-celeryworker --tail 200 | grep -iE 'task|parse_document|create_index' | grep -i '{document_id}'")

    print("\n6. 实时监控日志:")
    print(f"   docker logs -f aperag-celeryworker | grep -i '{document_id}'")

    print("\n7. 查看所有最近的错误:")
    print(f"   docker logs aperag-celeryworker --tail 200 | grep -iE 'error|exception|failed|timeout'")


def analyze_index_status(document_id: str):
    """分析索引状态并提供诊断建议"""
    print("\n" + "=" * 80)
    print("📊 索引状态分析")
    print("=" * 80)

    indexes = get_document_indexes(document_id)
    if not indexes:
        print("\n⚠️  未找到任何索引记录")
        return

    index_map = {idx.index_type: idx for idx in indexes}

    for index_type in [DocumentIndexType.VECTOR, DocumentIndexType.VISION, DocumentIndexType.GRAPH]:
        idx = index_map.get(index_type)
        if not idx:
            continue

        index_type_name = idx.index_type.value if hasattr(
            idx.index_type, 'value') else str(idx.index_type)
        status = idx.status.value if hasattr(
            idx.status, 'value') else str(idx.status)

        print(f"\n{index_type_name} 索引:")
        print(f"  - 状态: {status}")
        print(f"  - 更新时间: {idx.gmt_updated}")

        if idx.status == DocumentIndexStatus.FAILED:
            print(f"  - ❌ 失败原因: {idx.error_message}")
        elif idx.status == DocumentIndexStatus.CREATING:
            now = datetime.now(timezone.utc)
            elapsed = now - idx.gmt_updated.replace(
                tzinfo=timezone.utc) if idx.gmt_updated.tzinfo is None else now - idx.gmt_updated
            elapsed_minutes = elapsed.total_seconds() / 60
            print(f"  - ⚠️  CREATING 状态已持续: {elapsed_minutes:.1f} 分钟")

            if elapsed_minutes > 10:
                print(f"  - ❌ 警告: 可能已卡住！")
                if index_type == DocumentIndexType.VISION:
                    print(f"  - 💡 建议: 检查 Vision LLM 配置和网络连接")
                elif index_type == DocumentIndexType.GRAPH:
                    print(f"  - 💡 建议: 检查是否在等待 Vision 索引完成")


def main():
    """主函数"""
    document_name = "主接线.png"

    print("=" * 80)
    print("🔍 Celery 日志检查工具 - 主接线.png")
    print("=" * 80)

    # 1. 查找文档
    print(f"\n1️⃣  查找文档: {document_name}")
    print("-" * 80)
    document = find_document_by_name(document_name)

    if not document:
        print(f"\n❌ 未找到文档: {document_name}")
        print("\n💡 提示: 如果在本地运行失败，请在 Docker 容器中运行:")
        print(
            f"   docker exec aperag-celeryworker python check_celery_logs_for_document.py")
        sys.exit(1)

    print(f"\n✅ 找到文档:")
    print(f"   ID: {document.id}")
    print(f"   名称: {document.name}")
    print(f"   状态: {document.status}")
    print(f"   创建时间: {document.gmt_created}")

    # 2. 分析索引状态
    analyze_index_status(document.id)

    # 3. 检查 Celery 日志
    check_celery_logs_docker(document.id, document.name)

    # 4. 提供诊断建议
    print("\n" + "=" * 80)
    print("💡 诊断建议")
    print("=" * 80)

    indexes = get_document_indexes(document.id)
    index_map = {idx.index_type: idx for idx in indexes}

    vision_idx = index_map.get(DocumentIndexType.VISION)
    graph_idx = index_map.get(DocumentIndexType.GRAPH)

    if vision_idx and vision_idx.status == DocumentIndexStatus.FAILED:
        print("\n🎯 Vision 索引失败:")
        print(f"   错误信息: {vision_idx.error_message}")
        print("\n   可能的原因:")
        print("   1. Vision LLM API 调用失败")
        print("   2. API 密钥无效或过期")
        print("   3. 网络连接问题")
        print("   4. Vision LLM 服务不可用")
        print("\n   建议操作:")
        print("   1. 检查 Vision LLM 环境变量配置")
        print("   2. 验证 API 密钥是否有效")
        print("   3. 检查网络连接")
        print("   4. 查看上面的错误日志获取详细信息")

    if vision_idx and vision_idx.status == DocumentIndexStatus.CREATING:
        now = datetime.now(timezone.utc)
        elapsed = now - vision_idx.gmt_updated.replace(
            tzinfo=timezone.utc) if vision_idx.gmt_updated.tzinfo is None else now - vision_idx.gmt_updated
        elapsed_minutes = elapsed.total_seconds() / 60

        if elapsed_minutes > 10:
            print("\n🎯 Vision 索引可能已卡住:")
            print(f"   CREATING 状态已持续 {elapsed_minutes:.1f} 分钟")
            print("\n   建议操作:")
            print("   1. 检查上面的 Celery 日志，查找 Vision LLM 调用相关错误")
            print("   2. 检查 Vision LLM 服务是否正常响应")
            print("   3. 如果确认卡住，可以重置索引状态:")
            print(
                f"      python reset_stuck_indexes.py --document-id {document.id} --index-type VISION")

    if graph_idx and graph_idx.status == DocumentIndexStatus.FAILED:
        print("\n🎯 Graph 索引失败:")
        print(f"   错误信息: {graph_idx.error_message}")
        print("\n   可能的原因:")
        print("   1. 知识图谱构建 LLM 调用失败")
        print("   2. Vision 索引未完成，导致无法获取 Vision-to-Text 内容")
        print("   3. 内容为空，无法提取实体和关系")
        print("\n   建议操作:")
        print("   1. 确保 Vision 索引已成功完成")
        print("   2. 检查知识图谱构建 LLM 配置")
        print("   3. 查看上面的错误日志获取详细信息")

    if graph_idx and graph_idx.status == DocumentIndexStatus.CREATING:
        if vision_idx and vision_idx.status != DocumentIndexStatus.ACTIVE:
            print("\n🎯 Graph 索引正在等待 Vision 索引完成:")
            print("   Graph 索引需要 Vision 索引完成后才能继续")
            print("   建议: 先解决 Vision 索引的问题")

    print("\n" + "=" * 80)
    print("✅ 检查完成")
    print("=" * 80)
    print("\n💡 提示: 如果上面的日志信息不够详细，可以:")
    print("   1. 使用上面提供的手动命令查看更多日志")
    print("   2. 实时监控日志: docker logs -f aperag-celeryworker")
    print("   3. 检查 Flower (Celery 监控工具): http://localhost:5555")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
