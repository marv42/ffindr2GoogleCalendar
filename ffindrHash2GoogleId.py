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

import getopt
import logging
import os
import re
import sys


class ffindrHash2GoogleId:

    def __init__(self, ffindrHash, service):
        self.inputFfindrHash = ffindrHash
        self.service = service

    def run(self):
        """Takes a ffindr RSS stream URL or a stream hash as an argument.

        Returns the calendar ID or '' if no ID found matching the hash or
        if some error occurred"""

        logging.info(self.inputFfindrHash)
        return self.get_calendar_id()

    def get_calendar_id(self):
        calendar_list = self.service.calendarList().list().execute()
        for entry in calendar_list['items']:
            if self.is_hash_in_description(entry):
                calendar_id = entry['id']
                logging.info(f"-> {calendar_id}")
                return calendar_id
        logging.warning("No calendar found with this ffindr hash")
        return ''

    def is_hash_in_description(self, entry):
        pattern_hash = re.compile(self.inputFfindrHash)
        return 'description' in entry and pattern_hash.search(str(entry['description']))


def usage():
    print("Usage : %s <ffindr hash>" % os.path.basename(__file__))


def main():
    """Runs the application."""

    # get parameter
    ###############

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h")
    except getopt.GetoptError:
        print("Unknown option")
        usage()
        sys.exit(1)

    if not len(args) == 2:
        print("Wrong number of arguments")
        usage()
        sys.exit(1)

    main_object = ffindrHash2GoogleId(args[0], args[1])

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()

    if not len(args) == 1:
        sys.exit(1)

    main_object.run()


if __name__ == '__main__':
    main()
