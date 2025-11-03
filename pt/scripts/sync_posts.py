#!/usr/bin/env python3
"""
Sincroniza artigos do site matildebatalha.pt para Markdown estático.

Principais funcionalidades:
- Descobre posts a partir da homepage ou de uma lista de URLs.
- Converte o conteúdo para Markdown com cabeçalhos rebaixados.
- Descarrega imagens para `static/<slug>/image-XX.ext` e atualiza as referências.
- Gera/atualiza `posts/index.json` com metadados e excertos.

Exemplo de utilização:
    python3 scripts/sync_posts.py \
        --home https://matildebatalha.pt/ \
        --urls-file post_urls.txt

Requerimentos: Python 3.10+ e beautifulsoup4.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Set
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parent.parent

HEADER_PREFIX = {
    "h1": "## ",
    "h2": "### ",
    "h3": "#### ",
    "h4": "##### ",
    "h5": "###### ",
    "h6": "###### ",
}

INLINE_WRAP = {
    "strong": ("**", "**"),
    "b": ("**", "**"),
    "em": ("*", "*"),
    "i": ("*", "*"),
    "code": ("`", "`"),
}


@dataclass
class PostMeta:
    title: str
    url: str
    date: Optional[str]
    categories: List[str]

    @property
    def slug(self) -> str:
        slug = self.url.rstrip("/").split("/")[-1]
        if not slug:
            slug = re.sub(r"[^a-z0-9-]+", "-", self.title.lower()).strip("-")
        return slug or "post"


def fetch_html(url: str) -> BeautifulSoup:
    with urlopen(url, timeout=40) as response:
        return BeautifulSoup(response.read(), "html.parser")


def discover_posts(soup: BeautifulSoup) -> List[PostMeta]:
    posts: List[PostMeta] = []
    for li in soup.select("ul.wp-block-post-template li.wp-block-post"):
        title_el = li.select_one(".wp-block-post-title a")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        url = title_el.get("href")
        if not url:
            continue
        time_el = li.select_one("time")
        date_iso = time_el.get("datetime") if time_el else None
        categories = [a.get_text(strip=True) for a in li.select(".taxonomy-category a")]
        posts.append(PostMeta(title=title, url=url, date=date_iso, categories=categories))
    return posts


def extract_meta_from_article(url: str, soup: BeautifulSoup) -> PostMeta:
    title_el = (
        soup.select_one("h1.wp-block-post-title")
        or soup.select_one("h1.entry-title")
        or soup.select_one("h1")
    )
    title = title_el.get_text(strip=True) if title_el else url.rstrip("/").split("/")[-1]
    time_el = soup.select_one("time")
    date_iso = time_el.get("datetime") if time_el else None
    categories = [a.get_text(strip=True) for a in soup.select(".taxonomy-category a, .cat-links a")]
    return PostMeta(title=title, url=url, date=date_iso, categories=categories)


def localise_images(content: Tag, slug: str, static_root: Path) -> None:
    images = list(content.find_all("img"))
    if not images:
        return
    slug_dir = static_root / slug
    if slug_dir.exists():
        shutil.rmtree(slug_dir)
    slug_dir.mkdir(parents=True, exist_ok=True)

    for idx, img in enumerate(images, start=1):
        src = img.get("src")
        if not src:
            img.decompose()
            continue
        parsed = urlparse(src)
        ext = Path(parsed.path).suffix or ".jpg"
        filename = f"image-{idx:02d}{ext}"
        destination = slug_dir / filename
        try:
            with urlopen(src, timeout=40) as response:
                data = response.read()
            destination.write_bytes(data)
            img["src"] = str(Path("static") / slug / filename).replace("\\", "/")
            parent = img.parent
            if hasattr(parent, "name") and parent.name == "a":
                parent["href"] = img["src"]
            for attr in ("srcset", "sizes", "data-src", "data-large-file"):
                if attr in img.attrs:
                    del img.attrs[attr]
        except Exception:
            img.decompose()


def remove_share_blocks(content: Tag) -> None:
    for node in content.select(".sharedaddy, .sd-sharing-enabled, .jetpack-likes-widget-wrapper, .sd-block"):
        node.decompose()
    for heading in content.find_all(re.compile("^h[1-6]$")):
        if heading.get_text(strip=True).lower().startswith("partilhar isto"):
            sibling = heading.find_next_sibling()
            while sibling:
                if isinstance(sibling, NavigableString):
                    next_sibling = sibling.next_sibling
                    sibling.extract()
                    sibling = next_sibling
                    continue
                text = sibling.get_text(strip=True).lower() if isinstance(sibling, Tag) else ""
                if isinstance(sibling, Tag) and ("partilhar" in text or "share=" in sibling.decode()):
                    next_sibling = sibling.find_next_sibling()
                    sibling.decompose()
                    sibling = next_sibling
                    continue
                break
            heading.decompose()


def node_to_markdown(node: Tag | NavigableString) -> str:
    if isinstance(node, NavigableString):
        return str(node)

    name = node.name.lower()
    if name in {"script", "style", "noscript", "svg", "iframe"}:
        return ""
    if name == "br":
        return "  \n"
    if name == "hr":
        return "\n---\n"
    if name in HEADER_PREFIX:
        content = "".join(node_to_markdown(child) for child in node.children).strip()
        return f"{HEADER_PREFIX[name]}{content}\n\n" if content else ""
    if name == "blockquote":
        inner = "".join(node_to_markdown(child) for child in node.children).strip()
        if not inner:
            return ""
        quoted = "\n".join(f"> {line}" if line else ">" for line in inner.splitlines())
        return f"{quoted}\n\n"
    if name == "ul":
        lines = []
        for li in node.find_all("li", recursive=False):
            body = "".join(node_to_markdown(child) for child in li.children).strip()
            if body:
                lines.append(f"- {body}")
            for sub in li.find_all(["ul", "ol"], recursive=False):
                sub_md = node_to_markdown(sub).strip("\n")
                if sub_md:
                    lines.append("\n".join("  " + line for line in sub_md.splitlines()))
        return ("\n".join(lines) + "\n\n") if lines else ""
    if name == "ol":
        lines = []
        idx = 1
        for li in node.find_all("li", recursive=False):
            body = "".join(node_to_markdown(child) for child in li.children).strip()
            lines.append(f"{idx}. {body}" if body else f"{idx}.")
            idx += 1
            for sub in li.find_all(["ul", "ol"], recursive=False):
                sub_md = node_to_markdown(sub).strip("\n")
                if sub_md:
                    lines.append("\n".join("   " + line for line in sub_md.splitlines()))
        return ("\n".join(lines) + "\n\n") if lines else ""
    if name == "a":
        text = "".join(node_to_markdown(child) for child in node.children).strip() or node.get("href", "")
        href = node.get("href", "")
        return f"[{text}]({href})" if href else text
    if name == "img":
        alt = node.get("alt", "").strip()
        src = node.get("src", "")
        return f"![{alt}]({src})" if src else ""
    if name == "figure":
        parts = "".join(node_to_markdown(child) for child in node.children)
        return f"{parts}\n\n"
    if name == "figcaption":
        text = "".join(node_to_markdown(child) for child in node.children).strip()
        return f"*{text}*" if text else ""
    if name == "pre":
        code = node.get_text("\n")
        return f"```\n{code.strip()}\n```\n\n"
    if name in INLINE_WRAP:
        inner = "".join(node_to_markdown(child) for child in node.children).strip()
        if not inner:
            return ""
        before, after = INLINE_WRAP[name]
        return f"{before}{inner}{after}"
    if name == "span":
        return "".join(node_to_markdown(child) for child in node.children)
    if name in {"div", "section", "main", "article"}:
        inner = "".join(node_to_markdown(child) for child in node.children).strip()
        return f"{inner}\n\n" if inner else ""
    return "".join(node_to_markdown(child) for child in node.children)


def markdown_excerpt(markdown: str, length: int = 60) -> str:
    plain = re.sub(r"```.*?```", "", markdown, flags=re.S)
    plain = re.sub(r"`([^`]*)`", r"\1", plain)
    plain = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", plain)
    plain = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", plain)
    plain = re.sub(r"\[\]\([^\)]*\)", "", plain)
    plain = plain.replace("**", "").replace("*", "")
    tokens = [
        token
        for token in plain.split()
        if token not in {"-", "---"} and not re.fullmatch(r"#*", token)
    ]
    if not tokens:
        return ""
    snippet = tokens[:length]
    ellipsis = "…" if len(tokens) > length else ""
    return " ".join(snippet) + ellipsis


def write_markdown(meta: PostMeta, markdown: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    date_prefix = meta.date[:10] if meta.date else datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"{date_prefix}-{meta.slug}.md"
    path = output_dir / filename

    front_matter = ["---"]
    front_matter.append(f'title: "{meta.title.replace("\"", "\\\"")}"')
    if meta.date:
        front_matter.append(f"date: {meta.date}")
    if meta.categories:
        categories = ", ".join(f'"{cat}"' for cat in meta.categories)
        front_matter.append(f"categories: [{categories}]")
    front_matter.append(f"source: {meta.url}")
    front_matter.append("---\n")

    path.write_text("\n".join(front_matter) + markdown)
    return path


def build_manifest(entries: Iterable[dict], destination: Path) -> None:
    destination.write_text(json.dumps(list(entries), indent=2, ensure_ascii=False))


def load_urls_from_file(path: Optional[str]) -> List[str]:
    if not path:
        return []
    url_file = Path(path)
    if not url_file.exists():
        raise FileNotFoundError(f"Ficheiro de URLs não encontrado: {url_file}")
    return [
        line.strip()
        for line in url_file.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def is_article_page(soup: BeautifulSoup) -> bool:
    return bool(soup.select_one(".wp-block-post-content, article.post"))


def sync(
    home_url: Optional[str],
    output_dir: Path,
    manifest_path: Path,
    static_dir: Path,
    extra_urls: Iterable[str],
) -> None:
    posts_by_url: dict[str, PostMeta] = {}
    seen_urls: Set[str] = set()

    if home_url:
        try:
            home_soup = fetch_html(home_url)
            for meta in discover_posts(home_soup):
                posts_by_url.setdefault(meta.url, meta)
        except Exception as error:
            print(f"Aviso: não foi possível ler homepage ({error}).")

    queue: List[str] = list(extra_urls)
    while queue:
        current = queue.pop(0)
        if current in seen_urls:
            continue
        seen_urls.add(current)
        try:
            soup = fetch_html(current)
        except Exception as error:
            print(f"Falha ao carregar {current}: {error}")
            continue
        if is_article_page(soup):
            meta = extract_meta_from_article(current, soup)
            posts_by_url[meta.url] = meta
        else:
            for meta in discover_posts(soup):
                if meta.url not in posts_by_url:
                    posts_by_url[meta.url] = meta
                    queue.append(meta.url)

    if not posts_by_url:
        raise RuntimeError("Nenhum artigo encontrado para sincronizar.")

    manifest_entries = []
    for url, meta in sorted(posts_by_url.items(), key=lambda item: item[1].date or "", reverse=True):
        try:
            soup = fetch_html(url)
        except URLError as error:
            print(f"Erro a carregar artigo {url}: {error}")
            continue
        meta = extract_meta_from_article(url, soup)
        content = (
            soup.select_one(".wp-block-post-content")
            or soup.find("article")
            or soup.find("main")
            or soup.body
        )
        if not content:
            print(f"Aviso: sem conteúdo para {url}")
            continue
        remove_share_blocks(content)
        localise_images(content, meta.slug, static_dir)
        markdown = node_to_markdown(content)
        markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"
        md_path = write_markdown(meta, markdown, output_dir)
        manifest_entries.append(
            {
                "title": meta.title,
                "date": meta.date,
                "categories": meta.categories,
                "path": md_path.name,
                "source": meta.url,
                "excerpt": markdown_excerpt(markdown),
            }
        )
        print(f"✓ {md_path.name}")

    build_manifest(manifest_entries, manifest_path)
    print(f"\nSincronização concluída: {len(manifest_entries)} artigos atualizados.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza posts em Markdown.")
    parser.add_argument("--home", default=None, help="URL da homepage a rastrear.")
    default_output = ROOT / "posts"
    parser.add_argument("--output", default=str(default_output), help="Diretório para Markdown.")
    parser.add_argument("--manifest", default=str(default_output / "index.json"), help="Ficheiro manifest JSON.")
    parser.add_argument("--static", default=str(ROOT / "static"), help="Diretório raiz para imagens locais.")
    parser.add_argument("--urls-file", help="Ficheiro com URLs adicionais (um por linha).")
    parser.add_argument("--url", action="append", dest="urls", help="URL adicional (pode repetir).")
    args = parser.parse_args()

    extra_urls = load_urls_from_file(args.urls_file)
    if args.urls:
        extra_urls.extend(args.urls)

    try:
        sync(
            home_url=args.home,
            output_dir=Path(args.output),
            manifest_path=Path(args.manifest),
            static_dir=Path(args.static),
            extra_urls=extra_urls,
        )
    except Exception as error:  # pragma: no cover
        raise SystemExit(f"Sincronização falhou: {error}") from error


if __name__ == "__main__":
    main()
