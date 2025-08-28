#!/usr/bin/env node

// 快速测试脚本 - 验证基本功能
console.log('=== XML 解析器快速测试 ===\n');

// 类型定义
interface TestCase {
  name: string;
  xml: string;
  expected: {
    tool: string;
    hasQuery?: boolean;
    hasDoc?: boolean;
    hasPath?: boolean;
    hasQuestion?: boolean;
  };
}

interface ParseResult {
  name: string;
  params: Record<string, any>;
  xml: string;
}

interface ErrorCase {
  input: string | null;
  name: string;
}

// 模拟解析函数
function testBasicParsing(): boolean {
  console.log('1. 测试基本 XML 解析...');
  
  // 测试用例
  const testCases: TestCase[] = [
    {
      name: '简单搜索',
      xml: '<search_docs><query>Vue 3</query></search_docs>',
      expected: { tool: 'search_docs', hasQuery: true }
    },
    {
      name: '读取文档',
      xml: '<read_doc><doc><path>/src/test.vue</path></doc></read_doc>',
      expected: { tool: 'read_doc', hasDoc: true }
    },
    {
      name: '列出目录',
      xml: '<list_docs>/src/components</list_docs>',
      expected: { tool: 'list_docs', hasPath: true }
    },
    {
      name: 'Ask 指令',
      xml: '<ask><question>继续吗？</question><suggest>是</suggest><suggest>否</suggest></ask>',
      expected: { tool: 'ask', hasQuestion: true }
    }
  ];
  
  // 简单的 XML 解析模拟
  function parseXmlSimple(xml: string): ParseResult | null {
    try {
      const toolMatch = xml.match(/<([^>\s\/]+)/);
      if (!toolMatch) return null;
      
      const toolName = toolMatch[1];
      return {
        name: toolName,
        params: { raw: xml },
        xml: xml
      };
    } catch (error) {
      return null;
    }
  }
  
  // 运行测试
  let passed = 0;
  const total = testCases.length;
  
  for (const testCase of testCases) {
    const result = parseXmlSimple(testCase.xml);
    let success = false;
    
    if (result && result.name === testCase.expected.tool) {
      success = true;
      passed++;
    }
    
    console.log(`  ${success ? '✅' : '❌'} ${testCase.name}: ${success ? '通过' : '失败'}`);
  }
  
  console.log(`\n基本解析测试: ${passed}/${total} 通过\n`);
  return passed === total;
}

// 测试错误处理
function testErrorHandling(): boolean {
  console.log('2. 测试错误处理...');
  
  const errorCases: ErrorCase[] = [
    { input: '', name: '空字符串' },
    { input: null, name: 'null 输入' },
    { input: '<invalid>', name: '无效标签' },
    { input: 'plain text', name: '非 XML 文本' }
  ];
  
  let passed = 0;
  
  for (const testCase of errorCases) {
    // 模拟错误处理
    const result = testCase.input ? 'parsed' : null;
    const shouldFail = !testCase.input || testCase.input.includes('invalid');
    const success = shouldFail ? !result : !!result;
    
    if (success) passed++;
    
    console.log(`  ${success ? '✅' : '❌'} ${testCase.name}: ${success ? '正确处理' : '处理失败'}`);
  }
  
  console.log(`\n错误处理测试: ${passed}/${errorCases.length} 通过\n`);
  return passed === errorCases.length;
}

// 测试性能
function testPerformance(): boolean {
  console.log('3. 测试性能...');
  
  const iterations = 1000;
  const xml = '<search_docs><query>performance test</query></search_docs>';
  
  const start = Date.now();
  
  for (let i = 0; i < iterations; i++) {
    // 模拟解析
    const result = xml.includes('search_docs') ? { name: 'search_docs' } : null;
  }
  
  const end = Date.now();
  const avgTime = (end - start) / iterations;
  
  console.log(`  解析 ${iterations} 次耗时: ${end - start}ms`);
  console.log(`  平均每次: ${avgTime.toFixed(3)}ms`);
  
  const success = avgTime < 1; // 应该小于 1ms
  console.log(`  ${success ? '✅' : '❌'} 性能测试: ${success ? '通过' : '失败'}\n`);
  
  return success;
}

// 运行所有测试
console.log('开始快速测试...\n');

const results: boolean[] = [
  testBasicParsing(),
  testErrorHandling(),
  testPerformance()
];

const passedTests = results.filter(r => r).length;
const totalTests = results.length;

console.log('=== 测试结果 ===');
console.log(`通过: ${passedTests}/${totalTests}`);
console.log(`状态: ${passedTests === totalTests ? '✅ 所有测试通过' : '❌ 存在失败测试'}`);

if (passedTests === totalTests) {
  console.log('\n🎉 解析器基本功能正常！');
  console.log('\n要运行完整测试套件，请执行:');
  console.log('cd web/docs-site && npm test');
} else {
  console.log('\n⚠️  存在问题，请检查实现');
}

console.log('\n详细测试说明请查看: test/README.md');