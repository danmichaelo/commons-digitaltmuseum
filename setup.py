from setuptools import setup

setup(name='digitaltmuseum',
      version='0.1',
      description='Wikimedia tooling for Digitalt museum',
      url='http://github.com/danmichaelo/digitaltmuseum',
      author='Dan Michael O. Heggø',
      author_email='danmichaelo@gmail.com',
      license='MIT',
      packages=['digitaltmuseum'],
      install_requires=['flask',
                        'pyyaml',
                        'mwclient',
                        'mwtemplates',
                        #'oursql',
                        'beautifulsoup4',
                        #flup
                        'flask',
                        'six',
                        'requests[security]',
                        ],
      zip_safe=False)
