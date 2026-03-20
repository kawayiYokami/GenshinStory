"""
原神Wiki 装扮数据解释器

负责将JSON数据转换为装扮数据模型，专注于提取装扮名称、简介和故事内容。
"""

import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.outfit_211 import OutfitModel
from giwiki_data_parser.services.dataloader import DataLoader


class OutfitInterpreter:
    """装扮数据解释器"""

    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)

    def interpret(self, data: Dict[str, Any]) -> Optional[OutfitModel]:
        """解析单个装扮数据 - 公共接口"""
        return self._interpret_single(data)

    def interpret_all(self) -> List[OutfitModel]:
        """解析所有装扮数据"""
        outfits = []
        raw_data_iterator = self.loader.get_outfits()

        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                outfit = self._interpret_single(data, file_path)
                if outfit:
                    outfits.append(outfit)
            except Exception as e:
                self.logger.error(f"解析装扮数据时出错: {e}")

        self.logger.info(f"成功解析 {len(outfits)} 个装扮")
        return outfits

    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[OutfitModel]:
        """解析单个装扮数据"""
        try:
            # 基础信息提取
            name = data.get("名称", "").strip()
            if not name:
                self.logger.warning("装扮名称为空，跳过")
                return None

            # 提取简介和故事
            introduction = data.get("简介", "").strip()
            story = data.get("故事", "").strip()
            sections = self._normalize_sections(data.get("分段内容", []))

            # 回填：如果主字段缺失，尝试从分段中推断
            if not introduction:
                introduction = self._extract_by_heading(
                    sections,
                    ["简介", "衣装简介", "风之翼简介", "介绍"],
                )
            if not story:
                story = self._extract_by_heading(
                    sections,
                    ["故事", "衣装故事", "风之翼故事", "背景"],
                )

            # 创建装扮对象
            outfit = OutfitModel(
                name=name,
                introduction=introduction,
                story=story,
                sections=sections,
            )

            # 从文件路径设置ID
            if file_path:
                outfit.set_id_from_filename(file_path)
            elif "_file_path" in data:
                outfit.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    outfit.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None

            return outfit

        except Exception as e:
            self.logger.error(f"解析装扮数据时出错: {e}")
            return None

    @staticmethod
    def _normalize_sections(raw_sections: Any) -> List[Dict[str, str]]:
        """将分段内容归一化为 [{heading,text}]。"""
        if not isinstance(raw_sections, list):
            return []

        sections: List[Dict[str, str]] = []
        for section in raw_sections:
            if not isinstance(section, dict):
                continue
            heading = str(section.get("heading", "") or "").strip()
            text = str(section.get("text", "") or "").strip()
            if not heading and not text:
                continue
            sections.append({
                "heading": heading,
                "text": text,
            })

        return sections

    @staticmethod
    def _extract_by_heading(sections: List[Dict[str, str]], heading_keywords: List[str]) -> str:
        """从分段中提取指定标题关键词对应的文本。"""
        chunks: List[str] = []
        for section in sections:
            heading = str(section.get("heading", "") or "")
            text = str(section.get("text", "") or "").strip()
            if not text:
                continue
            if any(keyword in heading for keyword in heading_keywords):
                chunks.append(text)
        return "\n\n".join(chunks).strip()
