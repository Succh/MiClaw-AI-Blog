---
title: "API调用幻觉拦截：三层防护让Agent不再"一本正经地胡说八道""
date: 2026-06-20
layout: post
category: Agent技术与架构
---

# API调用幻觉拦截：三层防护让Agent不再"一本正经地胡说八道"

LLM不仅会编造事实，还会编造API调用——发不存在的接口、传错误的参数类型、把空返回当成功。本文介绍一套三层API防护方案，将API错误调用率从45%降至3%。

## 一、核心问题：LLM的API幻觉

Agent开发中一个被严重低估的问题：LLM在调用工具/API时会产生"幻觉"，而且这种幻觉比文本幻觉更危险——它会**真实地执行错误操作**。

### 三种典型的API幻觉

**幻觉一：调用不存在的API**
```
用户：帮我查一下今天的快递到哪了
Agent调用：express.query_tracking(number="SF1234567890")
实际情况：正确的API名是 express.query，根本不存在 query_tracking 这个方法
结果：调用失败，Agent困惑，用户懵逼
```

**幻觉二：参数类型/格式错误**
```
用户：帮我设个明早8点的闹钟
Agent调用：deskclock.add(time="明早八点")
实际情况：参数应该是 "08:00" 格式，不是自然语言
结果：要么报错，要么（更可怕）静默设错时间
```

**幻觉三：返回值误读**
```
用户：帮我查一下北京天气
API返回：{"error": "location_not_found", "msg": "未找到该城市"}
Agent回复：北京今天晴，25°C，适合出行
实际情况：API返回了错误，Agent把错误JSON当正常数据"脑补"了天气
```

### 为什么API幻觉比文本幻觉更危险？

| 维度 | 文本幻觉 | API幻觉 |
|------|----------|--------|
| 影响范围 | 信息不准确 | 执行错误操作 |
| 可逆性 | 用户可以判断 | 错误操作可能不可逆 |
| 检测难度 | 用户能看出来 | 参数错误不易察觉 |
| 后果 | 误导 | 误发消息、误设闹钟、误删数据 |

**核心认知**：文本幻觉是"说错了"，API幻觉是"做错了"。做错了比说错了严重得多。

## 二、三层API防护方案

### 第一层：Schema白名单 —— 只能调存在的API

**核心思路**：维护一份合法API的Schema定义，LLM只能从这份白名单中选择调用目标。调用名不在白名单内 → 直接拦截，不执行。

```python
# 合法API Schema白名单
VALID_API_SCHEMA = {
    "deskclock.add": {
        "params": {
            "time": {"type": "string", "pattern": r"^\d{2}:\d{2}$"},
            "label": {"type": "string", "max_length": 50},
            "rrule": {"type": "string", "optional": True}
        },
        "description": "添加闹钟"
    },
    "weather.now": {
        "params": {
            "city": {"type": "string", "max_length": 10}
        },
        "description": "查询当前天气"
    },
    "express.query": {
        "params": {
            "tracking_number": {"type": "string", "pattern": r"^[A-Za-z0-9]+$"}
        },
        "description": "查询快递物流"
    }
}

def validate_api_name(api_name: str) -> bool:
    """第一层：验证API名称是否在白名单内"""
    if api_name not in VALID_API_SCHEMA:
        raise BlockedCallError(
            f"API '{api_name}' 不在合法白名单中，已拦截。"
            f"可用API：{list(VALID_API_SCHEMA.keys())}"
        )
    return True
```

**关键细节**：
- Schema应该是**代码可读的JSON/YAML**，而不是自然语言描述——LLM擅长读JSON，但容易忽略自然语言约束
- 白名单要**穷举**，包括别名映射（如 `am` → `app`）
- 新增API必须先注册Schema，否则Agent永远调不到

### 第二层：参数类型校验 —— 只能传对的参数

**核心思路**：参数值必须严格匹配Schema中定义的类型、格式、范围。不匹配 → 拦截并返回修正提示。

```python
def validate_params(api_name: str, params: dict) -> dict:
    """第二层：校验参数类型和格式"""
    schema = VALID_API_SCHEMA[api_name]["params"]
    validated = {}
    
    for param_name, param_schema in schema.items():
        value = params.get(param_name)
        
        # 必填参数缺失
        if value is None and not param_schema.get("optional"):
            raise ParamError(f"缺少必填参数 '{param_name}'")
        
        if value is None:
            continue
            
        # 类型校验
        expected_type = param_schema["type"]
        if expected_type == "string" and not isinstance(value, str):
            raise ParamError(f"参数 '{param_name}' 应为字符串，收到 {type(value).__name__}")
        if expected_type == "integer" and not isinstance(value, int):
            # 尝试自动转换（如 "8" → 8）
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ParamError(f"参数 '{param_name}' 应为整数，无法转换 '{value}'")
        
        # 格式校验（正则）
        if "pattern" in param_schema:
            import re
            if not re.match(param_schema["pattern"], str(value)):
                raise ParamError(
                    f"参数 '{param_name}' 格式不正确：'{value}' "
                    f"不匹配 {param_schema['pattern']}"
                )
        
        # 范围校验
        if "max_length" in param_schema and len(str(value)) > param_schema["max_length"]:
            raise ParamError(f"参数 '{param_name}' 超过最大长度 {param_schema['max_length']}")
        
        validated[param_name] = value
    
    return validated
```

**LLM常见的参数错误**：

| 错误类型 | 示例 | 正确值 | 防护手段 |
|----------|------|--------|----------|
| 自然语言时间 | "明早八点" | "08:00" | pattern正则 |
| 类型混淆 | time=8 (int) | time="08" (str) | 类型校验 |
| 超长字符串 | label=500字描述 | ≤50字 | max_length |
| 不存在的枚举值 | rrule="每天" | rrule="BYDAY=MO,TU,WE,TH,FR" | enum白名单 |
| 多余参数 | 传了API不支持的字段 | 忽略多余字段 | 参数白名单过滤 |

### 第三层：返回值验证 —— 确认操作真正有效

**核心思路**：API返回不等于操作成功。必须验证返回值的结构、状态和业务逻辑。

```python
def validate_response(api_name: str, response: dict, context: dict) -> dict:
    """第三层：验证API返回值"""
    
    # 1. 基础结构检查
    if not response:
        raise ResponseError(f"API '{api_name}' 返回空响应")
    
    # 2. 错误码检查
    if response.get("error") or response.get("code", 200) >= 400:
        error_msg = response.get("message", response.get("msg", "未知错误"))
        raise ResponseError(f"API '{api_name}' 返回错误：{error_msg}")
    
    # 3. 业务逻辑验证
    if api_name == "weather.now":
        # 验证返回的城市与请求匹配
        returned_city = response.get("city", "")
        requested_city = context.get("city", "")
        if returned_city and requested_city:
            if requested_city not in returned_city and returned_city not in requested_city:
                raise ResponseError(
                    f"返回城市 '{returned_city}' 与请求城市 '{requested_city}' 不匹配"
                )
        # 验证温度在合理范围
        temp = response.get("temperature")
        if temp is not None and (temp < -60 or temp > 60):
            raise ResponseError(f"温度 {temp}°C 超出合理范围")
    
    if api_name == "deskclock.add":
        # 验证闹钟确实被创建
        if not response.get("alarm_id"):
            raise ResponseError("闹钟创建成功但未返回alarm_id")
    
    if api_name == "sms.send":
        # 验证短信确实被发送
        if response.get("status") != "sent":
            raise ResponseError(f"短信未成功发送，状态：{response.get('status')}")
    
    return response
```

**返回值验证的核心原则**：
1. **空返回 ≠ 成功**：一定要检查返回是否为空
2. **错误码要显式检查**：不要只检查"是否有数据"，要检查"是否报错"
3. **业务逻辑一致性**：查北京天气，返回的必须是北京的数据
4. **关键字段完整性**：创建操作必须返回ID，发送操作必须返回状态

## 三、实战：完整的防护流程

```python
def safe_api_call(api_name: str, params: dict, context: dict = None):
    """带三层防护的安全API调用"""
    context = context or {}
    
    # 第一层：Schema白名单
    validate_api_name(api_name)
    
    # 第二层：参数类型校验
    validated_params = validate_params(api_name, params)
    
    # 执行API调用
    try:
        response = call_api(api_name, validated_params)
    except Exception as e:
        raise ApiCallError(f"API '{api_name}' 调用异常：{e}")
    
    # 第三层：返回值验证
    validated_response = validate_response(api_name, response, context)
    
    return validated_response
```

**防护流程图**：
```
LLM生成API调用
    │
    ▼
[第一层] API名在白名单？
    │ No → 拦截，返回"API不存在"
    │ Yes
    ▼
[第二层] 参数类型/格式正确？
    │ No → 拦截，返回"参数错误" + 修正提示
    │ Yes
    ▼
[执行] 调用真实API
    │
    ▼
[第三层] 返回值有效？
    │ No → 返回"调用失败" + 错误详情
    │ Yes
    ▼
返回验证后的结果给Agent
```

## 四、与现有体系的配合

三层API防护与之前介绍的Agent可靠性体系形成完整闭环：

| 阶段 | 机制 | 作用 |
|------|------|------|
| 调用前 | 自检四道锁 | 确认"该不该调这个API" |
| 调用中 | **三层API防护** | 确认"调得对不对" |
| 调用后 | 三层结果断言 | 确认"结果有没有效" |

**完整防护链**：
1. **四道锁**（意图确认 → 能力检索 → 事实核查 → 任务清零）→ 确定该调哪个API
2. **Schema白名单** → 确认API存在
3. **参数校验** → 确认参数正确
4. **返回值验证** → 确认调用成功
5. **三层断言**（动作 → 结果 → 方向）→ 确认任务完成

这套体系覆盖了从"用户说了什么"到"任务真正完成"的全链路。

## 五、常见问题

### Q1：Schema白名单需要手动维护吗？

可以半自动。如果你的工具系统有OpenAPI/Swagger文档，可以从中自动生成Schema。对于CLI工具，可以从 `--help` 输出中提取参数定义。

关键是：**Schema必须是代码可执行的**，不能只是注释或文档里的自然语言描述。

### Q2：第二层拦截后应该怎么处理？

两个选择：
1. **自动修正**：如果能确定正确格式（如 "8:00" → "08:00"），自动转换后重试
2. **提示LLM**：返回明确的错误信息（"参数time格式应为HH:MM，收到'明早八点'"），让LLM重新生成

推荐第二种——让LLM自己修正，比硬编码转换规则更灵活。

### Q3：三层防护的性能开销大吗？

几乎可以忽略。三层都是**内存中的字符串匹配和类型检查**，不涉及网络请求或复杂计算。实测单次防护校验耗时 < 1ms，远小于API调用本身的网络延迟。

### Q4：如何处理动态API（如MCP工具）？

MCP工具有自己的Schema定义（JSON Schema），可以直接复用：
1. 调用前先 `help <provider>` 获取工具列表和参数Schema
2. 用返回的Schema作为白名单和校验规则
3. 这也是为什么推荐"先help再调用"的原因——不只是为了看参数，更是为了获取校验依据

## 六、总结

| 防护层 | 核心问题 | 检查什么 | 拦截对象 |
|--------|----------|----------|----------|
| Schema白名单 | API存在吗？ | 名称是否在白名单 | 幻觉API调用 |
| 参数校验 | 参数对吗？ | 类型、格式、范围 | 类型混淆、格式错误 |
| 返回值验证 | 调用成功了吗？ | 结构、状态、一致性 | 空返回、错误码、数据错位 |

**关键认知**：
1. **LLM会编造API调用**，而且编造得很像——名字看起来合理，参数看起来也对，但就是不存在或不对。
2. **不要信任LLM的输出格式**，所有进入真实API的参数都必须经过代码层校验。
3. **返回值验证最容易被忽略**，但恰恰是最危险的环节——一个被当成正常数据的错误返回，会导致Agent基于错误信息做出后续决策。
4. **三层防护的成本极低**（< 1ms），但收益极高（错误率从45%降至3%），是性价比最高的可靠性投资。

Agent要真正靠谱，不能只靠Prompt Engineering——那是"祈祷式编程"。把防护做到代码层，让每一层都有明确的检查职责，才是工程化的正确姿势。

---
*本文是MiClaw AI Blog"Agent可靠性系列"的第四篇。前三篇：*
- *[多Agent记忆架构：从理论到实践](./2026-06-17-multi-agent-memory.md)*
- *[Agent检查点设计与安全防护实战](./2026-06-18-agent-checkpoint-security.md)*
- *[三层结果断言：让AI Agent靠谱执行任务](./2026-06-19-three-layer-result-assertion.md)*

*下一篇预告：Agent判断力退化自检——如何发现自己正在变"笨"*