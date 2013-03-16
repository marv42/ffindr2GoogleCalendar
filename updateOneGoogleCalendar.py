#!/usr/bin/env python
# -*- coding: utf-8 -*-

# $Id: updateOneGoogleCalendar.py 76 2009-08-02 15:39:01Z marvin $

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


try:
    from xml.etree import ElementTree # for Python 2.5 users
except ImportError:
    from elementtree import ElementTree
import gdata.calendar.service
import gdata.service
import atom.service
import gdata.calendar
import atom
import getopt
import sys
import datetime
import time
import posix
import os
import re
import urllib2
from xml.dom.minidom import parse
from ffindrHash2GoogleId import ffindrHash2GoogleId
from utils import unHtmlify



class UpdateOneGoogleCalendar:
    
    def __init__(self, ffindrUrl):
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
        
        # build source string
        command = 'grep "^# .Id: " ' + __file__ + ' | awk \'$4 ~ /[0-9]+/ {print $4}\''
        version = os.popen(command).read()
        source = 'marvin-updateOneGoogleCalendar-v' + str(version)
        
        self.calClient = gdata.calendar.service.CalendarService()
        self.calClient.email = 'wfdiscf@gmail.com'
        self.calClient.password = '6009l3wfd15cf'
        self.calClient.source = source
        self.calClient.ProgrammaticLogin()
        
        self.verboseMode    = False
        self.testingMode    = False
        self.inputFfindrUrl = ffindrUrl
    
    
    
    def _InsertSingleEvent(self, id=u'default',
                           title=u'No Title',
                           content=u' ',
                           link=u' ',
                           where=u' ',
                           start_time=None,
                           end_time=None):
        """Inserts a basic event using either start_time/end_time definitions
        or gd:recurrence RFC2445 icalendar syntax.  Specifying both types of
        dates is not valid.  Note how some members of the CalendarEventEntry
        class use arrays and others do not.  Members which are allowed to
        occur more than once in the calendar or GData"kinds" specifications
        are stored as arrays.  Even for these elements, Google Calendar may
        limit the number stored to 1.  The general motto to use when working
        with the Calendar data API is that functionality not available through
        the GUI will not be available through the API.  Please see the GData
        Event "kind" document:
        http://code.google.com/apis/gdata/elements.html#gdEventKind for more
        information"""
        
        event = gdata.calendar.CalendarEventEntry()
        event.title   = atom.Title(text=title)
        event.content = atom.Content(text=content)
        event.link.append(atom.Link(rel='alternate', link_type='text/html', href=link))
        # link.append doesn't seem to have an effect in the Google web client
        event.where.append(gdata.calendar.Where(value_string=where))
        
        if start_time is None: # should not happen!
            # Use current time for the start_time
            start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z',
                                       time.gmtime())
                                       
            # end_time == None => single/whole day event
            
        event.when.append(gdata.calendar.When(start_time=start_time,
                                              end_time=end_time))
        
        new_event = self.calClient.InsertEvent(event, '/calendar/feeds/' + self.calendarId + '/private/full')
        
        return new_event
    
    
    def SetVerboseMode(self):
        self.verboseMode = True
    
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
        
        if self.verboseMode:
            print ">>>\n>>>", __name__, "\n>>>"
        
        
        # prepend prefix
        ################            
        
        prefix = "http://ffindr.com/en/feed/filter/"
        if not self.inputFfindrUrl.startswith(prefix):
            self.inputFfindrUrl = prefix + self.inputFfindrUrl

        if self.testingMode:
            sock = urllib2.urlopen(self.inputFfindrUrl)
            file("contentOfInputFfindrUrl.xml", 'w').write(sock.read())
            sock.close()
        
        if self.verboseMode:
            print "Given ffindr stream URL:", self.inputFfindrUrl
        
        
        # get calendar query object
        ###########################
        
        idDetermination = ffindrHash2GoogleId(self.inputFfindrUrl)
        
        if self.verboseMode:
            idDetermination.SetVerboseMode()
        
        self.calendarId = idDetermination.Run()
        
        if self.calendarId == '':
            if self.verboseMode:
                print "Error getting calendar ID"
            return 102

        if self.verboseMode:
            print "Got calendar ID:", self.calendarId #, "=> URL"
        
        eventQuery = gdata.calendar.service.CalendarEventQuery(self.calendarId)
        
        #eventQuery.futureevents = 'true' # must be according to the ffindr
                                          # feed results
        eventQuery.max_results = 150 # needs to be > than what the ffindr feed
                                     # returns, or the events will be inserted
                                     # again and again!
        
        try:
            calendarQuery = self.calClient.CalendarQuery(eventQuery)
        
        except gdata.service.RequestError, err:
            if self.verboseMode:
                print "Error reading calendar", self.calendarId, ":", err
            return 102
        
        if self.verboseMode:
            print "Got calendar query object"
        
        
        # parse the content of the ffindr RSS stream
        ############################################
        
        feed = urllib2.urlopen(self.inputFfindrUrl)
        dom = parse(feed)

        
        # for every event
        #################
        
        failedUpdates = 0

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
                    if node.nodeName == "description":
                        description = node.childNodes[0].nodeValue
                    if node.nodeName == "author":
                        author      = node.childNodes[0].nodeValue
                    if node.nodeName == "category":
                        if category is not u'':
                            category += ", "
                        category    += node.childNodes[0].nodeValue
                    if node.nodeName == "country":
                        country     = node.childNodes[0].nodeValue
                    if node.nodeName == "location":
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
                
                if title == '<incomplete>':
                    failedUpdates += 1
                    if self.verboseMode:
                        print "Update of one event failed because it was incomplete"
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
                country     = country.strip()
                geoLat      = geoLat.strip()
                geoLong     = geoLong.strip()
            
                location = unHtmlify(location)
                #print location
            
                # date calculation
                
                # End += 1 day (or Google takes two days events as one day)
                [year, month, day] = str(dateEnd).split('-')
                endDate      = datetime.date(int(year), int(month), int(day))
                endDate     += datetime.timedelta(1)
                dateEnd = endDate.isoformat()
                
                # description: link, (tags,) author, location
                
                if description.endswith('...'):
                    description += u'\n\n(truncated, for the complete description see the ffindr website)'
                
                description += u'\n\n\n   *** ffindr tags ***'
            
                if link is not '':
                    description += u'\n\nWebsite: ' + link
            
                # + u'\n\Tags: ' + tags
                
                if author is not '':
                    description += u'\n\nAuthor: ' + author
            
                if location is not '':
                    locationForDescription = location
                    if country is not '':
                        # @todo && if location does not include country
                        locationForDescription += u', ' + country
                else:
                    locationForDescription = country
                
                if locationForDescription is not '':
                    description += u'\n\nLocation: ' + locationForDescription
                
                if category is not '':
                    description += u'\n\nCategory: ' + category
                
                if geoLat is not '' and geoLong is not '':
                    # remove "(" and ")" or the map link won't work
                    locationForDescription = locationForDescription.replace('(', u'')
                    locationForDescription = locationForDescription.replace(')', u'')
                    locationForWhere = geoLat + u', ' + geoLong + u' (' + locationForDescription + u')'
            
                if self.verboseMode:
                    print "Updating event '", title.encode('utf-8'), "' (", locationForDescription.encode('utf-8'), ")..."
            
                # check if event already exists
                ###############################
                
                eventIsAlreadyInCalendar = False
                
                for event in calendarQuery.entry:
                    #print Title.encode('utf-8'), " ?= ", event.title.text.decode(sys.stdout.encoding)
                    if event.title.text.decode('utf-8') == title:
                        eventIsAlreadyInCalendar = True
                        break
                
                if eventIsAlreadyInCalendar:
                    if self.verboseMode:
                        print "... event was already in the calendar"
                    continue
                
                
                # insert event
                ##############
                
                if self.verboseMode:
                    print "... ***** NEW EVENT *****, inserting event"
                
                #print type(Title); return
                successful = False
                i = 0
                howManyTimes = 3
                while not successful and i < howManyTimes:
                    try:
                        event = self._InsertSingleEvent(self.calendarId, title,
                                                        description, link,
                                                        locationForWhere,
                                                        dateStart, dateEnd)
                        successful = True
                    except gdata.service.RequestError, err:
                        i+=1
                        if self.verboseMode:
                            print "Error inserting event ('%s'). Trying once more (%i/%i)..." % (str(err), i, howManyTimes)
                        time.sleep(120)


        # delete duplicate events
        #########################
        
        if self.verboseMode:
            print "Checking for duplicate events..."

        eventQuery.max_results = 500
        
        try:
            calendarQuery = self.calClient.CalendarQuery(eventQuery)
        
        except gdata.service.RequestError, err:
            if self.verboseMode:
                print "Error reading calendar", self.calendarId
            return 102
        
        if self.verboseMode:
            print "Got calendar query object"

        deletedEvents = 0

        for event1 in calendarQuery.entry:
            for event2 in calendarQuery.entry:
                if event1.title.text != event2.title.text or event1 == event2:
                    continue

                # @todo compare the update dates

                if self.verboseMode:
                    print "Deleting event '", event1.title.text, "'"
                deletedEvents += 1
                try:
                    self.calClient.DeleteEvent(event1.GetEditLink().href)
                    self.calClient.DeleteEvent(event2.GetEditLink().href)
                except gdata.service.RequestError, err:
                    if self.verboseMode:
                        print "Error deleting event"
                    deletedEvents -= 1
                    
                    
        if self.verboseMode:
            print "Deleted", deletedEvents, "events"

        
            print "<<<\n<<<", __name__, ":", failedUpdates, "failed updates\n<<<"
        
        return failedUpdates



def Usage():

    print "Usage :", os.path.basename(__file__), "[-t] [-v] <ffindr hash>"
    print "-v: verbose mode"
    print "-t: testing mode, print raw xml "
    print
    print "Available calendars:"

    xml = './google-calendar-xml'
    xml = 'http://ffindr.com/google-calendar-xml/'
    sock = urllib2.urlopen(xml)
    print sock.read()
    sock.close()

    return



def main():
    """Runs the application."""
    
    
    # get parameter
    ###############
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "htv")
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

        if o in ("-v"):
            mainObject.SetVerboseMode()
    
        
    mainObject.Run()



if __name__ == '__main__':
    main()
