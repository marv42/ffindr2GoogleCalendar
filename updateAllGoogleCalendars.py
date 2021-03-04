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

__author__ = 'marv42+updateAllGoogleCalendars@gmail.com'

from time import sleep

from createAndUpdateGoogleCalendar import CreateAndUpdateGoogleCalendar, FFINDR_JSON
from datetime import datetime, timedelta
import getopt
import json
import logging
import os
import sys


class UpdateAllGoogleCalendars:

    def __init__(self):
        self.calendars = []

    def run(self):
        self.load_ffindr_json()
        for c in range(len(self.calendars)):
            a_calendar = self.calendars[c]
            if not self.update_calendar(a_calendar):
                return 1
        return 0

    def load_ffindr_json(self):
        json_file = os.path.dirname(os.path.abspath(__file__)) + '/' + FFINDR_JSON
        logging.info(json_file)
        json_object = json.load(open(json_file))
        self.calendars = json_object["filters"]

    def update_calendar(self, calendar):
        logging.info("'%s'" % calendar["name"])
        create_and_update = CreateAndUpdateGoogleCalendar(calendar["hash"], calendar["uc"])
        return_json = json.loads(create_and_update.run())
        if return_json['error'] != 'NULL':
            logging.info("failed, waiting one minute ...")
            self.wait_one_minute()
            logging.info("... trying once more ...")
            return_json = json.loads(create_and_update.run())
            if return_json['error'] != 'NULL':
                logging.info("... failed")
                return False
        return True

    @staticmethod
    def wait_one_minute():
        t0 = datetime.now()
        while t0 + timedelta(minutes=1) > datetime.now():
            sleep(10)


def usage():
    print(f"Usage : {os.path.basename(__file__)}")
    return


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h")
    except getopt.GetoptError:
        print("Unknown option")
        usage()
        sys.exit(1)
    if not len(args) == 0:
        print("Wrong number of arguments")
        usage()
        sys.exit(1)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
    return UpdateAllGoogleCalendars().run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        filename='updateAllGoogleCalendars.log',
                        format='[%(asctime)s %(filename)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)
    main()
