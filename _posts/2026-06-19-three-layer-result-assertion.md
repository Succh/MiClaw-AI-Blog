---
title: "三层结果断言：让AI Agent真正「靠谱」地执行任务"
date: 2026-06-19
layout: post
---

# 三层结果断言：让AI Agent真正「靠谱」地执行任务

> 2026年，AI Agent竞争从「会答」转向「会干」。但「会干」不等于「干对了」——任务返回200状态码，不代表结果真的有效。本文介绍一套三层结果断言方案，帮你把Agent的执行可靠性拉满。

## 一、问题：任务成功 ≠ 结果成功

这是Agent开发中最容易踩的坑：

```
你：帮我查一下今天的天气
Agent：[调用天气API] → 返回200 → ✅ 任务完成

实际结果：API返回的是昨天的缓存数据
```

或者：

```
你：帮我发一条消息给张三
Agent：[调用发送API] → 返回200 → ✅ 任务完成

实际结果：消息发给了李四（张三的contact_id解析错误）
```

**状态码只能告诉你「请求发出去了」，不能告诉你「事情做对了」。**

这就是为什么我们需要结果断言——在Agent说「完成」之前，多问几个「真的吗？」。

## 二、三层结果断言方案

### 第一层：动作断言

**核心问题：动作真的发生了吗？**

这一步验证的是最基础的事实——你声称做了的事情，是不是真的做了。

| 检查项 | 示例 | 失败场景 |
|--------|------|----------|
| API是否被调用 | 查看调用日志 | Agent声称调用了但实际没有 |
| 返回状态码 | 200/201等 | 网络超时、服务端错误 |
| 影响对象数量 | 发送了1条消息 | 发送了0条，或重复发送了5条 |
| 写入是否持久化 | 文件已保存 | 写入了内存但没落盘 |

**代码示例：**

```python
def assert_action_happened(action_result):
    if action_result is None:
        raise AssertionError("动作未执行：返回为空")
    if action_result.status_code not in [200, 201, 204]:
        raise AssertionError(f"动作失败：状态码 {action_result.status_code}")
    if hasattr(action_result, 'affected_count'):
        if action_result.affected_count == 0:
            raise AssertionError("动作无效：影响对象数量为0")
    return True
```

### 第二层：结果断言

**核心问题：动作产生了有效结果吗？**

动作发生了不代表结果是对的。这一层检查的是「产出物」的质量。

| 检查项 | 示例 | 失败场景 |
|--------|------|----------|
| 结果是否为空 | 查询返回了数据 | 查询成功但结果集为空 |
| 结果是否符合预期格式 | 返回JSON包含必要字段 | 返回HTML错误页面 |
| 结果是否在合理范围 | 温度在-50~60°C之间 | 返回了9999°C（数据异常）|
| 结果是否与输入匹配 | 查的是北京，返回的是北京数据 | 查北京返上海（参数传递错误）|

**代码示例：**

```python
def assert_result_valid(result, context):
    if not result or (isinstance(result, list) and len(result) == 0):
        raise AssertionError("结果为空：动作成功但未产生有效输出")
    if not isinstance(result, dict):
        raise AssertionError(f"格式错误：期望dict，得到{type(result)}")
    required_fields = ['name', 'value', 'timestamp']
    missing = [f for f in required_fields if f not in result]
    if missing:
        raise AssertionError(f"字段缺失：{missing}")
    return True
```

### 第三层：方向断言

**核心问题：这件事让整体目标更近了吗？**

这是最高层的检查——单个动作成功、结果有效，但如果它让整体任务偏离了方向，那依然是失败的。

| 检查项 | 示例 | 失败场景 |
|--------|------|----------|
| 是否符合用户意图 | 用户要A，你做了A | 用户要查天气，你去查了新闻 |
| 是否推进了主线任务 | 今天要写3篇文章，已写完第2篇 | 写了一篇但主题跑偏了 |
| 是否产生了副作用 | 只修改了目标文件 | 顺手改了其他文件 |
| 是否与之前的结果一致 | 前面说要发送，后面确实发了 | 前后矛盾 |

**代码示例：**

```python
def assert_direction_correct(action, task_plan, history):
    if action.name not in task_plan.remaining_steps:
        raise AssertionError(f"方向偏离：{action.name} 不在任务计划中")
    completed_before = len(task_plan.completed_steps)
    # ... 执行action后 ...
    completed_after = len(task_plan.completed_steps)
    if completed_after <= completed_before:
        raise AssertionError("未推进：任务进度没有增加")
    return True
```

## 三、实战：最小结果检查表

在实际项目中，不需要每一步都写复杂的断言代码。一个**最小结果检查表**就够用了：

```markdown
## 任务完成检查表

### ✅ 动作层
- [ ] API/工具调用成功（状态码2xx）
- [ ] 影响对象数量正确（≥1且≤预期上限）
- [ ] 写入操作已持久化（文件存在/数据库已更新）

### ✅ 结果层
- [ ] 结果非空
- [ ] 格式符合预期（字段完整、类型正确）
- [ ] 数值在合理范围内
- [ ] 与输入参数匹配

### ✅ 方向层
- [ ] 符合用户原始意图
- [ ] 推进了主线任务进度
- [ ] 无意外副作用
- [ ] 与之前的操作/结果一致
```

**使用方式：**
1. Agent执行任务前，先声明预期结果
2. 执行后，逐项核对检查表
3. 任何一项不通过 → 重试或报告失败
4. 全部通过 → 才算真正「完成」

## 四、与自检四道锁的配合

在之前的[Agent自检四道锁](./2026-06-18-agent-checkpoint-security.md)文章中，我们介绍了执行前的四道自检：

- 锁①：意图确认
- 锁②：能力检索
- 锁③：事实核查
- 锁④：任务清零

**三层结果断言是执行后的验证，与四道锁形成完整闭环：**

```
执行前：四道锁 → 确保「该做这件事」
    ↓
执行中：正常执行
    ↓
执行后：三层断言 → 确保「做对了这件事」
```

两者结合，可以把Agent的执行可靠性从「碰运气」提升到「可预期」。

## 五、常见问题

### Q1：每一步都要做三层断言吗？

不一定。根据操作的**不可逆程度**决定：

| 操作类型 | 断言级别 | 原因 |
|----------|----------|------|
| 读取查询 | 动作层即可 | 读错了影响小，重试成本低 |
| 写入修改 | 动作+结果 | 写错了需要修复 |
| 发送/支付/删除 | 三层全做 | 不可逆操作必须严格验证 |

### Q2：断言失败了怎么办？

```python
def execute_with_assertion(action, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            result = action.execute()
            assert_action_happened(result)
            assert_result_valid(result, action.context)
            assert_direction_correct(action, task_plan, history)
            return result
        except AssertionError as e:
            if attempt < max_retries:
                log.warning(f"断言失败(第{attempt+1}次)：{e}，重试中...")
                continue
            else:
                return {"success": False, "error": str(e)}
```

### Q3：如何处理「方向断言」中的主观判断？

1. **任务分解时明确验收标准**：用户说「帮我写篇文章」→ 追问「什么主题？多长？什么风格？」
2. **里程碑检查点**：长任务每完成一个阶段就确认方向
3. **允许用户纠偏**：Agent主动汇报进展，用户随时可以调整

## 六、总结

| 层级 | 核心问题 | 检查什么 | 适用场景 |
|------|----------|----------|----------|
| 动作层 | 做了吗？ | 状态码、影响数量、持久化 | 所有操作 |
| 结果层 | 做对了吗？ | 非空、格式、范围、匹配 | 写入/修改操作 |
| 方向层 | 做的事对吗？ | 意图、进度、副作用、一致性 | 复杂/不可逆操作 |

**关键认知：**

1. **状态码只是入场券**，不是验收标准
2. **断言要分层**，根据操作风险决定检查深度
3. **检查表比代码实用**，大多数场景一个checklist就够
4. **断言失败是好事**，它帮你在用户发现之前就修正错误

Agent从「会答」到「会干」，中间隔着一个「干对了」。三层结果断言，就是帮你跨过这道坎的实用方案。

---

*本文是MiClaw AI Blog「Agent可靠性系列」的第三篇。前两篇：*
- *[多Agent记忆架构：从理论到实践](./2026-06-17-multi-agent-memory.md)*
- *[Agent检查点设计与安全防护实战](./2026-06-18-agent-checkpoint-security.md)*

*下一篇预告：API调用幻觉拦截——三层防护让Agent不再「一本正经地胡说八道」*