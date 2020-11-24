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
# import json
import sys


class ffindrHash2GoogleId:

    def __init__(self, ffindrHash, service):
        """Creates a CalendarService and provides ClientLogin auth details to
        it.  The email and password are required arguments for ClientLogin.
        The CalendarService automatically sets the service to be 'cl', as is
        appropriate for calendar.  The 'source' defined below is an arbitrary
        string, but should be used to reference your name or the name of your
        organization, the app name and version, with '-' between each of the
        three values.  The account_type is specified to authenticate either
        Google Accounts or Google Apps accounts.  See gdata.service or
        http://code.google.com/apis/accounts/AuthForInstalledApps.html for
        more info on ClientLogin.  NOTE: ClientLogin should only be used for
        installed applications and not for multi-user web applications."""

        self.inputFfindrHash = ffindrHash
        self.service = service

    def run(self):
        """Takes a ffindr RSS stream URL or a stream hash as an argument.

        Returns the calendar ID or '' if no ID found matching the hash or
        if some error occurred"""

        logging.info(self.inputFfindrHash)

        # search the hash in all calendars
        ##################################

        calendar_list = self.service.calendarList().list().execute()
        # print json.dumps(calendar_list, sort_keys=True, indent=4); sys.exit(0)

        pattern_hash = re.compile(self.inputFfindrHash)

        calendar_id = ''

        for entry in calendar_list['items']:
            if 'description' in entry and pattern_hash.search(str(entry['description'])):
                calendar_id = entry['id']
                logging.info("-> %s" % calendar_id)
                break

        if calendar_id == '':
            logging.warning("No calendar found with this ffindr hash")

        return calendar_id


def Usage():
    print("Usage : %s <ffindr hash>" % os.path.basename(__file__))


def main():
    """Runs the application."""

    # get parameter
    ###############

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h")
    except getopt.GetoptError:
        print("Unknown option")
        Usage()
        sys.exit(1)

    if not len(args) == 2:
        print("Wrong number of arguments")
        Usage()
        sys.exit(1)

    main_object = ffindrHash2GoogleId(args[0], args[1])

    for o, a in opts:
        if o in ("-h", "--help"):
            Usage()
            sys.exit()

    if not len(args) == 1:
        sys.exit(1)

    main_object.run()


if __name__ == '__main__':
    main()
