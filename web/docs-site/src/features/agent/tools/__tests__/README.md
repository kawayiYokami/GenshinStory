# read_doc 工具测试说明

## 测试概述

`read_doc` 工具用于读取文档内容。测试文件验证工具在不同参数输入下的行为。

## 测试文件

### 1. 基础测试 (read_doc.test.ts)
包含基本的测试用例，验证工具在各种参数输入下的行为。

### 2. 简单测试 (read_doc.simple.test.ts)
简化版本的测试，展示了测试的基本工作原理。

### 3. 增强测试 (read_doc.enhanced.test.ts)
包含详细日志和更全面的测试用例，覆盖更多场景。

## 测试用例说明

### 1. 参数处理测试

#### 应该能处理简单的 path 参数
- 输入: `{ path: 'test.md' }`
- 预期: 工具能正确处理 path 参数，不返回参数格式错误

#### 应该能处理 args 对象参数
- 输入: `{ args: { doc: { path: 'test.md' } } }`
- 预期: 工具能正确处理嵌套的 args 参数，不返回参数格式错误

#### 应该处理空参数
- 输入: `{}`
- 预期: 工具返回参数格式错误信息

### 2. 错误处理测试

#### 应该处理解析器错误
- 模拟解析器抛出异常
- 预期: 工具返回内部执行失败的错误信息

#### 应该处理本地工具错误
- 模拟本地工具抛出异常
- 预期: 工具返回内部执行失败的错误信息

### 3. 结果处理测试

#### 应该正确处理单个文档的结果
- 模拟单个文档的读取结果
- 预期: 工具返回正确的后续提示

#### 应该正确处理多个文档的结果
- 模拟多个文档的读取结果
- 预期: 工具返回正确的后续提示

## 运行测试

```bash
# 运行基础测试
npm run test:run -- src/features/agent/tools/__tests__/read_doc.test.ts

# 运行简单测试
npx vitest run src/features/agent/tools/__tests__/read_doc.simple.test.ts

# 运行增强测试
npx vitest run src/features/agent/tools/__tests__/read_doc.enhanced.test.ts

# 运行所有测试
npx vitest run src/features/agent/tools/__tests/

# 以监视模式运行测试
npx vitest src/features/agent/tools/__tests/
```

## 测试输出解释

测试运行时会显示以下信息：
- 测试文件名称和路径
- 每个测试用例的执行结果（通过/失败）
- 执行时间统计
- 总体测试结果汇总
- 详细的日志输出（在增强测试中）

## 测试结果示例

```
✓ src/features/agent/tools/__tests__/read_doc.enhanced.test.ts (10 tests) 9ms
  ✓ read_doc 工具增强测试 > 参数处理 > 应该能处理简单的 path 参数 4ms
  ✓ read_doc 工具增强测试 > 参数处理 > 应该能处理 args 对象参数 1ms
  ✓ read_doc 工具增强测试 > 参数处理 > 应该能处理直接的 path 对象 1ms
  ✓ read_doc 工具增强测试 > 参数处理 > 应该能处理嵌套的 args 结构 1ms
  ✓ read_doc 工具增强测试 > 参数处理 > 应该处理空参数 0ms
  ✓ read_doc 工具增强测试 > 参数处理 > 应该处理无效的参数结构 0ms
  ✓ read_doc 工具增强测试 > 错误处理 > 应该处理解析器错误 0ms
  ✓ read_doc 工具增强测试 > 错误处理 > 应该处理本地工具错误 0ms
  ✓ read_doc 工具增强测试 > 结果处理 > 应该正确处理单个文档的结果 0ms
  ✓ read_doc 工具增强测试 > 结果处理 > 应该正确处理多个文档的结果 0ms
```

这表示所有测试都通过了，工具在各种参数输入下都能正确工作。