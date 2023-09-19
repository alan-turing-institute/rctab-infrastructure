"""Configuration file for the Sphinx documentation builder."""
import os
import pathlib
import sys
from importlib import metadata
from unittest.mock import MagicMock

import pulumi
import sphinx_rtd_theme

import rctab_infrastructure as ri

# Add repo root to path for autodoc

sys.path.insert(0, os.path.abspath(".."))

# Patch Pulumi so that importing constants.py doesn't cause errors


def require_or_get(*args, **kwargs):
    """A dummy method for pulumi.Config."""
    if args:
        if args[0] == "ticker":
            # A valid ticker
            return "ab"
        elif args[0] in ("auto_deploy", "ignore_whitelist"):
            return "true"
        elif args[0] == "whitelist":
            return "00000000-0000-0000-0000-000000000000"
        elif args[0] == "log_level":
            return "WARNING"
        elif args[0] == "db_root_cert_path":
            return str(pathlib.Path(__file__).absolute())
    return "something"


def secret(*args, **kwargs):
    """A dummy method for pulumi.Config."""
    return pulumi.Output.secret("something secret")


pulumi.Config = MagicMock()
pulumi.Config.return_value.require.side_effect = require_or_get
pulumi.Config.return_value.get.side_effect = require_or_get
pulumi.Config.return_value.get_secret.side_effect = secret

# General configuration

project = "rctab-infrastructure"
author = "The Alan Turing Institute's Research Computing Team"
copyright = f"2023, {author}"

version = metadata.version(ri.__package__)
release = version

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_logo = "RCTab-hex.png"
html_theme_options = {
    "logo_only": True,
    "display_version": True,
}

# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
]

# -- Options for HTML output

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ["_static"]

html_logo = "RCTab-hex.png"


def setup(app):
    """Tasks to perform during app setup."""
    app.add_css_file("css/custom.css")
