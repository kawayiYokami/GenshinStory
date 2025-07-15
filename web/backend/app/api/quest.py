from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from typing import List, Dict, Any, Optional

from ..services.game_data import GameDataAPI, get_game_data_service
from ..services.utility import package_list_as_self_describing, convert_to_frontend_tree

router = APIRouter()


@router.get("/quest/list", response_model=List[Dict[str, Any]])
def get_quest_list(game_data: GameDataAPI = Depends(get_game_data_service)):
    """
    获取一个带分组的、智能的任务列表，用于前端的顶级列表视图。
    - 返回值直接匹配前端 ListGroup[] 结构。
    - 对于大多数任务分类，子项是章节。
    - 对于零散任务(ORPHAN_MISC)分类，子项是任务。
    """
    # 1. 从完美的服务层获取原始、完整的任务树
    structured_tree = game_data.quest.get_quest_tree()

    # 2. 在API层进行智能转换，构建前端期望的 ListGroup[] 结构
    frontend_groups = []
    for category_data in structured_tree:
        group_name = category_data.get("title")
        category_key = category_data.get("category")
        
        children = []
        # 特殊处理零散任务 - 直接提取任务作为子项
        if category_key == "ORPHAN_MISC":
            for chapter in category_data.get("chapters", []):
                for quest in chapter.quests:
                    children.append({
                        "id": quest.quest_id,
                        "name": quest.quest_title,
                        "data": {"type": "quest", "id": quest.quest_id}
                    })
        
        # 其他任务类型 - 提取章节作为子项
        else:
            for chapter in category_data.get("chapters", []):
                if chapter.quests: # 确保章节下有任务
                    children.append({
                        "id": chapter.id,
                        "name": chapter.title,
                        "data": {"type": "chapter", "id": chapter.id}
                    })
        
        # 只有当分组下有内容时，才添加该分组
        if children:
            frontend_groups.append({
                "groupName": group_name,
                "children": children
            })

    return frontend_groups


@router.get("/quest/tree")
def get_quest_tree(
    game_data: GameDataAPI = Depends(get_game_data_service)
) -> List[Dict[str, Any]]:
    """
    获取任务树，并将其从 game_data_parser 的业务结构
    转换为前端 Element Plus Tree 需要的 key/label/children 格式。
    
    树结构逻辑：
    - 零散任务(ORPHAN_MISC): 任务直接在分类下，无中间章节层级
    - 其他任务类型: 只显示到章节层级，不显示具体任务
    """
    try:
        # 1. 从 service 获取标准树结构
        service_tree = game_data.quest.get_quest_tree()

        # 2. 调用通用转换器处理
        # 在任务树中，叶子节点是 'quest'，但中间层是 'chapter'
        # 我们需要一种方式来处理这种混合/多层级的情况
        # 目前的 convert_to_frontend_tree 还不支持，所以我们暂时保留这里的定制逻辑
        # TODO: 未来可以增强 convert_to_frontend_tree 以支持多级类型
        
        frontend_tree = []
        for category_node in service_tree:
            category_id = category_node.get("id")
            
            # 创建顶层节点 (e.g., "魔神任务")
            top_level_node = {
                "key": f"questcategory-{category_id}",
                "label": category_node.get("title"),
                "data": {"type": "questcategory", "id": category_id},
                "children": []
            }

            # 遍历章节 (第二层)
            for chapter_node_data in category_node.get("children", []):
                chapter_id = chapter_node_data.get("id")
                
                # 创建章节节点
                child_node = {
                    "key": f"chapter-{chapter_id}",
                    "label": chapter_node_data.get("title"),
                    "data": {"type": "chapter", "id": chapter_id},
                    "isLeaf": True, # 默认章节是叶子
                    "children": []
                }

                # 如果章节下有任务 (第三层)，则它不是叶子，并添加任务节点
                quest_children = chapter_node_data.get("children", [])
                if quest_children:
                    child_node["isLeaf"] = False
                    for quest_node_data in quest_children:
                        quest_id = quest_node_data.get("id")
                        child_node["children"].append({
                            "key": f"quest-{quest_id}",
                            "label": quest_node_data.get("title"),
                            "data": {"type": "quest", "id": quest_id},
                            "isLeaf": True
                        })
                
                top_level_node["children"].append(child_node)

            frontend_tree.append(top_level_node)
            
        return frontend_tree

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"转换任务树为前端格式时出错: {str(e)}")


@router.get("/quest/{quest_id}/metadata")
def get_quest_metadata(
    quest_id: int,
    game_data: GameDataAPI = Depends(get_game_data_service)
) -> Dict[str, Any]:
    """
    获取单个任务的完整结构化元数据。
    """
    quest = game_data.quest.get_quest_by_id(quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    try:
        if hasattr(quest, 'model_dump'):
            return quest.model_dump()
        else:
            # 手动转换
            return {
                "quest_id": quest.quest_id,
                "quest_title": quest.quest_title,
                "quest_description": quest.quest_description,
                "chapter_id": quest.chapter_id,
                "chapter_title": quest.chapter_title,
                "series_id": quest.series_id,
                "chapter_num": quest.chapter_num,
                "quest_type": quest.quest_type,
                "source_json": quest.source_json,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "title": step.title,
                        "step_description": step.step_description,
                        "dialogue_nodes": [
                            {
                                "speaker": node.speaker,
                                "content": node.content,
                                "node_type": node.node_type,
                                "id": node.id
                            }
                            for node in step.dialogue_nodes
                        ]
                    }
                    for step in quest.steps
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"序列化任务数据失败: {str(e)}")


@router.get("/quest/{quest_id}/content", response_class=PlainTextResponse)
def get_quest_content(
    quest_id: int,
    game_data: GameDataAPI = Depends(get_game_data_service)
) -> str:
    """
    获取单个任务格式化后的 Markdown 内容。
    """
    markdown_content = game_data.quest.get_quest_as_markdown(quest_id)
    if not markdown_content:
        raise HTTPException(status_code=404, detail="任务内容未找到")
    
    return markdown_content


@router.get("/chapter/{chapter_id}/content", response_class=PlainTextResponse)
def get_chapter_content(
    chapter_id: int,
    game_data: GameDataAPI = Depends(get_game_data_service)
) -> str:
    """
    获取单个章节格式化后的 Markdown 内容。
    """
    markdown_content = game_data.quest.get_chapter_as_markdown(chapter_id)
    if not markdown_content:
        raise HTTPException(status_code=404, detail="章节内容未找到")
    
    return markdown_content
