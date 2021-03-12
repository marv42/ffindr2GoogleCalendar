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

from EventData import EventData
from FfindrHash2GoogleId import FfindrHash2GoogleId
from xml.dom.minidom import parse
from datetime import datetime, date, timedelta
import getopt
import logging
import os
import sys
from urllib.request import urlopen
import json

MAX_EVENT_DURATION_DAYS = 8


class UpdateOneGoogleCalendar:

    def __init__(self, service):
        self.service = service
        self.calendarId = ''

    def run(self, ffindr_hash, url):
        """Updates a calendar in the WFDF Google calendar account with the
        events of a ffindr (www.ffindr.com) RSS stream.

        "Updating a calendar" means, inserting the events the titles of which
        don't yet exist in the calendar.

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
            if itemNode.nodeName != "item":
                continue
            ed = self.get_event_data(itemNode.childNodes)
            if 'DELETED' in ed.title:
                continue
            if ed.title == '<incomplete>':
                logging.warning("Update of one event failed because it was incomplete")
                continue
            ed = EventData.strip(ed)
            ed.location = html.unescape(ed.location)
            duration = self.get_fixed_duration(ed)
            if duration.days > MAX_EVENT_DURATION_DAYS:
                continue
            location_for_where = self.build_description(ed)
            logging.info(f"event {ed.title.encode('utf-8')}")
            if self.event_is_already_in_calendar(existing_events, ed.title):
                logging.info("... was already in the calendar")
                continue
            logging.info("### NEW ###")
            source = {'url': ed.link, 'title': ed.title}
            event = {'source': source, 'start': {'date': ed.date_start}, 'end': {'date': ed.date_end},
                     'location': location_for_where, 'description': ed.description, 'summary': ed.title}
            self.service.events().insert(calendarId=self.calendarId, body=event).execute()

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
        location_for_description = ''
        if len(ed.location) != 0:
            location_for_description = ed.location
        if len(location_for_description) != 0:
            ed.description += u'\n\nLocation: ' + location_for_description
        if len(ed.category) != 0:
            ed.description += u'\n\nCategory: ' + ed.category
        location_for_where = u''
        if len(ed.geo_lat) != 0 and len(ed.geo_long) != 0:
            # remove "(" and ")" or the map link won't work
            location_for_description = location_for_description.replace('(', u'')
            location_for_description = location_for_description.replace(')', u'')
            location_for_where = ed.geo_lat + u', ' + ed.geo_long + u' (' + location_for_description + u')'
        return location_for_where

    @staticmethod
    def get_fixed_duration(event_data):
        [year, month, day] = str(event_data.date_start).split('-')
        start_date = date(int(year), int(month), int(day))
        [year, month, day] = str(event_data.date_end).split('-')
        end_date = date(int(year), int(month), int(day))
        # end += 1 day (or Google takes two days events as one day)
        end_date += timedelta(1)
        event_data.date_end = end_date.isoformat()
        return end_date - start_date

    @staticmethod
    def get_event_data(child_nodes):
        event_data = EventData()
        for node in child_nodes:
            if node.nodeName == "title":
                event_data.title = node.childNodes[0].nodeValue
            if node.nodeName == "link":
                event_data.link = node.childNodes[0].nodeValue
            if node.nodeName == "description" and len(node.childNodes) > 0:
                event_data.description = node.childNodes[0].nodeValue
            if node.nodeName == "author":
                event_data.author = node.childNodes[0].nodeValue
            if node.nodeName == "category":
                if len(event_data.category) != 0:
                    event_data.category += ", "
                event_data.category += node.childNodes[0].nodeValue
            if node.nodeName == "location" and len(node.childNodes) > 0:
                event_data.location = node.childNodes[0].nodeValue
            if node.nodeName == "dateStart":
                event_data.date_start = node.childNodes[0].nodeValue
            if node.nodeName == "dateEnd":
                event_data.date_end = node.childNodes[0].nodeValue
            if node.nodeName == "geo:lat":
                event_data.geo_lat = node.childNodes[0].nodeValue
            if node.nodeName == "geo:long":
                event_data.geo_long = node.childNodes[0].nodeValue
        return event_data

    def delete_duplicate_events(self):
        events = self.get_events_in_calendar()
        for event1 in events:
            summary1 = event1.get('summary')
            for event2 in events:
                summary2 = event2.get('summary')
                if summary1 == summary2 and \
                        event1['id'] != event2['id']:
                    logging.info(summary1)
                    self.delete_event(event1['id'])
                    self.delete_event(event2['id'])
                    break

    def delete_event(self, id):
        logging.info("deleting event %s" % id)
        # TODO geht ned
        response = self.service.events().delete(calendarId=self.calendarId, eventId=id)
        if json.loads(response.to_json())['body'] is not None:
            logging.info("... failed")

    @staticmethod
    def event_is_already_in_calendar(existing_events, title):
        it_is = False
        for event in existing_events:
            event_title = event.get('source')
            if event_title is not None:
                event_title = event.get('title')
            if event_title is None:
                event_title = event.get('summary')
            if event_title == title:
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
                                                    timeMin=today.strftime('%Y-%m-%dT%H:%M:%S-00:00')).execute()
            for event in event_page['items']:
                events.append(event)
            page_token = event_page.get('nextPageToken')
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
