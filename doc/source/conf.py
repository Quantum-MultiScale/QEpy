import sys
import sphinx_rtd_theme
import os
project = 'QEpy'
copyright = '2019-2024 QEpy community'
author = 'QEpy Developers'
release = '7.2.0'

header = '../../qepy/__init__.py'
if os.path.isfile(header):
    with open(header, 'r') as fh:
        for line in fh :
            if '__version__' in line:
                release = line.split('=')[1]
                break


source_suffix = '.rst'
master_doc = 'index'

nbsphinx_execute = 'never'

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.doctest',
              'sphinx.ext.mathjax',
              'sphinx.ext.viewcode',
              'sphinx.ext.napoleon',
              'sphinx.ext.intersphinx',
              'sphinx.ext.autosummary',
              'sphinx_copybutton',
              'sphinx_inline_tabs',
              'nbsphinx',
              'sphinx_panels',
              ]

templates_path = ['templates']
exclude_patterns = ['build']
# exclude_patterns = ['build', 'source/tutorials/jupyter/*ipynb']

html_theme = 'sphinx_rtd_theme'
# html_theme = 'sphinx_bootstrap_theme'
# html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
# html_favicon = 'static/qepy.ico'
# html_logo = 'static/qepy.png'
html_style = 'custom.css'
html_static_path = ['static']
html_last_updated_fmt = '%A, %d %b %Y %H:%M:%S'

html_theme_options = {
    'prev_next_buttons_location': 'both',
}

latex_show_urls = 'inline'
latex_show_pagerefs = True
latex_engine = 'xelatex'
latex_documents = [('index', 'QEpy.tex', 'QEpy', 'QEpy-Developers', 'howto', not True)]


smartquotes = False


#Add external links to source code
def linkcode_resolve(domain, info):
    print('info module', info)
    if domain != 'py' or not info['module']:
        return None

    filename = info['module'].replace('.', '/')+'.py'
    return "https ://gitlab.com/shaoxc/qepy/tree/master/%s" % filename
