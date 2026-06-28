"""
知识库批量构建与分块工具
========================
功能：
1. 将知识库Markdown文件分块（chunking），适配RAG向量检索
2. 按Markdown标题层级自动拆分章节
3. 输出JSONL格式（每行一个chunk，可直接导入向量数据库）
4. 支持导出纯文本合并（可直接粘贴到平台知识库模块）
5. 生成知识库统计报告

使用方式：
    # 构建知识库（Markdown -> JSONL chunks）
    python build_knowledge_base.py --input ../knowledge-base/ --output ../output/kb_chunks.jsonl

    # 生成统计报告
    python build_knowledge_base.py --input ../knowledge-base/ --stats

    # 同时导出纯文本
    python build_knowledge_base.py --input ../knowledge-base/ --output ../output/kb_chunks.jsonl --output-txt ../output/kb_flat.txt

    # 自定义chunk大小
    python build_knowledge_base.py --input ../knowledge-base/ --max-chunk-size 500

依赖：无（纯Python标准库）
"""

import json
import re
import argparse
import time
from pathlib import Path


# ============================================================
# 全局配置
# ============================================================

MAX_CHUNK_SIZE = 800     # 每个chunk最大字符数
CHUNK_OVERLAP = 100      # 块间重叠字符数

# 知识库文件元数据映射
KB_THEMES = {
    "kb-01-AI基础原理.md": {
        "theme_id": "ai_basics", "theme_name": "AI基础原理",
        "grade_level": "all",
        "keywords": ["人工智能","机器学习","深度学习","神经网络","大语言模型","计算机视觉","语音识别"]
    },
    "kb-02-生活AI应用.md": {
        "theme_id": "ai_applications", "theme_name": "生活AI应用",
        "grade_level": "all",
        "keywords": ["推荐算法","语音助手","人脸识别","自动驾驶","AI医疗","AI教育","AI娱乐","AI环保"]
    },
    "kb-03-数字隐私保护.md": {
        "theme_id": "privacy", "theme_name": "数字隐私保护",
        "grade_level": "all",
        "keywords": ["隐私","个人信息","人脸泄露","数据安全","知情同意","青少年保护"]
    },
    "kb-04-AI伦理.md": {
        "theme_id": "ai_ethics", "theme_name": "AI伦理",
        "grade_level": "初二-初三",
        "keywords": ["伦理","算法偏见","责任","就业","学术诚信","版权","AI武器"]
    },
    "kb-05-算法陷阱.md": {
        "theme_id": "algorithm_traps", "theme_name": "算法陷阱",
        "grade_level": "初二-初三",
        "keywords": ["信息茧房","深度伪造","Deepfake","网络钓鱼","算法上瘾","游戏沉迷"]
    },
    "kb-06-青少年科创案例.md": {
        "theme_id": "maker_cases", "theme_name": "青少年科创案例",
        "grade_level": "all",
        "keywords": ["科创","案例","Arduino","Micro:bit","Teachable Machine","比赛","获奖"]
    },
}


# ============================================================
# Markdown解析
# ============================================================

def parse_markdown_sections(content: str) -> list[dict]:
    """按 ## 和 ### 标题将内容拆分为章节"""
    sections = []
    pattern = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(content))

    if not matches:
        sections.append({
            "heading": "", "level": 0,
            "content": content.strip()
        })
        return sections

    for i, match in enumerate(matches):
        heading = match.group(2).strip()
        level = len(match.group(1))  # 2 or 3
        start = match.end() + 1
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections.append({
            "heading": heading,
            "level": level,
            "content": content[start:end].strip()
        })
    return sections


def chunk_text(text: str, max_size: int = MAX_CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """智能分块：优先在段落边界断开，超出max_size时按句子分割"""
    if len(text) <= max_size:
        return [text] if text.strip() else []

    chunks = []
    paragraphs = text.split("\n\n")
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 单段落超长 -> 按句子分割
        if len(para) > max_size:
            sentences = re.split(r"(?<=[。！？.!?])\s*", para)
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                if len(current) + len(sent) + 1 <= max_size:
                    current += sent + " "
                else:
                    if current.strip():
                        chunks.append(current.strip())
                    overlap_text = current[-overlap:] if overlap > 0 and len(current) > overlap else ""
                    current = (overlap_text + " " + sent + " ").lstrip()
            continue

        # 正常段落拼接
        if len(current) + len(para) + 1 <= max_size:
            current += para + "\n\n"
        else:
            if current.strip():
                chunks.append(current.strip())
            overlap_text = current[-overlap:] if overlap > 0 and len(current) > overlap else ""
            current = (overlap_text + "\n\n" + para + "\n\n").lstrip()

    if current.strip():
        chunks.append(current.strip())
    return chunks


# ============================================================
# 构建与导出
# ============================================================

def build_chunks(md_dir: str, output_path: str, max_chunk_size: int = MAX_CHUNK_SIZE):
    """构建知识库分块，输出JSONL"""
    md_path = Path(md_dir)
    if not md_path.exists():
        print(f"[ERROR] 目录不存在: {md_dir}")
        return

    md_files = sorted(md_path.glob("kb-*.md"))
    if not md_files:
        print(f"[ERROR] 无kb-*.md文件: {md_dir}")
        return

    all_chunks = []
    chunk_id = 0

    for md_file in md_files:
        theme = KB_THEMES.get(md_file.name, {})
        content = md_file.read_text(encoding="utf-8")
        sections = parse_markdown_sections(content)

        for section in sections:
            text_chunks = chunk_text(section["content"], max_size=max_chunk_size)
            for i, chunk_content in enumerate(text_chunks):
                chunk_id += 1
                all_chunks.append({
                    "chunk_id": f"chunk_{chunk_id:04d}",
                    "source_file": md_file.name,
                    "theme_id": theme.get("theme_id", ""),
                    "theme_name": theme.get("theme_name", ""),
                    "grade_level": theme.get("grade_level", "all"),
                    "section_heading": section["heading"],
                    "chunk_index": i,
                    "content": chunk_content,
                    "char_count": len(chunk_content),
                    "keywords": theme.get("keywords", []),
                })

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    total_chars = sum(c["char_count"] for c in all_chunks)
    avg = total_chars / len(all_chunks) if all_chunks else 0
    print(f"[DONE] 知识库分块完成: {len(md_files)}文件 -> {len(all_chunks)}块, "
          f"总{total_chars:,}字符, 均{avg:.0f}字符/块")
    print(f"  输出: {output_path}")


def export_flat_text(md_dir: str, output_path: str):
    """合并所有知识库为纯文本（可直接粘贴到平台知识库）"""
    md_path = Path(md_dir)
    md_files = sorted(md_path.glob("kb-*.md"))

    blocks = [
        f"# 智创探客·青少年AI科普知识库",
        f"# 导出: {time.strftime('%Y-%m-%d %H:%M:%S')} | 主题数: {len(md_files)}",
        "=" * 60, ""
    ]
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        # 跳过第一行（源文件标题），保留内容
        lines = content.split("\n")
        body_start = next((i for i, l in enumerate(lines)
                          if l.strip() and not l.startswith("# ") and not l.startswith(">")), 1)
        blocks.append("\n".join(lines[body_start:]))
        blocks.extend(["", "---", ""])

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))
    print(f"[DONE] 纯文本导出 -> {output_path}")


def print_stats(md_dir: str):
    """打印知识库统计"""
    md_path = Path(md_dir)
    md_files = sorted(md_path.glob("kb-*.md"))

    print("\n" + "=" * 60)
    print("  智创探客·知识库统计报告")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}  |  主题: {len(md_files)} 个")
    print("=" * 60)

    total_chars = 0
    for f in md_files:
        content = f.read_text(encoding="utf-8")
        chars = len(content)
        total_chars += chars
        h2 = len(re.findall(r"^## ", content, re.MULTILINE))
        h3 = len(re.findall(r"^### ", content, re.MULTILINE))
        theme = KB_THEMES.get(f.name, {})
        est_tokens = int(chars / 1.5)
        print(f"  {f.name}: {theme.get('theme_name','?')} | "
              f"{chars:,}字 | {h2+h3}章 | ~{est_tokens:,}tokens")
    print(f"  总计: {total_chars:,}字 | ~{int(total_chars/1.5):,}tokens")
    print("=" * 60 + "\n")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="知识库构建与分块工具")
    parser.add_argument("--input", default="../knowledge-base/", help="知识库目录")
    parser.add_argument("--output", default="../output/kb_chunks.jsonl", help="JSONL输出")
    parser.add_argument("--output-txt", default="", help="纯文本输出")
    parser.add_argument("--stats", action="store_true", help="仅打印统计")
    parser.add_argument("--max-chunk-size", type=int, default=MAX_CHUNK_SIZE,
                        help=f"最大chunk字符数(默认{MAX_CHUNK_SIZE})")

    args = parser.parse_args()

    if args.stats:
        print_stats(args.input)
    else:
        build_chunks(args.input, args.output, max_chunk_size=args.max_chunk_size)
        if args.output_txt:
            export_flat_text(args.input, args.output_txt)


if __name__ == "__main__":
    main()
