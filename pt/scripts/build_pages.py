#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.site_builder import PageSpec, render_home, render_pages, render_post_shell  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
STATIC_PAGES_DIR = ROOT / "static" / "pages"
OTHER_LANG_PREFIX = "../en"

PAGES = [
    PageSpec(
        slug="contactos",
        url="https://matildebatalha.pt/contactos-2/",
        filename="contactos.html",
        counterpart="contact.html",
    ),
    PageSpec(
        slug="curriculum-vitae",
        url="https://matildebatalha.pt/curruculum-vitae/",
        filename="curriculum-vitae.html",
        counterpart="curriculum-vitae.html",
    ),
    PageSpec(
        slug="emdr",
        url="https://matildebatalha.pt/emdr-eye-movement-desensitization-and-reprocessing/",
        filename="emdr.html",
        counterpart="emdr.html",
    ),
    PageSpec(
        slug="hipnoterapia-clinica",
        url="https://matildebatalha.pt/hipnoterapia-clinica/",
        filename="hipnoterapia-clinica.html",
        counterpart="clinical-hypnotherapy.html",
    ),
    PageSpec(
        slug="honorarios",
        url="https://matildebatalha.pt/honorarios/",
        filename="honorarios.html",
        counterpart="fees.html",
    ),
    PageSpec(
        slug="sistemas-familiares-internos",
        url="https://matildebatalha.pt/sistemas-familiares-internos/",
        filename="sistemas-familiares-internos.html",
        counterpart="internal-family-systems.html",
    ),
    PageSpec(
        slug="psicogeneologia",
        url="https://matildebatalha.pt/psicogeneologia/",
        filename="psicogeneologia.html",
        counterpart="psychogenealogy.html",
    ),
    PageSpec(
        slug="psicologia-clinica",
        url="https://matildebatalha.pt/psicologia-clinica/",
        filename="psicologia-clinica.html",
        counterpart="clinical-psychology.html",
    ),
    PageSpec(
        slug="supervisao-clinica",
        url="https://matildebatalha.pt/supervisao-clinica/",
        filename="supervisao-clinica.html",
        counterpart="clinical-supervision.html",
    ),
    PageSpec(
        slug="terapia-familiar-e-de-casal",
        url="https://matildebatalha.pt/terapia-familiar-e-de-casal/",
        filename="terapia-familiar-e-de-casal.html",
        counterpart="family-and-couple-therapy.html",
    ),
    PageSpec(
        slug="queres-trabalhar-comigo",
        url="https://matildebatalha.pt/queres-trabalhar-comigo/",
        filename="queres-trabalhar-comigo.html",
        counterpart="work-with-me.html",
    ),
]


def build_language_switcher(current: str, counterpart: str | None) -> str:
    other = f"{OTHER_LANG_PREFIX}/{counterpart}" if counterpart else f"{OTHER_LANG_PREFIX}/index.html"
    return (
        '<div class="language-switcher" aria-label="Selecionar idioma">'
        f'<a class="language-option current" href="{current}" lang="pt">🇵🇹 PT</a>'
        f'<a class="language-option" href="{other}" lang="en">🇬🇧 EN</a>'
        "</div>"
    )


def main() -> None:
    templates = {
        "base": ROOT / "templates" / "base.html",
        "header": ROOT / "templates" / "header.html",
        "footer": ROOT / "templates" / "footer.html",
        "menu": ROOT / "templates" / "menu" / "main.html",
        "home": ROOT / "templates" / "home.html",
        "post": ROOT / "templates" / "post.html",
    }
    render_home(
        output_dir=ROOT,
        templates=templates,
        language_switcher_builder=build_language_switcher,
    )
    render_pages(
        output_dir=ROOT,
        templates=templates,
        pages=PAGES,
        static_pages_dir=STATIC_PAGES_DIR,
        language_switcher_builder=build_language_switcher,
    )
    render_post_shell(
        output_dir=ROOT,
        templates=templates,
        language_switcher_builder=build_language_switcher,
    )


if __name__ == "__main__":
    main()
