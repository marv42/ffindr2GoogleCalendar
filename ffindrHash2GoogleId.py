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

__author__ = 'marv42@gmail.com'


from authentication import Authentication
import logging
import re
# import json



class ffindrHash2GoogleId:

    def __init__(self, ffindrHash):
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

        authentication = Authentication()
        self.service = authentication.getService()

        self.inputFfindrHash = ffindrHash



    def Run(self):
        """Takes a ffindr RSS stream URL or a stream hash as an argument.

        Returns the calendar ID or '' if no ID found matching the hash or
        if some error occurred"""

        logging.info(self.inputFfindrHash)


        # search the hash in all calendars
        ##################################

        calendarList = self.service.calendarList().list().execute()
        #print json.dumps(calendarList, sort_keys=True, indent=4); sys.exit(0)

        patternHash = re.compile(self.inputFfindrHash)

        calendarId = ''

        for entry in calendarList['items']:
            if patternHash.search(str(entry['description'])):
                calendarId = entry['id']
                logging.info("-> %s" % calendarId)
                break

        if calendarId == '':
            logging.warning("No calendar found with this ffindr hash")

        return calendarId



def Usage():
    print "Usage : %s <ffindr hash>" % os.path.basename(__file__)



def main():
    """Runs the application."""

    # get parameter
    ###############

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h")
    except getopt.GetoptError:
        print "Unknown option"
        Usage()
        sys.exit(1)

    if not len(args) == 1:
        print "Wrong number of arguments"
        Usage()
        sys.exit(1)

    mainObject = ffindrHash2GoogleId(args[0])


    for o, a in opts:
        if o in ("-h", "--help"):
            Usage()
            sys.exit()

    if not len(args) == 1:
        sys.exit(1)


    mainObject.Run()



if __name__ == '__main__':
    main()
