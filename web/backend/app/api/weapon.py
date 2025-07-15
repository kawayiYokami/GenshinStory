# web/backend/app/api/weapons.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from typing import List, Dict, Any

from ..services.game_data import GameDataAPI, get_game_data_service
from ..services.utility import package_list_as_self_describing, convert_to_frontend_tree

router = APIRouter()

@router.get("/weapon/list", response_model=List[Dict[str, Any]])
def get_weapon_list(game_data: GameDataAPI = Depends(get_game_data_service)):
    """获取按类型分组的武器列表，用于 ListPane。"""
    # 1. 调用服务层获取已经按类型分组的树状数据
    service_tree = game_data.weapon.get_tree()

    # 2. 将数据结构转换为前端 ListPane 期望的 { groupName, children } 格式
    #    并为每个子项（武器）添加自描述的 data 字段
    frontend_list = []
    for group in service_tree:
        # 深拷贝子项以避免修改原始缓存数据
        children_with_data = [
            {**item, "data": {"type": "weapon", "id": item["id"]}}
            for item in group.get("children", [])
        ]
        frontend_list.append({
            "groupName": group.get("title", "未知分类"),
            "children": children_with_data
        })
    
    return frontend_list

@router.get("/weapon/{weapon_id}/content", response_class=PlainTextResponse)
def get_weapon_content(weapon_id: int, game_data: GameDataAPI = Depends(get_game_data_service)):
    """获取单个武器的 Markdown 内容。"""
    content = game_data.weapon.get_weapon_as_markdown(weapon_id)
    if not content:
        raise HTTPException(status_code=404, detail="Weapon content not found")
    return content

@router.get("/weapon/tree", response_model=List[Dict[str, Any]])
def get_weapon_tree(game_data: GameDataAPI = Depends(get_game_data_service)):
    """获取武器的层级树状结构，用于前端 Tree 控件。"""
    service_tree = game_data.weapon.get_tree()
    # 在武器树中，叶子节点是 'weapon'，顶级节点是 'weapontype'
    return convert_to_frontend_tree(service_tree, leaf_type="weapon", id_prefix="weapontype")