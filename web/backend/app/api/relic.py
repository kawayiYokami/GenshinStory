# web/backend/app/api/relics.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from typing import List, Dict, Any

from ..services.game_data import GameDataAPI, get_game_data_service
from ..services.utility import package_list_as_self_describing, convert_to_frontend_tree

router = APIRouter()

# --- Relic Sets ---

@router.get("/relicset/list", response_model=List[Dict[str, Any]])
def get_relic_set_list(game_data: GameDataAPI = Depends(get_game_data_service)):
    """获取所有圣遗物套装的简明列表，并包装为自描述结构。"""
    raw_list = game_data.relic.list_relic_sets()
    return package_list_as_self_describing(raw_list, "relicset")

@router.get("/relicset/tree", response_model=List[Dict[str, Any]])
def get_relic_set_tree(game_data: GameDataAPI = Depends(get_game_data_service)):
    """
    获取圣遗物套装的树状结构，返回一个单一的根节点，
    其子节点为所有圣遗物套装。
    """
    series_list = game_data.relic.get_tree()
    
    children_nodes = []
    for series in series_list:
        series_id = series.get("id")
        series_title = series.get("title")
        
        if series_id and series_title:
            children_nodes.append({
                "key": f"relicset-{series_id}",
                "label": series_title,
                "data": {"type": "relicset", "id": series_id},
                "isLeaf": True
            })
            
    # 创建一个单一的根节点
    root_node = [{
        "key": "root-relicset",
        "label": "所有圣遗物套装",
        "data": {"type": "root"},
        "isLeaf": False,
        "children": sorted(children_nodes, key=lambda x: x['label']) # Sort by name
    }]
            
    return root_node

@router.get("/relicset/{relic_set_id}/content", response_class=PlainTextResponse)
def get_relic_set_content(relic_set_id: int, game_data: GameDataAPI = Depends(get_game_data_service)):
    """获取单个圣遗_物套装的 Markdown 内容。"""
    content = game_data.relic.get_relic_set_as_markdown(relic_set_id)
    if not content:
        raise HTTPException(status_code=404, detail="Relic set content not found")
    return content

# --- Relic Pieces ---

@router.get("/relicpiece/list", response_model=List[Dict[str, Any]])
def get_relic_piece_list(game_data: GameDataAPI = Depends(get_game_data_service)):
    """获取所有圣遗物散件的简明列表，并包装为自描述结构。"""
    raw_list = game_data.relic.list_relics()
    return package_list_as_self_describing(raw_list, "relicpiece")

@router.get("/relicpiece/{relic_piece_id}/content", response_class=PlainTextResponse)
def get_relic_piece_content(relic_piece_id: int, game_data: GameDataAPI = Depends(get_game_data_service)):
    """获取单个圣遗物散件的 Markdown 内容。"""
    content = game_data.relic.get_relic_as_markdown(relic_piece_id)
    if not content:
        raise HTTPException(status_code=404, detail="Relic piece content not found")
    return content