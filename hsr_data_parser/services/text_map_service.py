import json
import re
from typing import Dict
from .loader_service import DataLoader
from .text_join_service import TextJoinService
from ..utils.text_transformer import TextTransformer

class TextMapService:
    """Service to handle text map resolving."""
    TEXTJOIN_REGEX = re.compile(r'\{TEXTJOIN#(\d+)\}')

    def __init__(self, loader: DataLoader, language_code: str = "CHS"):
        self._text_map: Dict[str, str] = {}
        self._language_code = language_code
        self._loader = loader
        self._transformer = TextTransformer()
        self._text_join_service = TextJoinService(loader)
        self._load_text_map()

    def _load_text_map(self):
        """Loads the text map from the specified language file."""
        text_map_path = f"turnbasedgamedata/TextMap/TextMap{self._language_code}.json"
        try:
            with open(text_map_path, "r", encoding="utf-8") as f:
                self._text_map = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"严重错误: 无法加载 TextMap 文件 at '{text_map_path}'. Error: {e}")
            self._text_map = {}

    def _resolve_text_join(self, text: str, visited: set = None) -> str:
        """
        Recursively resolves {TEXTJOIN#...} placeholders in a string.
        """
        if visited is None:
            visited = set()

        # Find all {TEXTJOIN#...} placeholders
        matches = list(self.TEXTJOIN_REGEX.finditer(text))
        if not matches:
            return text

        # Replace placeholders from right to left to handle nested cases correctly
        for match in reversed(matches):
            join_id = int(match.group(1))

            # Prevent infinite recursion
            if join_id in visited:
                print(f"警告: 检测到循环引用 TextJoin ID {join_id}, 已跳过。")
                continue
            
            # Get the final text hash from the TextJoinService, which handles the lookup chain
            text_hash = self._text_join_service.get_text_hash_by_join_id(join_id)
            
            if text_hash is not None:
                # Handle the special case for Player Character placeholders
                if text_hash == -1:
                    resolved_replacement = "开拓者"
                else:
                    # Get the replacement text from the text map using the final hash
                    replacement_text = self._text_map.get(str(text_hash))
                    
                    # Recursively resolve any nested placeholders
                    if replacement_text is not None:
                        visited.add(join_id)
                        resolved_replacement = self._resolve_text_join(replacement_text, visited)
                        visited.remove(join_id)
                    else:
                        resolved_replacement = None

                # If we have a valid resolved text, wrap it in brackets.
                # Otherwise, keep the original placeholder.
                if resolved_replacement is not None and resolved_replacement != "":
                    final_text = f"「{resolved_replacement}」"
                else:
                    final_text = match.group(0) # Keep original e.g., {TEXTJOIN#59}
                
                text = text[:match.start()] + final_text + text[match.end():]
            # If we can't find a final text_hash, the original placeholder is also kept by default.
        
        return text

    def get(self, text_hash: any, default: str = "") -> str:
        """Gets a string from a text map hash, resolves {TEXTJOIN}, and cleans it."""
        raw_text = self._text_map.get(str(text_hash), default)
        
        # First, resolve any {TEXTJOIN} placeholders
        resolved_text = self._resolve_text_join(raw_text)
        
        # Then, apply the final transformations
        return self._transformer.transform(resolved_text)