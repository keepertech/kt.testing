# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

import os


# -- Project information -----------------------------------------------------

project = 'kt.testing'
copyright = '2020, Keeper Technology LLC'
author = 'Keeper Technology'

# The full version, including alpha/beta/rc tags
release = os.environ.get('KT_VERSION') or ''
version = release or '(development)'

# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autodoc.typehints',
    'sphinx.ext.intersphinx',
]


intersphinx_mapping = {
    'python': (
        'https://docs.python.org/3', None),
    'zope.exceptions': (
        'https://zopeexceptions.readthedocs.io/en/latest', None),
    'zope.component': (
        'https://zopecomponent.readthedocs.io/en/latest', None),
    'zope.interface': (
        'https://zopeinterface.readthedocs.io/en/latest', None),
    'zope.schema': (
        'https://zopeschema.readthedocs.io/en/latest', None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = []

source_suffix = '.rst'
master_doc = 'index'
language = None
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    # 'issues_url': 'https://github.com/keepertech/kt.testing/issues/',
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

html_last_updated_fmt = ''


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'kt-testing'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'kt-testing.tex', 'kt.testing Documentation',
     'Keeper Technology', 'manual'),
]


autodoc_default_options = {
    'members': True,
    'inherited-members': True,
    'special-members': '__init__',
    # 'show-inheritance': False,
}

autoclass_content = 'class'
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'

# Bibliographic Dublin Core info.
epub_title = 'kt.testing'

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']
