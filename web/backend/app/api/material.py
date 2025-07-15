from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from typing import List, Dict, Any

from ..services.game_data import GameDataAPI, get_game_data_service
from ..services.utility import convert_to_frontend_tree
from game_data_parser.formatters.material_formatter import format_material

router = APIRouter()

@router.get("/material/list", response_model=List[Dict[str, Any]])
def get_material_list(game_data: GameDataAPI = Depends(get_game_data_service)):
    """
    获取所有材料的简明列表 (id, name)。
    """
    all_materials = game_data.material.get_all()
    # Note: this is a simplified list, not self-describing, for now.
    return [{"id": m.id, "name": m.name} for m in all_materials]

@router.get("/material/tree", response_model=List[Dict[str, Any]])
def get_material_tree(game_data: GameDataAPI = Depends(get_game_data_service)):
    """
    获取材料的层级树状结构，用于前端 Tree 控件。
    """
    service_tree = game_data.material.get_tree()
    # In the material tree, the leaf node is 'material', and the top-level node is 'materialcategory'.
    return convert_to_frontend_tree(service_tree, leaf_type="material", id_prefix="materialcategory")

@router.get("/material/{material_id}/content", response_class=PlainTextResponse)
def get_material_content(material_id: int, game_data: GameDataAPI = Depends(get_game_data_service)):
    """
    获取单个材料的格式化Markdown内容。
    """
    # The formatter needs the book suit mapping, which the service has loaded.
    # We can access it via the service instance.
    material = game_data.material.get_by_id(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # 直接调用导入的 format_material 函数
    return format_material(material, book_suits=game_data.material._book_suits)