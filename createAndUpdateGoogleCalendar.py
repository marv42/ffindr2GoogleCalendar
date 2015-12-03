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


from updateOneGoogleCalendar import UpdateOneGoogleCalendar
from authentication import Authentication
import logging
import re
from xml.sax import ContentHandler
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces
import json



class FfindrChannelContentHandler(ContentHandler):

    def __init__(self):
        self.inChannelContent = True
        self.inTitleContent   = False

    def startElement(self, name, attrs):
        if name == 'item':
            # exclude item content
            self.inChannelContent = False

        elif self.inChannelContent:
            if name == 'title':
                self.inTitleContent = True
                self.title = ""

    def characters(self, ch):
        if self.inTitleContent:
            self.title = self.title + ch

    def ignorableWhitespace(self, ch):
        if self.inTitleContent:
            self.title = self.title + ch

    def endElement(self, name):
        if name == 'title':
            self.inTitleContent = False

    def getTitle(self):
        return self.title




class CreateAndUpdateGoogleCalendar:

    def __init__(self, hash, url):
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

        self.ffindrHash    = hash
        self.url           = url
        self.calendarTitle = 'no Title'
        self.calendarId    = -1
        self.debugMode     = False

    def _InsertCalendar(self,
                        title='Standard ffindr Stream Calendar Title',
                        description='Standard ffindr Stream Calendar',
                        time_zone='Europe/Paris',
                        hidden=False,
                        location='Paris',
                        color='#2952A3'):
        """Creates a new calendar using the specified data."""

        description = 'This calendar is generated automatically from the ffindr RSS stream "%s" (http://ffindr.com/en/feed/filter/%s).\n\nIf you want your tournament to be listed here, enter it to ffindr.\n\nffindr is one of the biggest frisbee tournament portals on the web: www.ffindr.com' % (title, self.ffindrHash)

        colorlist = ("#0D7813", "#1B887A", "#29527A", "#2952A3", "#28754E", "#4A716C", "#4E5D6C", "#5229A3", "#528800", "#5A6986", "#6E6E41", "#705770", "#7A367A", "#865A5A", "#88880E", "#8D6F47", "#A32929", "#AB8B00", "#B1365F", "#B1440E", "#BE6D00")
        randomColor = colorlist[random.randrange(len(colorlist))]

        calendar = gdata.calendar.CalendarListEntry()
        calendar.title = atom.Title(text=title)
        calendar.summary = atom.Summary(text=description)
        calendar.where = gdata.calendar.Where(value_string=location)
        calendar.color = gdata.calendar.Color(value=randomColor)
        calendar.timezone = gdata.calendar.Timezone(value=time_zone)

        if hidden:
            calendar.hidden = gdata.calendar.Hidden(value='true')
        else:
            calendar.hidden = gdata.calendar.Hidden(value='false')

        #params={ ' ': ' '} ?
        #new_calendar = self.calClient.InsertCalendar(new_calendar=calendar, url_params=params)

        # TODO
        new_calendar = self.calClient.InsertCalendar(new_calendar=calendar)
        return new_calendar


    def _CreateAclRule(self):

        rule = gdata.calendar.CalendarAclEntry()
        rule.scope = gdata.calendar.Scope(scope_type='default') # all users, no value
        roleValue = 'http://schemas.google.com/gCal/2005#read'
        rule.role = gdata.calendar.Role(value=roleValue)
        aclUrl = 'http://www.google.com/calendar/feeds/%s/acl/full' % self.calendarId
        #aclUrl = '/calendar/feeds/%s/acl/full' % self.calendarId
        # TODO
        returned_rule = self.calClient.InsertAclEntry(rule, aclUrl)


    def SetDebugMode(self):
        self.debugMode = True



    #def error(self, exception):
    #    sys.stderr.write("\%s\n" % exception)

    def Run(self):
        """If the calendar doesn't already exist, creates a new empty calendar
        from a ffindr RSS stream (given by the CGI) in the WFDF Google
        calendar account and calls updateOneGoogleCalendar.

        Return values:

        0: creation and updating of calendar successful
        1: creation of calendar successful but updating failed
        2: creation of calendar successful but we couldn't set the permissions because we couldn't determine the calendar ID from the URL
        3: creation of calendar failed because Google couldn't create it
        4: creation of calendar failed, Google connectivity problems
        5: creation of calendar failed, other error

        We don't have to care if the insertion of the events ('update') was
        successful or not. If not, we assume it to be successful on the next
        update of the calendar."""

        if self.ffindrHash == '':
            logging.error("no ffindr hash given")
            return json.dumps({'result': 'NULL', 'error': 'No ffindr hash given'})
        if self.url == '':
            logging.error("no url given")
            return json.dumps({'result': 'NULL', 'error': 'No URL given'})

        if self.debugMode:
            # raw XML:
            sock = urllib.urlopen(self.url)
            htmlSource = sock.read()
            sock.close()
            print htmlSource
            sys.exit()


        # parse the content of the RSS stream
        ############################################

        # setup XML parser
        parser = make_parser()

        # tell the parser we are not interested in XML namespaces
        parser.setFeature(feature_namespaces, 0)

        cch = FfindrChannelContentHandler()
        parser.setContentHandler(cch)
        parser.setEntityResolver(cch)

        parser.parse(self.url)

        calendarTitle = cch.getTitle()


        # check if calendar already exists
        ##################################

        calendarList = self.service.calendarList().list().execute()
        #print calendarList; sys.exit()

        googlePrefix = "http://www.google.com/calendar/feeds/default/owncalendars/full/"

        patternHash = re.compile(self.ffindrHash)

        calendarExistedAlready = False
        for entry in calendarList['items']:
            if patternHash.search(str(entry['description'])):
                calendarExistedAlready = True
                self.calendarId = entry['id']
                self.calendarId = self.calendarId[len(googlePrefix):len(self.calendarId)]
                break

        publicUrl = "http://www.google.com/calendar/embed?src=%s" % self.calendarId # rather with GetLink() (?)

        if not calendarExistedAlready:

            # try to create new calendar
            ############################

            #logging.info("... calendar is not yet a Google calendar")
            logging.info("trying to create the Google calendar ...")

            try:
                newCalendar = self._InsertCalendar(title=calendarTitle)

            except gdata.service.RequestError, err:
                if err[0]['status'] == 500:
                    # Internal Server Error
                    print err[0]['status']
                    print err[0]['body']
                    print err[0]['reason']
                    return json.dumps({'result': 'NULL', 'error': 'Google couldn\'t create a new calendar'})

                elif err[0]['status'] == 403:
                    #command = 'mail -s "ffindr2Google: not enough quota" marv42@gmail.com'
                    #os.system(command)
                    print err[0]['status']
                    print err[0]['body']
                    print err[0]['reason']
                    return json.dumps({'result': 'NULL', 'error': 'Google couldn\'t create a new calendar'})

                else:
                    print err[0]['status']
                    print err[0]['body']
                    print err[0]['reason']
                    return json.dumps({'result': 'NULL', 'error': 'Google connectivity problems'})

            except:
                return json.dumps({'result': 'NULL', 'error': 'Google connectivity problems'})

            logging.info("... successful")

            self.calendarId = newCalendar.id.text


            # set permissions
            #################

            if self.calendarId.startswith(googlePrefix):
                self.calendarId = self.calendarId[len(googlePrefix):len(self.calendarId)]

            else:
                logging.error("error stripping prefix")
                return json.dumps({'result': 'NULL', 'error': 'Couldn\'t determine the calendar ID from the URL (error stripping prefix)'})
                # because we wouldn't be able to set the permissions with this ID

            logging.info("setting permissions / make calendar public ...")

            self._CreateAclRule() # make calendar public
            #self._CreateAclRule("user@gmail.com")


            # send information mail
            #######################

            publicUrl = "http://www.google.com/calendar/embed?src=%s" % self.calendarId
            command = 'echo "... has just been created with the URL ' + publicUrl + '." | mail -s "New Google calendar" marv42@gmail.com'
            os.system(command)

        # call updateOneGoogleCalendar
        ##############################

        # we don't have to check if we have got a valid URL --
        # updateOneGoogleCalendar will check this

        updateObject = UpdateOneGoogleCalendar(self.ffindrHash, self.url)

        updateSuccessful = updateObject.Run()
        logging.info("(debug with: 'updateOneGoogleCalendar.py -t %s %s')" % (self.ffindrHash, self.url))
        if not updateSuccessful == 0:
            logging.info("... failed")
            return json.dumps({'result': 'NULL', 'error': 'Creation successful but updating failed'})


        # get the calendar URL
        ######################

        return json.dumps({'error': 'NULL', 'result': publicUrl})



def Usage():
    print "Usage : %s [-d] <ffindr hash> <UC URL> " % os.path.basename(__file__)
    print
    print "Available hashes:"

    xml = './google-calendar.xml'
    sock = urllib.urlopen(xml)
    print sock.read()
    sock.close()

    return 0, ''



def main():
    """Runs the application."""

    try:
        opts, args = getopt.getopt(sys.argv[1:], "dh")
    except getopt.GetoptError:
        print "Unknown option"
        Usage()
        sys.exit(5)

    for o, a in opts:
        if o in ("-h", "--help"):
            Usage()
            sys.exit()

    if not len(args) == 2:
        print "Wrong number of arguments"
        print Usage()
        sys.exit(5)


    mainObject = CreateAndUpdateGoogleCalendar(args[0], args[1])


    for o, a in opts:
        if o in ("-d"):
            mainObject.SetDebugMode()


    mainObject.Run()



if __name__ == '__main__':
    main()
