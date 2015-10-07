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


from ffindrHash2GoogleId import ffindrHash2GoogleId
from authentication import Authentication
from utils import unHtmlify
from xml.dom.minidom import parse
from datetime import datetime, date, timedelta
import getopt
import logging
import os
import sys
import urllib2
import json


class UpdateOneGoogleCalendar:

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

        self.testingMode = False
        self.ffindrHash = ffindrHash


    def SetTestingMode(self):
        self.testingMode = True

    def Run(self):
        """Updates a calendar in the WFDF Google calendar account with the
        events of a ffindr (www.ffindr.com) RSS stream.

        "Updating a calendar" means, inserting the events the titles of which
        don't yet exist in the calendar.

        *** Updating events is not yet implemented ***

        Workaround: delete non-up-to-date events by hand and they will be
        inserted correctly the next time.

        return values:
        0 = successfully updated calendar
        1 -- 100 = number of events the update of which failed
        101 = error: wrong number of parameters
        102 = error: unknown calendar ID or Google connectivity problems
        103 = error: unknown ffindr stream URL
        104 = error: parse error, inconsistent amount of elements"""


        ffindrUrlPrefix = "http://ffindr.com/en/feed/filter/"
        if self.testingMode:
            url = "%s%s" % (ffindrUrlPrefix, self.ffindrHash)
            logging.info(url)
            sock = urllib2.urlopen(url)
            file("contentOfInputFfindrUrl.xml", 'w').write(sock.read())
            sock.close()
            logging.info("see contentOfInputFfindrUrl.xml")

        logging.info(self.ffindrHash)


        # get calendar query object
        ###########################

        idDetermination = ffindrHash2GoogleId(self.ffindrHash)


        self.calendarId = idDetermination.Run()

        if self.calendarId == '':
            logging.error("error getting calendar ID")
            return 102

        logging.info(self.calendarId) #, "=> URL"

        #calendar = self.service.calendarList().get(calendarId=self.calendarId).execute()
        #print json.dumps(calendar, sort_keys=True, indent=4); sys.exit(0)


        # parse the content of the ffindr RSS stream
        ############################################

        feed = urllib2.urlopen("%s%s" % (ffindrUrlPrefix, self.ffindrHash))
        dom = parse(feed)


        # for every event
        #################

        today = datetime.today()
        pageToken = None
        events = []
        while True:
            eventPage = self.service.events().list(calendarId=self.calendarId,
                                                   pageToken=pageToken,
                                                   timeMin=today.strftime('%Y-%m-%dT%H:%M:%S-00:00')).execute()
            for event in eventPage['items']:
                events.append(event)
            pageToken = eventPage.get('nextPageToken')
            if not pageToken:
                break

        # firstChild == "rss", firstChild.firstChild == <text>, firstChild.childNodes[1] == "channel"
        for itemNode in dom.firstChild.childNodes[1].childNodes:
            if itemNode.nodeName == "item":

                author      = u''
                category    = u''
                description = u''
                for node in itemNode.childNodes:
                    if node.nodeName == "title":
                        title       = node.childNodes[0].nodeValue
                    if node.nodeName == "link":
                        link        = node.childNodes[0].nodeValue
                    if node.nodeName == "description" and len(node.childNodes) > 0:
                        description = node.childNodes[0].nodeValue
                    if node.nodeName == "author":
                        author      = node.childNodes[0].nodeValue
                    if node.nodeName == "category":
                        if category is not u'':
                            category += ", "
                        category    += node.childNodes[0].nodeValue
                    if node.nodeName == "location" and len(node.childNodes) > 0:
                        location    = node.childNodes[0].nodeValue
                    if node.nodeName == "dateStart":
                        dateStart   = node.childNodes[0].nodeValue
                    if node.nodeName == "dateEnd":
                        dateEnd     = node.childNodes[0].nodeValue
                    if node.nodeName == "geo:lat":
                        geoLat      = node.childNodes[0].nodeValue
                    if node.nodeName == "geo:long":
                        geoLong     = node.childNodes[0].nodeValue



                # assign the values of the ffindr stream to the calendar properties
                ###################################################################

                # set up the gd properties with the ffindr values

                if 'DELETED' in title:
                    continue
                if title == '<incomplete>':
                    logging.warning("Update of one event failed because it was incomplete")
                    continue

                # strip

                title       = title.strip()
                link        = link.strip()
                #tags        = tags.strip()
                description = description.strip()
                #content     = content.strip()
                author      = author.strip()
                category    = category.strip()
                dateStart   = dateStart.strip()
                dateEnd     = dateEnd.strip()
                location    = location.strip()
                geoLat      = geoLat.strip()
                geoLong     = geoLong.strip()

                location = unHtmlify(location)
                #print location

                # date calculation

                [year, month, day] = str(dateStart).split('-')
                startDate = date(int(year), int(month), int(day))
                [year, month, day] = str(dateEnd).split('-')
                endDate = date(int(year), int(month), int(day))
                # end += 1 day (or Google takes two days events as one day)
                endDate += timedelta(1)
                dateEnd = endDate.isoformat()
                if (endDate - startDate).days > 7: # 1 week
                    continue

                # description: link, (tags,) author, location

                if description.endswith('...'):
                    description += u'\n\n(truncated, for the complete description see the ffindr website)'

                description += u'\n\n\n   *** ffindr tags ***'

                if link is not '':
                    description += u'\n\nWebsite: ' + link

                # + u'\n\Tags: ' + tags

                if author is not '':
                    description += u'\n\nAuthor: ' + author

                locationForDescription = ''
                if location is not '':
                    locationForDescription = location

                if locationForDescription is not '':
                    description += u'\n\nLocation: ' + locationForDescription

                if category is not '':
                    description += u'\n\nCategory: ' + category

                if geoLat is not '' and geoLong is not '':
                    # remove "(" and ")" or the map link won't work
                    locationForDescription = locationForDescription.replace('(', u'')
                    locationForDescription = locationForDescription.replace(')', u'')
                    locationForWhere = geoLat + u', ' + geoLong + u' (' + locationForDescription + u')'

                logging.info("event '%s'" % title.encode('utf-8'))

                # check if event already exists
                ###############################

                eventIsAlreadyInCalendar = False

                for event in events:
                    eventTitle = event.get('source')
                    if eventTitle is not None:
                        eventTitle = event.get('title')
                    if eventTitle is None:
                        eventTitle = event.get('summary')
                    if eventTitle == title:
                        eventIsAlreadyInCalendar = True
                        break

                if eventIsAlreadyInCalendar:
                    logging.info("... was already in the calendar")
                    continue


                # insert event
                ##############

                logging.info("### NEW ###")
                #print type(Title); return

                source = {}
                source['url'] = link
                source['title'] = title
                event = {}
                event['source'] = source
                event['start'] = { 'date': dateStart }
                event['end'] = { 'date': dateEnd }
                event['location'] = locationForWhere
                event['description'] = description
                event['summary'] = title
                newEvent = self.service.events().insert(calendarId=self.calendarId, body=event).execute()


        # delete duplicate events
        #########################

        def deleteEvent(id):
            logging.info("deleting event %s" % id)
            # TODO geht ned
            response = self.service.events().delete(calendarId=self.calendarId,
                                                    eventId=id)
            if json.loads(response.to_json())['body'] != None:
                logging.info("... failed")

        for event1 in events:
            summary1 = event1.get('summary')
            for event2 in events:
                summary2 = event2.get('summary')
                if summary1 == summary2 and \
                       event1['id'] != event2['id']:
                    logging.info(summary1)
                    deleteEvent(event1['id'])
                    deleteEvent(event2['id'])
                    break

        return 0



def Usage():

    print "Usage : %s [-t] <ffindr hash>" % os.path.basename(__file__)
    print "-t: testing mode, print raw xml "

    print
    print "Available calendars:"
    for line in file("google-calendar.json"):
        if "hash" in line:
            print line,

    return



def main():
    """Runs the application."""


    # get parameter
    ###############

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ht")
    except getopt.GetoptError as e:
        Usage()
        sys.exit(str(e))

    for o, a in opts:
        if o in ("-h", "--help"):
            Usage()
            sys.exit()

    if not len(args) == 1:
        Usage()
        sys.exit("Wrong number of arguments")


    mainObject = UpdateOneGoogleCalendar(args[0])


    for o, a in opts:
        if o in ("-t"):
            mainObject.SetTestingMode()


    mainObject.Run()



if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO,
                        filename='updateAllGoogleCalendars.log',
                        format='[%(asctime)s %(filename)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

    main()
