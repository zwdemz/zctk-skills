"""
青少年AI科创案例采集与清洗工具
==============================
功能：
1. 内置7个真实青少年AI科创案例（来自公开报道）
2. 导出为标准化JSON供知识库使用
3. 可选导出Markdown格式
4. 支持从URL列表批量采集（需安装requests/bs4）

使用方式：
    # 导出内置案例为JSON
    python collect_cases.py --source builtin --output ../knowledge-base/cases.json

    # 同时导出Markdown
    python collect_cases.py --source builtin --output ../output/cases.json --output-md ../knowledge-base/cases_extra.md

    # 从URL列表采集（需联网）
    python collect_cases.py --source urls-file --urls-file urls.txt --output cases.json

依赖：pip install requests beautifulsoup4 lxml（仅URL采集模式需要）
"""

import json
import re
import sys
import argparse
import time
from pathlib import Path
from typing import Optional

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

# ============================================================
# 配置
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

REQUEST_TIMEOUT = 15
REQUEST_DELAY = 1.5

# ============================================================
# 内置案例库（7个公开报道案例）
# ============================================================

BUILTIN_CASES = [
    {
        "title": "AI自动分类回收桶",
        "source_name": "香港万钧伯裘书院",
        "grade": "初二",
        "category": "视觉识别",
        "award": "青协香港学生科学比赛初中组季军",
        "tech_stack": ["机器学习", "图像识别", "Micro:bit", "舵机"],
        "materials": ["摄像头", "舵机", "垃圾桶", "Micro:bit"],
        "description": "利用AI视觉识别建立垃圾分类模型，每种回收物拍摄近500张照片训练，Micro:bit控制伺服马达转动垃圾桶盖自动导向对应分类格，识别准确率70%以上。适合用Teachable Machine入门实现。",
        "difficulty": "⭐⭐⭐",
        "tags": ["垃圾分类", "环保", "视觉识别", "Micro:bit"]
    },
    {
        "title": "便携式手机脉诊仪《巧中医》",
        "source_name": "信阳市胜利路学校",
        "grade": "初三",
        "category": "智能硬件",
        "award": "NOC智能物联网创新设计一等奖",
        "tech_stack": ["传感器", "物联网", "Arduino", "手机APP"],
        "materials": ["心率传感器", "Arduino", "蓝牙模块", "手机"],
        "description": "结合中医脉诊理念与物联网技术，通过传感器采集脉搏数据，无线传输至手机APP分析显示。入门版可用Arduino+心率传感器采集脉搏并可视化。",
        "difficulty": "⭐⭐⭐",
        "tags": ["中医", "健康监测", "物联网", "Arduino"]
    },
    {
        "title": "智能全自动腊肉晾晒架《晒肉宝》",
        "source_name": "信阳市浉河中学",
        "grade": "初二",
        "category": "智能硬件",
        "award": "NOC智能物联网创新设计二等奖",
        "tech_stack": ["传感器", "Arduino", "步进电机", "自动化"],
        "materials": ["温湿度传感器", "光敏传感器", "步进电机", "Arduino"],
        "description": "温湿度传感器+光敏传感器检测环境条件，自动控制晾晒架的伸缩和翻转，实现智能晾晒。源自日常生活，实用性强，适合模仿。",
        "difficulty": "⭐⭐",
        "tags": ["日常生活", "自动化", "传感器", "Arduino"]
    },
    {
        "title": "成绩管理系统",
        "source_name": "温州市洞头区实验中学",
        "grade": "初一",
        "category": "软件应用",
        "award": "NOC AI创新编程初中组一等奖",
        "tech_stack": ["Python", "图形化界面"],
        "materials": ["电脑"],
        "description": "教师端成绩管理系统，具备添加/删除/排序/统计成绩功能，包含账号系统保护数据安全。最接地气的选题，代码量适中，适合初学者模仿。",
        "difficulty": "⭐⭐",
        "tags": ["Python", "学校管理", "软件应用", "数据库"]
    },
    {
        "title": "AI植物树叶分类系统",
        "source_name": "苏州中学园区校",
        "grade": "初二",
        "category": "视觉识别",
        "award": "AI创想家选拔赛",
        "tech_stack": ["机器学习", "图像识别", "Python", "大模型"],
        "materials": ["摄像头", "电脑"],
        "description": "从数据采集（拍校园植物叶子）到预处理、模型构建、优化评估全流程。学生运用AI解决植物分类实际问题并撰写小组论文。入门版可用Teachable Machine实现。",
        "difficulty": "⭐⭐⭐",
        "tags": ["植物识别", "校园", "图像分类", "Python"]
    },
    {
        "title": "AI空气检测仪",
        "source_name": "公开报道小学生科创项目",
        "grade": "初一",
        "category": "智能硬件",
        "award": "",
        "tech_stack": ["传感器", "Arduino", "语音模块", "PM2.5"],
        "materials": ["PM2.5传感器", "温湿度传感器", "Arduino", "语音模块", "LED"],
        "description": "传感器检测空气中PM2.5和温湿度，超标时触发语音提醒和LED报警。传感器成本低、功能明确，非常适合入门。可扩展为校园环境监测网络。",
        "difficulty": "⭐",
        "tags": ["环保", "空气质量", "传感器", "Arduino", "入门"]
    },
    {
        "title": "智慧单元楼（智能物联网系统）",
        "source_name": "第九届全国青少年人工智能创新挑战赛",
        "grade": "初三",
        "category": "智能硬件",
        "award": "全国青少年人工智能创新挑战赛",
        "tech_stack": ["物联网", "人脸识别", "传感器", "智能控制"],
        "materials": ["ESP32/Arduino", "摄像头", "传感器组", "继电器"],
        "description": "智能物联网+AI综合项目，包含人脸识别门禁、智能照明控制、安防监控等功能。入门版可用Arduino+传感器实现其中1-2个子功能。",
        "difficulty": "⭐⭐⭐",
        "tags": ["物联网", "智能家居", "人脸识别", "综合项目"]
    },
]


# ============================================================
# 网页抓取功能（可选，需requests+bs4）
# ============================================================

def fetch_page(url: str) -> Optional[str]:
    """抓取网页HTML"""
    if not HAS_DEPS:
        print(f"[SKIP] 缺少requests/bs4依赖，跳过: {url}")
        return None
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.encoding = resp.apparent_encoding or "utf-8"
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"[ERROR] 抓取失败 {url}: {e}")
        return None


def extract_text(html: str) -> str:
    """从HTML提取纯文本"""
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def extract_case_info(text: str, url: str) -> dict:
    """从文本提取案例结构化信息"""
    case = {
        "title": "", "source_url": url, "source_name": "",
        "grade": "", "category": "", "award": "",
        "tech_stack": [], "materials": [], "description": "",
        "difficulty": "", "tags": []
    }
    # 标题提取
    lines = text.split("\n")
    for line in lines[:30]:
        line = line.strip()
        if 5 < len(line) < 80 and any(kw in line for kw in ["AI", "智能", "人工", "识别", "分类"]):
            case["title"] = line
            break
    # 技术关键词
    for kw in ["Arduino", "Micro:bit", "Python", "Scratch", "树莓派", "ESP32",
               "机器学习", "深度学习", "计算机视觉", "语音识别", "图像识别",
               "人脸识别", "传感器", "舵机", "Teachable Machine"]:
        if kw.lower() in text.lower():
            case["tech_stack"].append(kw)
    # 材料关键词
    for mw in ["摄像头", "LED", "传感器", "舵机", "电机", "蜂鸣器", "显示屏"]:
        if mw in text:
            case["materials"].append(mw)
    # 分类判断
    if any(kw in text for kw in ["图像识别", "计算机视觉", "摄像头识别"]):
        case["category"] = "视觉识别"
    elif any(kw in text for kw in ["Arduino", "Micro:bit", "传感器", "硬件"]):
        case["category"] = "智能硬件"
    elif any(kw in text for kw in ["APP", "软件", "系统", "管理"]):
        case["category"] = "软件应用"
    # 获奖信息
    award_match = re.search(r"(?:荣获|获得|斩获|夺得)(.{2,30}?(?:等奖|奖|冠军|亚军|季军))", text)
    if award_match:
        case["award"] = award_match.group(1).strip()
    # 描述
    desc = re.sub(r"\s+", " ", text[:800]).strip()
    case["description"] = desc[:300]
    case["tags"] = list(set(case["tech_stack"] + case["materials"]))[:10]
    return case


def collect_from_urls(url_list: list[str], output_path: str):
    """从URL列表批量采集"""
    if not HAS_DEPS:
        print("[ERROR] 需要安装依赖: pip install requests beautifulsoup4 lxml")
        sys.exit(1)
    cases = []
    for i, url in enumerate(url_list, 1):
        print(f"[{i}/{len(url_list)}] {url}")
        html = fetch_page(url)
        if html:
            text = extract_text(html)
            case = extract_case_info(text, url)
            cases.append(case)
        time.sleep(REQUEST_DELAY)
    output = {
        "total": len(cases),
        "collected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cases": cases,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[DONE] 采集 {len(cases)} 条 -> {output_path}")


# ============================================================
# 导出功能
# ============================================================

def export_builtin_json(output_path: str):
    """导出内置案例为JSON"""
    output = {
        "total": len(BUILTIN_CASES),
        "source": "公开报道的青少年科创比赛获奖作品",
        "collected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cases": BUILTIN_CASES,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[DONE] 导出 {len(BUILTIN_CASES)} 条案例JSON -> {output_path}")


def export_builtin_markdown(output_path: str):
    """导出内置案例为Markdown"""
    lines = [
        "# 青少年AI科创案例库（补充）",
        "",
        f"共收录 {len(BUILTIN_CASES)} 个真实案例，来源为公开报道的青少年科创比赛获奖作品。",
        f"导出时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
        "", "---", ""
    ]
    for i, c in enumerate(BUILTIN_CASES, 1):
        lines += [
            f"## 案例{i}：{c['title']}",
            "",
            f"- **来源**：{c['source_name']}",
            f"- **年级**：{c['grade']}",
            f"- **分类**：{c['category']}",
            f"- **难度**：{c['difficulty']}",
        ]
        if c["award"]:
            lines.append(f"- **获奖**：{c['award']}")
        lines += [
            f"- **技术栈**：{'、'.join(c['tech_stack'])}",
            f"- **材料**：{'、'.join(c['materials'])}",
            f"- **标签**：{'、'.join(c['tags'])}",
            "",
            f"**简介**：{c['description']}",
            "", "---", ""
        ]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[DONE] 导出 {len(BUILTIN_CASES)} 条案例Markdown -> {output_path}")


# ============================================================
# CLI入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="青少年AI科创案例采集与清洗工具")
    parser.add_argument("--source", choices=["urls", "urls-file", "builtin"],
                        default="builtin", help="数据来源")
    parser.add_argument("--urls", nargs="*", default=[], help="URL列表（source=urls时）")
    parser.add_argument("--urls-file", default="", help="URL文件路径（source=urls-file时）")
    parser.add_argument("--output", default="./output/cases.json", help="输出JSON路径")
    parser.add_argument("--output-md", default="", help="同时输出Markdown路径")

    args = parser.parse_args()

    if args.source == "urls" and args.urls:
        collect_from_urls(args.urls, args.output)
    elif args.source == "urls-file" and args.urls_file:
        url_path = Path(args.urls_file)
        if not url_path.exists():
            print(f"[ERROR] 文件不存在: {args.urls_file}")
            sys.exit(1)
        urls = [l.strip() for l in url_path.read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.startswith("#")]
        collect_from_urls(urls, args.output)
    else:
        export_builtin_json(args.output)
        if args.output_md:
            export_builtin_markdown(args.output_md)


if __name__ == "__main__":
    main()
