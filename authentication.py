#!/usr/bin/env python
# -*- coding: utf-8 -*-

#     Copyright (C) 2015 Stefan Horter

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = 'marv42+updateAllGoogleCalendars@gmail.com'

import gflags
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.tools import run_flow

from credentials import client_id, client_secret, developer_key


class Authentication:

    @staticmethod
    def get_service():
        """return an authenticated calendar service"""
        flow = OAuth2WebServerFlow(client_id, client_secret,
                                   scope='https://www.googleapis.com/auth/calendar')
        gflags.DEFINE_boolean('auth_local_webserver', False, 'disable the local server feature')
        storage = Storage('storage.dat')
        credentials = storage.get()
        if not credentials or credentials.invalid:
            credentials = run_flow(flow, storage)
        credentials.authorize(Http())
        return build(serviceName='calendar', version='v3', http=credentials.authorize(Http()),
                     developerKey=developer_key)
