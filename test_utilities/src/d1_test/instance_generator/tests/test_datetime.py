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

import logging
import time
import unittest

import d1_test.d1_test_case
import d1_test.instance_generator.dates as dates

#===============================================================================


class TestDateTime(d1_test.d1_test_case.D1TestCase):
  def setUp(self):
    pass

  def test_0010(self):
    """random_date(): Dates are random"""
    for i in range(10):
      t1 = dates.random_date()
      t2 = dates.random_date()
      assert t1 != t2

  def test_0020(self):
    """random_date(): Dates are random, with restricted time span"""
    for i in range(10):
      t1 = dates.random_date(100, 200)
      t2 = dates.random_date(50, 60)
      assert t2 < t1

  def test_0030(self):
    """now()"""
    for i in range(10):
      now_1 = dates.now()
      time.sleep(0.01)
      now_2 = dates.now()
      assert now_2 > now_1


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  unittest.main()