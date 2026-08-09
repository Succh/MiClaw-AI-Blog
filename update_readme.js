let f = require('fs').readFileSync('README.md', 'utf8');
f = f.replace('Posts-97-blue', 'Posts-98-blue');
f = f.replace('**97** | **5** | **30**', '**98** | **5** | **31**');
f = f.replace('Agent技术与架构 | 63', 'Agent技术与架构 | 64');
let lines = f.split('\n');
let idx = lines.findIndex(l => l.includes('Claude Code'));
if (idx >= 0) lines.splice(idx, 0, '| 08-09 | [AI Agent的错误记忆：为什么你的Agent总在同一个坑里摔跤？](articles/2026-08-09-agent-error-memory.md) |');
require('fs').writeFileSync('README.md', lines.join('\n'));
print('README updated');
