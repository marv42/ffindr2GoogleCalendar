#!/usr/bin/env python
# -*- coding: utf-8 -*-

# $Id: updateAllGoogleCalendars.py 76 2009-08-02 15:39:01Z marvin $

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


from createAndUpdateGoogleCalendar import CreateAndUpdateGoogleCalendar
import datetime
import getopt
import json
import logging
import os
import posix
import sys
import time
import urllib



class UpdateAllGoogleCalendars:

    def __init__(self):
        logging.basicConfig(format='[%(filename)s] %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.WARNING)

    def SetVerboseMode(self):
        self.logger.setLevel(logging.INFO)


    def Run(self):
        """Get all ffindr hashes from ffindr and call updateOneGoogleCalendar
        for each of them"""

        jsonFile = os.path.dirname(os.path.abspath(__file__)) + '/google-calendar.json'


        # parse the content of the ffindr RSS stream
        ############################################

        self.logger.info(jsonFile)

        jsonObject = json.load(open(jsonFile))


        # for all calendars
        ###################

        filters = jsonObject["filters"]
        for f in range(len(filters)):

            self.logger.info("'%s'" % filters[f]["name"])

            createAndUpdate = CreateAndUpdateGoogleCalendar(filters[f]["hash"])

            if self.logger.isEnabledFor(logging.INFO):
                createAndUpdate.SetVerboseMode()

            returnJson = json.loads(createAndUpdate.Run())
            #print returnJson

            if returnJson['error'] != 'NULL':
                self.logger.info("failed, waiting one minute ...")

                # wait one minute and try again
                ###############################

                t = datetime.datetime.now()
                while t + datetime.timedelta(0,0,0,0,1) > datetime.datetime.now():
                    continue

                self.logger.info("... trying once more ...")

                returnJson = json.loads(createAndUpdate.Run())

                if returnJson['error'] != 'NULL':
                    self.logger.info( "... failed")


def Usage():

    print "Usage : %s [-v]" % os.path.basename(__file__)
    print "-v: verbose mode"
    return



def main():
    """Runs the application."""

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv")
    except getopt.GetoptError:
        print "Unknown option"
        Usage()
        sys.exit(1)

    if not len(args) == 0:
        print "Wrong number of arguments"
        Usage()
        sys.exit(1)


    mainObject = UpdateAllGoogleCalendars()


    for o, a in opts:
        if o in ("-v"):
            mainObject.SetVerboseMode()

        if o in ("-h", "--help"):
            Usage()
            sys.exit()


    mainObject.Run()



if __name__ == '__main__':
    main()
