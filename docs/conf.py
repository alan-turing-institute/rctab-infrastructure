"""Configuration file for the Sphinx documentation builder."""

import os
import pathlib
import sys
from importlib import metadata
from unittest.mock import MagicMock

import pulumi
import sphinx_rtd_theme

import rctab_infrastructure as ri

# Patch Pulumi so that importing constants.py doesn't cause errors


def require_or_get(*args, **kwargs):
    """A dummy method for pulumi.Config."""
    valid_values = {
        "ticker": "ab",
        "auto_deploy": "true",
        "ignore_whitelist": "true",
        "log_level": "WARNING",
        "db_root_cert_path": str(pathlib.Path(__file__).absolute()),
        "whitelist": None,
        "expiry_email_freq": "1",
    }
    if args and args[0] in valid_values:
        return valid_values[args[0]]
    return "something"


def secret(*args, **kwargs):
    """A dummy method for pulumi.Config."""
    valid_values = {
        "usage_mgmt_group": None,
    }
    if args and args[0] in valid_values:
        value = valid_values[args[0]]
    else:
        value = "something secret"

    return pulumi.Output.secret(value)


pulumi.Config = MagicMock()
pulumi.Config.return_value.require.side_effect = require_or_get
pulumi.Config.return_value.get.side_effect = require_or_get
pulumi.Config.return_value.get_secret.side_effect = secret

# -- General configuration

project = "rctab-infrastructure"
author = "The Alan Turing Institute's Research Computing Team"
copyright = f"2023, {author}"

version = metadata.version(ri.__package__)
release = version

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",
    "myst_parser",
]

# -- Options for HTML output

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ["_static"]

html_theme_options = {
    "logo_only": True,
    "display_version": True,
}

html_logo = "RCTab-hex.png"


def setup(app):
    """Tasks to perform during app setup."""
    app.add_css_file("css/custom.css")


# -- Options for autosummary extension

autosummary_generate = True

# -- Options for MyST

myst_heading_anchors = 4
