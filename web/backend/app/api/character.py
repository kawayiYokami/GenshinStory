# web/backend/app/api/character.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from typing import List, Dict, Any

from ..services.game_data import GameDataAPI, get_game_data_service
from ..services.utility import package_list_as_self_describing, convert_to_frontend_tree

router = APIRouter()

@router.get("/character/list", response_model=List[Dict[str, Any]])
def get_character_list(game_data: GameDataAPI = Depends(get_game_data_service)):
    """获取所有角色的简明列表，并包装为自描述结构。"""
    # Note: list_characters returns a list of Character objects, not dicts.
    # We need to convert them to a JSON-serializable format.
    raw_list = game_data.character.list_characters()
    dict_list = [char.model_dump(mode='json') for char in raw_list]
    return package_list_as_self_describing(dict_list, "character")

@router.get("/character/{character_id}/content", response_class=PlainTextResponse)
def get_character_content(character_id: int, game_data: GameDataAPI = Depends(get_game_data_service)):
    """获取单个角色的 Markdown 内容。"""
    content = game_data.character.get_character_as_markdown(character_id)
    if not content:
        raise HTTPException(status_code=404, detail="Character content not found")
    return content

@router.get("/character/tree", response_model=List[Dict[str, Any]])
def get_character_tree(game_data: GameDataAPI = Depends(get_game_data_service)):
    """获取角色的层级树状结构，用于前端 Tree 控件。"""
    service_tree = game_data.character.get_tree()
    # 在角色树中，叶子节点是 'character'，顶级节点是 'nation'
    return convert_to_frontend_tree(service_tree, leaf_type="character", id_prefix="nation")