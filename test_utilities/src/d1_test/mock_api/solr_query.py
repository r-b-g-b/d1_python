#!/usr/bin/env python

# This work was created by participants in the DataONE project, and is
# jointly copyrighted by participating institutions in DataONE. For
# more information on DataONE, see our web site at http://dataone.org.
#
#   Copyright 2009-2019 DataONE
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
"""Mock:

CNRead.query(session, queryEngine, query) → OctetStream
https://releases.dataone.org/online/api-documentation-v2.0.1/apis/CN_APIs.html#CNRead.query
MNQuery.query(session, queryEngine, query) → OctetStream
http://jenkins-1.dataone.org/jenkins/job/API%20Documentation%20-%20trunk/ws/api-documentation/build/html/apis/MN_APIs.html#MNQuery.query

A DataONEException can be triggered by adding a custom header. See
d1_exception.py

"""

import re

import responses

import d1_common.url

import d1_test.mock_api.util

# Config

QUERY_ENDPOINT_RX = r"v([123])/query(/(.*))?"


def add_callback(base_url):
    responses.add_callback(
        responses.GET,
        re.compile(r"^" + d1_common.url.joinPathElements(base_url, QUERY_ENDPOINT_RX)),
        callback=d1_test.mock_api.util.echo_get_callback,
        content_type="",
    )
