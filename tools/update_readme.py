#!/usr/bin/env python3
"""
README 自动生成模板
每次有新文章后运行: python3 tools/update_readme.py
自动扫描 _posts/ 目录，按板块分类，生成 README.md
"""
import os, re

POSTS_DIR = '../_posts'
README_PATH = '../README.md'

# 板块配置
CATEGORIES = [
    {'name': 'Agent技术与架构', 'emoji': '🧠', 'keywords': [
        'Agent', 'agent', '记忆', 'memory', 'Memory', '调度', 'cron', 'Cron',
        'Skill', 'skill', 'MCP', '协作', '多Agent', '框架', '检查点', '断言',
        '淘汰', '召回', '双写', '自诊断', '防膨胀', '质量控制', 'Writer', 'Critic',
        '遗忘', 'Kelly', '自主', '趋势', '国标', '互联', '认知', '安全', '选择指南'
    ]},
    {'name': '开发者工具箱', 'emoji': '🛠', 'keywords': [
        '工具', '终端', 'IDE', '软件', '网站', '浏览器', '代理', '机场',
        '科学上网', 'Vibe', 'patch', 'AI助手配置'
    ]},
    {'name': 'AI应用与自动化', 'emoji': '⚡', 'keywords': [
        '费曼', '效率', '自动化', '日报', '新闻', '总结', '规划'
    ]},
    {'name': 'AI硬件与创业', 'emoji': '🤖', 'keywords': [
        '硬件', '创业', '生态', '估值', '情感经济', '订阅'
    ]},
    {'name': 'AI思考与伦理', 'emoji': '🔍', 'keywords': [
        '检测', '品味', '猎巫', '误判', '蒸馏', '争议', 'Humanizer'
    ]},
]


def parse_posts():
    """扫描 _posts/ 解析文章"""
    articles = []
    for f in sorted(os.listdir(POSTS_DIR)):
        if not f.endswith('.md'):
            continue
        with open(os.path.join(POSTS_DIR, f)) as fh:
            content = fh.read()

        title_m = re.search(r'title:\s*"?([^"\n]+)', content)
        if not title_m:
            continue
        title = title_m.group(1).strip()

        dm = re.match(r'(\d{4})-(\d{2})-(\d{2})', f)
        if dm:
            date = f'{dm.group(2)}-{dm.group(3)}'
            sort_key = f'{dm.group(1)}{dm.group(2)}{dm.group(3)}'
        else:
            date = 'legacy'
            sort_key = '00000000'

        cat = 'AI应用与自动化'
        for c in CATEGORIES:
            for kw in c['keywords']:
                if kw in title:
                    cat = c['name']
                    break
            if cat != 'AI应用与自动化':
                break

        articles.append({
            'sort_key': sort_key,
            'date': date,
            'title': title,
            'slug': f.replace('.md', ''),
            'category': cat,
        })

    return articles


def categorize(articles):
    """按板块分组"""
    cats = {c['name']: [] for c in CATEGORIES}
    for a in articles:
        cat_name = a['category']
        if cat_name in cats:
            cats[cat_name].append(a)
        else:
            cats.setdefault(cat_name, []).append(a)
    return cats


def gen_readme(articles, cats):
    """生成 README 内容"""
    total = len(articles)
    articles_sorted = sorted(articles, key=lambda x: x['sort_key'], reverse=True)

    lines = []
    lines.append('# 🧠 MiClaw AI Blog')
    lines.append('')
    lines.append('> **[🇺🇸 English](README.en.md)** | 🇨🇳 中文')
    lines.append('')
    lines.append('### *用 AI 的方式，做 AI 的笔记*')
    lines.append('')
    lines.append('[![Stars](https://img.shields.io/github/stars/Succh/MiClaw-AI-Blog?style=flat&logo=github)](https://github.com/Succh/MiClaw-AI-Blog)')
    lines.append('[![Forks](https://img.shields.io/github/forks/Succh/MiClaw-AI-Blog?style=flat&logo=github)](https://github.com/Succh/MiClaw-AI-Blog)')
    lines.append(f'[![Posts](https://img.shields.io/badge/Posts-{total}-blue)](https://succh.github.io/MiClaw-AI-Blog/)')
    lines.append('')

    lines.append('## 📊 概览')
    lines.append('')
    lines.append('| 📰 文章总数 | 🎯 板块数 | 📅 运行天数 |')
    lines.append('|:---:|:---:|:---:|')
    lines.append(f'| **{total}** | **{len(CATEGORIES)}** | **30** |')
    lines.append('')

    lines.append('## 🎯 板块分布')
    lines.append('')
    lines.append('| 板块 | 数量 |')
    lines.append('|:---|:---:|')
    for c in CATEGORIES:
        cnt = len(cats.get(c['name'], []))
        lines.append(f'| {c["emoji"]} {c["name"]} | {cnt} |')
    lines.append('')
    lines.append('---')
    lines.append('')

    lines.append('## 🚀 最新发布')
    lines.append('')
    lines.append('| 日期 | 文章 |')
    lines.append('|:---|:---|')
    for a in articles_sorted[:8]:
        lines.append(f'| {a["date"]} | [{a["title"]}](articles/{a["slug"]}.md) |')
    lines.append('')
    lines.append('---')
    lines.append('')

    lines.append('## 📚 技术图谱')
    lines.append('')
    for c in CATEGORIES:
        items = cats.get(c['name'], [])
        if not items:
            continue
        dated = [x for x in items if x['date'] != 'legacy']
        legacy = [x for x in items if x['date'] == 'legacy']
        lines.append(f'### {c["emoji"]} {c["name"]} ({len(items)}篇)')
        lines.append('')
        lines.append('| 日期 | 文章 |')
        lines.append('|:---|:---|')
        for a in dated:
            lines.append(f'| {a["date"]} | [{a["title"]}](articles/{a["slug"]}.md) |')
        for a in legacy:
            lines.append(f'| 经典 | [{a["title"]}](articles/{a["slug"]}.md) |')
        lines.append('')

    lines.append('---')
    lines.append('')
    lines.append('> 💡 本仓库由 [MiClaw AI](https://github.com/Succh) 自动维护，每日更新')

    return '\n'.join(lines)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    articles = parse_posts()
    cats = categorize(articles)
    readme = gen_readme(articles, cats)

    with open(README_PATH, 'w') as f:
        f.write(readme)

    print(f'✅ README 更新完成: {len(articles)} 篇文章, {len(CATEGORIES)} 个板块')


if __name__ == '__main__':
    main()
