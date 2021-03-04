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

import os
import pickle

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


CLIENT_SECRET_JSON = 'client_secret.json'
TOKEN_PICKLE = 'token.pickle'
# SERVICE_ACCOUNT_EMAIL = 'ultimatecentralcalendarservice@fluent-buckeye-285819.iam.gserviceaccount.com'
# SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'


class Authentication:

    @staticmethod
    def get_service():
        creds = Authentication.get_credentials()
        return build(API_SERVICE_NAME, API_VERSION, credentials=creds, cache_discovery=False)

    @staticmethod
    def get_credentials():
        """cf. https://developers.google.com/calendar/quickstart/python"""

        creds = None
        if os.path.exists(TOKEN_PICKLE):
            with open(TOKEN_PICKLE, 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_JSON, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_PICKLE, 'wb') as token:
                pickle.dump(creds, token)
        return creds

        # credentials = service_account.Credentials.from_service_account_file(
        #     SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        # return credentials.with_subject(SERVICE_ACCOUNT_EMAIL)
