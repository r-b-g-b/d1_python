#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:mod:`setup`
====================

:Synopsis: Create egg.
:Author: DataONE (Dahl)
"""

from setuptools import setup, find_packages
import d1_client

setup(
  name='DataONE_ClientLib',
  version=d1_client.__version__,
  description='A DataONE client library for Python',
  author='Dave Vieglais',
  author_email='vieglais at ku edu',
  url='http://dataone.org',
  license='Apache License, Version 2.0',
  packages = find_packages(),

  # Dependencies that are available through PYPI / easy_install.
  install_requires = [
    'DataONE_Common >= 1.0.0c6',
  ],

  package_data = {
  }
)
