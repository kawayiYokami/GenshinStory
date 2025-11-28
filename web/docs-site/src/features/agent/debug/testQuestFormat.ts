import JsonParserService from '../services/JsonParserService';

// 测试quest格式的JSON解析
const testCases = [
  {
    name: 'quest格式 - ask_choice',
    input: '{"ask_choice": {"question": "是否需要深入分析教令院与阿如村的其他关联？", "suggestions": ["查阅塞塔蕾的背景信息", "分析教令院在阿如村的其他任务记录", "探索卡里尔对话中的隐喻细节"]}}',
    expected: {
      tool: "ask_choice",
      question: "是否需要深入分析教令院与阿如村的其他关联？",
      suggestions: [
        "查阅塞塔蕾的背景信息",
        "分析教令院在阿如村的其他任务记录",
        "探索卡里尔对话中的隐喻细节"
      ]
    }
  }
];

console.log('=== 测试quest格式的JsonParserService ===\n');

testCases.forEach((testCase, index) => {
  console.log(`\n测试 ${index + 1}: ${testCase.name}`);
  console.log('输入:', JSON.stringify(testCase.input));

  try {
    const result = JsonParserService.parseLlmResponse(testCase.input);
    if (result) {
      console.log('✓ 解析成功:', result);

      // 检查是否与期望匹配
      const resultStr = JSON.stringify(result);
      const expectedStr = JSON.stringify(testCase.expected);

      if (resultStr === expectedStr) {
        console.log('✓ 完全匹配期望结果');
      } else {
        console.log('⚠ 与期望不完全匹配');
        console.log('期望:', testCase.expected);
      }
    } else {
      console.log('✗ 解析失败');
      console.log('期望:', testCase.expected);
    }
  } catch (error) {
    console.log('✗ 解析异常:', error instanceof Error ? error.message : String(error));
  }
});

console.log('\n=== 测试完成 ===');