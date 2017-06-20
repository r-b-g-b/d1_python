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

from __future__ import absolute_import

import logging

import cryptography.hazmat.backends.openssl.x509
import freezegun

import d1_common.cert.subject_info
import d1_common.cert.subjects
import d1_common.cert.x509

import d1_test.d1_test_case


class TestCert(d1_test.d1_test_case.D1TestCase):
  cert_simple_subject_info_pem = d1_test.d1_test_case.D1TestCase.load_sample(
    'cert_with_simple_subject_info.pem'
  )
  cert_no_subject_info_pem = d1_test.d1_test_case.D1TestCase.load_sample(
    'cert_without_subject_info.pem'
  )

  def test_0010(self):
    """Deserialize PEM to cryptography.Certificate object"""
    cert_obj = d1_common.cert.x509.deserialize_pem(
      self.cert_simple_subject_info_pem
    )
    assert type(
      cert_obj
    ) == cryptography.hazmat.backends.openssl.x509._Certificate

  def test_0020(self):
    """Extract primary subject from certificate and returns as
    DataONE compliant serialization
    """
    cert_obj = d1_common.cert.x509.deserialize_pem(
      self.cert_simple_subject_info_pem
    )
    primary_str = d1_common.cert.x509.extract_subject_from_dn(cert_obj)
    assert primary_str == 'CN=Roger Dahl A1779,O=Google,C=US,DC=cilogon,DC=org'

  def test_0030(self):
    """Extract SubjectInfo from certificate, SubjectInfo present"""
    cert_obj = d1_common.cert.x509.deserialize_pem(
      self.cert_simple_subject_info_pem
    )
    extracted_subject_info_xml = d1_common.cert.x509.extract_subject_info_extension(
      cert_obj
    )
    self.assert_equals_sample(
      extracted_subject_info_xml, 'cert_simple_subject_info'
    )

  def test_0040(self):
    """Extract SubjectInfo from certificate, SubjectInfo missing"""
    cert_obj = d1_common.cert.x509.deserialize_pem(
      self.cert_no_subject_info_pem
    )
    missing_subject_info = d1_common.cert.x509.extract_subject_info_extension(
      cert_obj
    )
    assert missing_subject_info is None

  def test_0050(self):
    """Extract primary and equivalent subjects from certificate, SubjectInfo
    present
    """
    primary_str, equivalent_set = d1_common.cert.subjects.extract_subjects(
      self.cert_simple_subject_info_pem
    )
    assert primary_str == \
      'CN=Roger Dahl A1779,O=Google,C=US,DC=cilogon,DC=org'
    assert sorted(equivalent_set) == \
      [
        'CN=Roger Dahl A1779,O=Google,C=US,DC=cilogon,DC=org',
        'verifiedUser',
      ]

  def test_0060(self):
    """Extract primary and equivalent subjects from certificate, SubjectInfo
    missing
    """
    primary_str, equivalent_set = d1_common.cert.subjects.extract_subjects(
      self.cert_no_subject_info_pem
    )
    assert primary_str == \
      'CN=Roger Dahl A538,O=Google,C=US,DC=cilogon,DC=org'
    assert equivalent_set == set()

  @freezegun.freeze_time('2021-01-01')
  def test_0070(self):
    """log_cert_info(): Outputs expected log"""
    cert_obj = d1_common.cert.x509.deserialize_pem(
      self.cert_simple_subject_info_pem
    )
    with d1_test.d1_test_case.capture_log() as log_stream:
      d1_common.cert.x509.log_cert_info(logging.warn, 'test msg', cert_obj)
    self.assert_equals_sample(
      log_stream.getvalue(), 'x509_log_cert_info_expected'
    )
