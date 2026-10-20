#!/usr/bin/env python3
"""检索《高性价比人生指南》条目（自包含解析器，不依赖其他脚本）。

用法示例：
    python search_entries.py --query 燃气 软管
    python search_entries.py --section 34 --grade A
    python search_entries.py --query 药 过期 --audience 老人 --ratio 极高
    python search_entries.py --query 押金 --json

过滤参数（可叠加）：
    --query    关键词（空格分隔，任一命中即算，按命中数排序）
    --section  只看第 N 节（1-34）
    --grade    只看证据等级 A/B/C
    --audience 只看适用人群（含该词的条目，如：老人/怀孕/婴幼儿/孩子/35岁/女性）
    --ratio    只看性价比档：极高 / 高 / 一般
    --max      最多输出几条（默认 8）
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SRC = Path("E:/Projects/HowToLiveBetter")
TITLE_RE = re.compile(r"^###\s+(\d+)\.\s*(.+?)\s*$")
TAG_RE = re.compile(r"<!--\s*成本标签:(.*?)-->")
KV_RE = re.compile(r"(钱|时间|毅力|收益|口径|人群)\s*=\s*([^\s,]+)")
FIELD_RE = re.compile(r"^-\s*(成本|说人话|收益|证据等级|来源|备注)\s*[:：]\s*(.*)$")
W = {"钱": {"0": 0, "少": 1, "多": 2}, "时间": {"少": 0, "中": 1, "多": 2}, "毅力": {"否": 0, "些": 1, "是": 2}}
MAP = {"钱": "money", "时间": "time", "毅力": "will", "收益": "level", "口径": "lens", "人群": "audience"}
ORDER = {"极高": 0, "高": 1, "一般": 2}


def parse_book(src: Path):
    entries = []
    for i, f in enumerate(sorted(src.glob("book/*.md")), 1):
        sec_name = f.stem.split("-", 1)[1]
        cur = None
        for line in f.read_text(encoding="utf-8").splitlines():
            m = TITLE_RE.match(line)
            if m:
                if cur:
                    entries.append(cur)
                cur = {"section": i, "section_name": sec_name, "no": int(m.group(1)),
                       "title": m.group(2), "cost": "", "plain": "", "benefit": "",
                       "grade": "", "source": "", "note": ""}
                continue
            if not cur:
                continue
            t = TAG_RE.search(line)
            if t:
                for k, v in KV_RE.findall(t.group(1)):
                    cur[MAP[k]] = v
                continue
            fm = FIELD_RE.match(line)
            if fm:
                key = {"成本": "cost", "说人话": "plain", "收益": "benefit",
                       "证据等级": "grade", "来源": "source", "备注": "note"}[fm.group(1)]
                cur[key] = (cur[key] + "\n" + fm.group(2)).strip() if cur[key] else fm.group(2)
                continue
            if line.strip() and not line.startswith("#"):
                cur["note"] = (cur["note"] + "\n" + line).strip()
        if cur:
            entries.append(cur)

    for e in entries:
        e["id"] = f"{e['section']}-{e['no']}"
        e["grade"] = (e["grade"].strip()[:1] or "").upper()
        cs = (W["钱"].get(e.get("money"), 0) + W["时间"].get(e.get("time"), 0)
              + W["毅力"].get(e.get("will"), 0))
        lv = e.get("level")
        e["cost_score"] = cs
        e["ratio"] = ("极高" if (lv == "大" and cs == 0) else
                      "高" if (lv == "大" and cs <= 2 or lv == "中" and cs == 0) else
                      "一般")
        e["disputed"] = e["note"].startswith("争议")
    return entries


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DEFAULT_SRC))
    ap.add_argument("--query", nargs="*", default=[])
    ap.add_argument("--section", type=int)
    ap.add_argument("--grade")
    ap.add_argument("--audience")
    ap.add_argument("--ratio")
    ap.add_argument("--max", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    src = Path(a.src)
    if not (src / "book").is_dir():
        print(f"数据不存在：{src}，先运行 sync_book.py", file=sys.stderr)
        return 1

    entries = parse_book(src)
    hits = []
    for e in entries:
        if a.section and e["section"] != a.section:
            continue
        if a.grade and e["grade"] != a.grade.upper():
            continue
        if a.ratio and e["ratio"] != a.ratio:
            continue
        if a.audience and a.audience not in (e.get("audience") or ""):
            continue
        if a.query:
            blob = " ".join([e["title"], e["plain"], e["benefit"], e["note"]])
            score = sum(blob.count(k) for k in a.query)
            if score == 0:
                continue
            e["_score"] = score
        hits.append(e)

    if a.query:
        hits.sort(key=lambda e: (-e["_score"], ORDER[e["ratio"]], {"A": 0, "B": 1, "C": 2}.get(e["grade"], 3)))
    else:
        hits.sort(key=lambda e: (ORDER[e["ratio"]], {"A": 0, "B": 1, "C": 2}.get(e["grade"], 3)))
    hits = hits[: a.max]

    if a.json:
        for e in hits:
            e.pop("_score", None)
        print(json.dumps(hits, ensure_ascii=False, indent=1))
        return 0

    if not hits:
        print("没有命中条目——如实告知用户书里没写，不要编造。")
        return 0
    for e in hits:
        tag = f"钱={e.get('money')} 时间={e.get('time')} 毅力={e.get('will')} 收益={e.get('level')}"
        disp = f" 口径={e.get('lens')}" + (f" 人群={e.get('audience')}" if e.get("audience") else "")
        print(f"◆ 第 {e['section']} 节第 {e['no']} 条（{e['section_name']}）｜{e['ratio']}｜证据 {e['grade']}"
              + ("｜争议" if e["disputed"] else ""))
        print(f"  标题：{e['title']}")
        print(f"  成本标签：{tag}{disp}")
        print(f"  说人话：{e['plain']}")
        src1 = e["source"].split("；")[0][:160]
        print(f"  来源（首个）：{src1}")
        if e["note"]:
            print(f"  备注：{e['note'][:200]}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
