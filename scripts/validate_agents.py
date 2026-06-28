"""
Agent YML 结构校验工具 — 导入平台前本地验证
"""
import re
import sys
from pathlib import Path

AGENTS_DIR = "../agents"

def check_agent(path: str) -> list[str]:
    errors = []
    name = Path(path).name
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        return [f"[FATAL] {name}: 文件读取失败 — {e}"]

    # 顶层结构检查
    for kw in ["app:", "kind:", "version:", "workflow:"]:
        if kw not in text:
            errors.append(f"[MISS] {name}: 缺少 '{kw}'")
    if 'mode:' not in text:
        errors.append(f"[MISS] {name}: app.mode 未定义")

    # 工作流特征检查
    if 'features:' not in text:
        errors.append(f"[WARN] {name}: features 未配置")
    if 'opening_statement:' not in text:
        errors.append(f"[WARN] {name}: 缺少开场白")
    if 'retriever_resource:' not in text:
        errors.append(f"[WARN] {name}: retriever_resource 未配置")
    if 'sensitive_word_avoidance:' not in text:
        errors.append(f"[WARN] {name}: sensitive_word_avoidance 未配置")

    # 图结构检查
    if 'edges:' not in text or 'nodes:' not in text:
        errors.append(f"[FATAL] {name}: graph缺少 edges/nodes")
        return errors

    # 提取所有节点 ID
    node_ids = set(re.findall(r"\n\s+id:\s+(\S+)", text))
    if not node_ids:
        errors.append(f"[FATAL] {name}: 未找到任何节点")

    # 提取边引用的 source/target
    edge_refs = set()
    for m in re.finditer(r"^\s{6}source:\s+(\S+)|^\s{6}target:\s+(\S+)", text, re.MULTILINE):
        ref = m.group(1) or m.group(2)
        edge_refs.add(ref)

    orphans = edge_refs - node_ids
    for o in orphans:
        errors.append(f"[ORPHAN] {name}: edge引用 '{o}' 不在节点列表中")

    # LLM 模型配置检查
    if "name: DeepSeek-V3" in text or "name: Doubao" in text:
        pass  # 有模型配置
    elif 'provider:' in text:
        pass
    else:
        errors.append(f"[CONFIG] {name}: 未检测到 LLM 模型配置")

    # 知识检索 dataset_ids 提示
    if 'knowledge-retrieval' in text and 'dataset_ids:' in text:
        # 检查是否有非空 dataset_id
        ds = re.findall(r"dataset_ids:\s*\[([^\]]*)\]", text)
        for d in ds:
            if not d.strip() or d.strip() == '':
                errors.append(f"[TODO] {name}: dataset_ids 为空，导入后需填写")

    return errors

def main():
    agents_path = (Path(__file__).parent / AGENTS_DIR).resolve()
    if not agents_path.exists():
        print(f"[ERROR] directory not found: {agents_path}")
        sys.exit(1)

    yml_files = sorted(agents_path.glob("agent-*.yml"))
    if not yml_files:
        print(f"[ERROR] no agent files found")
        sys.exit(1)

    fatal = 0
    warn = 0
    for f in yml_files:
        errs = check_agent(str(f))
        tag = "OK" if not errs else f"{len(errs)} issue(s)"
        print(f"  {f.name}: {tag}")
        for e in errs:
            if e.startswith("[TODO]") or e.startswith("[WARN]"):
                print(f"    [WARN] {e}")
                warn += 1
            else:
                print(f"    [ERR]  {e}")
                fatal += 1

    print(f"\n  Files: {len(yml_files)} | Errors: {fatal} | Warnings: {warn}")
    sys.exit(1 if fatal > 0 else 0)

if __name__ == "__main__":
    main()
