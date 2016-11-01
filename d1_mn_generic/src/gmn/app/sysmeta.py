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

"""Utilities for manipulating System Metadata

- Translate System Metadata between XML and PyXB.
- Translate System Metadata between PyXB and GMN database representations.
- Query the database for System Metadata properties.
"""

# Stdlib.
import datetime

# App

import d1_common.date_time
import d1_common.types.dataoneTypes
import d1_common.types.exceptions
import app.auth
import app.models
import app.util
import pyxb
import sysmeta_obsolescence
import sysmeta_replica
import sysmeta_sid
import sysmeta_util


def archive_object(pid):
  """Set the status of an object as archived.

  Preconditions:
  - The object with the pid is verified to exist.
  - The object is not a replica.
  - The object is not archived.
  """
  sciobj_row = sysmeta_util.get_sci_row(pid)
  sciobj_row.is_archived = True
  sciobj_row.save()
  _update_modified_timestamp(sciobj_row)


# ------------------------------------------------------------------------------
# XML
# ------------------------------------------------------------------------------

def deserialize(sysmeta_xml):
  if not isinstance(sysmeta_xml, unicode):
    try:
      sysmeta_xml = sysmeta_xml.decode('utf8')
    except UnicodeDecodeError as e:
      raise d1_common.types.exceptions.InvalidRequest(
        0,
        u'The System Metadata XML doc is not valid UTF-8 encoded Unicode. '
        u'error="{}", xml="{}"'.format(str(e), sysmeta_xml)
      )
  try:
    return d1_common.types.dataoneTypes_v2_0.CreateFromDocument(sysmeta_xml)
  except pyxb.ValidationError as e:
    err_str = e.details()
  except pyxb.PyXBException as e:
    err_str = str(e)
  raise d1_common.types.exceptions.InvalidSystemMetadata(
    0,
    u'System Metadata XML doc validation failed. error="{}", xml="{}"'
      .format(err_str, sysmeta_xml)
  )


def serialize(sysmeta_obj):
  try:
    return sysmeta_obj.toxml().encode('utf-8')
  except pyxb.IncompleteElementContentError as e:
    raise d1_common.types.exceptions.ServiceFailure(
      0,
      u'Unable to serialize PyXB to XML. error="{}"'.format(
        e.details
      )
    )

# ------------------------------------------------------------------------------

def create(sysmeta_obj, url):
  """Create database representation of a System Metadata object and closely
  related internal state.

  Preconditions:
  - PID is verified not to exist. E.g., with view_asserts.is_unused(pid).
  - Any supplied SID is verified to be valid for the given operation. E.g., with
  view_asserts.is_valid_sid_for_chain_if_specified().

  Postconditions:
  - New rows are created in ScienceObject, Permission and related tables as
  necessary to hold portions of the System Metadata XML document and
  internal values that are required for performance when processing requests.

  Notes:
  - The authoritative location for System Metadata is the XML files that are
  stored in the directory tree managed by the sysmeta_file module. The XML files
  are created and updated first, then the database is updated to match.
  - The System Metadata portions of the database are essentially a cache of the
  actual System Metadata that enables processing of requests without having to
  read and deserialize the XML files.
  """
  pid = sysmeta_obj.identifier.value()
  sci_row = app.models.ScienceObject()
  sci_row.pid = app.models.did(pid)
  _base_pyxb_to_model(sci_row, sysmeta_obj, url)
  sci_row.save()
  _access_policy_pyxb_to_model(sci_row, sysmeta_obj)
  return sci_row
  # _update_obsolescence_chain(sci_row, sysmeta_obj)
  # _update_sid(sci_row, sysmeta_obj).
  # _update_modified_timestamp(sci_row, sysmeta_obj)


def update(sysmeta_obj, url=None):
  """Update database representation of a System Metadata object. The System
  Metadata must already be verified to be correct and suitable for the
  operation which is being performed.
  """
  pid = sysmeta_obj.identifier.value()
  sci_row = sysmeta_util.get_sci_row(pid)
  _base_pyxb_to_model(sci_row, sysmeta_obj, url=url)
  _access_policy_pyxb_to_model(sci_row, sysmeta_obj)


def update_sci_row(sysmeta_obj, url=None):
  pid = sysmeta_obj.identifier.value()
  sci_row = sysmeta_util.get_sci_row(pid)
  _base_pyxb_to_model(sci_row, sysmeta_obj, url=url)


def update_access_policy(sysmeta_obj):
  pid = sysmeta_obj.identifier.value()
  sci_row = sysmeta_util.get_sci_row(pid)
  _access_policy_pyxb_to_model(sci_row, sysmeta_obj)


def is_did(did):
  return app.models.IdNamespace.objects.filter(
    did=did).exists()


def is_pid(did):
  """An identifier is a PID if it exists in IdNamespace and is not a SID.
  Includes unprocessed replicas and obsolescence chain placeholders for remote
  objects.
  """
  return is_did(did) and not app.sysmeta_sid.is_sid(did)


def is_pid_of_existing_object(pid):
  """Excludes SIDs, unprocessed replicas and obsolescence chain placeholders for
  remote objects.
  """
  return app.models.ScienceObject.objects.filter(
    pid__did=pid).exists()


def is_archived(pid):
  return is_pid_of_existing_object(pid) \
         and sysmeta_util.get_sci_row(pid).is_archived


def update_modified_timestamp(pid):
  sci_row = sysmeta_util.get_sci_row(pid)
  _update_modified_timestamp(sci_row)


def pyxb_to_model(sysmeta_obj, url=None):
  return _pyxb_to_model(sysmeta_obj, url)


def model_to_pyxb(pid):
  return _model_to_pyxb(pid)


def get_identifier_type(did):
  if not app.sysmeta.is_did(did):
    return u'unused on this Member Node'
  elif app.sysmeta_sid.is_sid(did):
    return u'a Series ID (SID)'
  elif app.sysmeta.is_pid_of_existing_object(did):
    return u'a Persistent ID (PID) of an existing local object'
  elif app.sysmeta_re.is_local_replica(did):
    return u'a Persistent ID (PID) of a local replica'
  elif app.sysmeta.is_obsolescence_chain_placeholder(did):
    return \
      u'a Persistent ID (PID) that is reserved due to being referenced in ' \
      u'the obsolescence chain of a local replica'
  else:
    assert False, u'Unable to classify identifier'

#
# Private
#


# _update_access_policy(sci_row, sysmeta_obj)
# _update_sid(sci_row, sysmeta_obj)
# _update_modified_timestamp(sci_row, sysmeta_obj)


def _pyxb_to_model(sysmeta_obj, url=None):
  # Depends on Django's implicit view transactions (ATOMIC_REQUESTS).
  sciobj_model = sysmeta_util.get_sci_row(sysmeta_obj.identifier.value())
  _base_pyxb_to_model(sciobj_model, sysmeta_obj, url, is_replica_bool)
  _access_policy_pyxb_to_model(sciobj_model, sysmeta_obj)
  sysmeta_obj.replicationPolicy = _access_policy_model_to_pyxb(sciobj_model)
  sysmeta_obj.replica = _replica_model_to_pyxb(sciobj_model)
  sciobj_model.save()


def _model_to_pyxb(pid):
  sciobj_model = sysmeta_util.get_sci_row(pid)
  sysmeta_obj = _base_model_to_pyxb(sciobj_model)
  access_policy_pyxb = _access_policy_model_to_pyxb(sciobj_model)
  if len(access_policy_pyxb.allow):
    sysmeta_obj.accessPolicy = access_policy_pyxb
  if _has_replication_policy(sciobj_model):
    sysmeta_obj.replicationPolicy = _replication_policy_model_to_pyxb(sciobj_model)
  sysmeta_obj.replica = sysmeta_replica.replica_model_to_pyxb(sciobj_model)
  return sysmeta_obj


def _base_pyxb_to_model(sci_row, sysmeta_obj, url=None):
  # The PID is used for looking up the sci_row so will always match and does
  # need to be updated.
  #
  # Any SID in the sysmeta is not updated in the DB here because the DB version
  # of the SID is used for mapping directly to the last PID in the chain. Since
  # any number of objects in a chain may specify (the same) SID for the chain,
  # updating the SID here would cause it to map to the object with the most
  # recently modified sysmeta in the chain.
  #
  # System Metadata fields
  sci_row.serial_version = sysmeta_obj.serialVersion
  sci_row.modified_timestamp = sysmeta_obj.dateSysMetadataModified
  sci_row.uploaded_timestamp = sysmeta_obj.dateUploaded
  sci_row.format = app.models.format(sysmeta_obj.formatId)
  sci_row.checksum = sysmeta_obj.checksum.value()
  sci_row.checksum_algorithm = app.models.checksum_algorithm(
    sysmeta_obj.checksum.algorithm
  )
  sci_row.size = sysmeta_obj.size
  sci_row.submitter = app.models.subject(sysmeta_obj.submitter.value())
  sci_row.rights_holder = app.models.subject(sysmeta_obj.rightsHolder.value())
  sci_row.origin_member_node = app.models.node(sysmeta_obj.originMemberNode.value())
  sci_row.authoritative_member_node = app.models.node(sysmeta_obj.authoritativeMemberNode.value())
  sysmeta_obsolescence._set_obsolescence(
    sci_row,
    sysmeta_util.get_value(sysmeta_obj, 'obsoletes'),
    sysmeta_util.get_value(sysmeta_obj, 'obsoletedBy'),
  )
  sci_row.is_archived = sysmeta_obj.archived or False
  # Internal fields
  if url is not None:
    sci_row.url = url

def _base_model_to_pyxb(sciobj_model):
  def sub_sciobj(sub_sciobj_model):
    if sub_sciobj_model is None:
      return None
    return sub_sciobj_model.did

  base_pyxb = d1_common.types.dataoneTypes.systemMetadata()
  base_pyxb.identifier = d1_common.types.dataoneTypes.Identifier(sciobj_model.pid.did)
  base_pyxb.serialVersion = sciobj_model.serial_version
  base_pyxb.dateSysMetadataModified = sciobj_model.modified_timestamp
  base_pyxb.dateUploaded = sciobj_model.uploaded_timestamp
  base_pyxb.formatId = sciobj_model.format.format
  base_pyxb.checksum = d1_common.types.dataoneTypes.Checksum(sciobj_model.checksum)
  base_pyxb.checksum.algorithm = sciobj_model.checksum_algorithm.checksum_algorithm
  base_pyxb.size = sciobj_model.size
  base_pyxb.submitter = sciobj_model.submitter.subject
  base_pyxb.rightsHolder = sciobj_model.rights_holder.subject
  base_pyxb.originMemberNode = sciobj_model.origin_member_node.urn
  base_pyxb.authoritativeMemberNode = sciobj_model.authoritative_member_node.urn
  base_pyxb.obsoletes = sub_sciobj(sciobj_model.obsoletes)
  base_pyxb.obsoletedBy = sub_sciobj(sciobj_model.obsoleted_by)
  base_pyxb.archived = sciobj_model.is_archived
  base_pyxb.seriesId = sysmeta_sid.get_sid_by_pid(sciobj_model.pid.did)

  return base_pyxb

# ------------------------------------------------------------------------------
# Access Policy
# ------------------------------------------------------------------------------


def _access_policy_pyxb_to_model(sci_row, sysmeta_obj):
  """Create or update the database representation of the sysmeta_obj access
  policy.

  If called without an access policy, any existing permissions on the object
  are removed and the access policy for the rights holder is recreated.

  Preconditions:
    - Each subject has been verified to a valid DataONE account.
    - Subject has changePermission for object.

  Postconditions:
    - The Permission and related tables contain the new access policy.

  Notes:
    - There can be multiple rules in a policy and each rule can contain multiple
      subjects. So there are two ways that the same subject can be specified
      multiple times in a policy. If this happens, multiple, conflicting action
      levels may be provided for the subject. This is handled by checking for an
      existing row for the subject for this object and updating it if it
      contains a lower action level. The end result is that there is one row for
      each subject, for each object and this row contains the highest action
      level.
  """
  app.models.Permission.objects.filter(
    sciobj__pid__did=sysmeta_obj.identifier.value()
  ).delete()

  # Add an implicit allow rule with all permissions for the rights holder.
  allow_rights_holder = d1_common.types.dataoneTypes.AccessRule()
  permission = d1_common.types.dataoneTypes.Permission(
    app.auth.CHANGEPERMISSION_STR
  )
  allow_rights_holder.permission.append(permission)
  allow_rights_holder.subject.append(sysmeta_obj.rightsHolder.value())
  top_level = _get_highest_level_action_for_rule(allow_rights_holder)
  _insert_permission_rows(sci_row, allow_rights_holder, top_level)

  # Create db entries for all subjects for which permissions have been granted.
  if sysmeta_obj.accessPolicy:
    for allow_rule in sysmeta_obj.accessPolicy.allow:
      top_level = _get_highest_level_action_for_rule(allow_rule)
      _insert_permission_rows(sci_row, allow_rule, top_level)


def _get_highest_level_action_for_rule(allow_rule):
  top_level = 0
  for permission in allow_rule.permission:
    level = app.auth.action_to_level(permission)
    if level > top_level:
      top_level = level
  return top_level


def _insert_permission_rows(sci_row, allow_rule, top_level):
  for s in allow_rule.subject:
    permission_model = app.models.Permission(
      sciobj=sci_row,
      subject=app.models.subject(s.value()),
      level=top_level
    )
    permission_model.save()


def _access_policy_model_to_pyxb(sciobj_model):
  access_policy_pyxb = d1_common.types.dataoneTypes.AccessPolicy()
  for permission_model in app.models.Permission.objects.filter(sciobj=sciobj_model):
    # Skip implicit permissions for rights-holder.
    if permission_model.subject.subject == sciobj_model.rights_holder.subject:
      continue
    access_rule_pyxb = d1_common.types.dataoneTypes.AccessRule()
    permission_pyxb = d1_common.types.dataoneTypes.Permission(
       app.auth.level_to_action(permission_model.level)
    )
    access_rule_pyxb.permission.append(permission_pyxb)
    access_rule_pyxb.subject.append(permission_model.subject.subject)
    access_policy_pyxb.allow.append(access_rule_pyxb)
  return access_policy_pyxb

# ------------------------------------------------------------------------------
# Replication Policy
# ------------------------------------------------------------------------------

# <replicationPolicy xmlns="" replicationAllowed="false" numberReplicas="0">
#     <preferredMemberNode>preferredMemberNode0</preferredMemberNode>
#     <preferredMemberNode>preferredMemberNode1</preferredMemberNode>
#     <blockedMemberNode>blockedMemberNode0</blockedMemberNode>
#     <blockedMemberNode>blockedMemberNode1</blockedMemberNode>
# </replicationPolicy>

def _replication_policy_pyxb_to_model(sciobj_model, sysmeta_obj):
  replication_policy_model = app.models.ReplicationPolicy()
  replication_policy_model.sciobj = sciobj_model
  replication_policy_model.replication_is_allowed = \
    sysmeta_obj.replicationPolicy.replicationAllowed
  replication_policy_model.desired_number_of_replicas = \
    sysmeta_obj.replicationPolicy.numberReplicas
  replication_policy_model.save()

  def add(node_ref_pyxb, rep_node_model):
    for rep_node_urn in node_ref_pyxb:
      node_urn_model = app.models.Node.objects.get_or_create(
        urn=rep_node_urn.value()
      )[0]
      rep_node_obj = rep_node_model()
      rep_node_obj.node = node_urn_model
      rep_node_obj.replication_policy = replication_policy_model
      rep_node_obj.save()

  add(sysmeta_obj.replicationPolicy.preferredMemberNode, app.models.PreferredMemberNode)
  add(sysmeta_obj.replicationPolicy.blockedMemberNode, app.models.BlockedMemberNode)

  return replication_policy_model


def _has_replication_policy(sciobj_model):
  return app.models.ReplicationPolicy.objects.filter(sciobj=sciobj_model).exists()


def _replication_policy_model_to_pyxb(sciobj_model):
  replication_policy_model = app.models.ReplicationPolicy.objects.get(sciobj=sciobj_model)
  replication_policy_pyxb = d1_common.types.dataoneTypes.ReplicationPolicy()
  replication_policy_pyxb.replicationAllowed = replication_policy_model.replication_is_allowed
  replication_policy_pyxb.numberReplicas = replication_policy_model.desired_number_of_replicas
  
  def add(rep_pyxb, rep_node_model):
    for rep_node in rep_node_model.objects.filter(replication_policy=replication_policy_model):
      rep_pyxb.append(rep_node.node.urn)

  add(replication_policy_pyxb.preferredMemberNode, app.models.PreferredMemberNode)
  add(replication_policy_pyxb.blockedMemberNode, app.models.BlockedMemberNode)

  return replication_policy_pyxb


def _update_modified_timestamp(sci_row):
  sci_row.modified_timestamp = datetime.datetime.utcnow()
  sci_row.save()