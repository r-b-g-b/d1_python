#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
:mod:`auth`
===========

:Synopsis:
  Authentication. For now, based on IP only.

.. moduleauthor:: Roger Dahl
'''

# Stdlib.
try:
  from functools import update_wrapper
except ImportError:
  from django.utils.functional import update_wrapper

# Django.
from django.http import Http404
from django.http import HttpResponse

# MN API.
import d1common.exceptions

# App.
import settings
import sys_log
import util


def cn_check_required(f):
  '''Function decorator that checks if the IP address of the client matches a
  known CN IP and blocks acccess to the decorated function if there is no match.
  
  For now, it's not really necessary to tap into Django's authentication system.
  We could just check the IP each time, but we set up a session because it'll
  come in handy shortly.
  
  Raises d1common.exceptions.NotAuthorized (errorCode=401, detailCode=1040)
  '''

  def wrap(request, *args, **kwargs):
    # Check if we already have a session for this user.
    if 'cn_user' not in request.session.keys() and settings.ENABLE_IP_AUTH == True:
      sys_log.info(
        'client({0}): Session not found for user at IP'.format(
          util.request_to_string(
            request
          )
        )
      )
      # Check if IP belongs to a CN.
      if request.META['REMOTE_ADDR'] in settings.CN_IP:
        # This is a valid IP, so we create a session object.
        sys_log.info(
          'client({0}): IP is valid CN IP'.format(
            util.request_to_string(
              request
            )
          )
        )
        request.session['cn_user'] = True
      else:
        raise d1common.exceptions.NotAuthorized(
          1040, 'Attempted to access functionality only available to Coordinating Nodes'
        )
    else:
      sys_log.info(
        'client({0}): User has session'.format(
          util.request_to_string(
            request
          )
        )
      )

    return f(request, *args, **kwargs)

  wrap.__doc__ = f.__doc__
  wrap.__name__ = f.__name__

  return wrap


def mn_check_required(f):
  '''Function decorator that checks if the IP address of the client matches a
  known MN IP and blocks acccess to the decorated function if there is no match.
  :return:
  '''

  def wrap(request, *args, **kwargs):
    # Check if we already have a session for this user.
    if 'mn_user' not in request.session.keys() and settings.ENABLE_IP_AUTH == True:
      sys_log.info(
        'client({0}): Session not found for user at IP'.format(
          util.request_to_string(
            request
          )
        )
      )
      # Check if IP belongs to a MN.
      if request.META['REMOTE_ADDR'] in settings.MN_IP:
        # This is a valid IP, so we create a session object.
        sys_log.info(
          'client({0}): IP is valid MN IP'.format(
            util.request_to_string(
              request
            )
          )
        )
        request.session['mn_user'] = True
      else:
        raise d1common.exceptions.NotAuthorized(
          1040, 'Attempted to access functionality only available to Member Nodes.'
        )
    else:
      sys_log.info(
        'client({0}): User has session'.format(
          util.request_to_string(
            request
          )
        )
      )

    return f(request, *args, **kwargs)

  wrap.__doc__ = f.__doc__
  wrap.__name__ = f.__name__

  return wrap
