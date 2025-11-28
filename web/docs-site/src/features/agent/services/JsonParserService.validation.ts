// 简单的验证脚本，用于测试 JsonParserService 的修复
import { JsonParserService } from './JsonParserService';

// 创建服务实例
const service = new JsonParserService();

// 测试用例1：包含重复行文本的响应
console.log('=== 测试用例1：重复行文本 ===');
const testCase1 = `Some text here
Another line of text
{ "tool": "search_docs", "query": "test" }
Another line of text
{ "tool": "read_doc", "path": "/path/to/file" }`;

const result1 = service.parseLlmResponse(testCase1);
console.log('期望结果:', { tool: 'read_doc', path: '/path/to/file' });
console.log('实际结果:', result1);
console.log('测试通过:', JSON.stringify(result1) === JSON.stringify({ tool: 'read_doc', path: '/path/to/file' }));
console.log('');

// 测试用例2：更复杂的重复行案例
console.log('=== 测试用例2：复杂重复行 ===');
const testCase2 = `Introduction
This is a test line
This is a test line
{ "tool": "ask_choice", "question": "What do you want?" }
This is a test line
{ "tool": "search_docs", "query": "final query" }`;

const result2 = service.parseLlmResponse(testCase2);
console.log('期望结果:', { tool: 'search_docs', 'query': 'final query' });
console.log('实际结果:', result2);
console.log('测试通过:', JSON.stringify(result2) === JSON.stringify({ tool: 'search_docs', query: 'final query' }));
console.log('');

// 测试用例3：空行和空白字符
console.log('=== 测试用例3：空行和空白字符 ===');
const testCase3 = `

Some text

{ "tool": "search_docs", "query": "test with spaces" }

`;

const result3 = service.parseLlmResponse(testCase3);
console.log('期望结果:', { tool: 'search_docs', query: 'test with spaces' });
console.log('实际结果:', result3);
console.log('测试通过:', JSON.stringify(result3) === JSON.stringify({ tool: 'search_docs', query: 'test with spaces' }));
console.log('');

// 测试用例4：带有代码围栏的JSON
console.log('=== 测试用例4：代码围栏 ===');
const testCase4 = `Here's the result:
\`\`\`json
{ "tool": "read_doc", "path": "/api/docs" }
\`\`\`
End of response`;

const result4 = service.parseLlmResponse(testCase4);
console.log('期望结果:', { tool: 'read_doc', path: '/api/docs' });
console.log('实际结果:', result4);
console.log('测试通过:', JSON.stringify(result4) === JSON.stringify({ tool: 'read_doc', path: '/api/docs' }));
console.log('');

// 测试用例5：嵌套结构
console.log('=== 测试用例5：嵌套结构 ===');
const testCase5 = `Response:
{ "tool_call": { "name": "search_docs", "arguments": { "query": "nested query" } } }`;

const result5 = service.parseLlmResponse(testCase5);
console.log('期望结果:', { tool: 'search_docs', query: 'nested query' });
console.log('实际结果:', result5);
console.log('测试通过:', JSON.stringify(result5) === JSON.stringify({ tool: 'search_docs', query: 'nested query' }));
console.log('');

// 边界情况测试：相同文本多次出现在不同位置
console.log('=== 边界测试：相同文本多次出现 ===');
const edgeCase = `Start
{ "tool": "first", "value": "1" }
Middle
{ "tool": "second", "value": "2" }
Middle
{ "tool": "third", "value": "3" }`;

const edgeResult = service.parseLlmResponse(edgeCase);
console.log('期望结果:', { tool: 'third', value: '3' });
console.log('实际结果:', edgeResult);
console.log('测试通过:', JSON.stringify(edgeResult) === JSON.stringify({ tool: 'third', value: '3' }));