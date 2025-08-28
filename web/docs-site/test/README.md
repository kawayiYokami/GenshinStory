# 测试说明文档

## 概述

本项目已从 DOMParser 迁移到 fast-xml-parser，以提供更好的 XML 解析能力、错误处理和跨平台兼容性。本文档详细说明如何进行测试。

## 测试环境

### 依赖安装
```bash
npm install
```

确保已安装以下关键依赖：
- `vitest` - 测试框架
- `fast-xml-parser` - XML 解析库
- `happy-dom` - 测试环境

## 测试运行

### 1. 单元测试

运行所有测试：
```bash
npm test
# 或者
npx vitest run
```

运行特定测试文件：
```bash
npx vitest run src/features/agent/services/toolParserService.test.ts
```

查看测试覆盖率：
```bash
npx vitest run --coverage
```

### 2. 快速测试

运行快速验证脚本：
```bash
npx tsx test/quick-test.ts
```

### 3. 压力测试

运行压力测试脚本：
```bash
npx tsx stress.test.ts
```

## 测试标准

### 1. 功能测试标准

#### XML 解析测试 (toolParserService.test.ts)

**必须通过的测试场景：**

1. **标准 XML 工具调用**
   ```xml
   <search_docs>
     <query>Vue 3 composition API</query>
   </search_docs>
   ```
   - 期望：正确解析工具名和参数

2. **嵌套 XML 结构**
   ```xml
   <read_doc>
     <doc>
       <path>/src/components/Test.vue</path>
       <line_range>1-10</line_range>
     </doc>
   </read_doc>
   ```
   - 期望：保留嵌套对象结构

3. **多文档请求**
   ```xml
   <read_doc>
     <doc><path>/src/test1.vue</path></doc>
     <doc><path>/src/test2.vue</path></doc>
   </read_doc>
   ```
   - 期望：正确解析为数组

4. **JSON 格式工具调用**
   ```json
   {
     "function": {
       "name": "search_docs",
       "arguments": "{\"query\":\"Vue 3\"}"
     }
   }
   ```
   - 期望：正确解析 JSON 参数

5. **Ask UI 指令**
   ```xml
   <ask>
     <question>继续分析吗？</question>
     <suggest>是</suggest>
     <suggest>否</suggest>
     <suggest>建议</suggest>
   </ask>
   ```
   - 期望：正确解析问题和建议列表

#### 错误处理测试

**必须正确处理的错误场景：**

1. **无效工具名称**
   ```xml
   <invalid_tool><param>value</param></invalid_tool>
   ```
   - 期望：返回 null，记录错误日志

2. **格式错误的 XML**
   ```xml
   <search_docs><unclosed>
   ```
   - 期望：优雅处理，不崩溃

3. **空输入**
   - 期望：返回 null

4. **超大 XML** (>5MB)
   - 期望：拒绝并返回错误

5. **深度嵌套** (>100层)
   - 期望：拒绝并返回错误

### 2. 性能测试标准

#### 压力测试指标 (stress.test.ts)

**性能要求：**

1. **解析速度**
   - 简单 XML：< 1ms
   - 复杂 XML（100个文档）：< 10ms
   - 大型 XML（1000个文档）：< 100ms

2. **内存使用**
   - 单次解析：< 1MB 增长
   - 批量解析（100次）：< 10MB 增长
   - 无内存泄漏

3. **并发处理**
   - 1000 次连续解析无错误
   - 错误率 < 0.1%

4. **错误恢复**
   - 处理无效输入时不崩溃
   - 错误信息清晰明确

### 3. 安全测试标准

**安全要求：**

1. **XXE 防护**
   - 禁用外部实体解析
   - 禁用 DTD 处理

2. **输入验证**
   - 大小限制：5MB
   - 深度限制：100层
   - 属性数量限制：100个

3. **错误信息**
   - 不泄露敏感信息
   - 提供有用的错误提示

## 测试覆盖率要求

### 代码覆盖率目标
- **整体覆盖率**：≥ 90%
- **行覆盖率**：≥ 90%
- **分支覆盖率**：≥ 85%
- **函数覆盖率**：≥ 95%

### 关键路径覆盖
1. 所有解析函数
2. 所有错误处理路径
3. 所有工具类型
4. 边界条件

## 故障排查

### 常见测试失败

1. **导入错误**
   ```
   Error: Cannot find package '@/features/...'
   ```
   解决：确保在 `web/docs-site` 目录下运行测试

2. **类型错误**
   ```
   TypeError: Cannot read properties of undefined
   ```
   解决：检查 parserAdapter 返回的数据结构

3. **异步问题**
   ```
   Error: Test timeout
   ```
   解决：增加测试超时时间或检查异步操作

### 调试技巧

1. **查看详细输出**
   ```bash
   npx vitest run --reporter=verbose
   ```

2. **只运行失败测试**
   ```bash
   npx vitest run --run
   ```

3. **生成覆盖率报告**
   ```bash
   npx vitest run --coverage --coverage.reporters=html
   ```
   然后打开 `coverage/index.html`

## 测试数据

### 测试用例示例

位于 `src/test/mocks.ts`，包含：
- 标准工具调用
- 边界情况
- 错误场景
- 性能测试数据

### 自定义测试

创建新测试时，请：
1. 遵循现有测试结构
2. 包含正面和负面测试
3. 添加适当的断言
4. 考虑边界条件

## 持续集成

测试将在以下情况下自动运行：
- 提交代码
- 创建 Pull Request
- 合并到主分支

确保所有测试通过后再提交代码。

## 更新日志

### v2.0.0 - fast-xml-parser 迁移
- ✅ 替换 DOMParser 为 fast-xml-parser
- ✅ 新增结构化错误处理
- ✅ 增强安全限制
- ✅ 提升解析性能
- ✅ 改进跨平台兼容性

## 联系方式

如有测试相关问题，请：
1. 查看本文档
2. 检查测试输出日志
3. 参考现有测试用例