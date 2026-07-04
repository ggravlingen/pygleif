"""Sphinx configuration for pygleif documentation."""

from __future__ import annotations

import pathlib

version_file = pathlib.Path(__file__).resolve().parent.parent / "pygleif" / "VERSION"
release = version_file.read_text().strip()
version = release

project = "pygleif"
copyright = "2026, Patrik"  # noqa: A001
author = "Patrik"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "myst_parser",
]

myst_enable_extensions = [
    "colon_fence",
]

autosummary_generate = True
autodoc_typehints = "description"
autodoc_member_order = "bysource"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}

templates_path: list[str] = []
exclude_patterns: list[str] = []

html_theme = "furo"


def _skip_parametrized_generics(
    app: object,  # noqa: ARG001 - sphinx callback signature
    what: str,  # noqa: ARG001
    name: str,
    obj: object,  # noqa: ARG001
    skip: bool,  # noqa: FBT001
    options: object,  # noqa: ARG001
) -> bool:
    """Skip pydantic's synthetic ``Model[Param]`` module members.

    Pydantic v2 registers each parametrized generic model (e.g.
    ``ResourceData[CountryAttributes]``) in the defining module's
    namespace; documenting them duplicates the generic base classes.
    """
    return skip or "[" in name


def setup(app) -> None:  # noqa: ANN001 - sphinx application
    """Register the autodoc skip hook."""
    app.connect("autodoc-skip-member", _skip_parametrized_generics)
