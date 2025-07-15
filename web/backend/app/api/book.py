# web/backend/app/api/books.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from typing import List, Dict, Any

from ..services.game_data import GameDataAPI, get_game_data_service
from ..services.utility import package_list_as_self_describing, convert_to_frontend_tree

router = APIRouter()

@router.get("/book/list", response_model=List[Dict[str, Any]])
def get_book_list(game_data: GameDataAPI = Depends(get_game_data_service)):
    """获取所有书籍的简明列表，并包装为自描述结构。"""
    raw_list = game_data.book.list_books()
    return package_list_as_self_describing(raw_list, "book")

@router.get("/series/{series_id}/content", response_class=PlainTextResponse)
def get_book_series_content(series_id: int, game_data: GameDataAPI = Depends(get_game_data_service)):
    """获取整个书籍系列的 Markdown 内容。"""
    content = game_data.book.get_book_series_as_markdown(series_id)
    if not content:
        raise HTTPException(status_code=404, detail="Book series content not found")
    return content

# 旧的 /book/{book_id}/content 路由已被上面的新路由取代，故移除。

@router.get("/book/tree", response_model=List[Dict[str, Any]])
def get_book_tree(game_data: GameDataAPI = Depends(get_game_data_service)):
    """
    获取书籍系列的树状结构。
    为了适配前端控件，返回一个单一的根节点，其子节点为所有书籍系列。
    """
    series_list = game_data.book.get_tree()
    
    children_nodes = []
    for series in series_list:
        series_id = series.get("id")
        series_title = series.get("title")
        
        if series_id and series_title:
            children_nodes.append({
                "key": f"bookseries-{series_id}",
                "label": series_title,
                "data": {"type": "series", "id": series_id},
                "isLeaf": True
            })
            
    # 创建一个单一的根节点，包含所有书籍系列作为其子节点
    root_node = [{
        "key": "root-bookseries",
        "label": "所有书籍系列",
        "data": {"type": "root"},
        "isLeaf": False,
        "children": children_nodes
    }]
            
    return root_node