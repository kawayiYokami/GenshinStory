import { performance } from 'perf_hooks';
import parserAdapter from '../src/features/agent/services/parserAdapter.ts';

// 测试数据
const testCases = {
  simple: `<search_docs>
  <query>Vue 3 composition API</query>
</search_docs>`,

  nested: `<read_doc>
  <doc>
    <path>/src/components/Test.vue</path>
    <line_range>1-10</line_range>
    <line_range>20-30</line_range>
  </doc>
</read_doc>`,

  multipleDocs: `<read_doc>
  <doc>
    <path>/src/components/Test.vue</path>
  </doc>
  <doc>
    <path>/src/utils/helper.ts</path>
  </doc>
</read_doc>`,

  largeXml: Array(100).fill(0).map((_, i) => 
    `<doc>
      <path>/src/file${i}.vue</path>
      <line_range>${i}-${i+10}</line_range>
    </doc>`
  ).join('\n'),

  cdata: `<search_docs>
  <query><![CDATA[Vue 3 & React]]></query>
</search_docs>`,

  ask: `<ask>
  <question>您想要继续分析这个组件吗？</question>
  <suggest>是的，请继续</suggest>
  <suggest>不，先看看其他文件</suggest>
  <suggest>给我一些建议</suggest>
</ask>`
};

// 测试函数
function runStressTest(iterations = 1000) {
  console.log('开始压力测试...\n');
  
  for (const [name, xml] of Object.entries(testCases)) {
    console.log(`测试 ${name}:`);
    
    // 预热
    parserAdapter.parseSingleToolCall(xml);
    
    // 执行测试
    const start = performance.now();
    let success = 0;
    let errors = 0;
    
    for (let i = 0; i < iterations; i++) {
      try {
        const result = parserAdapter.parseSingleToolCall(xml);
        if (result) success++;
        else errors++;
      } catch (error) {
        errors++;
      }
    }
    
    const end = performance.now();
    const avgTime = (end - start) / iterations;
    
    console.log(`  成功: ${success}/${iterations}`);
    console.log(`  错误: ${errors}/${iterations}`);
    console.log(`  平均时间: ${avgTime.toFixed(3)}ms`);
    console.log(`  总时间: ${(end - start).toFixed(2)}ms`);
    console.log('');
  }
  
  // 内存使用测试
  console.log('内存使用测试:');
  const before = process.memoryUsage();
  
  // 解析大量 XML
  const largeXml = Array(1000).fill(0).map((_, i) => 
    `<doc><path>/src/file${i}.vue</path></doc>`
  ).join('\n');
  
  for (let i = 0; i < 100; i++) {
    parserAdapter.parseSingleToolCall(`<read_doc>${largeXml}</read_doc>`);
  }
  
  const after = process.memoryUsage();
  console.log(`  RSS 增长: ${((after.rss - before.rss) / 1024 / 1024).toFixed(2)}MB`);
  console.log(`  Heap 增长: ${((after.heapUsed - before.heapUsed) / 1024 / 1024).toFixed(2)}MB`);
  console.log('');
  
  // 错误处理测试
  console.log('错误处理测试:');
  const invalidXmls = [
    '',
    null,
    undefined,
    '<invalid>',
    '<search_docs><unclosed>',
    'a'.repeat(10 * 1024 * 1024), // 10MB
    '<search_docs>' + '<a>'.repeat(200) + '</search_docs>' // 深度嵌套
  ];
  
  for (const xml of invalidXmls) {
    try {
      const start = performance.now();
      const result = parserAdapter.parseSingleToolCall(xml);
      const end = performance.now();
      console.log(`  ${typeof xml}: ${result ? '成功' : '失败'} (${(end - start).toFixed(3)}ms)`);
    } catch (error) {
      console.log(`  ${typeof xml}: 抛出异常 - ${error.message}`);
    }
  }
}

// 运行测试
if (import.meta.url === `file://${process.argv[1]}`) {
  runStressTest();
}

export { runStressTest, testCases };