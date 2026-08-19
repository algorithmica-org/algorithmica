#!/usr/bin/env python3
"""Build an EPUB from the Algorithmica HPC book content.

Usage:
    python3 build-epub.py [--lang en|ru] [--include-drafts] [--output FILE]

Requirements:
    - Python 3.8+
    - pandoc (https://pandoc.org/installing.html)

The script reads Hugo content directories, orders pages by their front matter
`weight` field, strips YAML front matter, resolves image paths, and invokes
pandoc to produce an EPUB3 file with MathML for LaTeX rendering.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

BOOK_CONFIGS = {
    "en": {
        "content_dir": "content/english/hpc",
        "title": "Algorithms for Modern Hardware",
        "author": "Sergey Slotin",
        "lang": "en-US",
        "output": "algorithms-for-modern-hardware.epub",
    },
    "ru": {
        "content_dir": "content/russian/cs",
        "title": "Алгоритмика",
        "author": "Sergey Slotin",
        "lang": "ru-RU",
        "output": "algoritmika.epub",
    },
}

FRONT_MATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
SKIP_CHAPTERS = {"slides"}


def parse_front_matter(text):
    """Extract YAML front matter fields without a YAML dependency."""
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    fm_block = match.group(0)
    body = text[match.end():]
    meta = {}
    for line in fm_block.split("\n"):
        if ":" in line and not line.startswith("---"):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body


def get_weight(meta):
    try:
        return int(meta.get("weight", "0"))
    except ValueError:
        return 0


def is_draft(meta):
    return meta.get("draft", "").lower() == "true"


def collect_chapters(content_dir):
    """Walk the content directory and return ordered list of (chapter_meta, chapter_dir, pages)."""
    content_path = Path(content_dir)
    chapters = []

    for item in content_path.iterdir():
        if not item.is_dir():
            if item.suffix == ".md" and item.name != "_index.md":
                text = item.read_text(encoding="utf-8")
                meta, body = parse_front_matter(text)
                chapters.append((meta, None, [(meta, item)]))
            continue

        if item.name in SKIP_CHAPTERS or item.name == "img":
            continue

        index_file = item / "_index.md"
        if not index_file.exists():
            continue

        index_text = index_file.read_text(encoding="utf-8")
        chapter_meta, chapter_body = parse_front_matter(index_text)

        pages = []
        for md_file in sorted(item.glob("*.md")):
            if md_file.name == "_index.md":
                if chapter_body.strip():
                    pages.append((chapter_meta, md_file))
                continue
            page_text = md_file.read_text(encoding="utf-8")
            page_meta, _ = parse_front_matter(page_text)
            pages.append((page_meta, md_file))

        pages.sort(key=lambda p: get_weight(p[0]))
        chapters.append((chapter_meta, item, pages))

    chapters.sort(key=lambda c: get_weight(c[0]))
    return chapters


def resolve_image_path(match, md_file, repo_root):
    """Resolve a relative image path to an absolute filesystem path.

    Hugo serves pages at /chapter/page/ (extra directory level), so ../img/foo.png
    from a page actually means the sibling img/ directory in the same chapter folder.
    On the filesystem, ../img/ from chapter/page.md goes one level too high, so we
    handle this Hugo-specific path resolution.
    """
    alt = match.group(1)
    img_path = match.group(2)

    if img_path.startswith("http://") or img_path.startswith("https://"):
        return match.group(0)

    md_dir = md_file.parent

    # Direct filesystem resolution first
    resolved = (md_dir / img_path).resolve()
    if resolved.exists():
        return f"![{alt}]({resolved})"

    # Hugo path fix: ../img/X from chapter/page.md means chapter/img/X
    # because Hugo renders as /chapter/page/ (adds a virtual directory level)
    if img_path.startswith("../img/"):
        filename = img_path[len("../img/"):]
        hugo_resolved = (md_dir / "img" / filename).resolve()
        if hugo_resolved.exists():
            return f"![{alt}]({hugo_resolved})"

    # Try static/img/ as a fallback (Hugo's static asset directory)
    static_path = (Path(repo_root) / "static" / img_path.lstrip("/")).resolve()
    if static_path.exists():
        return f"![{alt}]({static_path})"

    # Try static/img/<filename> as last resort
    filename = Path(img_path).name
    static_fallback = (Path(repo_root) / "static" / "img" / filename).resolve()
    if static_fallback.exists():
        return f"![{alt}]({static_fallback})"

    # Return absolute path even if missing (pandoc will warn but continue)
    return f"![{alt}]({resolved})"


def process_page(md_file, repo_root, include_drafts):
    """Read a page, strip front matter, resolve images, return processed markdown."""
    text = md_file.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)

    if not include_drafts and is_draft(meta):
        return None, meta

    img_re = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
    body = img_re.sub(lambda m: resolve_image_path(m, md_file, repo_root), body)

    # Remove HTML comments
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)

    return body, meta


def build_epub(config, include_drafts, output_path, repo_root):
    content_dir = Path(config["content_dir"])
    if not content_dir.exists():
        print(f"Error: content directory '{content_dir}' not found.", file=sys.stderr)
        print("Run this script from the repository root.", file=sys.stderr)
        sys.exit(1)

    chapters = collect_chapters(content_dir)

    with tempfile.TemporaryDirectory() as tmpdir:
        combined_path = Path(tmpdir) / "book.md"
        page_count = 0

        with open(combined_path, "w", encoding="utf-8") as out:
            for chapter_meta, chapter_dir, pages in chapters:
                if not include_drafts and is_draft(chapter_meta):
                    continue

                chapter_title = chapter_meta.get("title", "")

                first_page = True
                for page_meta, md_file in pages:
                    body, meta = process_page(md_file, repo_root, include_drafts)
                    if body is None:
                        continue

                    page_title = meta.get("title", "")

                    if first_page and md_file.name == "_index.md":
                        out.write(f"\n# {chapter_title}\n\n")
                        if body.strip():
                            out.write(body)
                            out.write("\n\n")
                        first_page = False
                    elif first_page and chapter_title:
                        out.write(f"\n# {chapter_title}\n\n")
                        if page_title and page_title != chapter_title:
                            out.write(f"## {page_title}\n\n")
                        out.write(body)
                        out.write("\n\n")
                        first_page = False
                    else:
                        if page_title:
                            out.write(f"## {page_title}\n\n")
                        out.write(body)
                        out.write("\n\n")

                    page_count += 1

        if page_count == 0:
            print("Error: no pages found to include.", file=sys.stderr)
            sys.exit(1)

        print(f"Collected {page_count} pages across {len(chapters)} sections.")

        cmd = [
            "pandoc",
            str(combined_path),
            "--from", "markdown+tex_math_dollars+pipe_tables+fenced_code_blocks",
            "--to", "epub3",
            "--mathml",
            "--toc",
            "--toc-depth=2",
            "--metadata", f"title={config['title']}",
            "--metadata", f"author={config['author']}",
            "--metadata", f"lang={config['lang']}",
            "--epub-chapter-level=1",
            "--wrap=none",
            "-o", str(output_path),
        ]

        cover = Path(repo_root) / "static" / "img" / "cover.png"
        if not cover.exists():
            cover = Path(repo_root) / "static" / "img" / "logo.png"
        if cover.exists():
            cmd.extend(["--epub-cover-image", str(cover)])

        print("Running pandoc...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("pandoc stderr:", result.stderr, file=sys.stderr)
            sys.exit(result.returncode)

        if result.stderr:
            warnings = [l for l in result.stderr.strip().split("\n") if l.strip()]
            if warnings:
                print(f"  ({len(warnings)} warnings from pandoc)")

        file_size = os.path.getsize(output_path)
        print(f"Done: {output_path} ({file_size / 1024 / 1024:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(
        description="Build an EPUB from Algorithmica book content."
    )
    parser.add_argument(
        "--lang",
        choices=["en", "ru"],
        default="en",
        help="Which edition to build (default: en)",
    )
    parser.add_argument(
        "--include-drafts",
        action="store_true",
        help="Include pages marked as draft",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: based on language)",
    )
    args = parser.parse_args()

    config = BOOK_CONFIGS[args.lang]
    output_path = Path(args.output) if args.output else Path(config["output"])

    if not shutil.which("pandoc"):
        print("Error: pandoc not found. Install it: https://pandoc.org/installing.html", file=sys.stderr)
        sys.exit(1)

    repo_root = Path(__file__).parent.resolve()
    build_epub(config, args.include_drafts, output_path, repo_root)


if __name__ == "__main__":
    main()
