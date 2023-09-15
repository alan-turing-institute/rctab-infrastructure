"""Configuration file for the Sphinx documentation builder."""
from importlib import metadata

import rctab_infrastructure as ri

project = "rctab-infrastructure"
author = "The Alan Turing Institute's Research Computing Team"
copyright = f"2023, {author}"

# -- General configuration ---------------------------------------------------

version = metadata.version(ri.__package__)
release = version

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "alabaster"
html_static_path = ["_static"]

# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
]

# -- Options for HTML output

html_theme = "sphinx_rtd_theme"
