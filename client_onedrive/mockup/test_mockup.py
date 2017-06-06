#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This work was created by participants in the DataONE project, and is
# jointly copyrighted by participating institutions in DataONE. For
# more information on DataONE, see our web site at http://dataone.org.
#
#   Copyright 2009-2016 DataONE
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

import datetime

import callbacks

import d1_test.d1_test_case


class TestMockup(d1_test.d1_test_case.D1TestCase):
  def setUp(self):
    self.c = callbacks.FUSECallbacks()

  def _get_paths(self, d):
    return [f[0] for f in d]

  def test_0010(self):
    """_count_path_elements(): Returns number of path elements"""
    assert self.c._count_path_elements('') == 0
    assert self.c._count_path_elements('a') == 1
    assert self.c._count_path_elements('a/b') == 2

  def test_0020(self):
    """_get_first_path_elements(): Returns first path elements"""
    assert self.c._get_first_path_elements('a', 1) == 'a'
    assert self.c._get_first_path_elements('a/b', 1) == 'a'
    assert self.c._get_first_path_elements('a/b/c', 2) == 'a/b'
    assert self.c._get_first_path_elements('a/b/c', 10) == 'a/b/c'

  def test_0030(self):
    """_get_all_children(): Returns all sub-paths"""
    assert self._get_paths(self.c._get_all_children('')) == \
      ['d/d2/f3a', 'd/d2/f3b', 'd/f2a', 'd/f2b', 'd/f2c', 'fa', 'fb']
    assert self._get_paths(self.c._get_all_children('d/d2')) == \
      ['d/d2/f3a', 'd/d2/f3b']

  def test_0040(self):
    """_get_path_element(): Returns path element by index"""
    assert self.c._get_path_element('', 0) == ''
    assert self.c._get_path_element('a', 0) == 'a'
    assert self.c._get_path_element('a/b', 0) == 'a'
    assert self.c._get_path_element('a/b/c', 1) == 'b'
    assert self.c._get_path_element('a/b/c', 2) == 'c'

  def test_0050(self):
    """_is_direct_child(): Determine if path is path is direct child"""
    assert self.c._is_direct_child('', 'a')
    assert self.c._is_direct_child('a/b', 'a/b/c')
    assert not self.c._is_direct_child('a/b', 'a/b/c/d')
    assert not self.c._is_direct_child('a/b', 'a/b')
    assert not self.c._is_direct_child('a/b', 'a')

  def test_0060(self):
    """_get_direct_children(): Returns direct sub-paths"""
    assert self.c._get_direct_children('') == ['d', 'fa', 'fb']
    assert self.c._get_direct_children('d') == ['d2', 'f2a', 'f2b', 'f2c']
    assert self.c._get_direct_children('d/d2') == ['f3a', 'f3b']

  def test_0070(self):
    """_is_dir(): Returns True for directories"""
    assert self.c._is_dir('')
    assert self.c._is_dir('d')
    assert self.c._is_dir('d/d2')
    assert not self.c._is_dir('a')
    assert not self.c._is_dir('a/d')
    assert not self.c._is_dir('fa')
    assert not self.c._is_dir('d/f2a')

  def test_0080(self):
    """_get_meta_file(): """
    assert self.c._get_meta_file('fa') == \
      (50, datetime.datetime(2005, 5, 23, 11, 12, 13))
    assert self.c._get_meta_file('d/d2/f3b') == \
      (56, datetime.datetime(2005, 5, 23, 11, 12, 13))