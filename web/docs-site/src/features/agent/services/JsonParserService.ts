interface JsonCandidate {
  json: any;
  score: number;
  startIndex: number;
  endIndex: number;
  original: string;
}

export interface ExtractionResult {
  json: Record<string, any>;
  startIndex: number;
  endIndex: number;
  original: string;
}

function stripCodeFences(text: string): string {
  if (!text) return text;
  return text.replace(/```json/gi, '').replace(/```/g, '').trim();
}

function findJsonCandidates(text: string): { content: string; startIndex: number; endIndex: number }[] {
  const candidates: { content: string; startIndex: number; endIndex: number }[] = [];
  if (!text) return candidates;

  let inString = false;
  let escape = false;
  let depth = 0;
  let startIdx: number | null = null;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];

    if (inString) {
      if (escape) {
        escape = false;
      } else if (ch === '\\') {
        escape = true;
      } else if (ch === '"') {
        inString = false;
      }
      continue;
    }

    if (ch === '"') {
      inString = true;
      continue;
    }

    if (ch === '{') {
      if (depth === 0) {
        startIdx = i;
      }
      depth++;
    } else if (ch === '}') {
      if (depth > 0) {
        depth--;
        if (depth === 0 && startIdx !== null) {
          candidates.push({
            content: text.substring(startIdx, i + 1),
            startIndex: startIdx,
            endIndex: i + 1
          });
          startIdx = null;
        }
      }
    }
  }

  return candidates;
}

export class JsonParserService {
  parseLlmResponse(responseText: string): Record<string, any> | null {
    const result = this.extractJson(responseText);

    if (result === null) {
      return null;
    }

    const jsonData = result.json;

    if ('feedback_data' in jsonData) {
      let feedbackData = jsonData.feedback_data;

      if (typeof feedbackData === 'string') {
        try {
          feedbackData = JSON.parse(feedbackData);
        } catch (error) {
          return null;
        }
      }

      return feedbackData as Record<string, any>;
    } else {
      return jsonData;
    }
  }

  extractJson(
    text: string,
    separator: string = '---JSON---',
    requiredFields: string[] | null = null,
    optionalFields: string[] | null = null
  ): ExtractionResult | null {
    if (typeof text !== 'string') {
      return null;
    }

    if (!text.trim()) {
      return null;
    }

    let jsonPart = text;
    let offset = 0;

    if (text.includes(separator)) {
      const parts = text.split(separator);
      if (parts.length > 1) {
        jsonPart = parts[1].trim();
        offset = text.indexOf(jsonPart);
      } else {
        return null;
      }
    } else {
      offset = 0;
    }

    const preStripOffset = offset;
    jsonPart = stripCodeFences(jsonPart);
    const adjustedOffset = jsonPart ? text.indexOf(jsonPart) : preStripOffset;

    const candidates = findJsonCandidates(jsonPart);
    const qualifiedJsons: JsonCandidate[] = [];

    for (const candidate of candidates) {
      try {
        const parsedJson = JSON.parse(candidate.content);
        if (typeof parsedJson !== 'object' || parsedJson === null || Array.isArray(parsedJson)) {
          continue;
        }

        if (!parsedJson.tool_call) {
          continue;
        }

        const toolCall = parsedJson.tool_call;
        if (!toolCall.name || !toolCall.arguments) {
          continue;
        }

        const VALID_TOOLS = ['search_docs', 'read_doc', 'list_docs', 'ask'];
        if (!VALID_TOOLS.includes(toolCall.name)) {
          continue;
        }

        if (requiredFields) {
          if (!requiredFields.every(field => field in parsedJson)) {
            continue;
          }
        }

        let score = 0;
        if (optionalFields) {
          score = optionalFields.filter(field => field in parsedJson).length;
        }

        qualifiedJsons.push({
          json: parsedJson,
          score,
          startIndex: adjustedOffset + candidate.startIndex,
          endIndex: adjustedOffset + candidate.endIndex,
          original: candidate.content
        });

      } catch (error) {
        continue;
      }
    }

    if (qualifiedJsons.length === 0) {
      return null;
    }

    qualifiedJsons.sort((a, b) => b.score - a.score);
    const bestJsonItem = qualifiedJsons[0];

    return {
      json: bestJsonItem.json,
      startIndex: bestJsonItem.startIndex,
      endIndex: bestJsonItem.endIndex,
      original: bestJsonItem.original
    };
  }
}

export default new JsonParserService();