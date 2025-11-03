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
OTHER_LANG_PREFIX = "../pt"

PAGES = [
    PageSpec(
        slug="contactos",
        url="https://matildebatalha.pt/contactos-2/",
        filename="contact.html",
        title="Contact",
        counterpart="contactos.html",
    ),
    PageSpec(
        slug="curriculum-vitae",
        url="https://matildebatalha.pt/curruculum-vitae/",
        filename="curriculum-vitae.html",
        title="Curriculum vitae",
        counterpart="curriculum-vitae.html",
    ),
    PageSpec(
        slug="emdr",
        url="https://matildebatalha.pt/emdr-eye-movement-desensitization-and-reprocessing/",
        filename="emdr.html",
        title="EMDR",
        counterpart="emdr.html",
    ),
    PageSpec(
        slug="hipnoterapia-clinica",
        url="https://matildebatalha.pt/hipnoterapia-clinica/",
        filename="clinical-hypnotherapy.html",
        title="Clinical Hypnotherapy",
        counterpart="hipnoterapia-clinica.html",
    ),
    PageSpec(
        slug="honorarios",
        url="https://matildebatalha.pt/honorarios/",
        filename="fees.html",
        title="Fees",
        counterpart="honorarios.html",
    ),
    PageSpec(
        slug="sistemas-familiares-internos",
        url="https://matildebatalha.pt/sistemas-familiares-internos/",
        filename="internal-family-systems.html",
        title="Internal Family Systems",
        counterpart="sistemas-familiares-internos.html",
    ),
    PageSpec(
        slug="psicogeneologia",
        url="https://matildebatalha.pt/psicogeneologia/",
        filename="psychogenealogy.html",
        title="Psychogenealogy & Transgenerational Therapy",
        counterpart="psicogeneologia.html",
    ),
    PageSpec(
        slug="psicologia-clinica",
        url="https://matildebatalha.pt/psicologia-clinica/",
        filename="clinical-psychology.html",
        title="Clinical Psychology",
        counterpart="psicologia-clinica.html",
    ),
    PageSpec(
        slug="supervisao-clinica",
        url="https://matildebatalha.pt/supervisao-clinica/",
        filename="clinical-supervision.html",
        title="Clinical Supervision",
        counterpart="supervisao-clinica.html",
    ),
    PageSpec(
        slug="terapia-familiar-e-de-casal",
        url="https://matildebatalha.pt/terapia-familiar-e-de-casal/",
        filename="family-and-couple-therapy.html",
        title="Family & Couple Therapy",
        counterpart="terapia-familiar-e-de-casal.html",
    ),
    PageSpec(
        slug="queres-trabalhar-comigo",
        url="https://matildebatalha.pt/queres-trabalhar-comigo/",
        filename="work-with-me.html",
        title="Work with me",
        counterpart="queres-trabalhar-comigo.html",
    ),
]


def build_language_switcher(current: str, counterpart: str | None) -> str:
    other = f"{OTHER_LANG_PREFIX}/{counterpart}" if counterpart else f"{OTHER_LANG_PREFIX}/index.html"
    return (
        '<div class="language-switcher" aria-label="Select language">'
        f'<a class="language-option" href="{other}" lang="pt">🇵🇹 PT</a>'
        f'<a class="language-option current" href="{current}" lang="en">🇬🇧 EN</a>'
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
