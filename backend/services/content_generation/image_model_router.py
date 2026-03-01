"""图像生成模型路由器 - 根据 provider 能力注册表统一路由"""
import logging
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.model_config import ModelConfig
from services.content_generation.provider_capabilities import IMAGE_PROVIDER_CAPABILITIES

logger = logging.getLogger(__name__)

# provider 默认 API 基地址
_DEFAULT_API_BASES: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "zhipuai": "https://open.bigmodel.cn/api/paas/v4",
    "siliconflow": "https://api.siliconflow.cn/v1",
}


class ImageModelRouter:
    """图像生成模型路由器"""

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def _get_model_config(self, model_config_id: int) -> ModelConfig | None:
        stmt = select(ModelConfig).where(
            ModelConfig.id == model_config_id,
            ModelConfig.tenant_id == self.tenant_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _build_request_body(
        config: ModelConfig, prompt: str, params: dict, caps: dict
    ) -> dict:
        """根据能力注册表动态构建请求体"""
        body: dict = {"model": config.model_name, "prompt": prompt}
        mapping = caps.get("param_mapping", {})

        # 映射 size
        if "size" in mapping:
            size_value = params.get("size", caps.get("default_size", "1024x1024"))
            body[mapping["size"]] = size_value

        # 映射 n（批量数量）
        if caps.get("supports_batch") and "n" in mapping:
            body[mapping["n"]] = params.get("n", 1)

        # 合并 extra_body
        body.update(caps.get("extra_body", {}))
        return body

    @staticmethod
    def _parse_response(data: dict, parser_type: str) -> list[str]:
        """根据 response_parser 类型统一解析响应"""
        if parser_type == "data_url":
            return [item["url"] for item in data.get("data", [])]
        elif parser_type == "images_url":
            images = data.get("images", data.get("data", []))
            return [item.get("url", "") for item in images]
        return []

    async def generate_image(
        self,
        prompt: str,
        model_config_id: int,
        params: dict | None = None,
    ) -> list[str]:
        """生成图像，返回图像URL列表"""
        config = await self._get_model_config(model_config_id)
        if not config:
            raise ValueError("模型配置不存在")

        provider = config.provider
        caps = IMAGE_PROVIDER_CAPABILITIES.get(provider)
        if not caps:
            raise ValueError(f"不支持的图像生成提供商: {provider}")

        params = params or {}
        api_base = config.api_base or _DEFAULT_API_BASES.get(provider, "")
        body = self._build_request_body(config, prompt, params, caps)

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{api_base}/images/generations",
                headers={"Authorization": f"Bearer {config.api_key}"},
                json=body,
            )
            resp.raise_for_status()
            return self._parse_response(resp.json(), caps["response_parser"])
