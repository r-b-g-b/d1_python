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
'''
:mod:`settings`
===============

:Synopsis:
  App level settings.
  
  This file contains settings that do not normally need to be modified when
  installing GMN. See settings_site.py for site specific settings.

:Author:
  DataONE (Dahl)
  
:Dependencies:
  - python 2.6
'''

# Stdlib.
import os
import sys

# Add site specific settings.
from settings_site import *

# Discover the path of this module
_here = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

# GMN does not use templates in production. However, some of the testing
# functions use them.
TEMPLATE_DEBUG = True

# Only set cookies when running through SSL.
SESSION_COOKIE_SECURE = True

MANAGERS = ADMINS

# GMN MUST run in the UTC time zone. Under Windows, the system time zone must
# also be set to UTC.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
  'django.template.loaders.filesystem.load_template_source',
  'django.template.loaders.app_directories.load_template_source',
  'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
  'django.middleware.common.CommonMiddleware',
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  #'django.middleware.profile.ProfileMiddleware',
  # TransactionMiddleware causes each view to be wrapped in an implicit
  # transaction. The transaction is automatically committed on successful
  # return from the view and rolled back otherwise.
  'django.middleware.transaction.TransactionMiddleware',
  'service.mn.middleware.request_handler.request_handler',
  'service.mn.middleware.exception_handler.exception_handler',
  'service.mn.middleware.response_handler.response_handler',
  #'service.mn.middleware.profiling_handler.profiling_handler',
  'service.mn.middleware.view_handler.view_handler',
)

ROOT_URLCONF = 'service.urls'

TEMPLATE_DIRS = (_here('mn/templates'), )

INSTALLED_APPS = (
  'service.mn',

  #    'django.contrib.auth',
  'django.contrib.contenttypes',
  #    'django.contrib.sessions',
  #    'django.contrib.sites',
  'django.contrib.admin',
  'django.contrib.admindocs',
)

# TODO: May be able to simplify url regexes by turning this on.
APPEND_SLASH = False
