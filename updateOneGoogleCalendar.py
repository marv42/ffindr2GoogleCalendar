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

import html

from Exceptions import UnknownCalendar
from ffindrHash2GoogleId import ffindrHash2GoogleId
from authentication import Authentication
from xml.dom.minidom import parse
from datetime import datetime, date, timedelta
import getopt
import logging
import os
import sys
from urllib.request import urlopen
import json


class UpdateOneGoogleCalendar:

    def __init__(self, hash, url, service):
        self.testingMode = False
        self.ffindrHash = hash
        self.url = url
        self.service = service

    def set_testing_mode(self):
        self.testingMode = True
        authentication = Authentication()
        self.service = authentication.get_service()

    def run(self):
        """Updates a calendar in the WFDF Google calendar account with the
        events of a ffindr (www.ffindr.com) RSS stream.

        "Updating a calendar" means, inserting the events the titles of which
        don't yet exist in the calendar.

        *** Updating events is not yet implemented ***

        Workaround: delete non-up-to-date events by hand and they will be
        inserted correctly the next time."""

        if self.testingMode:
            sock = urlopen(self.url)
            with open("contentOfInputFfindrUrl.xml", 'w') as f:
                print(sock.read(), file=f)
            sock.close()
            logging.info("see contentOfInputFfindrUrl.xml")

        logging.info(self.url)
        self.set_calendar_id()
        events = self.get_events_in_calendar()

        title = u''
        link = u''
        description = u''
        author = u''
        category = u''
        location = u''
        date_start = u''
        date_end = u''
        geo_lat = u''
        geo_long = u''
        feed = urlopen(self.url)
        dom = parse(feed)
        # firstChild == "rss", firstChild.firstChild == <text>, firstChild.childNodes[1] == "channel"
        for itemNode in dom.firstChild.childNodes[1].childNodes:
            if itemNode.nodeName != "item":
                continue
            for node in itemNode.childNodes:
                if node.nodeName == "title":
                    title = node.childNodes[0].nodeValue
                if node.nodeName == "link":
                    link = node.childNodes[0].nodeValue
                if node.nodeName == "description" and len(node.childNodes) > 0:
                    description = node.childNodes[0].nodeValue
                if node.nodeName == "author":
                    author = node.childNodes[0].nodeValue
                if node.nodeName == "category":
                    if len(category) != 0:
                        category += ", "
                    category += node.childNodes[0].nodeValue
                if node.nodeName == "location" and len(node.childNodes) > 0:
                    location = node.childNodes[0].nodeValue
                if node.nodeName == "dateStart":
                    date_start = node.childNodes[0].nodeValue
                if node.nodeName == "dateEnd":
                    date_end = node.childNodes[0].nodeValue
                if node.nodeName == "geo:lat":
                    geo_lat = node.childNodes[0].nodeValue
                if node.nodeName == "geo:long":
                    geo_long = node.childNodes[0].nodeValue

            if 'DELETED' in title:
                continue
            if title == '<incomplete>':
                logging.warning("Update of one event failed because it was incomplete")
                continue

            title = title.strip()
            link = link.strip()
            description = description.strip()
            author = author.strip()
            category = category.strip()
            date_start = date_start.strip()
            date_end = date_end.strip()
            location = location.strip()
            geo_lat = geo_lat.strip()
            geo_long = geo_long.strip()

            location = html.unescape(location)

            [year, month, day] = str(date_start).split('-')
            start_date = date(int(year), int(month), int(day))
            [year, month, day] = str(date_end).split('-')
            end_date = date(int(year), int(month), int(day))
            # end += 1 day (or Google takes two days events as one day)
            end_date += timedelta(1)
            date_end = end_date.isoformat()
            if (end_date - start_date).days > 7:
                continue

            # description: link, (tags,) author, location
            if description.endswith('...'):
                description += u'\n\n(truncated, for the complete description see the ffindr website)'

            description += u'\n\n\n   *** ffindr tags ***'

            if len(link) != 0:
                description += u'\n\nWebsite: ' + link

            # + u'\n\Tags: ' + tags

            if len(author) != 0:
                description += u'\n\nAuthor: ' + author

            location_for_description = ''
            if len(location) != 0:
                location_for_description = location

            if len(location_for_description) != 0:
                description += u'\n\nLocation: ' + location_for_description

            if len(category) != 0:
                description += u'\n\nCategory: ' + category

            location_for_where = u''
            if len(geo_lat) != 0 and len(geo_long) != 0:
                # remove "(" and ")" or the map link won't work
                location_for_description = location_for_description.replace('(', u'')
                location_for_description = location_for_description.replace(')', u'')
                location_for_where = geo_lat + u', ' + geo_long + u' (' + location_for_description + u')'

            logging.info(f"event {title.encode('utf-8')}")
            if self.event_is_already_in_calendar(events, title):
                logging.info("... was already in the calendar")
                continue

            logging.info("### NEW ###")
            source = {'url': link, 'title': title}
            event = {'source': source, 'start': {'date': date_start}, 'end': {'date': date_end},
                     'location': location_for_where, 'description': description, 'summary': title}
            self.service.events().insert(calendarId=self.calendarId, body=event).execute()

        self.delete_duplicate_events(events)

    def delete_duplicate_events(self, events):
        def delete_event(id):
            logging.info("deleting event %s" % id)
            # TODO geht ned
            response = self.service.events().delete(calendarId=self.calendarId,
                                                    eventId=id)
            if json.loads(response.to_json())['body'] is not None:
                logging.info("... failed")

        for event1 in events:
            summary1 = event1.get('summary')
            for event2 in events:
                summary2 = event2.get('summary')
                if summary1 == summary2 and \
                        event1['id'] != event2['id']:
                    logging.info(summary1)
                    delete_event(event1['id'])
                    delete_event(event2['id'])
                    break

    @staticmethod
    def event_is_already_in_calendar(events, title):
        it_is = False
        for event in events:
            event_title = event.get('source')
            if event_title is not None:
                event_title = event.get('title')
            if event_title is None:
                event_title = event.get('summary')
            if event_title == title:
                it_is = True
                break
        return it_is

    def set_calendar_id(self):
        id_determination = ffindrHash2GoogleId(self.ffindrHash, self.service)
        self.calendarId = id_determination.run()
        if self.calendarId == '':
            logging.error("error getting calendar ID")
            raise UnknownCalendar("unknown calendar ID or Google connectivity problems")
        logging.info(self.calendarId)  # , "=> URL"

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
    print("Usage : %s [-t] <ffindr hash> <UC URL> <service>" % os.path.basename(__file__))
    print("-t: testing mode, print raw xml ")
    print()
    print("Available calendars:")
    with open("google-calendar.json") as f:
        for line in f:
            if "hash" in line:
                print(line, end=' ')


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ht")
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
    main_object = UpdateOneGoogleCalendar(args[0], args[1], args[2])
    for o, a in opts:
        if o in "-t":
            main_object.set_testing_mode()
    main_object.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        filename='updateAllGoogleCalendars.log',
                        format='[%(asctime)s %(filename)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

    main()
