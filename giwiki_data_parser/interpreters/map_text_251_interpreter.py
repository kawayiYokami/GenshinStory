"""地图文本解释器"""
import logging
from typing import Dict, Any, List, Optional

from giwiki_data_parser.models.map_text_251 import MapTextModel
from giwiki_data_parser.services.dataloader import DataLoader


class MapTextInterpreter:
    """地图文本解释器"""
    
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.logger = logging.getLogger(__name__)
    
    def interpret(self, data: Dict[str, Any]) -> Optional[MapTextModel]:
        """解析单个地图文本数据 - 公共接口"""
        return self._interpret_single(data)
    
    def interpret_all(self) -> List[MapTextModel]:
        """解析所有地图文本数据"""
        map_texts = []
        raw_data_iterator = self.loader.get_map_text()
        
        for data in raw_data_iterator:
            try:
                # 从数据中获取文件路径信息
                file_path = data.get("_file_path", "")
                map_text = self._interpret_single(data, file_path)
                if map_text:
                    map_texts.append(map_text)
            except Exception as e:
                self.logger.error(f"解析地图文本数据时出错: {e}")
        
        self.logger.info(f"成功解析 {len(map_texts)} 个地图文本")
        return map_texts
    
    def _interpret_single(self, data: Dict[str, Any], file_path: str = "") -> Optional[MapTextModel]:
        """解析单个地图文本数据"""
        try:
            # 提取基本信息
            title = data.get("文本标题", "")
            text_type = data.get("类型", "")
            region = data.get("地区", "")
            location_images = data.get("位置图片", [])
            content = data.get("文本内容", [])
            
            # 创建地图文本对象
            map_text = MapTextModel(
                name=title,
                title=title,
                text_type=text_type,
                region=region,
                location_images=location_images,
                content=content
            )
            
            # 从文件路径设置ID
            if file_path:
                map_text.set_id_from_filename(file_path)
            elif "_file_path" in data:
                map_text.set_id_from_filename(data["_file_path"])
            elif "_file_id" in data:
                file_id = str(data["_file_id"])
                if file_id.isdigit():
                    map_text.id = file_id
                else:
                    self.logger.warning(f"非数字文件ID，跳过: {file_id}")
                    return None
            
            return map_text
            
        except Exception as e:
            self.logger.error(f"解析单个地图文本数据时出错: {e}")
            return None
    
    def _has_story_content(self, content: List[str]) -> bool:
        """检查是否包含故事内容"""
        if not content:
            return False
        
        # 地图文本通常包含世界观和故事内容
        story_indicators = [
            "传说", "故事", "历史", "记录", "日记", "回忆",
            "对话", "留言", "广告", "通告", "记事", "祈祷",
            "警告", "传闻", "流言", "见证", "经历"
        ]
        
        content_text = " ".join(content)
        return any(indicator in content_text for indicator in story_indicators)
    
    def _extract_content_tags(self, title: str, content: List[str], region: str) -> List[str]:
        """提取内容标签"""
        tags = ["地图文本"]
        
        # 根据标题添加标签
        if "订货板" in title or "广告板" in title:
            tags.append("商业文化")
        if "记事" in title or "日记" in title:
            tags.append("历史记录")
        if "通告" in title or "公告" in title:
            tags.append("官方通告")
        
        # 根据地区添加标签
        if region:
            tags.append(f"地区-{region}")
        
        # 根据内容添加标签
        content_text = " ".join(content)
        if "花神" in content_text or "利露帕尔" in content_text:
            tags.append("神话传说")
        if "工厂" in content_text or "机械" in content_text:
            tags.append("工业文明")
        if "镇灵" in content_text:
            tags.append("镇灵文化")
        if "执律庭" in content_text or "枫丹" in content_text:
            tags.append("枫丹文化")
        if "蒙德" in content_text:
            tags.append("蒙德文化")
        if "璃月" in content_text:
            tags.append("璃月文化")
        if "须弥" in content_text:
            tags.append("须弥文化")
        
        return tags