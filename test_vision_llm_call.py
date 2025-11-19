#!/usr/bin/env python3
"""测试 Vision LLM 调用

用法:
    # 使用环境变量配置
    python test_vision_llm_call.py <image_path>

    # 或指定所有参数
    python test_vision_llm_call.py <image_path> --prompt "描述这张图片"

环境变量:
    VISION_LLM_PROVIDER: Vision LLM 提供商 (默认: openai)
    VISION_LLM_MODEL: Vision LLM 模型名称 (默认: gpt-4o)
    VISION_LLM_BASE_URL: API 基础 URL (默认: https://api.openai.com/v1)
    VISION_LLM_API_KEY: API 密钥 (必需)
"""

import argparse
import asyncio
import base64
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 延迟导入 CompletionService，以便在导入失败时给出更好的错误提示
try:
    from aperag.llm.completion.completion_service import CompletionService
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("\n提示: 请确保:")
    print("  1. 已安装所有依赖 (pip install -r requirements.txt)")
    print("  2. 在项目根目录运行此脚本")
    print("  3. 如果使用虚拟环境，请先激活虚拟环境")
    sys.exit(1)


def encode_image_to_data_uri(image_path: str) -> str:
    """将图片文件编码为 data URI"""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    # 根据文件扩展名确定 MIME 类型
    ext = path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(ext, "image/jpeg")

    with path.open("rb") as f:
        image_data = f.read()
        base64_data = base64.b64encode(image_data).decode("utf-8")
        return f"data:{mime_type};base64,{base64_data}"


def test_sync_call(
    service: CompletionService,
    prompt: str,
    images: list[str],
    test_name: str = "同步调用测试",
):
    """测试同步调用"""
    print(f"\n{'='*80}")
    print(f"{test_name}")
    print(f"{'='*80}")
    print(f"Prompt: {prompt[:100]}..." if len(
        prompt) > 100 else f"Prompt: {prompt}")
    print(f"图片数量: {len(images)}")
    print(f"模型: {service.provider}/{service.model}")
    print(f"开始调用...")

    start_time = time.time()
    try:
        response = service.generate(history=[], prompt=prompt, images=images)
        elapsed_time = time.time() - start_time

        print(f"\n✅ 调用成功!")
        print(f"⏱️  耗时: {elapsed_time:.2f} 秒")
        print(f"📝 响应长度: {len(response)} 字符")
        print(f"\n响应内容:")
        print("-" * 80)
        print(response)
        print("-" * 80)

        return response, elapsed_time
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ 调用失败!")
        print(f"⏱️  耗时: {elapsed_time:.2f} 秒")
        print(f"错误信息: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, elapsed_time


async def test_async_call(
    service: CompletionService,
    prompt: str,
    images: list[str],
    test_name: str = "异步调用测试",
):
    """测试异步调用"""
    print(f"\n{'='*80}")
    print(f"{test_name}")
    print(f"{'='*80}")
    print(f"Prompt: {prompt[:100]}..." if len(
        prompt) > 100 else f"Prompt: {prompt}")
    print(f"图片数量: {len(images)}")
    print(f"模型: {service.provider}/{service.model}")
    print(f"开始调用...")

    start_time = time.time()
    try:
        response = await service.agenerate(history=[], prompt=prompt, images=images)
        elapsed_time = time.time() - start_time

        print(f"\n✅ 调用成功!")
        print(f"⏱️  耗时: {elapsed_time:.2f} 秒")
        print(f"📝 响应长度: {len(response)} 字符")
        print(f"\n响应内容:")
        print("-" * 80)
        print(response)
        print("-" * 80)

        return response, elapsed_time
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ 调用失败!")
        print(f"⏱️  耗时: {elapsed_time:.2f} 秒")
        print(f"错误信息: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, elapsed_time


def main():
    parser = argparse.ArgumentParser(
        description="测试 Vision LLM 调用",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "image_path",
        type=str,
        help="图片文件路径或 data URI",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="请详细描述这张图片的内容，包括所有可见的文字、对象和场景。",
        help="提示词 (默认: 请详细描述这张图片的内容)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Vision LLM 提供商 (覆盖环境变量)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Vision LLM 模型名称 (覆盖环境变量)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="API 基础 URL (覆盖环境变量)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API 密钥 (覆盖环境变量)",
    )
    parser.add_argument(
        "--sync-only",
        action="store_true",
        help="仅测试同步调用",
    )
    parser.add_argument(
        "--async-only",
        action="store_true",
        help="仅测试异步调用",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="温度参数 (默认: 0.1)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="超时时间（秒），默认使用服务默认值",
    )

    args = parser.parse_args()

    # 读取配置
    # 注意: provider 应该是 completion_dialect (如 "openai")，而不是 provider 名称 (如 "siliconflow")
    # 如果从环境变量读取的是 provider 名称，需要查询数据库获取 completion_dialect
    vision_llm_provider_name = args.provider or os.getenv(
        "VISION_LLM_PROVIDER", "openai")
    model = args.model or os.getenv("VISION_LLM_MODEL", "gpt-4o")
    base_url = args.base_url or os.getenv(
        "VISION_LLM_BASE_URL", "https://api.openai.com/v1")
    api_key = args.api_key or os.getenv("VISION_LLM_API_KEY")

    # 尝试从数据库获取 completion_dialect，如果失败则使用 provider 名称作为 dialect
    provider = vision_llm_provider_name
    try:
        from aperag.db.ops import db_ops
        llm_provider = db_ops.query_llm_provider_by_name(
            vision_llm_provider_name)
        if llm_provider and llm_provider.completion_dialect:
            provider = llm_provider.completion_dialect
            logger.info(
                f"Using completion_dialect '{provider}' for provider '{vision_llm_provider_name}'")
    except Exception as e:
        # 如果查询失败，使用 provider 名称作为 dialect（向后兼容）
        logger.warning(
            f"Failed to get completion_dialect for '{vision_llm_provider_name}': {e}. Using as-is.")
        provider = vision_llm_provider_name

    if not api_key:
        print("❌ 错误: 未设置 API 密钥")
        print("请通过以下方式之一设置:")
        print("  1. 环境变量: VISION_LLM_API_KEY")
        print("  2. 命令行参数: --api-key")
        sys.exit(1)

    # 处理图片
    if args.image_path.startswith("data:"):
        # 已经是 data URI
        images = [args.image_path]
        print(f"使用 data URI (长度: {len(args.image_path)} 字符)")
    else:
        # 本地文件
        try:
            data_uri = encode_image_to_data_uri(args.image_path)
            images = [data_uri]
            print(f"✅ 成功加载图片: {args.image_path}")
            print(f"   Data URI 长度: {len(data_uri)} 字符")
        except Exception as e:
            print(f"❌ 加载图片失败: {e}")
            sys.exit(1)

    # 创建服务
    print(f"\n{'='*80}")
    print("Vision LLM 配置")
    print(f"{'='*80}")
    print(f"提供商: {provider}")
    print(f"模型: {model}")
    print(f"Base URL: {base_url}")
    print(f"API Key: {api_key[:20]}..." if len(
        api_key) > 20 else f"API Key: {api_key}")
    print(f"温度: {args.temperature}")
    if args.timeout:
        print(f"超时: {args.timeout} 秒")

    try:
        # 检查 CompletionService 是否支持 timeout 参数
        import inspect
        sig = inspect.signature(CompletionService.__init__)
        supports_timeout = "timeout" in sig.parameters

        service_kwargs = {
            "provider": provider,
            "model": model,
            "base_url": base_url,
            "api_key": api_key,
            "temperature": args.temperature,
            "vision": True,
            "caching": False,  # 禁用缓存以便测试
        }
        # timeout 参数可能在某些版本中不支持，只在支持时添加
        if args.timeout is not None and supports_timeout:
            service_kwargs["timeout"] = args.timeout
            logger.info(f"使用超时设置: {args.timeout} 秒")
        elif args.timeout is not None and not supports_timeout:
            logger.warning(f"当前版本的 CompletionService 不支持 timeout 参数，将使用默认超时")

        service = CompletionService(**service_kwargs)
        print(f"✅ 服务创建成功")
    except Exception as e:
        print(f"❌ 创建服务失败: {e}")
        sys.exit(1)

    # 运行测试
    results = []

    if not args.async_only:
        # 测试同步调用
        response, elapsed = test_sync_call(service, args.prompt, images)
        results.append(("同步调用", response is not None, elapsed))

    if not args.sync_only:
        # 测试异步调用
        async def run_async_test():
            return await test_async_call(service, args.prompt, images)

        response, elapsed = asyncio.run(run_async_test())
        results.append(("异步调用", response is not None, elapsed))

    # 总结
    print(f"\n{'='*80}")
    print("测试总结")
    print(f"{'='*80}")
    for test_name, success, elapsed in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{test_name}: {status} (耗时: {elapsed:.2f} 秒)")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
