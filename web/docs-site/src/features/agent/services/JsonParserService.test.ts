import { describe, it, expect, vi, beforeEach } from 'vitest';
import { JsonParserService } from '@/features/agent/services/JsonParserService';

describe('JsonParserService', () => {
  let jsonParserService: JsonParserService;

  beforeEach(() => {
    // 每个测试前重置 mock
    vi.clearAllMocks();
    // 创建新的 JsonParserService 实例
    jsonParserService = new JsonParserService();
  });

  describe('parseLlmResponse', () => {
    it('应该正确解析包含 feedback_data 的 JSON 响应', () => {
      const response = `{
        "feedback_data": {
          "status": "success",
          "message": "操作完成"
        }
      }`;

      const result = jsonParserService.parseLlmResponse(response);
      expect(result).toEqual({
        status: 'success',
        message: '操作完成'
      });
    });

    it('应该正确解析 feedback_data 为字符串的 JSON 响应', () => {
      const response = `{
        "feedback_data": "{\\"status\\": \\"success\\", \\"message\\": \\"操作完成\\"}"
      }`;

      const result = jsonParserService.parseLlmResponse(response);
      expect(result).toEqual({
        status: 'success',
        message: '操作完成'
      });
    });

    it('应该在 feedback_data 为无效字符串时返回 null', () => {
      const response = `{
        "feedback_data": "invalid json string"
      }`;

      const result = jsonParserService.parseLlmResponse(response);
      expect(result).toBeNull();
    });

    it('应该在没有 feedback_data 时返回整个 JSON', () => {
      const response = `{
        "status": "success",
        "message": "操作完成"
      }`;

      const result = jsonParserService.parseLlmResponse(response);
      expect(result).toEqual({
        status: 'success',
        message: '操作完成'
      });
    });

    it('应该在无效输入时返回 null', () => {
      const result = jsonParserService.parseLlmResponse('');
      expect(result).toBeNull();
    });
  });

  describe('extractJson', () => {
    it('应该从文本中提取 JSON 对象', () => {
      const text = '这里有一些文本 {"name": "test", "value": 123} 更多文本';

      const result = jsonParserService.extractJson(text);
      expect(result).toEqual({
        name: 'test',
        value: 123
      });
    });

    it('应该使用分隔符提取 JSON 对象', () => {
      const text = '前导文本 ---JSON--- {"name": "test", "value": 123}';

      const result = jsonParserService.extractJson(text);
      expect(result).toEqual({
        name: 'test',
        value: 123
      });
    });

    it('应该去除代码围栏并提取 JSON', () => {
      const text = '```json\n{"name": "test", "value": 123}\n```';

      const result = jsonParserService.extractJson(text);
      expect(result).toEqual({
        name: 'test',
        value: 123
      });
    });

    it('应该根据必需字段筛选 JSON 对象', () => {
      const text = '文本 {"name": "test"} 文本 {"name": "test", "value": 123}';

      const result = jsonParserService.extractJson(text, '---JSON---', ['name', 'value']);
      expect(result).toEqual({
        name: 'test',
        value: 123
      });
    });

    it('应该根据可选字段评分选择最佳 JSON 对象', () => {
      const text = '文本 {"name": "test"} 文本 {"name": "test", "value": 123} 文本 {"name": "test", "value": 123, "extra": "field"}';

      const result = jsonParserService.extractJson(text, '---JSON---', null, ['name', 'value', 'extra']);
      expect(result).toEqual({
        name: 'test',
        value: 123,
        extra: 'field'
      });
    });

    it('应该在没有合格候选时返回 null', () => {
      const text = '文本 {"name": "test"} 文本';

      const result = jsonParserService.extractJson(text, '---JSON---', ['missing_field']);
      expect(result).toBeNull();
    });

    it('应该忽略非对象类型的 JSON', () => {
      const text = '文本 ["array"] 文本 "string" 文本 {"name": "test"}';

      const result = jsonParserService.extractJson(text);
      expect(result).toEqual({
        name: 'test'
      });
    });
  });
});