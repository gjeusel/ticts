#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

import sphinx_rtd_theme

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "IPython.sphinxext.ipython_console_highlighting",
    "IPython.sphinxext.ipython_directive",
]

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False

# Embed Ipython configuration:
ipython_mplbackend = ""

# Execute ipython_startup_file before each ipython embed
ipython_startup_file = Path(__file__).parent / "ipython_init.py"
content = open(ipython_startup_file).read()
ipython_execlines = [content]

# Add any paths that contain templates here, relative to this directory.
# templates_path = ['.']
templates_path = ["_templates"]

if os.getenv("SPELLCHECK"):
    extensions += ("sphinxcontrib.spelling", )
    spelling_show_suggestions = True
    spelling_lang = "en_US"

# The suffix(es) of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = u"ticts"
author = ""

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# Disable docstring inheritance
autodoc_inherit_docstrings = False

extlinks = {
    # 'issue': ('https://github.com/gjeusel/ticts/issues
    # 'pr': ('https://github.com/gjeusel/ticts/pulls
}

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "collapse_navigation": False,
    "display_version": True,
    "logo_only": True,
}

html_logo = "_static/img/logo.svg"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_context = {
    "css_files": [
        "https://fonts.googleapis.com/css?family=Lato",
        "_static/css/custom_theme.css",
    ]
}
