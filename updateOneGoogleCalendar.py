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

import html

from EventData import EventData, TITLE, LINK, DESCRIPTION, AUTHOR, CATEGORY, LOCATION, DATE_START, DATE_END, GEO_LAT, \
    GEO_LONG
from FfindrHash2GoogleId import FfindrHash2GoogleId
from xml.dom.minidom import parse
from datetime import datetime, date, timedelta
import getopt
import logging
import os
import sys
from urllib.request import urlopen
import json

DATE_SEP = '-'
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S-00:00'

DELETED = 'DELETED'
INCOMPLETE = '<incomplete>'
NEXT_PAGE_TOKEN = 'nextPageToken'
ITEMS = 'items'
ITEM = "item"
URL = 'url'
DATE = 'date'
SOURCE = 'source'
START = 'start'
END = 'end'
SUMMARY = 'summary'
ID = 'id'
BODY = 'body'

MAX_EVENT_DURATION_DAYS = 8


class UpdateOneGoogleCalendar:

    def __init__(self, service):
        self.service = service
        self.calendarId = ''

    def run(self, ffindr_hash, url):
        """Updates a calendar with the events of an UltimateCentral RSS stream,
        i.e. insert the events the titles of which don't yet exist in the calendar.

        *** Updating events is not yet implemented ***
        Workaround: delete non-up-to-date events by hand and they will be
        inserted correctly the next time."""

        logging.info(url)
        self.set_calendar_id(ffindr_hash)
        self.insert_events_into_calendar(url)
        self.delete_duplicate_events()

    def set_calendar_id(self, ffindr_hash):
        self.calendarId = FfindrHash2GoogleId().get_calendar_id(ffindr_hash, self.service)
        logging.info(self.calendarId)

    def insert_events_into_calendar(self, url):
        existing_events = self.get_events_in_calendar()
        feed = urlopen(url)
        dom = parse(feed)
        # firstChild == "rss", firstChild.firstChild == <text>, firstChild.childNodes[1] == "channel"
        for itemNode in dom.firstChild.childNodes[1].childNodes:
            if itemNode.nodeName != ITEM:
                continue
            ed = self.get_event_data(itemNode.childNodes)
            if DELETED in ed.title:
                continue
            if ed.title == INCOMPLETE:
                logging.warning("Update of one event failed because it was incomplete")
                continue
            ed = EventData.strip(ed)
            duration = self.get_fixed_duration(ed)
            if duration.days > MAX_EVENT_DURATION_DAYS:
                continue
            self.fix_end_date(ed)
            logging.info(f"event {ed.title.encode('utf-8')}")
            if self.event_is_already_in_calendar(existing_events, ed.title):
                logging.info("... was already in the calendar")
                continue
            self.build_description(ed)
            location = self.get_location_for_event(ed)
            self.insert_event(ed, location)

    @staticmethod
    def build_description(ed):
        # description: link, (tags,) author, location
        if ed.description.endswith('...'):
            ed.description += u'\n\n(truncated, for the complete description see the ffindr website)'
        ed.description += u'\n\n\n   *** ffindr tags ***'
        if len(ed.link) != 0:
            ed.description += u'\n\nWebsite: ' + ed.link
        # + u'\n\Tags: ' + tags
        if len(ed.author) != 0:
            ed.description += u'\n\nAuthor: ' + ed.author
        ed.location = html.unescape(ed.location)
        location_for_description = UpdateOneGoogleCalendar.get_location_for_description(ed)
        if len(location_for_description) != 0:
            ed.description += u'\n\nLocation: ' + location_for_description
        if len(ed.category) != 0:
            ed.description += u'\n\nCategory: ' + ed.category

    @staticmethod
    def get_location_for_description(ed):
        location = ''
        if len(ed.location) != 0:
            location = ed.location
        return location

    def get_location_for_event(self, ed):
        location = u''
        if len(ed.geo_lat) != 0 and len(ed.geo_long) != 0:
            location_for_description = self.get_location_for_description(ed)
            # remove "(" and ")" or the map link won't work
            location_for_description = location_for_description.replace('(', u'')
            location_for_description = location_for_description.replace(')', u'')
            location = ed.geo_lat + u', ' + ed.geo_long + u' (' + location_for_description + u')'
        return location

    def insert_event(self, ed, location):
        logging.info("### NEW ###")
        source = {URL: ed.link, TITLE: ed.title}
        start = {DATE: ed.date_start}
        end = {DATE: ed.date_end}
        event = {SOURCE: source, START: start, END: end, LOCATION: location,
                 DESCRIPTION: ed.description, SUMMARY: ed.title}
        self.service.events().insert(calendarId=self.calendarId, body=event).execute()

    @staticmethod
    def get_fixed_duration(event_data):
        start_date = UpdateOneGoogleCalendar.get_start_date(event_data.date_start)
        end_date = UpdateOneGoogleCalendar.get_fixed_end_date(event_data.date_end)
        return end_date - start_date

    @staticmethod
    def get_start_date(date_start):
        [year, month, day] = str(date_start).split(DATE_SEP)
        start_date = date(int(year), int(month), int(day))
        return start_date

    @staticmethod
    def get_fixed_end_date(date_end):
        [year, month, day] = str(date_end).split(DATE_SEP)
        end_date = date(int(year), int(month), int(day))
        # end += 1 day or Google takes two days events as one day
        end_date += timedelta(1)
        return end_date

    @staticmethod
    def fix_end_date(event_data):
        end_date = UpdateOneGoogleCalendar.get_fixed_end_date(event_data.date_end)
        event_data.date_end = end_date.isoformat()

    @staticmethod
    def get_event_data(child_nodes):
        event_data = EventData()
        for node in child_nodes:
            UpdateOneGoogleCalendar.set_event_data(event_data, node)
        return event_data

    @staticmethod
    def set_event_data(event_data, node):
        node_name = node.nodeName
        if node_name == TITLE:
            event_data.title = node.childNodes[0].nodeValue
        if node_name == LINK:
            event_data.link = node.childNodes[0].nodeValue
        if node_name == DESCRIPTION and len(node.childNodes) > 0:
            event_data.description = node.childNodes[0].nodeValue
        if node_name == AUTHOR:
            event_data.author = node.childNodes[0].nodeValue
        if node_name == CATEGORY:
            if len(event_data.category) != 0:
                event_data.category += ", "
            event_data.category += node.childNodes[0].nodeValue
        if node_name == LOCATION and len(node.childNodes) > 0:
            event_data.location = node.childNodes[0].nodeValue
        if node_name == DATE_START:
            event_data.date_start = node.childNodes[0].nodeValue
        if node_name == DATE_END:
            event_data.date_end = node.childNodes[0].nodeValue
        if node_name == GEO_LAT:
            event_data.geo_lat = node.childNodes[0].nodeValue
        if node_name == GEO_LONG:
            event_data.geo_long = node.childNodes[0].nodeValue

    def delete_duplicate_events(self):
        events = self.get_events_in_calendar()
        for event1 in events:
            summary1 = event1.get(SUMMARY)
            for event2 in events:
                summary2 = event2.get(SUMMARY)
                if summary1 == summary2 and \
                        event1[ID] != event2[ID]:
                    logging.info(summary1)
                    self.delete_event(event1[ID])
                    self.delete_event(event2[ID])
                    break

    def delete_event(self, event_id):
        logging.info("deleting event %s" % event_id)
        # TODO geht ned
        response = self.service.events().delete(calendarId=self.calendarId, eventId=event_id)
        if json.loads(response.to_json())[BODY] is not None:
            logging.info("... failed")

    @staticmethod
    def event_is_already_in_calendar(existing_events, title):
        it_is = False
        for event in existing_events:
            existing_event_title = event.get(SOURCE)
            if existing_event_title is not None:
                existing_event_title = event.get(TITLE)
            if existing_event_title is None:
                existing_event_title = event.get(SUMMARY)
            if existing_event_title == title:
                it_is = True
                break
        return it_is

    def get_events_in_calendar(self):
        events = []
        today = datetime.today()
        page_token = None
        while True:
            event_page = self.service.events().list(calendarId=self.calendarId,
                                                    pageToken=page_token,
                                                    timeMin=today.strftime(DATE_FORMAT)).execute()
            for event in event_page[ITEMS]:
                events.append(event)
            page_token = event_page.get(NEXT_PAGE_TOKEN)
            if not page_token:
                break
        return events


def usage():
    print("Usage : %s <ffindr hash> <UC URL> <service>" % os.path.basename(__file__))
    print()
    print("Available calendars:")
    with open("google-calendar.json") as f:
        for line in f:
            if "hash" in line:
                print(line, end=' ')


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h")
    except getopt.GetoptError as e:
        usage()
        sys.exit(str(e))
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
    if not len(args) == 3:
        usage()
        sys.exit("Wrong number of arguments")
    UpdateOneGoogleCalendar(args[2]).run(args[0], args[1])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        filename='updateAllGoogleCalendars.log',
                        format='[%(asctime)s %(filename)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)
    main()
