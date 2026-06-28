---
name: zctk-ai-science-agent
description: Use when building or modifying the 智创探客 AI science education agent for middle school students — includes agent YML configs, RAG knowledge base, Python tool scripts, and 桂教通 platform integration
---

# 智创探客 · AI 科普教育智能体

## Overview

Multi-agent AI science education system for middle school students (12-15 years old). 4 specialized agents + 6-theme RAG knowledge base + 2 Python tools. Deployable to 桂教通/Dify platform.

## When to Use

- Adding or modifying agent YML configurations
- Updating knowledge base content for middle school AI education
- Running case collection or knowledge base build scripts
- Fixing HTTP header encoding issues in low-code platform pages
- Preparing competition materials for 桂教通 platform

## Project Structure

```
zctk-skills/
├── SKILL.md                           # This file
├── README.md                          # Full documentation
├── agents/                            # 4 Agent YML configs
│   ├── agent-01-科普向导.yml          # Chat agent: AI Q&A
│   ├── agent-02-伦理剧场.yml          # Workflow agent: ethics scenarios
│   ├── agent-03-手抄报工坊.yml        # Workflow agent: poster generation
│   └── agent-04-课件生成器.yml        # Workflow agent: courseware generation
├── knowledge-base/                    # 6-theme RAG knowledge base
│   ├── kb-01-AI基础原理.md            # ML/DL/LLM basics
│   ├── kb-02-生活AI应用.md            # Real-world AI applications
│   ├── kb-03-数字隐私保护.md          # Digital privacy
│   ├── kb-04-AI伦理.md                # AI ethics
│   ├── kb-05-算法陷阱.md              # Algorithm traps
│   └── kb-06-青少年科创案例.md        # 7 real youth maker cases
├── scripts/                           # Python tools
│   ├── collect_cases.py               # Case collection & cleaning
│   ├── build_knowledge_base.py        # KB chunking & stats
│   └── requirements.txt
└── output/                            # Generated artifacts
```

## Agent Architecture

| # | Agent | Type | Trigger | Output |
|---|-------|------|---------|--------|
| 1 | 科普向导 | Chat | Student asks AI question | Plain text (<250 chars) |
| 2 | 伦理剧场 | Workflow | Student picks scenario | Branching ethics discussion |
| 3 | 手抄报工坊 | Workflow | Student enters topic | JSON poster content |
| 4 | 课件生成器 | Workflow | Teacher enters topic+grade | JSON courseware outline |

## Key Patterns

### HTTP Header Safety (Critical Fix)

Low-code platform env vars may contain Chinese characters. HTTP headers MUST be ASCII-only or fetch() throws:

```javascript
// Add BEFORE any fetch() call
const safeH = (v) => /^[\x00-\x7F]*$/.test(v) ? v : encodeURIComponent(v)

// Always wrap CONFIG values in headers
headers: { 'X-Tenant-Id': safeH(CONFIG.TENANT_ID) }
Authorization: `Bearer ${safeH(CONFIG.AGENT_API_KEY)}`
```

Files requiring this fix:
- `platform-pages/02-06.vue` — Standalone Vue SFC pages
- `1782620894517/form/form_zctk02-06.json` — Platform form JSON exports
- `zctk-lowcode/src/utils/request.ts` — Vite project request utility
- `zctk-lowcode/src/api/agent.ts` — Agent API calls

### Knowledge Base Operations

```bash
# Statistics report
python scripts/build_knowledge_base.py --input knowledge-base/ --stats

# Build JSONL chunks for vector DB import
python scripts/build_knowledge_base.py --input knowledge-base/ --output output/kb_chunks.jsonl
```

### Case Collection

```bash
# Built-in 7 cases (no network needed)
python scripts/collect_cases.py --source builtin --output output/cases.json

# URL batch collection (needs pip install -r requirements.txt)
python scripts/collect_cases.py --source urls-file --urls-file urls.txt --output output/cases.json
```

## Platform Import Steps

1. Create agent on 桂教通 → Import YML from `agents/`
2. Upload `knowledge-base/*.md` to platform knowledge base
3. Update `dataset_ids` in each agent to match platform KB IDs
4. Update `model.name` / `model.provider` to platform available models
5. Enable external sharing → copy share URL for Web integration

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Agent import fails: model mismatch | Update model/provider in YML to platform's options |
| fetch() "non ISO-8859-1 code point" | Apply safeH() to all CONFIG header values |
| Knowledge base returns nothing | Verify dataset_ids match platform's actual KB IDs |
| YML parse error on import | Check JSON — no trailing commas, valid escape sequences |

## Related Projects

- `E:\AIProgram\1782620894517\` — Low-code platform app export package
- `E:\AIProgram\zctk-lowcode\` — Vue3/Vite Web teaching tool
- `E:\AIProgram\platform-pages\` — Standalone Vue SFC pages
