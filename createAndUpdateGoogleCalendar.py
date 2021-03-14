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
import random
import re
import sys
from urllib.request import urlopen
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

import atom
import gdata.calendar

from Constants import CALENDAR_JSON
from Exceptions import UnknownCalendar, CalendarUpdateFailed
from FfindrChannelContentHandler import FfindrChannelContentHandler
from authentication import Authentication
from updateOneGoogleCalendar import UpdateOneGoogleCalendar
from FfindrHash2GoogleId import GOOGLE_CALENDAR_DESCRIPTION, GOOGLE_CALENDAR_ITEMS

ROLE_READ = 'http://schemas.google.com/gCal/2005#read'
CALENDAR_PREFIX_URL = "http://www.google.com/calendar/"
OWN_CALENDARS = f"{CALENDAR_PREFIX_URL}feeds/default/owncalendars/full/"


class CreateAndUpdateGoogleCalendar:

    def __init__(self, hash, url):
        self.ffindrHash = hash
        self.url = url
        self.service = Authentication().get_service()

    def __del__(self):
        self.service.close()

    def run(self):
        """If the calendar doesn't already exist, creates a new empty calendar
        from a ffindr RSS stream (given by the CGI) in the WFDF Google
        calendar account and calls updateOneGoogleCalendar.

        We don't have to care if the insertion of the events ('update') was
        successful or not. If not, we assume it to be successful on the next
        update of the calendar."""

        if self.ffindrHash == '':
            raise CalendarUpdateFailed("No ffindr hash given")
        if self.url == '':
            raise CalendarUpdateFailed("No URL given")
        if not self.calendar_already_exists():
            self.create_calendar()
        try:
            UpdateOneGoogleCalendar(self.service).run(self.ffindrHash, self.url)
        except UnknownCalendar:
            logging.info("... failed")
            raise CalendarUpdateFailed("Creation successful but updating failed")

    def calendar_already_exists(self):
        calendar_list = self.service.calendarList().list().execute()
        for entry in calendar_list[GOOGLE_CALENDAR_ITEMS]:
            if self.is_hash_in_description(entry):
                return True
        return False

    def is_hash_in_description(self, entry):
        pattern_hash = re.compile(self.ffindrHash)
        return GOOGLE_CALENDAR_DESCRIPTION in entry and \
               pattern_hash.search(str(entry[GOOGLE_CALENDAR_DESCRIPTION]))

    def parse_rss(self, content_handler):
        parser = make_parser()
        parser.setFeature(feature_namespaces, 0)
        parser.setContentHandler(content_handler)
        parser.setEntityResolver(content_handler)
        parser.parse(self.url)

    def create_calendar(self):
        logging.info("trying to create the Google calendar ...")
        content_handler = FfindrChannelContentHandler()
        self.parse_rss(content_handler)
        calendar_title = content_handler.get_title()
        new_calendar = self.insert_calendar(title=calendar_title)
        logging.info("... successful")
        calendar_id = self.get_calendar_id(new_calendar.id.text)
        self.make_calendar_public(calendar_id)

    def insert_calendar(self,
                        title='Standard Ultimate Central Stream Calendar Title',
                        time_zone='Europe/Paris',
                        hidden=False,
                        location='Paris'):
        """Creates a new calendar using the specified data."""
        description = f'This calendar is generated automatically from the Ultimate Central RSS stream "{title}" ' \
                      f'(http://ffindr.com/en/feed/filter/{self.ffindrHash}).\n\nIf you want your tournament to be ' \
                      f'listed here, enter it to Ultimate Central: www.ultimatecentral.com'
        color_list = ("#0D7813", "#1B887A", "#29527A", "#2952A3", "#28754E", "#4A716C", "#4E5D6C",
                      "#5229A3", "#528800", "#5A6986", "#6E6E41", "#705770", "#7A367A", "#865A5A",
                      "#88880E", "#8D6F47", "#A32929", "#AB8B00", "#B1365F", "#B1440E", "#BE6D00")
        random_color = color_list[random.randrange(len(color_list))]
        calendar = gdata.calendar.CalendarListEntry()
        calendar.title = atom.Title(text=title)
        calendar.summary = atom.Summary(text=description)
        calendar.where = gdata.calendar.Where(value_string=location)
        calendar.color = gdata.calendar.Color(value=random_color)
        calendar.timezone = gdata.calendar.Timezone(value=time_zone)
        if hidden:
            calendar.hidden = gdata.calendar.Hidden(value='true')
        else:
            calendar.hidden = gdata.calendar.Hidden(value='false')
        return self.service.InsertCalendar(new_calendar=calendar)

    @staticmethod
    def get_calendar_id(calendar_id):
        if calendar_id.startswith(OWN_CALENDARS):
            calendar_id = calendar_id[len(OWN_CALENDARS):len(calendar_id)]
        logging.info(f"calendar ID: {calendar_id}")
        return calendar_id

    def make_calendar_public(self, calendar_id):
        logging.info("setting permissions / make calendar public ...")
        rule = gdata.calendar.CalendarAclEntry()
        rule.scope = gdata.calendar.Scope(scope_type='default')  # all users, no value
        rule.role = gdata.calendar.Role(value=ROLE_READ)
        acl_url = f"{CALENDAR_PREFIX_URL}feeds/{calendar_id}/acl/full"
        self.service.InsertAclEntry(rule, acl_url)
        # self._CreateAclRule("user@gmail.com")


def usage():
    print(f"Usage : {os.path.basename(__file__)} <ffindr hash> <UC URL>")
    print()
    print("Available hashes:")
    sock = urlopen(f"./{CALENDAR_JSON}")
    print(sock.read())
    sock.close()
    return 0, ''


def main():
    """Runs the application."""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h")
    except getopt.GetoptError as e:
        print("Unknown option")
        usage()
        sys.exit(str(e))
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
    if len(args) != 2:
        print("Wrong number of arguments")
        print(usage())
        sys.exit(1)
    CreateAndUpdateGoogleCalendar(args[0], args[1]).run()


if __name__ == '__main__':
    main()
