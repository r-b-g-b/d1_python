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
"""Multithreaded LogRecord iterator
"""

from __future__ import absolute_import

import logging
import multiprocessing

import d1_client.mnclient_1_2
import d1_client.mnclient_2_0

# Defaults
LOG_RECORD_PAGE_SIZE = 100
MAX_WORKERS = 10
MAX_QUEUE_SIZE = 100
API_MAJOR = 2


class LogRecordIteratorMulti(object):
  """Multiprocessed LogRecord Iterator

  Fast retrieval of event log records from a DataONE Node.
  """

  def __init__(
      self,
      base_url,
      page_size=LOG_RECORD_PAGE_SIZE,
      max_workers=MAX_WORKERS,
      max_queue_size=MAX_QUEUE_SIZE,
      api_major=API_MAJOR,
      client_args_dict=None,
      get_log_records_arg_dict=None,
  ):
    self._base_url = base_url
    self._page_size = page_size
    self._max_workers = max_workers
    self._max_queue_size = max_queue_size
    self._api_major = api_major
    self._client_args_dict = client_args_dict or {}
    self._get_log_records_arg_dict = get_log_records_arg_dict or {}
    # d1_common.type_conversions.set_default_pyxb_namespace(api_major)
    self.total = _get_total_object_count(
      base_url, api_major, self._client_args_dict,
      self._get_log_records_arg_dict
    )

  def __iter__(self):
    manager = multiprocessing.Manager()
    queue = manager.Queue(maxsize=self._max_queue_size)

    process = multiprocessing.Process(
      target=_get_all_pages,
      args=(
        queue, self._base_url, self._page_size, self._max_workers,
        self._client_args_dict, self._get_log_records_arg_dict, self.total,
      ),
    )

    process.start()

    while True:
      log_entry_pyxb = queue.get()
      if log_entry_pyxb is None:
        logging.debug('Received None sentinel value. Stopping iteration')
        break
      yield log_entry_pyxb

    process.join()


def _get_total_object_count(
    base_url, api_major, client_args_dict, get_log_records_arg_dict
):
  client = _create_client(base_url, api_major, client_args_dict)
  args_dict = get_log_records_arg_dict.copy()
  args_dict['count'] = 0
  return client.getLogRecords(**args_dict).total


def _get_all_pages(
    queue, base_url, page_size, max_workers, client_args_dict,
    get_log_records_arg_dict, n_total
):
  logging.info('Creating pool of {} workers'.format(max_workers))
  pool = multiprocessing.Pool(processes=max_workers)
  n_pages = (n_total - 1) / page_size + 1

  for page_idx in range(n_pages):
    logging.debug(
      'apply_async(): page_idx={} n_pages={}'.format(page_idx, n_pages)
    )
    pool.apply_async(
      _get_page, args=(
        queue, base_url, page_idx, n_pages, page_size, client_args_dict,
        get_log_records_arg_dict
      )
    )
  # Prevent any more tasks from being submitted to the pool. Once all the
  # tasks have been completed the worker processes will exit.
  pool.close()
  # Wait for the worker processes to exit
  pool.join()
  # Use None as sentinel value to stop the generator
  queue.put(None)


def _get_page(
    queue, base_url, page_idx, n_pages, page_size, client_args_dict,
    get_log_records_arg_dict
):
  client = d1_client.mnclient_2_0.MemberNodeClient_2_0(
    base_url, **client_args_dict
  )
  try:
    log_records_pyxb = client.getLogRecords(
      start=page_idx * page_size, count=page_size, **get_log_records_arg_dict
    )
    logging.debug('Retrieved page: {}/{}'.format(page_idx + 1, n_pages))
    for log_entry_pyxb in log_records_pyxb.logEntry:
      queue.put(log_entry_pyxb)
  except Exception as e:
    logging.error(
      'Failed to retrieve page: {}/{}. Error: {}'.
      format(page_idx + 1, n_pages, e.message)
    )


def _create_client(base_url, api_major, client_dict):
  if api_major <= 1:
    return d1_client.mnclient_1_2.MemberNodeClient_1_2(base_url, **client_dict)
  else:
    return d1_client.mnclient_2_0.MemberNodeClient_2_0(base_url, **client_dict)