from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from ..services.game_data import GameDataAPI, get_game_data_service

router = APIRouter()

@router.get("/readable/{readable_id}/content", response_class=PlainTextResponse)
def get_readable_content(readable_id: int, game_data: GameDataAPI = Depends(get_game_data_service)):
    """
    Retrieves the full details of a single readable item as Markdown.
    """
    markdown_content = game_data.readable.get_readable_as_markdown(readable_id)
    if markdown_content is None:
        raise HTTPException(status_code=404, detail="Readable not found")
    return markdown_content