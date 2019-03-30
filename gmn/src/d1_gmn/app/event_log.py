
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
"""Event Log utilities.

The Event Log is a log of all operations performed on SciObjs. It is retrieved with
MNCore.getLogRecords() and aggregated by CNs.

"""
import re

import d1_gmn.app.auth
import d1_gmn.app.models

import d1_common.types.exceptions

import django.conf


def create_log_entry(object_model, event, ip_address, user_agent, subject):
    event_log_model = d1_gmn.app.models.EventLog()
    event_log_model.sciobj = object_model
    event_log_model.event = d1_gmn.app.models.event(event)
    event_log_model.ip_address = d1_gmn.app.models.ip_address(ip_address)
    event_log_model.user_agent = d1_gmn.app.models.user_agent(user_agent)
    event_log_model.subject = d1_gmn.app.models.subject(subject)
    event_log_model.save()
    return event_log_model


def create(pid, request, timestamp=None):
    _log(pid, request, 'create', timestamp)


def log_read_event(pid, request, timestamp=None):
    if not _is_ignored_read_event(request):
        _log(pid, request, 'read', timestamp)


def log_update_event(pid, request, timestamp=None):
    _log(pid, request, 'update', timestamp)


def log_delete_event(pid, request, timestamp=None):
    _log(pid, request, 'delete', timestamp)


def log_replicate_event(pid, request, timestamp=None):
    _log(pid, request, 'replicate', timestamp)


def log_synchronization_failed_event(pid, request, timestamp=None):
    _log(pid, request, 'synchronization_failed', timestamp)


def log_replication_failed_event(pid, request, timestamp=None):
    _log(pid, request, 'replication_failed', timestamp)


def has_event_log(pid):
    d1_gmn.app.models.EventLog.objects.filter(sciobj__pid__did=pid).exists()


def _log(pid, request, event, timestamp=None):
    """Log an operation that was performed on a sciobj."""
    # Support logging events that are not associated with an object.
    sciobj_model = None
    if pid is not None:
        try:
            sciobj_model = d1_gmn.app.models.ScienceObject.objects.filter(pid__did=pid)[
                0
            ]
        except IndexError:
            raise d1_common.types.exceptions.ServiceFailure(
                0,
                'Attempted to create event log for non-existing object. pid="{}"'.format(
                    pid
                ),
            )

    event_log_model = create_log_entry(
        sciobj_model,
        event,
        request.META['REMOTE_ADDR'],
        request.META.get('HTTP_USER_AGENT', '<not provided>'),
        request.primary_subject_str,
    )

    # The datetime is an optional parameter. If it is not provided, a
    # "auto_now_add=True" value in the the model defaults it to Now. The
    # disadvantage to this approach is that we have to update the timestamp in a
    # separate step if we want to set it to anything other than Now.
    if timestamp is not None:
        event_log_model.timestamp = timestamp
        event_log_model.save()


def _is_ignored_read_event(request):
    """Return True if this read event was generated by an automated process, as
    indicated by the user configurable LOG_IGNORE* settings.

    See settings_site.py for description and rationale for the settings.

    """
    if (
        django.conf.settings.LOG_IGNORE_TRUSTED_SUBJECT
        and d1_gmn.app.auth.is_trusted_subject(request)
    ):
        return True
    if (
        django.conf.settings.LOG_IGNORE_NODE_SUBJECT
        and d1_gmn.app.auth.is_client_side_cert_subject(request)
    ):
        return True
    if _has_regex_match(
        request.META['REMOTE_ADDR'], django.conf.settings.LOG_IGNORE_IP_ADDRESS
    ):
        return True
    if _has_regex_match(
        request.META.get('HTTP_USER_AGENT', '<not provided>'),
        django.conf.settings.LOG_IGNORE_USER_AGENT,
    ):
        return True
    if _has_regex_match(
        request.primary_subject_str, django.conf.settings.LOG_IGNORE_SUBJECT
    ):
        return True
    return False


def _has_regex_match(s, rx_list):
    for rx_str in rx_list:
        if re.match(rx_str, s, re.IGNORECASE):
            return True
    return False
