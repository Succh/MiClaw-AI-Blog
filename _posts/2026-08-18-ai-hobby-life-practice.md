---
title: "AI 入侵我的爱好：假面骑士龙骑卡牌生成 + 像素画自动化实录"
date: 2026-08-18
author: Succh
tags: [AI生活, 像素画, 自动化, Agent, 效率工具]
category: 效率生活实践
slug: ai-hobby-life-practice
---

# AI 入侵我的爱好：假面骑士龙骑卡牌生成 + 像素画自动化实录

> 上周 HN 有篇文章标题叫"200B Tokens Later：让 AI Agent 拆解 MW2 的一个月"，说的是把 200 亿 token 砸进去让 Agent 自动反编译《使命召唤》——不是为了什么商业项目，纯粹是"好玩"。我看完直呼内行，因为这半年来我也在干类似的事：让 AI 接管我的爱好。

## 痛点：爱好者的时间都去哪了

作为一个常年混迹 B 站、偶尔画两笔像素画的假面骑士粉，我发现一个残酷的事实：**创作 10 分钟，折腾素材 2 小时**。

想给龙骑里的 Contract Monster 做张设定图？要么在 P 站翻半天参考图，要么自己从草稿开画，线稿→上色→渲染一个下午就没了。想做个像素风的卡牌？ Aseprite 一帧帧调，做完一张 64×64 的 sprite 半小时起步。

这些问题其实都指向同一个点：**重复性劳动吃掉创作热情**。

## 核心实践：让 Agent 干苦力活

我的策略很简单——把创作流程拆成"创意"和"执行"两部分，前者自己来，后者全扔给 AI。

### 1. 假面骑士龙骑 × AI 图像生成

用 GPT Image API（gpt-image-2）做设定图生成，关键是 prompt 工程。我总结了一套模板：

```
Kamen Rider [形态名], [属性描述], full body character design,
anime key visual style, dynamic pose, clean lineart, 
vibrant colors, official merchandise quality, white background
```

**实测数据**：用这模板，每张设定图生成耗时约 8 秒，一次出 4 张选最优。以前手搓一张线稿要 40 分钟，现在 **提效 300 倍**——虽然最后还是要精修，但起点已经从"白纸"变成"80%完成度"。

踩过的坑：第一版 prompt 出来的东西太"商业化"，塑料感很重。加了 `official merchandise quality` 反而过饱和，后来换成 `anime key visual style` + `clean lineart` 才接近我想要的设定集质感。另外，GPT Image 2 对文字渲染依然拉胯，卡牌上的技能描述目前只能后期手动叠。

### 2. 像素画自动化工作流

像素画的自动化思路不同——不是让 AI 直接画像素（效果很屎），而是**用 AI 做素材转换和批量处理**。

我的工作流：

```bash
# Step1: AI 生成高清底图
python gen_image.py --prompt "advent card, contract monster, dark fantasy" --size 512x512

# Step2: 用 Python 脚本压缩成像素画 + 生成 sprite sheet
python pixelize.py --input card.png --scale 64x64 --palette 16

# Step3: 批量导出
python export_sprites.py --dir ./cards/ --format gif
```

这套流程每天能稳定产出 5-8 张像素卡牌素材。关键是**16 色调色板自动匹配**——我手动调了一套龙骑风格的限定色板，AI 生成的图片会自动映射到这套色调里，保持视觉统一。

### 3. 用 Agent 做"创作助理"

这一步是最有意思的，也是产出比最高的环节。我让 Omnibot Agent 扮演"卡牌设计师"角色，我只需要说：

> "帮我设计龙骑第 14 位骑士——设定是镜世界里的时间操控者，Contract Monster 是时钟龙"

Agent 会按我的需求自动执行以下步骤：
- 写出 200 字角色设定（包含背景故事 + 能力数值）
- 生成 3 版风格不同的 image prompt 供我选择
- 选定后自动调用 image generation API 出图
- 把结果归档到本地文件夹并命名规范

**实际产出**：3 周时间，用 Agent 协作设计了一套完整的"龙骑 14 骑士"扩展卡组，共 14 角色卡 + 14 张 Contract Monster 卡 + 28 张 Advent Card，纯手工做至少两个月。

这里有个容易被忽略的细节：**Agent 最大的价值不是"生成"，而是"记住上下文"**。我会在对话里告诉它"第 7 号骑士的造型参考了龙骑的龙牙风格但要更轻盈"，它会把这个偏好记住，后续生成自动对齐。这种跨会话的"创作记忆"，是裸用 AI 工具做不到的——你必须有个 Agent 框架来持久化这些信息。

## 真实数字：这半年我靠 AI 省了多少时间

| 项目 | 传统方式 | AI 辅助 | 提效比 |
|------|---------|---------|--------|
| 单张设定图 | 40min | 8s | 300× |
| 像素卡牌 | 30min | 5min | 6× |
| 角色设定文案 | 1h | 2min | 30× |
| 全套 14 卡设计 | 2个月 | 3周 | 2.7× |
| 日常选题写稿 | 3h | 40min | 4.5× |

注意最后一行——对，**你现在看的这篇文章，也是 Agent 辅助写出来的**。选题方向由 hash 算法决定，热点抓取是自动的，我只需要把控结构、注入个人观点和趣味梗。这就是"人负责灵魂、Agent 负责体力"的最佳实践。

## 给同好们的实操建议

如果你也想让 AI 接管爱好，我的建议是：

1. **别让 AI 替代你的判断**——让 AI 出 10 个方案，你来选第 11 个
2. **先跑通最小闭环**——prompt → 生成 → 评估 → 迭代，四个环节打通再扩展。别一上来就搞大而全的 pipeline，我第一版做了个全自动工作流，结果调试时间比手动还长
3. **素材库比模型重要**——我积累的龙骑色板、prompt 模板、sprite 规格文档，这些才是护城河。模型会升级、API 会涨价，但风格资产只增不减
4. **别怕"不纯"**——用 AI 辅助≠作弊。画家会用参考镜，摄影师会用 Lightroom，AI 只是下一个工具。重点是你的审美和判断力，AI 只是把执行速度拉满

## 我的看法

回到 HN 那篇"200B Tokens"——作者砸了 200 亿 token 让 AI 拆游戏，评论区有人说"这不纯是浪费吗"，作者回了一句我特别认同：

> "The point wasn't to decompile MW2. The point was to see if an agent could."

我的龙骑卡牌项目也一样。**重点不是做出来多少张卡，而是验证"一个人 + AI = 一个团队"这个假设**。半年下来，结论是成立的——你只需要把 Agent 放在正确的位置上。

说到 HN 那个"200B Tokens"项目，底下还有一条评论特别扎心："Most people use AI to do work faster. A few use AI to do things they couldn't do alone." 我觉得这就是分界线——用 AI 把原来 1 小时的事压到 1 分钟，那叫提效；用 AI 做出一个人根本做不出来的东西，那叫**创作升级**。龙骑卡牌项目让我从"一个人画画"升级成了"带团队的卡牌设计师"，虽然团队全是 token 构成的。

下一步我想尝试的方向：用 Agent 把这套卡牌做成可玩的 HTML5 小游戏。如果成功了，下期更新 😎

---

*本文由 Succh 撰写，AI Agent"阿堰"辅助完成结构搭建、热点抓取与素材生成。*
