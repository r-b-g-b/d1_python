#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This work was created by participants in the DataONE project, and is
# jointly copyrighted by participating institutions in DataONE. For
# more information on DataONE, see our web site at http://dataone.org.
#
#   Copyright 2013 DataONE
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""DataONE Test Utilities package
"""
import setuptools


def main():
  setuptools.setup(
    name='dataone.test_utilities',
    version='2.3.0rc1',
    description='Utilities for testing DataONE infrastructure components',
    author='DataONE Project',
    author_email='developers@dataone.org',
    url='https://github.com/DataONEorg/d1_python',
    license='Apache License, Version 2.0',
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
      'dataone.libclient == 2.3.0rc1',
      #
      'contextlib2 == 0.5.5',
      'decorator == 4.0.11',
      'freezegun == 0.3.9',
      'lxml == 3.7.3',
      'mock == 2.0.0',
      'multi-mechanize == 1.2.0',
      'pyasn1 == 0.2.3',
      'pyxb == 1.2.5',
      'rdflib == 4.2.2',
      'requests == 2.14.2',
      'responses == 0.5.1',
      'setuptools == 35.0.2',
    ],
    setup_requires=[
      'setuptools_git >= 1.1',
    ],
    classifiers=[
      'Development Status :: 5 - Production/Stable',
      'Intended Audience :: Developers',
      'Topic :: Scientific/Engineering',
      'License :: OSI Approved :: Apache 2.0 License',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 2.7',
    ],
    keywords=(
      'DataONE source code unit tests ingeration tests coverage travis '
      'coveralls'
    ),
  )


if __name__ == '__main__':
  main()