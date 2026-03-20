#!/usr/bin/env python3
"""模型元数据缓存服务：从远程开源数据库获取模型上下文上限等信息"""

import json
import logging
import time
import asyncio
from pathlib import Path
from typing import Dict, Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

MODEL_METADATA_URL = "https://models.dev/api.json"
CACHE_UPDATE_INTERVAL = 24 * 60 * 60  # 24小时


class ModelMetadata(BaseModel):
    """模型元数据"""
    name: str
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    provider: str = "unknown"
    enable_image: bool = False
    enable_audio: bool = False
    enable_tools: bool = False
    last_updated: float = 0


class ModelMetadataCache:
    """模型元数据缓存"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "model_metadata.json"
        self._cache: Dict[str, ModelMetadata] = {}
        self._last_update = 0.0
        self._refresh_lock = asyncio.Lock()
        self._load_cache()

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _load_cache(self) -> None:
        """从文件加载缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._last_update = data.get("_last_update", 0)
                    for name, meta in data.items():
                        if name == "_last_update":
                            continue
                        self._cache[name] = ModelMetadata(**meta)
                logger.info(f"已加载模型元数据缓存: {len(self._cache)} 个模型")
            except Exception as e:
                logger.warning(f"加载模型元数据缓存失败: {e}")
                self._cache = {}

    def _save_cache(self) -> None:
        """保存缓存到文件"""
        try:
            data = {"_last_update": self._last_update}
            for name, meta in self._cache.items():
                data[name] = meta.model_dump()
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存模型元数据缓存失败: {e}")

    def _is_cache_expired(self) -> bool:
        """检查缓存是否过期"""
        return time.time() - self._last_update > CACHE_UPDATE_INTERVAL

    @staticmethod
    def _normalize_model_name(name: str) -> str:
        """规范化模型名：仅保留最后一个 / 之后的片段，并转小写。"""
        return (name or "").strip().lower().rsplit("/", 1)[-1]

    @staticmethod
    def _extract_provider_hint(name: str) -> Optional[str]:
        raw = (name or "").strip().lower()
        if "/" not in raw:
            return None
        head = raw.split("/", 1)[0].strip()
        return head or None

    async def fetch_remote_metadata(self) -> Dict[str, ModelMetadata]:
        """从远程获取模型元数据"""
        models = {}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info("正在从 models.dev 获取模型元数据...")
                response = await client.get(MODEL_METADATA_URL)
                response.raise_for_status()
                root = response.json()

                for provider_name, provider_data in root.items():
                    if not isinstance(provider_data, dict):
                        continue
                    models_obj = provider_data.get("models", {})
                    if not isinstance(models_obj, dict):
                        continue

                    for model_id, model_value in models_obj.items():
                        if not isinstance(model_value, dict):
                            continue

                        # 提取上下文窗口
                        limit = model_value.get("limit", {})
                        context_window = limit.get("context")
                        max_output = limit.get("output")

                        # 提取能力
                        modalities = model_value.get("modalities", {})
                        input_modalities = modalities.get("input", [])
                        enable_image = "image" in str(input_modalities).lower()
                        enable_audio = "audio" in str(input_modalities).lower()
                        enable_tools = bool(model_value.get("tool_call", False))

                        try:
                            models[model_id.lower()] = ModelMetadata(
                                name=model_id,
                                context_window=self._safe_int(context_window),
                                max_output_tokens=self._safe_int(max_output),
                                provider=provider_name,
                                enable_image=enable_image,
                                enable_audio=enable_audio,
                                enable_tools=enable_tools,
                                last_updated=time.time()
                            )
                        except Exception as e:
                            logger.warning(f"跳过异常模型元数据: model_id={model_id}, error={e}")
                            continue

                logger.info(f"从 models.dev 获取到 {len(models)} 个模型")
        except Exception as e:
            logger.error(f"从 models.dev 获取模型元数据失败: {e}")

        return models

    async def get_model_metadata(self, model_name: str) -> Optional[ModelMetadata]:
        """获取模型元数据"""
        # 检查是否需要刷新缓存
        if self._is_cache_expired():
            async with self._refresh_lock:
                if self._is_cache_expired():
                    logger.info("模型元数据缓存已过期，正在刷新...")
                    new_models = await self.fetch_remote_metadata()
                    if new_models:
                        self._cache = new_models
                        self._last_update = time.time()
                        self._save_cache()
                    else:
                        # 刷新失败，使用旧缓存
                        logger.warning("刷新失败，使用旧缓存")

        # 仅按最后一个 / 之后的片段做精确匹配，避免前缀错配
        requested_tail = self._normalize_model_name(model_name)
        if not requested_tail:
            return None

        matches = [
            metadata
            for model_id, metadata in self._cache.items()
            if self._normalize_model_name(model_id) == requested_tail
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            logger.warning(f"模型名匹配存在歧义: requested={model_name}, matched={len(matches)}")
            provider_hint = self._extract_provider_hint(model_name)
            if provider_hint:
                provider_matched = [
                    item
                    for item in matches
                    if item.provider.lower() == provider_hint
                    or self._extract_provider_hint(item.name) == provider_hint
                ]
                if len(provider_matched) == 1:
                    return provider_matched[0]
                if len(provider_matched) > 1:
                    return sorted(provider_matched, key=lambda item: item.name)[0]
            # 无 provider 提示时，仍返回一个稳定结果，避免功能不可用
            return sorted(matches, key=lambda item: (item.provider, item.name))[0]

        return None


# 全局缓存实例
_cache_dir = Path(__file__).parent.parent / "data" / "model_metadata_cache"
model_metadata_cache = ModelMetadataCache(_cache_dir)
