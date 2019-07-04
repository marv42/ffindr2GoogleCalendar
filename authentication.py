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

__author__ = 'marv42@gmail.com'


import os
import gflags
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from httplib2 import Http
from googleapiclient.discovery import build



class Authentication():

    def getService(self):
        """return an authenticated calendar service"""

        # build source string
        command = 'git log -1 %s' % __file__
        version = os.popen(command).read()
        source = 'marvin-GoogleCalendar-v %s' % str(version)

        flags = gflags.FLAGS
        flow = OAuth2WebServerFlow(
            client_id = '394520942578-jeevvdv54ja8fhphjr8pov9ctma39tvg.apps.googleusercontent.com',
            client_secret = 'p7dBLBNzYjCw4ZxroRN4AeCK',
            scope='https://www.googleapis.com/auth/calendar',
            user_agent='Python/2.7')
        #flags.auth_local_webserver = False
        gflags.DEFINE_boolean('auth_local_webserver', False, 'disable the local server feature')

        storage = Storage('storage.dat')
        credentials = storage.get()
        if not credentials or credentials.invalid:
            credentials = run(flow, storage)

        http = credentials.authorize(Http())
        return build(serviceName='calendar', version='v3', http=credentials.authorize(Http()), developerKey='AIzaSyCWEafQZtzhVicb4u-PRD3qVxKldUHibDE')

