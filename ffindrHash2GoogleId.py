#!/usr/bin/env python
# -*- coding: utf-8 -*-

# $Id: ffindrHash2GoogleId.py 74 2009-08-02 10:55:32Z marvin $

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
    
__author__ = 'stefanhorter@gmail.com'


try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree
import gdata.calendar.service
import gdata.service
import atom.service
import gdata.calendar
import atom
import getopt
import sys
import os
import re
import urllib
import pdb



class ffindrHash2GoogleId:

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
        
        # build source string
        command = 'grep "^# .Id: " ' + __file__ + ' | awk \'$4 ~ /[0-9]+/ {print $4}\''
        version = os.popen(command).read()
        source = 'marvin-ffindrHash2GoogleId-v' + str(version)
                
        self.calClient = gdata.calendar.service.CalendarService()
        self.calClient.email = 'wfdiscf@gmail.com'
        self.calClient.password = '6009l3wfd15cf'
        self.calClient.source = source
        self.calClient.ProgrammaticLogin()
        
        self.verboseMode     = False
        self.inputFfindrHash = ffindrHash
        
    
    def SetVerboseMode(self):
        self.verboseMode = True
    
    
    def Run(self):
        """Takes a ffindr RSS stream URL or a stream hash as an argument.

        Returns the calendar ID or '' if no ID found matching the hash or
        if some error occurred"""
        
        if self.verboseMode:
            print ">>>\n>>>", os.path.basename(__file__), "\n>>>"
        
        if self.verboseMode:
            print "Given ffindr hash:", self.inputFfindrHash
        
        
        # search the hash in all calendars
        ##################################
        
        try:
            allCalendarsFeed = self.calClient.GetOwnCalendarsFeed()
            # GetOwnCalendarsFeed instead of GetAllCalendarsFeed gets secondary calendars only
            #print allCalendarsFeed; sys.exit(0)
        
        except gdata.service.RequestError, err:
            print err[0]['status']
            print err[0]['body']
            print err[0]['reason']
            return ''
        
        except:
            print "error"
            return ''
        
        patternHash = re.compile(self.inputFfindrHash)

        calendarId = ''

        for entry in allCalendarsFeed.entry:
            if patternHash.search(str(entry.summary)):
                calendarId = urllib.unquote(entry.id.text.split('/').pop())
                if self.verboseMode:
                    print "... found calendar, ID:", calendarId
                break
        
        if self.verboseMode:
            if calendarId == '':
                print "No calendar found with this ffindr hash"
            print "<<<\n<<<", os.path.basename(__file__), ": return\n<<<"

        return calendarId



def Usage():
    print "Usage :", os.path.basename(__file__), "[-v] <ffindr hash>"



def main():
    """Runs the application."""
    
    # get parameter
    ###############
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv")
    except getopt.GetoptError:
        print "Unknown option"
        Usage()
        sys.exit(1)
    
    if not len(args) == 1:
        print "Wrong number of arguments"
        Usage()
        sys.exit(1)
        
    mainObject = ffindrHash2GoogleId(args[0])
    
    
    for o, a in opts:
        if o in ("-h", "--help"):
            Usage()
            sys.exit()
        
        if o in ("-v"):
            mainObject.SetVerboseMode()
            
    if not len(args) == 1:
        sys.exit(1)
    
    
    mainObject.Run()



if __name__ == '__main__':
    main()
