#!/usr/bin/env python3
"""确保《高性价比人生指南》正文在本地且为最新。

用法：
    python sync_book.py                    # 用默认路径 E:/Projects/HowToLiveBetter
    python sync_book.py --src D:/hltb      # 指定其他本地目录

行为：
- 目录已存在  -> git pull --ff-only（失败则提示，不强制覆盖本地改动）
- 目录不存在  -> git clone --depth 1
- 输出当前 HEAD 日期与条目数，供答复时标注"数据同步至哪一天"。
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_SRC = Path("E:/Projects/HowToLiveBetter")
REPO = "https://github.com/eternity4719/HowToLiveBetter.git"


def run_git(args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DEFAULT_SRC))
    a = ap.parse_args()
    src = Path(a.src)

    if not (src / "book").is_dir():
        print(f"[sync] 本地不存在 {src}，开始浅克隆 …")
        r = run_git(["clone", "--depth", "1", REPO, str(src)], cwd=src.parent if src.parent.is_dir() else Path.home())
        if r.returncode != 0:
            print(f"[sync] 克隆失败：{r.stderr.strip()}")
            return 1
    else:
        r = run_git(["pull", "--ff-only"], cwd=src)
        if r.returncode != 0:
            print(f"[sync] pull 失败（可能本地有改动或无网络），继续用现有副本：{r.stderr.strip()}")

    head = run_git(["log", "-1", "--date=short", "--pretty=%ad"], cwd=src)
    ver = head.stdout.strip() if head.returncode == 0 else "未知"
    n = sum(1 for _ in (src / "book").glob("*.md"))
    print(f"[sync] OK  数据同步至 {ver}  共 {n} 节  路径 {src}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
