"""Sphinx configuration for the FalkorDB Python ORM documentation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

project = "FalkorDB Python ORM"
author = "FalkorDB Team"
copyright = "2026, FalkorDB"
release = "1.2.2"
version = release

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "README.md",
    "MIGRATION_GUIDE.md",
    "api/decorators.md",
    "api/repository.md",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

html_theme = "furo"
html_title = "FalkorDB Python ORM"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "top_of_page_buttons": ["view", "edit"],
    "source_repository": "https://github.com/FalkorDB/falkordb-py-orm/",
    "source_branch": "main",
    "source_directory": "docs/",
    "light_css_variables": {
        "color-brand-primary": "`#e92063`",
        "color-brand-content": "`#c0185b`",
        "color-sidebar-background": "`#fbfbff`",
        "color-sidebar-background-border": "`#e4e7f0`",
        "color-sidebar-link-text--top-level": "`#252a39`",
        "color-sidebar-item-background--current": "`#fce7f0`",
        "color-sidebar-item-expander-background--hover": "`#f7d7e4`",
        "color-highlight-on-target": "`#fff1f6`",
        "font-stack": "Inter, Aptos, Segoe UI, sans-serif",
        "font-stack--monospace": "IBM Plex Mono, SFMono-Regular, Consolas, monospace",
    },
    "dark_css_variables": {
        "color-brand-primary": "`#ff6fa3`",
        "color-brand-content": "`#ff8ab3`",
        "color-sidebar-background": "`#11131b`",
        "color-sidebar-background-border": "`#2b3040`",
        "color-sidebar-link-text--top-level": "`#ece9f2`",
        "color-sidebar-item-background--current": "`#341726`",
        "color-sidebar-item-expander-background--hover": "`#432034`",
        "color-highlight-on-target": "`#2b1825`",
        "font-stack": "Inter, Aptos, Segoe UI, sans-serif",
        "font-stack--monospace": "IBM Plex Mono, SFMono-Regular, Consolas, monospace",
    },
}

html_context = {
    "github_user": "FalkorDB",
    "github_repo": "falkordb-py-orm",
    "github_version": "main",
    "doc_path": "docs",
}

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_typehints = "description"
autodoc_member_order = "bysource"
napoleon_google_docstring = True
napoleon_numpy_docstring = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True