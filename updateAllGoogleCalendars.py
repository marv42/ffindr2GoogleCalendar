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

from authentication import Authentication
from createAndUpdateGoogleCalendar import CreateAndUpdateGoogleCalendar
import datetime
import getopt
import json
import logging
import os
import sys


class UpdateAllGoogleCalendars:

    def run(self):
        """Get all ffindr hashes from ffindr and call updateOneGoogleCalendar
        for each of them"""

        authentication = Authentication()
        self.service = authentication.get_service()

        json_file = os.path.dirname(os.path.abspath(__file__)) + '/google-calendar.json'

        # parse the content of the RSS stream
        ############################################

        logging.info(json_file)

        json_object = json.load(open(json_file))

        # for all calendars
        ###################

        filters = json_object["filters"]
        for f in range(len(filters)):

            logging.info("'%s'" % filters[f]["name"])

            create_and_update = CreateAndUpdateGoogleCalendar(
                filters[f]["hash"], filters[f]["uc"], self.service)

            return_json = json.loads(create_and_update.run())
            # print return_json

            if return_json['error'] != 'NULL':
                logging.info("failed, waiting one minute ...")

                # wait one minute and try again
                ###############################

                t = datetime.datetime.now()
                while t + datetime.timedelta(0, 0, 0, 0, 1) > datetime.datetime.now():
                    continue

                logging.info("... trying once more ...")

                return_json = json.loads(create_and_update.run())

                if return_json['error'] != 'NULL':
                    logging.info("... failed")
                    return 1


def usage():
    print("Usage : %s" % os.path.basename(__file__))
    return


def main():
    """Runs the application."""

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

    main_object = UpdateAllGoogleCalendars()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()

    return main_object.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        filename='updateAllGoogleCalendars.log',
                        format='[%(asctime)s %(filename)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

    main()
