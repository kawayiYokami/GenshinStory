import logging
from typing import List, Dict, Any, Optional

from giwiki_data_parser.models.artifact_218 import ArtifactSet, ArtifactPiece
from giwiki_data_parser.services.dataloader import DataLoader

class ArtifactInterpreter:
    """圣遗物解释器"""
    
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)
    
    def interpret(self, data: Dict[str, Any]) -> Optional[ArtifactSet]:
        """解析单个圣遗物数据 - 公共接口"""
        return self._interpret_single(data)
    
    def interpret_all(self) -> List[ArtifactSet]:
        """解析所有圣遗物数据"""
        artifacts = []
        raw_data_iterator = self.loader.get_artifacts()
        
        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                artifact = self._interpret_single(data, file_path)
                if artifact:
                    artifacts.append(artifact)
            except Exception as e:
                self.logger.error(f"解析圣遗物数据时出错: {e}")
        
        self.logger.info(f"成功解析 {len(artifacts)} 个圣遗物套装")
        return artifacts
    
    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[ArtifactSet]:
        """解析单个圣遗物数据"""
        try:
            # 解析圣遗物列表
            artifact_list = data.get("圣遗物列表", {})
            
            # 解析各个部位
            flower = self._parse_artifact_piece(artifact_list.get("生之花"))
            feather = self._parse_artifact_piece(artifact_list.get("死之羽"))
            sands = self._parse_artifact_piece(artifact_list.get("时之沙"))
            goblet = self._parse_artifact_piece(artifact_list.get("空之杯"))
            circlet = self._parse_artifact_piece(artifact_list.get("理之冠"))
            
            # 创建圣遗物套装对象
            set_name = data.get("套装名称", "")
            artifact_set = ArtifactSet(
                name=set_name,
                title=set_name,  # 使用套装名称作为标题
                set_name=set_name,
                artifact_type=data.get("类型"),
                flower=flower,
                feather=feather,
                sands=sands,
                goblet=goblet,
                circlet=circlet
            )
            
            # 从文件路径设置ID
            if file_path:
                artifact_set.set_id_from_filename(file_path)
            elif "_file_path" in data:
                artifact_set.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    artifact_set.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None
            
            return artifact_set
            
        except Exception as e:
            self.logger.error(f"解析单个圣遗物数据时出错: {e}")
            return None
    
    def _parse_artifact_piece(self, piece_data: Optional[Dict[str, Any]]) -> Optional[ArtifactPiece]:
        """解析单个圣遗物部件"""
        if not piece_data or not isinstance(piece_data, dict):
            return None
        
        try:
            name = piece_data.get("名称", "")
            description = piece_data.get("描述", "")
            story = piece_data.get("故事", "")
            
            # 只有当有名称和故事时才创建对象
            if name and story:
                return ArtifactPiece(
                    name=name,
                    description=description,
                    story=story
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"解析圣遗物部件时出错: {e}")
            return None