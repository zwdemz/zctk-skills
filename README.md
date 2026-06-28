# 智创探客 · Skills 智能体

> 面向初中生的 AI 科普教育智能体集群，包含 4 个专业 Agent + 6 大知识库 + Python 工具脚本。
> 适配桂教通智能体创作平台，YML 配置可直接导入使用。

---

## 一、项目简介

智创探客是面向 12-15 岁初中生的人工智能科普教育智能体系统，兼顾学生自主学习与教师教学支撑。

**核心价值**：普及 AI 基础通识 → 提升数字素养 → 引导正确数字伦理观。

---

## 二、目录结构

```
zctk-skills-agent/
├── agents/                          # 智能体 YML 配置
│   ├── agent-01-科普向导.yml        # 对话 Agent：趣味 AI 科普问答
│   ├── agent-02-伦理剧场.yml        # 工作流 Agent：伦理两难情景思辨
│   ├── agent-03-手抄报工坊.yml      # 工作流 Agent：手抄报 JSON 生成
│   └── agent-04-课件生成器.yml      # 工作流 Agent：班会课件大纲生成
├── knowledge-base/                  # RAG 知识库（Markdown）
│   ├── kb-01-AI基础原理.md          # 机器学习/深度学习/大模型通俗版
│   ├── kb-02-生活AI应用.md          # 推荐/语音助手/自动驾驶/医疗/教育
│   ├── kb-03-数字隐私保护.md        # 隐私风险/防护/青少年注意事项
│   ├── kb-04-AI伦理.md              # 算法偏见/责任/学术诚信/版权
│   ├── kb-05-算法陷阱.md            # 信息茧房/深度伪造/钓鱼/上瘾
│   └── kb-06-青少年科创案例.md      # 7个真实案例 + 实验项目
├── scripts/                         # Python 工具
│   ├── collect_cases.py             # 案例采集与清洗
│   ├── build_knowledge_base.py      # 知识库分块构建
│   └── requirements.txt
└── README.md
```

---

## 三、四个 Agent

| # | Agent | 类型 | 功能 |
|---|-------|------|------|
| ① | 探客·AI科普向导 | 对话 | AI 通识问答，通俗化讲解，RAG 检索 |
| ② | 思辨·伦理剧场 | 工作流 | 两难情景生成 + 立场分支追问 |
| ③ | 创作·手抄报工坊 | 工作流 | 输入主题 → JSON 手抄报内容 |
| ④ | 备课·课件生成器 | 工作流 | 输入主题 → 5页课件大纲 + 配图提示词 |

---

## 四、知识库

| 主题 | 适合年级 | 内容量 |
|------|---------|--------|
| AI 基础原理 | 初一~初三 | 8 章节 |
| 生活 AI 应用 | 初一~初三 | 8 场景 |
| 数字隐私保护 | 初一~初三 | 6 章节 |
| AI 伦理 | 初二~初三 | 8 议题 |
| 算法陷阱 | 初二~初三 | 7 警示 |
| 青少年科创案例 | 初一~初三 | 7 案例 + 3 实验 |

---

## 五、工具使用

### 案例采集

```bash
cd scripts
# 导出内置案例
python collect_cases.py --source builtin --output ../output/cases.json
# 也可导出 Markdown
python collect_cases.py --source builtin --output ../output/cases.json --output-md ../output/cases_extra.md
# 从URL采集（需联网+依赖）
pip install -r requirements.txt
python collect_cases.py --source urls-file --urls-file urls.txt --output ../output/cases.json
```

### 知识库构建

```bash
cd scripts
# 统计报告
python build_knowledge_base.py --input ../knowledge-base/ --stats
# 分块输出 JSONL
python build_knowledge_base.py --input ../knowledge-base/ --output ../output/kb_chunks.jsonl
# 纯文本合并
python build_knowledge_base.py --input ../knowledge-base/ --output ../output/kb_chunks.jsonl --output-txt ../output/kb_flat.txt
```

---

## 六、导入桂教通平台

1. 访问 [桂教通智能体创作平台](https://www.gx.smartedu.cn/portal)
2. 智能体创作 → 导入 → 选择 `agents/*.yml`
3. 知识库模块 → 上传 `knowledge-base/*.md`
4. 关联：Agent 的 dataset_ids 改为平台知识库的实际 ID
5. 配置：model.name / model.provider 改为平台可用模型
6. 开启对外分享 → 获取链接供 Web 教具调用

---

## 七、交付清单

- [x] 4 个 Agent YML（可直接导入）
- [x] 6 大主题知识库（含 7 个真实科创案例）
- [x] Python 采集工具（内置案例 + URL 采集）
- [x] Python 知识库构建（分块 + 统计 + 导出）
- [x] README 说明文档

---

*更新：2026-06-28*
