"""Crawl elf.co.jp PukiWiki content pages, dump as JSON.

Source: https://elf.co.jp/index.php?cmd=list (151 pages discovered)
Filter: skip session-key pages (uppercase+digits placeholder pages)
        keep: meaningful content pages (technical articles, guides, FAQs)

Output:
  src/mcp_server_elf/wiki_dump.json
    {
      "ページ名": {
        "url": "https://elf.co.jp/index.php?...",
        "title": "...",
        "text": "...",
        "char_count": int,
      },
      ...
    }

Usage:
    python scripts/crawl_wiki.py [--out PATH] [--sleep 0.5]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from html.parser import HTMLParser


# Pages to skip - session keys, placeholders, private, draft, duplicates
SKIP_PATTERNS = [
    re.compile(r"^[A-Z]{2,}[0-9A-Z]{4,}$"),    # session-key like AMPD28367436462, CRAY470A7241387
    re.compile(r"^[A-Z]+[0-9]+[A-Z]*[0-9]*$"), # session-key alt patterns
    re.compile(r"^User\d+"),                    # User1938206ws etc.
    re.compile(r"^magh\d", re.I),               # magh1490AX5203726481
    re.compile(r"^MAGH\d"),
    re.compile(r"^MAGL\d"),
    re.compile(r"^MAGMES"),
    re.compile(r"^MaiEd\d"),
    re.compile(r"^MOS\d"),
    re.compile(r"^MESH\d"),
    re.compile(r"^Iter\d"),
    re.compile(r"^Fplus$"),
    re.compile(r"^DEMO\d"),
    re.compile(r"^DLL\d"),
    re.compile(r"^EGMAP"),
    re.compile(r"^ELF\d{3,}"),
    re.compile(r"^ELFShield\d"),
    re.compile(r"^ELFMAGICJR"),
    re.compile(r"^USERMESH"),
    re.compile(r"^UserCSV"),
    re.compile(r"^UserMESH"),
    re.compile(r"^UserUN"),
    re.compile(r"^AVX\d"),
    re.compile(r"^AMPD"),
    re.compile(r"^CRAY"),
    re.compile(r"^LINUX\d"),
    re.compile(r"^closed$"),
    re.compile(r"^dll(ENG)?$"),
    re.compile(r"^guide$"),
    re.compile(r"非公開"),
    re.compile(r"準備中"),
    re.compile(r"練習"),
    re.compile(r"複製$"),
    re.compile(r"^menuTEST$"),
    re.compile(r"^MenuPPI$"),
    re.compile(r"^MenuSOLS$"),
    re.compile(r"動画テスト"),
    re.compile(r"アコーディオン$"),
    re.compile(r"meet in"),
    re.compile(r"^closed$"),
]


# Curated list of page names to crawl (from cmd=list output, manually filtered)
CURATED_PAGES = [
    "FrontPage", "FAQ", "README", "MAGICの紹介",
    # 解析手法系
    "解析手法", "解析手法の基本的説明",
    "解析手順の紹介(magic)", "解析手順の紹介(magicUS)", "解析手順の紹介(elfin)",
    "磁場解析", "磁場解析 ELF/MAGIC", "磁場解析事例",
    "電場解析", "電場解析 ELFIN", "電場解析事例",
    "軌道解析", "軌道解析 ELF/BEAM", "軌道解析事例",
    "解析事例",
    # 理論
    "有限要素法との違い", "ELF/MAGICとFEMの比較",
    "磁気モーメント法", "積分要素法", "表面電荷法",
    "理論の説明ガイド",
    # 比較事例
    "C型電磁石の磁場解析比較", "MRIの磁場解析比較", "渦",
    # ガイド類
    "スタートアップガイド", "スタートアップガイドmagic", "スタートアップガイドelfin",
    "ELFMAGICの例題ガイド", "ELFINの例題ガイド",
    "ELFBEAMの例題ガイド", "ELFBEAMの操作ガイド", "ELFBEAMの説明ガイド",
    "ELF/Bench 操作ガイド", "IEmesh 操作ガイド", "MaiEditor 操作ガイド",
    "MaiEditor3", "Wmap 操作ガイド", "IEmesh",
    "操作ガイドダウンロードページ",
    # 製品/ダウンロード関連
    "ソルバー", "ツール", "ツール類", "メッシュ", "ユーザー",
    "製品情報", "製品履歴", "ELFシリーズ履歴", "ソフトウェア履歴",
    "標準構成", "別売", "動作環境",
    "ダウンロード", "isoインストール", "デモ例題magic",
    "ドキュメント",
    # 会社・サポート
    "会社情報", "沿革", "採用情報", "サポート", "お問い合わせ",
    "セミナー", "オンラインセミナー、オンラインデモ",
    "論文紹介", "インフォメーション",
    # その他
    "Fplus",
]


def should_skip(name: str) -> bool:
    return any(p.search(name) for p in SKIP_PATTERNS)


class WikiTextExtractor(HTMLParser):
    """Extract main #body content from PukiWiki HTML."""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._title = ""
        self._depth_in_body = 0
        self._in_script = self._in_style = self._in_title = self._in_navi = False

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        attrs_d = dict(attrs)
        cls = attrs_d.get("class", "")
        idv = attrs_d.get("id", "")
        if t == "script": self._in_script = True
        elif t == "style": self._in_style = True
        elif t == "title": self._in_title = True
        elif idv in ("body", "content", "main") or "wikibody" in cls:
            self._depth_in_body += 1
        elif idv in ("navi", "menubar", "sidebar", "pageNavi1", "footer"):
            self._in_navi = True
        elif t in ("br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4"):
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        t = tag.lower()
        if t == "script": self._in_script = False
        elif t == "style": self._in_style = False
        elif t == "title": self._in_title = False
        elif t in ("p", "div", "li", "tr", "h1", "h2", "h3", "h4", "td"):
            self._chunks.append("\n")

    def handle_data(self, data):
        if self._in_script or self._in_style or self._in_navi:
            return
        if self._in_title:
            self._title += data
        self._chunks.append(data)

    def text(self) -> str:
        out = "".join(self._chunks)
        out = re.sub(r"[ \t]+", " ", out)
        out = re.sub(r"\n[ \t]+", "\n", out)
        out = re.sub(r"\n{3,}", "\n\n", out)
        return out.strip()

    @property
    def title(self) -> str:
        return self._title.strip()


def fetch(url: str, timeout: int = 30) -> bytes:
    req = Request(url, headers={"User-Agent": "mcp-server-elf/crawler"})
    with urlopen(req, timeout=timeout) as r:
        return r.read()


def crawl_page(name: str) -> dict:
    url = f"https://elf.co.jp/index.php?{quote(name)}"
    try:
        raw = fetch(url)
    except Exception as e:
        return {"url": url, "title": "", "text": "", "char_count": 0, "error": str(e)}

    # PukiWiki uses EUC-JP or UTF-8 - try UTF-8 first since modern PukiWiki defaults to it
    for enc in ("utf-8", "euc-jp", "cp932"):
        try:
            html = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        html = raw.decode("utf-8", errors="replace")

    parser = WikiTextExtractor()
    try:
        parser.feed(html)
    except Exception as e:
        return {"url": url, "title": "", "text": f"[parse error: {e}]", "char_count": 0}

    text = parser.text()
    return {
        "url": url,
        "title": parser.title,
        "text": text,
        "char_count": len(text),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).parent.parent / "src" / "mcp_server_elf" / "wiki_dump.json"))
    ap.add_argument("--sleep", type=float, default=0.5, help="Seconds between requests (be polite)")
    ap.add_argument("--pages", nargs="*", default=None, help="Page names to crawl (overrides --pagelist)")
    ap.add_argument("--pagelist", default=None, help="File with one page name per line")
    ap.add_argument("--no-skip", action="store_true", help="Disable skip filter (crawl ALL given pages)")
    args = ap.parse_args()

    if args.pages:
        raw_pages = args.pages
    elif args.pagelist:
        raw_pages = [ln.strip() for ln in Path(args.pagelist).read_text(encoding="utf-8").splitlines() if ln.strip()]
    else:
        raw_pages = CURATED_PAGES

    pages = raw_pages if args.no_skip else [p for p in raw_pages if not should_skip(p)]
    print(f"Crawling {len(pages)} pages from elf.co.jp (skip filter: {'OFF' if args.no_skip else 'ON'}) ...")

    dump = {}
    for i, name in enumerate(pages, 1):
        print(f"  [{i}/{len(pages)}] {name} ...", end=" ", flush=True)
        result = crawl_page(name)
        dump[name] = result
        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"{result['char_count']} chars")
        time.sleep(args.sleep)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")

    total_chars = sum(v.get("char_count", 0) for v in dump.values())
    print(f"\nWrote {out} ({out.stat().st_size/1024:.0f} KB)")
    print(f"Total: {len(dump)} pages, {total_chars/1000:.0f}k characters")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
