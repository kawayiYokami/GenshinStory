from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from typing import List, Dict, Any

# 唯一的、正确的导入方式
from ..services.game_data import GameDataAPI, get_game_data_service

router = APIRouter()

@router.get("/chapter/list")
def get_chapters_list(
    game_data: GameDataAPI = Depends(get_game_data_service)
) -> List[Dict[str, Any]]:
    """
    获取一个简化的章节列表，只包含ID和标题，用于前端目录展示。
    """
    all_chapters = game_data.quest.list_quest_chapters()
    
    # 手动组装返回结果，不暴露内部模型
    result = [
        {"id": chapter.id, "title": chapter.title, "number": getattr(chapter, 'number', '')}
        for chapter in all_chapters
    ]
    return result

@router.get("/chapter/{chapter_id}/content", response_class=PlainTextResponse)
def get_chapter_detail(
    chapter_id: int,
    game_data: GameDataAPI = Depends(get_game_data_service)
) -> str:
    """
    根据章节ID，获取该章节格式化后的Markdown文本。
    """
    markdown_text = game_data.quest.get_chapter_as_markdown(chapter_id)
    if markdown_text is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    return markdown_text
