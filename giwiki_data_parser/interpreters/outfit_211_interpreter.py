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

            # 创建装扮对象
            outfit = OutfitModel(
                name=name,
                introduction=introduction,
                story=story
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