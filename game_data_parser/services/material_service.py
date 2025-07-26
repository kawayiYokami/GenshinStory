import logging
from typing import List, Dict, Optional, Any
from collections import defaultdict

from ..models import Material
from ..interpreters.material_interpreter import MaterialInterpreter
from ..formatters.material_formatter import format_material
from ..dataloader import DataLoader

class MaterialService:
    """
    负责提供结构化的材料/道具数据服务。
    """
    def __init__(self, data_loader: DataLoader):
        self._loader = data_loader
        self._interpreter = MaterialInterpreter(data_loader)
        self.formatter = format_material
        
        self._materials: Dict[int, Material] = {}
        self._book_suits: Dict[int, str] = {}
        self._is_loaded = False

    def _load_data(self):
        """加载并处理所有材料数据。"""
        if self._is_loaded:
            return
        
        logging.info("首次加载所有材料数据...")
        # Load all book suit names first
        book_suit_configs = self._loader.get_json("ExcelBinOutput/BookSuitExcelConfigData.json")
        text_map = self._loader.get_json("TextMap/TextMapCHS.json")
        for suit in book_suit_configs:
            suit_name_hash = suit.get("suitNameTextMapHash")
            if suit_name_hash and str(suit_name_hash) in text_map:
                self._book_suits[suit["id"]] = text_map[str(suit_name_hash)]

        all_ids = self._interpreter.get_all_material_ids()
        for material_id in all_ids:
            material = self._interpreter.interpret(material_id)
            if material:
                self._materials[material_id] = material
        
        self._is_loaded = True
        logging.info(f"成功加载 {len(self._materials)} 个材料。")

    def get_all(self) -> List[Material]:
        """获取所有材料的列表。"""
        self._load_data()
        return list(self._materials.values())

    def get_by_id(self, material_id: int, index_context: Optional[Any] = None) -> Optional[Material]:
        """通过ID获取单个材料。"""
        # Note: _load_data needs to be adapted to pass the context,
        # but for a single get, we can call the interpreter directly.
        if self._is_loaded:
            return self._materials.get(material_id)
        else:
            # If not loaded, we interpret just this one with context
            return self._interpreter.interpret(material_id, index_context=index_context)

    def _determine_display_category(self, material: Material) -> str:
        """
        根据预设规则为材料确定最终的显示分类。
        优先级: 书籍 > 风之翼/名片 > 默认类型
        """
        # 规则 1: 书籍
        if material.is_book:
            return "书籍"

        # 规则 2: 风之翼 & 其他有故事的物品
        if material.story:
            return "名片与风之翼"
        
        # 规则 3: 默认使用 type_name
        return material.type_name or "未分类"

    def get_tree(self) -> List[Dict[str, Any]]:
        """
        获取统一的二级树状结构。
        使用 _determine_display_category 来决定一级分类。
        API结构为: [ {id, title, children: [ {id, title} ]} ]
        """
        self._load_data()
        
        grouped_by_category = defaultdict(list)
        for material in self._materials.values():
            # 使用新的方法决定分类
            category = self._determine_display_category(material)
            grouped_by_category[category].append(material)

        result_tree = []
        # 排序时可以加入更复杂的规则，例如按 type_name, material_type_raw
        sorted_categories = sorted(grouped_by_category.keys())

        for category_name in sorted_categories:
            materials_in_category = grouped_by_category[category_name]
            
            category_node = {
                "id": f"category::{category_name}",
                "title": category_name,
                "children": []
            }

            # 特殊处理: "书籍" 内部按系列排序
            if category_name == "书籍":
                sorted_materials = sorted(
                    materials_in_category,
                    key=lambda m: (m.set_id or float('inf'), m.id)
                )
            else:
                # 其他分类按ID排序。可以加入 type_name 或 material_type_raw 作为次要排序依据
                sorted_materials = sorted(
                    materials_in_category,
                    key=lambda m: (m.material_type_raw, m.id)
                )
            
            for material in sorted_materials:
                category_node["children"].append({
                    "id": str(material.id),
                    "title": material.name
                })
            
            result_tree.append(category_node)
            
        return result_tree

    def get_material_as_markdown(self, material_id: int) -> str:
        """
        获取单个材料的格式化Markdown文档。
        """
        material = self.get_by_id(material_id)
        if not material:
            return "未找到该材料。"

        # 修正：调用 formatter 并传递依赖
        return self.formatter(material, book_suits=self._book_suits)
