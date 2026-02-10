"""
原神Wiki 秘境数据解释器

负责将JSON数据转换为秘境数据模型。
"""

import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.domain_54 import DomainModel, DomainBrief
from giwiki_data_parser.services.dataloader import DataLoader


class DomainInterpreter:
    """秘境数据解释器"""

    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)

    def interpret(self, data: Dict[str, Any]) -> Optional[DomainModel]:
        """解析单个秘境数据 - 公共接口"""
        return self._interpret_single(data)

    def interpret_all(self) -> List[DomainModel]:
        """解析所有秘境数据"""
        domains = []
        raw_data_iterator = self.loader.get_domains()

        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                domain = self._interpret_single(data, file_path)
                if domain:
                    domains.append(domain)
            except Exception as e:
                self.logger.error(f"解析秘境数据时出错: {e}")

        self.logger.info(f"成功解析 {len(domains)} 个秘境")
        return domains

    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[DomainModel]:
        """解析单个秘境数据"""
        try:
            # 基础信息提取
            name = data.get("名称", "").strip()
            if not name:
                self.logger.warning("秘境名称为空，跳过")
                return None

            # 解析简述
            brief_list = []
            brief_data = data.get("简述", [])
            for brief_item in brief_data:
                if isinstance(brief_item, dict) and "名称" in brief_item and "描述" in brief_item:
                    brief = DomainBrief(
                        name=brief_item["名称"],
                        description=brief_item["描述"]
                    )
                    brief_list.append(brief)

            # 创建秘境对象
            domain = DomainModel(
                name=name,
                brief=brief_list
            )

            # 从文件路径设置ID
            if file_path:
                domain.set_id_from_filename(file_path)
            elif "_file_path" in data:
                domain.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    domain.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None

            return domain

        except Exception as e:
            self.logger.error(f"解析秘境数据时出错: {e}")
            return None