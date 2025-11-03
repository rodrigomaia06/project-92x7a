from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

from bs4 import BeautifulSoup, Tag


@dataclass
class PageSpec:
    slug: str
    url: str
    filename: str
    title: Optional[str] = None
    counterpart: Optional[str] = None


def fetch_html(url: str) -> BeautifulSoup:
    with urlopen(url, timeout=40) as response:
        return BeautifulSoup(response.read(), "html.parser")


def localise_images(content: Tag, slug: str, static_dir: Path) -> None:
    images = list(content.find_all("img"))
    if not images:
        return
    target_dir = static_dir / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    for item in target_dir.iterdir():
        if item.is_file():
            item.unlink()

    for idx, img in enumerate(images, start=1):
        src = img.get("src")
        if not src:
            img.decompose()
            continue
        parsed = urlparse(src)
        ext = Path(parsed.path).suffix or ".jpg"
        filename = f"image-{idx:02d}{ext}"
        destination = target_dir / filename
        try:
            with urlopen(src, timeout=40) as response:
                destination.write_bytes(response.read())
            img["src"] = str(Path("static/pages") / slug / filename).replace("\\", "/")
            for attr in ("srcset", "sizes", "data-src", "data-large-file"):
                if attr in img.attrs:
                    del img.attrs[attr]
        except Exception:
            img.decompose()


def absolutise_links(content: Tag, base_url: str) -> None:
    for link in content.find_all("a"):
        href = link.get("href")
        if not href or href.startswith("#"):
            continue
        link["href"] = urljoin(base_url, href)


def remove_share_blocks(content: Tag) -> None:
    for node in content.select(".sharedaddy, .sd-sharing-enabled, .jetpack-likes-widget-wrapper, .sd-block"):
        node.decompose()

    for heading in content.find_all(re.compile("^h[1-6]$")):
        if heading.get_text(strip=True).lower().startswith("partilhar isto"):
            sibling = heading.find_next_sibling()
            while sibling:
                text = sibling.get_text(strip=True).lower() if isinstance(sibling, Tag) else ""
                if isinstance(sibling, Tag) and ("partilhar" in text or "share=" in sibling.decode()):
                    next_sibling = sibling.find_next_sibling()
                    sibling.decompose()
                    sibling = next_sibling
                    continue
                if isinstance(sibling, Tag) and sibling.name in {"p", "ul", "ol"} and not sibling.get_text(strip=True):
                    next_sibling = sibling.find_next_sibling()
                    sibling.decompose()
                    sibling = next_sibling
                    continue
                break
            heading.decompose()

    for node in content.find_all(True):
        node_id = node.get("id")
        if isinstance(node_id, str) and node_id.startswith("__"):
            node.decompose()


def extract_content(url: str, slug: str, static_dir: Path) -> tuple[str, str, str]:
    soup = fetch_html(url)
    entry = (
        soup.select_one(".wp-block-post-content")
        or soup.select_one(".entry-content")
        or soup.find("article")
        or soup.find("main")
    )
    if not entry:
        raise RuntimeError(f"Não foi possível encontrar conteúdo para {url}")

    content = BeautifulSoup(str(entry), "html.parser")

    for tag in content.find_all(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    remove_share_blocks(content)
    localise_images(content, slug, static_dir)
    absolutise_links(content, url)

    heading = content.find("h1")
    title = heading.get_text(strip=True) if heading else slug.replace("-", " ").title()
    if heading:
        heading.decompose()

    for tag in content.find_all("p"):
        if not tag.get_text(strip=True) and not tag.find("img"):
            tag.decompose()

    body_html = content.decode_contents()
    description = re.sub(r"\s+", " ", content.get_text(" ", strip=True))
    description = description[:157] + "…" if len(description) > 160 else description
    return title, description, body_html


def render_pages(
    *,
    output_dir: Path,
    templates: dict[str, Path],
    pages: Iterable[PageSpec],
    static_pages_dir: Path,
    language_switcher_builder: Callable[[str, Optional[str]], str],
    content_adjuster: Optional[Callable[[str], str]] = None,
) -> None:
    base_template = templates["base"].read_text()
    header_template = templates["header"].read_text()
    footer_html = templates["footer"].read_text()
    menu_html = templates["menu"].read_text()

    for page in pages:
        heading, description, body_html = extract_content(page.url, page.slug, static_pages_dir)
        html_content = content_adjuster(body_html) if content_adjuster else body_html
        header_html = (
            header_template
            .replace("{{LANGUAGE_SWITCHER}}", language_switcher_builder(page.filename, page.counterpart))
            .replace("{{MENU}}", menu_html)
        )
        html = (
            base_template
            .replace("{{TITLE}}", page.title or heading)
            .replace("{{DESCRIPTION}}", description)
            .replace("{{HEADING}}", page.title or heading)
            .replace("{{CONTENT}}", html_content)
            .replace("{{HEADER}}", header_html)
            .replace("{{FOOTER}}", footer_html)
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / page.filename).write_text(html)
        print(f"✓ {page.filename}")


def render_home(
    *,
    output_dir: Path,
    templates: dict[str, Path],
    language_switcher_builder: Callable[[str, Optional[str]], str],
) -> None:
    home_template = templates["home"].read_text()
    header_template = templates["header"].read_text()
    footer_html = templates["footer"].read_text()
    menu_html = templates["menu"].read_text()

    header_html = (
        header_template
        .replace("{{LANGUAGE_SWITCHER}}", language_switcher_builder("index.html", "index.html"))
        .replace("{{MENU}}", menu_html)
    )
    html = (
        home_template
        .replace("{{HEADER}}", header_html)
        .replace("{{FOOTER}}", footer_html)
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(html)
    print("✓ index.html")


def render_post_shell(
    *,
    output_dir: Path,
    templates: dict[str, Path],
    language_switcher_builder: Callable[[str, Optional[str]], str],
) -> None:
    post_template = templates["post"].read_text()
    header_template = templates["header"].read_text()
    footer_html = templates["footer"].read_text()
    menu_html = templates["menu"].read_text()

    header_html = (
        header_template
        .replace("{{LANGUAGE_SWITCHER}}", language_switcher_builder("post.html", None))
        .replace("{{MENU}}", menu_html)
    )
    html = (
        post_template
        .replace("{{HEADER}}", header_html)
        .replace("{{FOOTER}}", footer_html)
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "post.html").write_text(html)
    print("✓ post.html")
