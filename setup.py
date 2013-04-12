from distutils.core import setup
import os
from setuptools import find_packages

# Find all packages here and below (should find ipanema and its children).
packages = find_packages()

setup(name='django-flexible-content',
      version='0.9.0',
      packages=packages,
      include_package_data=True,
      install_requires=['Django >= 1.4',
                        # Required for the multi-table inheritance fanciness
                        # used by content items. Not really *required*, but it
                        # has a cool InheritanceManager/InheritanceQuerySet
                        # that makes queries more efficient.
                        'django-model-utils',
                        # This lets the Video type verify YouTube and Vimeo IDs
                        'requests'])
