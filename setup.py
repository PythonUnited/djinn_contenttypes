import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'django',
    'requests',
    'djinn_core',
    'django-bootstrap-form',
    'djinn_forms>=1.2.3',
    'djinn_workflow'
    ]

setup(name='djinn_contenttypes',
      version="1.4.6",
      description='Djinn Intranet Contenttypes framework',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Framework :: Django",
          "Intended Audience :: Developers",
          "License :: Freely Distributable",
          "Programming Language :: Python",
          "Topic :: Internet :: WWW/HTTP :: Site Management",
          "Topic :: Software Development :: Libraries :: "
          "Application Frameworks"
      ],
      author='PythonUnited',
      author_email='info@pythonunited.com',
      license='beer-ware',
      url='https://github.com/PythonUnited/djinn-contenttypes',
      keywords='Djinn Contenttypes',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="djinn-contenttypes",
      entry_points="""\
      [djinn.app]
      js=djinn_contenttypes:get_js
      css=djinn_contenttypes:get_css
      urls=djinn_contenttypes:get_urls
      """
      )
