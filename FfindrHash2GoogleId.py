#!/usr/bin/env python
# -*- coding: utf-8 -*-

#     Copyright (C) 2008 Stefan Horter

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

import logging
import re

from Constants import GOOGLE_CALENDAR_ITEMS, GOOGLE_CALENDAR_ID, GOOGLE_CALENDAR_DESCRIPTION
from Exceptions import UnknownCalendar


class FfindrHash2GoogleId:

    def get_calendar_id(self, ffindr_hash, service):
        logging.info(ffindr_hash)
        calendar_list = service.calendarList().list().execute()
        for entry in calendar_list[GOOGLE_CALENDAR_ITEMS]:
            if self.is_hash_in_description(ffindr_hash, entry):
                calendar_id = entry[GOOGLE_CALENDAR_ID]
                logging.info(f"-> {calendar_id}")
                return calendar_id
        raise UnknownCalendar("No calendar found with this ffindr hash")

    @staticmethod
    def is_hash_in_description(ffindr_hash, entry):
        pattern_hash = re.compile(ffindr_hash)
        return GOOGLE_CALENDAR_DESCRIPTION in entry and \
               pattern_hash.search(str(entry[GOOGLE_CALENDAR_DESCRIPTION]))
