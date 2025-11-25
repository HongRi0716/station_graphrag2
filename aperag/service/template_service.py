# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""文件模板渲染服务 - 支持智能体生成标准化文档"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

logger = logging.getLogger(__name__)


class TemplateRenderService:
    """文件模板渲染服务"""

    def __init__(self, template_dir: str = None):
        """
        初始化模板渲染服务

        Args:
            template_dir: 模板目录路径，默认为 aperag/templates
        """
        if template_dir is None:
            # 默认模板目录
            template_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "templates"
            )

        self.template_dir = Path(template_dir)

        # 确保模板目录存在
        if not self.template_dir.exists():
            logger.warning(f"Template directory {self.template_dir} does not exist, creating it")
            self.template_dir.mkdir(parents=True, exist_ok=True)

        # 配置Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,  # 不自动转义，保留Markdown格式
            trim_blocks=True,  # 移除块后的第一个换行符
            lstrip_blocks=True,  # 移除块前的空白
            keep_trailing_newline=True  # 保留文件末尾的换行符
        )

        # 添加自定义过滤器
        self.env.filters['default'] = lambda value, default='': value if value else default

        logger.info(f"Template service initialized with directory: {self.template_dir}")

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        渲染模板文件

        Args:
            template_name: 模板文件名（如 "operation_ticket.md"）
            context: 模板上下文变量字典

        Returns:
            渲染后的文本内容

        Raises:
            TemplateNotFound: 模板文件不存在
            Exception: 渲染过程中的其他错误
        """
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(**context)
            logger.debug(f"Successfully rendered template: {template_name}")
            return rendered
        except TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            raise
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise

    def render_from_string(
        self,
        template_string: str,
        context: Dict[str, Any]
    ) -> str:
        """
        从字符串渲染模板

        Args:
            template_string: 模板字符串
            context: 模板上下文变量字典

        Returns:
            渲染后的文本内容
        """
        try:
            template = Template(template_string)
            rendered = template.render(**context)
            logger.debug("Successfully rendered template from string")
            return rendered
        except Exception as e:
            logger.error(f"Failed to render template from string: {e}")
            raise

    def template_exists(self, template_name: str) -> bool:
        """
        检查模板文件是否存在

        Args:
            template_name: 模板文件名

        Returns:
            True if template exists, False otherwise
        """
        template_path = self.template_dir / template_name
        return template_path.exists()

    def list_templates(self) -> list[str]:
        """
        列出所有可用的模板文件

        Returns:
            模板文件名列表
        """
        if not self.template_dir.exists():
            return []

        templates = []
        for file_path in self.template_dir.rglob("*.md"):
            relative_path = file_path.relative_to(self.template_dir)
            templates.append(str(relative_path))

        return sorted(templates)

    def get_template_path(self, template_name: str) -> Path:
        """
        获取模板文件的完整路径

        Args:
            template_name: 模板文件名

        Returns:
            模板文件的Path对象
        """
        return self.template_dir / template_name


# 全局单例
template_service = TemplateRenderService()
