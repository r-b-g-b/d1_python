#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This work was created by participants in the DataONE project, and is
# jointly copyrighted by participating institutions in DataONE. For
# more information on DataONE, see our web site at http://dataone.org.
#
#   Copyright ${year}
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

# {{{ http://code.activestate.com/recipes/146306/ (r1)
# With some of the modifications suggested in the user comments.

import os
import httplib
import mimetypes
import urlparse
import StringIO
import d1_common.const
import logging


class multipart(object):
  '''File-like MIME Multipart object.
  
  This class wraps files and returns the file data wrapped in a mime multipart
  structure when iterated, without buffering.

  :param: fields is a sequence of (name, value) elements for regular form fields.
  :param: files is a sequence of (name, filename, value) elements for data to be
    uploaded as files. The value elements of files can be file-like objects or
    strings.
  :return: None
  '''

  def __init__(self, headers, fields, files, chunk_size=1024**2):
    ''':param:
    :return:
    '''
    # Remove any provided headers that we need to generate ourselves.
    #   headers.keys() is a copy of the dictionary keys, so it's safe to
    #   mutate the dictionary while iterating.
    for header_key in headers.keys():
      if header_key.lower() in ('content-type', 'content-length', 'user-agent'):
        logging.warning(
          '{0} header was provided but overridden by internally generated version'.format(
            header_key
          )
        )
        del headers[header_key]

    self.chunk_size = chunk_size
    self.headers = headers
    self.fields = fields
    self.files = files
    self.file_idx = 0
    self.state = 'form_fields'
    self.CRLF = '\r\n'
    self.BOUNDARY = '----------6B3C785C-6290-11DF-A355-A6ECDED72085_$'
    self.io = StringIO.StringIO()

  def getContentLength(self):
    '''
    '''
    m = multipart(
      self.headers, self.fields, [
        (
          file[0], file[1], ''
        ) for file in self.files
      ]
    )
    content_length = len(m.read())
    for file in self.files:
      content_length += self._get_len(file)
    self.reset()
    return content_length

  def post(self, url):
    '''Post fields and files to an HTTP host as MIME Multipart.
    :return: (tuple) response status, response reason, response body
    '''

    scheme, host, path = urlparse.urlsplit(url)[:3]

    # Determine full length. We create a new multipart object that is a copy of
    # this one, but with empty files. We then add in the length of the files
    # separately.
    m = multipart(
      self.headers, self.fields, [
        (
          file[0], file[1], ''
        ) for file in self.files
      ]
    )
    content_length = len(m.read())
    for file in self.files:
      content_length += self._get_len(file)

    self.reset()

    # The headers do not count towards the size of the MIME Multipart doc.
    self.headers['Content-Type'] = self._get_content_type()
    self.headers['Content-Length'] = content_length
    self.headers['User-Agent'] = d1_common.const.USER_AGENT

    # "self" refers this class, which returns the wrapped files in a mime
    # multipart structure when iterated by httplib.HTTPConnection().
    http_connection = httplib.HTTPConnection(host)
    http_connection.request('POST', path, self, self.headers)
    res = http_connection.getresponse()
    return res.status, res.reason, res.read()

  def reset(self):
    '''Reset file-like object to initial state. This also sets seek to 0 on any
    file-like objects.'''
    self.file_idx = 0
    self.state = 'form_fields'
    self.io = StringIO.StringIO()

    for file in self.files:
      try:
        file[2].seek(0)
      except AttributeError, TypeError:
        pass

  def read(self, n=None):
    ''':param: (int) Bytes to read.
    :return: (str) Bytes read.
    '''
    if n is None:
      # Return everything at once.
      for s in self:
        self.io.write(s)
      return self.io.getvalue()
    else:
      # Return in chunks.

      # "top up" FLO.
      try:
        while True:
          self.io.seek(0, os.SEEK_END)
          if self.io.tell() >= n:
            break
          self.io.write(self.next())
      except StopIteration:
        pass

      # Get n bytes from front of FLO.
      self.io.seek(0)
      ret = self.io.read(n)

      # Remove n bytes from front of FLO.
      self.io = StringIO.StringIO(self.io.read())

    return ret

  def next(self):
    '''Iterate over MIME Multipart object.
    :return: Next section of MIME Multipart data. Some sections are empty.
    '''

    if self.state == 'form_fields':
      if len(self.files) > 0:
        self.state = 'file_head'
      else:
        self.state = 'body_foot'
      return self._form_fields()

    elif self.state == 'file_head':
      self.state = 'select'
      return self._file_head()

    elif self.state == 'select':
      key, filename, val = self.files[self.file_idx]
      if isinstance(val, str):
        self.state = 'str_val'
      elif isinstance(val, unicode):
        self.state = 'unicode_val'
      else:
        self.state = 'file_chunk'
      return ''

    elif self.state == 'str_val':
      self.state = 'file_foot'
      return self._str_val()

    elif self.state == 'unicode_val':
      self.state = 'file_foot'
      return self._unicode_val()

    elif self.state == 'file_chunk':
      data = self._file_chunk()
      if len(data) > 0:
        return data
      self.state = 'file_foot'
      return ''

    elif self.state == 'file_foot':
      self.state = 'next_file'
      return self._file_foot()

    elif self.state == 'next_file':
      self.file_idx += 1
      if self.file_idx < len(self.files):
        self.state = 'file_head'
        return ''
      else:
        self.state = 'body_foot'
        return ''

    elif self.state == 'body_foot':
      self.state = 'body_end'
      return self._body_foot()

    elif self.state == 'body_end':
      raise StopIteration

    else:
      raise Exception('Invalid state in {0}: {1}'.format(__file__, self.state))

  def _get_len(self, file):
    try:
      pos = file[2].tell()
      file[2].seek(0, os.SEEK_END)
      size = file[2].tell()
      file[2].seek(pos)
      return size
    except AttributeError:
      return len(file[2])

  def _get_content_type(self):
    return 'multipart/form-data; boundary={0}'.format(self.BOUNDARY)

  def _guess_mime_type(self, filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

  def _form_fields(self):
    L = []
    for (key, val) in self.fields:
      L.append('--' + self.BOUNDARY)
      L.append('Content-Disposition: form-data; name="%s"' % key)
      L.append('')
      L.append(val)
    return self.CRLF.join(L)

  def _file_head(self):
    key, filename, val = self.files[self.file_idx]
    L = []
    L.append('--' + self.BOUNDARY)
    L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
    L.append('Content-Type: %s' % self._guess_mime_type(filename))
    L.append('')
    L.append('')
    return self.CRLF.join(L)

  def _file_chunk(self):
    key, filename, val = self.files[self.file_idx]
    return val.read(self.chunk_size)

  def _file_foot(self):
    return self.CRLF

  def _str_val(self):
    key, filename, val = self.files[self.file_idx]
    return val

  def _unicode_val(self):
    key, filename, val = self.files[self.file_idx]
    return val.encode('utf-8')

  def _body_foot(self):
    L = []
    L.append('--' + self.BOUNDARY + '--')
    L.append('')
    return self.CRLF.join(L)

  def __iter__(self):
    self.reset()
    return self
