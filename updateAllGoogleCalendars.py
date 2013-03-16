#!/usr/bin/env python
# -*- coding: utf-8 -*-

# $Id: updateAllGoogleCalendars.py 76 2009-08-02 15:39:01Z marvin $


__author__ = 'marv42@gmail.com'


import getopt
import sys
import time
import datetime
import posix
import os
import urllib
from createAndUpdateGoogleCalendar import CreateAndUpdateGoogleCalendar
import simplejson
from xml.dom.minidom import parse



class UpdateAllGoogleCalendars:

    def __init__(self):
        self.verboseMode = False

    def SetVerboseMode(self):
        self.verboseMode = True


    def Run(self):
        """Get all ffindr hashes from ffindr and call updateOneGoogleCalendar
        for each of them"""

        inputXml = os.path.dirname(os.path.abspath(__file__)) + '/google-calendar.xml'


        # parse the content of the ffindr RSS stream
        ############################################

        if self.verboseMode:
            print "Input XML: ", inputXml

        if inputXml.startswith('http://'):
            f = urllib.urlopen(inputXml, 'r')
        else:
            f = open(inputXml, 'r')

        #if self.verboseMode:
        #    print "Handle: ", f
        dom = parse(f)


        # for all calendars
        ###################

        # firstChild == "ffindr", firstChild.firstChild == "filters"
        #print dom.firstChild.firstChild
        for filterNode in dom.firstChild.firstChild.childNodes:
            if filterNode.nodeName == "filter":

                for i in range(0, filterNode.attributes.length):
                    if filterNode.attributes.item(i).name == "name":
                        filterName = filterNode.attributes.item(i).value
                    if filterNode.attributes.item(i).name == "hash":
                        filterHash = filterNode.attributes.item(i).value

                if self.verboseMode:
                    print "Calling CreateAndUpdateGoogleCalendar on '", filterName, "' with hash", filterHash, "..."

                createAndUpdate = CreateAndUpdateGoogleCalendar(filterHash)

                if self.verboseMode:
                    createAndUpdate.SetVerboseMode()

                returnJson = simplejson.loads(createAndUpdate.Run())
                #print returnJson

                if returnJson['error'] == 'NULL':
                    if self.verboseMode:
                        print "... successfully updated                          *** O.k. ***"

                else:
                    if self.verboseMode:
                        print "... failed, waiting one minute ..."

                    # wait one minute and try again
                    ###############################

                    t = datetime.datetime.now()
                    while t + datetime.timedelta(0,0,0,0,1) > datetime.datetime.now():
                        continue

                    if self.verboseMode:
                        print "... trying once more ..."

                    returnJson = simplejson.loads(createAndUpdate.Run())

                    if not returnJson['error'] == 'NULL':
                        if self.verboseMode:
                            print "... failed"


def Usage():

    print "Usage :", os.path.basename(__file__), "[-v]"
    print "-v: verbose mode"
    return



def main():
    """Runs the application."""

    try:
        opts, args = getopt.getopt(sys.argv[1:], "htv")
    except getopt.GetoptError:
        print "Unknown option"
        Usage()
        sys.exit(1)

    if not len(args) == 0:
        print "Wrong number of arguments"
        Usage()
        sys.exit(1)


    mainObject = UpdateAllGoogleCalendars()


    for o, a in opts:
        if o in ("-v"):
            mainObject.SetVerboseMode()

        if o in ("-h", "--help"):
            Usage()
            sys.exit()


    mainObject.Run()



if __name__ == '__main__':
    main()
