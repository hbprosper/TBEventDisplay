#!/usr/bin/env python
#-----------------------------------------------------------------------------
# File:        TBEventDisplay.py
# Description: Simple event display for 2016 HGCal test beam experiments
# Created:     25-Mar-2016 Jeremy Thomas & Harrison B. Prosper
#              (adapted from TB 2014 display by Sam Bein & HBP)
#-----------------------------------------------------------------------------
import sys, os, re, time, platform
from time import ctime, sleep
from array import array
from HGCal.TBEventDisplay.Util import *
from HGCal.TBEventDisplay.TBUtil import *

from HGCal.TBEventDisplay.TBADCCounts import ADCCounts
from HGCal.TBEventDisplay.TBHeatMap import HeatMap
from HGCal.TBEventDisplay.TBLego import Lego
from HGCal.TBEventDisplay.TBDisplay3D import Display3D

from HGCal.TBStandaloneSimulator.TBFileReader import TBFileReader
from HGCal.TBStandaloneSimulator.TBGeometryUtil import *
from string import *
from ROOT import *
#------------------------------------------------------------------------------
WIDTH        = 1200            # Width of GUI in pixels
HEIGHT       =  900            # Height of GUI in pixels
VERSION      = \
"""
TBEventDisplay.py %s
Python            %s
Root              %s
""" % ('v1.0',
       platform.python_version(),
       gROOT.GetVersion())
#-----------------------------------------------------------------------------
# Help
HELP = \
"""
The time has come the walrus said
"""

ABOUT = \
"""
%s
\tCMS HGCal Test Beam 2016
\te-mail: harry@hep.fsu.edu
""" % VERSION

# read modes
R_REWIND  =-1
R_ONESHOT = 0
R_FORWARD = 1

MINDELAY  = 0.2

DEBUG = 0

CODE3D_1 =  '''
class Opacity:
   def __init__(self, element):
      self.element = element
      self.transparent = True
      self.transparency=99

   def __del__(self):
      pass

   def toggle(self):
      self.transparent = not self.transparent
      if self.transparent:
         self.transparency=99
      else:
         self.transparency=0
      for shape in self.element.shapes:
         shape.SetMainTransparency(self.transparency)
      # force a redraw of scene
      gEve.GetGlobalScene().SetRnrSelf(kFALSE)
      gEve.Redraw3D()

element.opacity= Opacity(element)
element.button = CheckButton(element.opacity, 
                             element.sidebar,
                             hotstring='Opaque',
                             method='toggle',
                             text='toggle between transparent and opaque')
'''


PAGES = [(0, 'Channels',   'ADCCounts(self, page)', None),
         (1, 'HeatMap',    'HeatMap(self, page)',   None),
         (2, 'LegoPlot',   'Lego(self, page)',      None),
         (3, 'Display3D',  'Display3D(self, page)', [CODE3D_1])]

#-----------------------------------------------------------------------------
# (A) Root Graphical User Interfaces (GUI)
#
#   A Root GUI is a double tree of widgets (that is, graphical objects) with
#   which the user can interact in order to orchestrate a series of actions.
#   One tree describes the child-to-parent relationships, while the other
#   describes the parent-to-child relationships. The latter describes the
#   graphical layout of widgets. In the Root GUI system the two trees are not
#   isomorphic. For example, the child-to-parent relationship of a TGPopupMenu
#   is TGPopupMenu -> TGWindow, however, TGMenuBar -> TGPopupMenu is 
#   a typical parent-to-child relationship.
#
#   o A child-to-parent relationship is defined by the child widget when the
#     latter is created.
#
#   o A parent-to-child relationship, that is, a specific layout of a widget
#     within another, is defined by the parent after it has been created
#     using its AddFrame method in which the child is specified.
#
#   Each widget can emit one or more signals, usually triggered by some user
#   manipulation of, or action on, the widget. For example, clicking on a
#   tab of a  TGTab, that is, a notebook, will cause the notebook to emit
#   the signal "Selected(Int_t)" along with the identity of the selected tab.
#   Signals are connected to "Slots", that is, actions. This is how a user
#   GUI interaction can be made to yield one or more actions. Any signal can be
#   connected to any slot. Indeed, the relationship between signals and slots
#   can be many-many. In practice, a slot is modeled as a procedure such as
#   a method of the GUI class.
#  
#   In summary, a Root GUI is a (double) tree of widgets with which the user
#   can interact, whose signals---usually generated by user interactions---are
#   connected to slots, that is, actions modeled as methods of the GUI class.
#
# (B) This GUI
#
#   window                   (TGWindow)
#
#     main                      (TGMainFrame)
#
#       menuBar                    (TGMenuBar)
#         menuFile                    (TGPopupMenu)
#         menuEdit                    (TGPopupMenu)
#         menuEvent                   (TGPopupMenu)
#         menuHelp                    (TGPopupMenu)
#
#       vframe                     (TGVerticalFrame)
#         toolBar                    (TGToolBar)
#           nextButton                  (TGPictureButton)
#           previousButton              (TGPictureButton)
#
#         hframe                     (TGHorizontalFrame)
#           noteBook                    (TGTab)
#
#         statusBar                  (TGSTatusBar)
#-----------------------------------------------------------------------------
class TBEventDisplay:
    """
    gui = TBEventDisplay(title)
    """

    def __init__(self, title, geometryModule,
                 filename=None, width=WIDTH, height=HEIGHT):

        # Initial directory for open file dialog
        self.openDir  = os.environ['PWD']
        self.filename = filename

        self.pageNameMap = {}
        for idd, pageName, constructor, buttons in PAGES:
            self.pageNameMap[idd] = pageName

        self.Color = root.Color
        self.accumulate = False
        # in accumulate mode update every self.skip events
        self.skip       = 50
        self.ADCmin     = 300     # minimum number of adc counts
        self.setMaxAll  = False   # set all histograms to the same maximum
        self.cellmap    = HGCCellMap()
        # histogram cache (one per sensor)
        self.hist       = []
        # get test beam geometry
        geometry        = createGeometry(geometry=geometryModule)
        self.geometry   = geometry['geometry']
        self.sensitive  = geometry['sensitive']
        self.shutterOpen= False

        # create 2-D histograms for each sensor
        self.initDataCache()

        #-------------------------------------------------------------------
        # Create main frame
        #-------------------------------------------------------------------
        # Establish a connection between the main frame's "CloseWindow()"
        # signal and the GUI's "close" slot, modeled as a method.
        # When the main frame issues the signal CloseWindow() this
        # triggers a call to the close method of this class.
        #-------------------------------------------------------------------
        print 'create main frame'
        self.root = root.GetRoot()
        self.main = TGMainFrame(self.root, width, height)
        self.main.SetWindowName(title)
        self.main.SetCleanup(kDeepCleanup)
        self.connection = Connection(self.main, "CloseWindow()",
                                     self,      "exit")
        #-------------------------------------------------------------------
        # Create menu bar
        #-------------------------------------------------------------------
        print 'create menu bar'
        self.menuBar = MenuBar(self, self.main)

        self.menuBar.Add('File',
                         [('&Open',  'openFile'),
                          ('&Close', 'closeFile'),
                          0,
                          ('E&xit',  'exit')])

        self.menuBar.Add('Edit',
                         [('&Undo',  'undo')])
        

        self.menuBar.Add('Event',
                         [('&Next',     'nextEvent'),
                          ('&Previous', 'previousEvent'),
                          ('&Goto',     'gotoEvent'),
                          0,
                          ('Set min[ADC]', 'setADCmin'),
                          ('Set delay',    'setDelay')])

        self.menuBar.Add('Help',
                         [('About', 'about'),
                          ('Usage', 'usage')])

        #-------------------------------------------------------------------
        # Add vertical frame to the main frame to contain toolbar, notebook
        # and status window
        #-------------------------------------------------------------------
        print 'create vertical frame'
        self.vframe = TGVerticalFrame(self.main, 1, 1)
        self.main.AddFrame(self.vframe, TOP_X_Y)

        #-------------------------------------------------------------------
        # Add horizontal frame to contain toolbar
        #-------------------------------------------------------------------
        print 'create horizontal frame'
        self.toolBar = TGHorizontalFrame(self.vframe)
        self.vframe.AddFrame(self.toolBar, TOP_X)

        self.nextButton = PictureButton(self, self.toolBar,
                                        picture='GoForward.gif',
                                        method='nextEvent',
                                        text='go to next event')

        self.forwardButton = PictureButton(self, self.toolBar,
                                           picture='StepForward.png',
                                           method='forwardPlayer',
                                           text='foward event player')
        
        self.stopButton = PictureButton(self, self.toolBar,
                                        picture='Stop.png',
                                        method='stopPlayer',
                                        text='stop event player')
        
        self.rewindButton = PictureButton(self, self.toolBar,
                                          picture='Rewind.png',
                                          method='rewindPlayer',
                                          text='rewind event player')

        self.previousButton = PictureButton(self, self.toolBar,
                                            picture='GoBack.gif',
                                            method='previousEvent',
                                            text='go to previous event') 

        self.accumulateButton = CheckButton(self, self.toolBar,
                                            hotstring='Accumulate',
                                            method='toggleAccumulate',
                                            text='Accumulate')

        self.setMaxAllButton  = CheckButton(self, self.toolBar,
                                            hotstring='Set max ALL',
                                            method='toggleSetMaxAll',
                                            text='set all histograms '\
                                                'to the same max value')
  
        self.snapCanvasButton = PictureButton(self, self.toolBar,
                                              picture='Camera.png',
                                              method='snapCanvas',
                                              text='make a pdf of this canvas')
        #-------------------------------------------------------------------
        # Add a notebook with multiple pages
        #-------------------------------------------------------------------  
        print 'create notebook'
        self.pageName = 'default'

        self.noteBook = NoteBook(self, self.vframe, 
                                 'setPage', width, height)

        # Add pages 
        self.display = {}
        for idd, pageName, constructor, sidebar in PAGES:
            self.noteBook.Add(pageName, sidebar)
            self.noteBook.SetPage(pageName)
            page = self.noteBook.page
            print '\t==> add display: %s\t-->\t%s' % (pageName, constructor)
            obj = eval(constructor)
            self.display[pageName] = obj

        #-------------------------------------------------------------------
        # Create a status bar, divided into two parts
        #-------------------------------------------------------------------
        self.statusBar = TGStatusBar(self.vframe, 1, 1, kDoubleBorder)
        self.statusBar.SetHeight(22)
        status_parts = array('i')
        status_parts.append(18)
        status_parts.append(18)
        status_parts.append(24)
        status_parts.append(20)
        status_parts.append(20)
        self.statusBar.SetParts(status_parts, len(status_parts))
        self.progressBar = ProgressBar(self, self.statusBar)
        self.vframe.AddFrame(self.statusBar, TOP_X)

    
        # Initial state
        self.nevents = 0
        self.eventNumber = -1
        self.Delay  = MINDELAY
        self.DELAY  = int(1000*MINDELAY)
        self.mutex  = TMutex(kFALSE)
        self.timer  = TTimer()
        self.timerConnection = Connection(self.timer, 'Timeout()',
                                          self, 'managePlayer')
        
        self.DEBUG  = DEBUG
        self.DEBUG_COUNT = 0

        # Initialize layout        
        self.main.MapSubwindows()
        self.main.Resize()
        self.main.MapWindow()

        if filename != None: 
            self.__openFile(filename)

        # graphics style
        self.setStyle()

        # To DEBUG a display uncomment next line
        #self.setPage(2)

    def __del__(self):
        pass


    def debug(self, message):
        if self.DEBUG < 1: return
        self.DEBUG_COUNT += 1
        print "%10d> %s" % (self.DEBUG_COUNT, message)

    #-----------------------------------------------------------------------
    #	M E T H O D S
    #-----------------------------------------------------------------------
    #	S L O T S    (that is, callbacks)

    def openFile(self):
        dialog = Dialog(self.root, self.main)
        self.filename = dialog.SelectFile(kFDOpen, self.openDir)
        self.openDir = dialog.IniDir()
        if self.filename[-5:] != '.root':
            dialog.ShowText("Oops!",
                            "Please select a root file",
                            230, 30)
            return
        self.__openFile(self.filename)


    def __openFile(self, filename):
        self.filename = filename
        self.closeFile()		
        self.reader = TBFileReader(filename)
        self.nevents= self.reader.entries()
        self.statusBar.SetText('events: %d' % self.nevents, 0)
        self.statusBar.SetText(filename, 2)
        self.eventNumber = -1
        self.nextEvent()
        self.progressBar.SetRange(0, self.nevents)
        self.progressBar.SetPosition(self.eventNumber)
        self.filetime = time.ctime(os.path.getctime(filename))
        
    def refreshFile(self):
        try:
            t = self.filetime
        except:
            return
        if self.filetime == time.ctime(os.path.getctime(self.filename)):
            return                 
        else:      
            eventNumber = self.eventNumber  
            self.reader = TBFileReader(self.filename)
            self.nevents= self.reader.entries()
            self.statusBar.SetText('event: %d / %d' % \
                                       (eventNumber, self.nevents-1), 0)
            self.filetime = time.ctime(os.path.getctime(self.filename))
            self.eventNumber = eventNumber
        
    def closeFile(self):
        try:
            if self.reader.file().IsOpen():
                self.reader.file().Close()
                del self.reader
        except:
            pass

    def setPage(self, idd):
        self.pageName = self.pageNameMap[idd]
        self.noteBook.SetPage(idd)
        if self.eventNumber >= 0:
            self.displayEvent()

    def nextEvent(self):
        self.debug("begin:nextEvent")
        if self.eventNumber > self.nevents-2:
            self.eventNumber = 0
        self.readEvent(R_FORWARD)
        self.displayEvent()
        self.debug("end:nextEvent")			

    def previousEvent(self):
        self.debug('begin:previousEvent')
        if self.eventNumber < 1:
            self.eventNumber = self.nevents 
        self.readEvent(R_REWIND)
        self.displayEvent()
        self.debug('end:previousEvent')

    def gotoEvent(self):
        self.debug('begin:gotoEvent')
        from string import atoi
        dialog = Dialog(self.root, self.main)
        self.eventNumber = atoi(dialog.GetInput('Goto event %d - %d' % \
                                                    (0, self.nevents-1),
                                                '0'))
        self.eventNumber = max(self.eventNumber, 0)
        self.eventNumber = min(self.eventNumber, self.nevents-1)

        # do a one-shot read
        self.readEvent(R_ONESHOT)
        self.displayEvent()
        self.debug('end:gotoEvent')

    def forwardPlayer(self):
        self.debug('begin:forwardPlayer')
        self.mutex.Lock()
        self.forward = True
        self.timer.Start(self.DELAY, kFALSE)
        self.mutex.UnLock()
        self.debug('end:forwardPlayer')
        
    def rewindPlayer(self):
        self.debug('begin:rewindPlayer')
        self.mutex.Lock()
        self.forward = False
        self.timer.Start(self.DELAY, kFALSE)
        self.mutex.UnLock()
        self.debug('end:rewindPlayer')

    def stopPlayer(self):
        self.debug('begin:stopPlayer')
        self.mutex.Lock()
        self.timer.Stop()
        self.cycle = False
        self.mutex.UnLock()
        self.debug('end:stopPlayer - STOP REQUESTED')

    def managePlayer(self):
        if self.forward:
            self.nextEvent()
        else:
            self.previousEvent()
       
    def snapCanvas(self):
        self.shutterOpen = True
        self.displayEvent()
        self.shutterOpen = False

    def toggleAccumulate(self):
        self.accumulate = not self.accumulate

    def toggleSetMaxAll(self):
        self.setMaxAll = not self.setMaxAll

    def usage(self):
        dialog = Dialog(self.root, self.main)
        dialog.SetText('Not done', 'Sorry!', 230, 30)

    def about(self):
        dialog = Dialog(self.root, self.main)
        dialog.SetText('Not done', 'Sorry!', 230, 30)

    def exit(self):
        self.closeFile()
        gApplication.Terminate()

    def notdone(self):
        dialog = Dialog(self.root, self.main)
        dialog.SetText('Not done', 'Sorry!', 230, 30)

    def run(self):
        gApplication.Run()

    def displayEvent(self):
        self.progressBar.Reset()
        self.progressBar.SetPosition(self.eventNumber)
        pageNumber = self.noteBook.pageNumber
        page = self.noteBook.pages[pageNumber]
        self.debug("begin:displayEvent - %s" % page.name)
        self.refreshFile()
        # pass event display object to draw
        self.display[page.name].Draw(self)
        self.redraw = False
        page.redraw = False
        self.debug("end:displayEvent")	

    def readEvent(self, which=R_ONESHOT):
        self.debug("begin:readEvent")
        try:
            reader = self.reader
        except:
            dialog = Dialog(self.root, self.main)
            dialog.SetText('Oops!', 'First open a root file',
                           230, 24)
            self.debug("end:readEvent")
            return

        # cache previous event number
        self.eventNumberPrev = self.eventNumber

        # loop over events and apply ADC cut

        if   which == R_ONESHOT:
            self.statusBar.SetText('event: %d / %d' % \
                                       (self.eventNumber, self.nevents-1),
                                   0)            
            self.reader.read(self.eventNumber)
            self.fillDataCache()

        elif which == R_FORWARD:
            if self.eventNumber < self.nevents-1:
                self.eventNumber += 1
                self.statusBar.SetText('event: %d / %d' % \
                                           (self.eventNumber, self.nevents-1),
                                       0)
                self.reader.read(self.eventNumber)
                self.fillDataCache()
        else:
            if self.eventNumber > 0:
                self.eventNumber -= 1
                self.statusBar.SetText('event: %d / %d' % \
                                           (self.eventNumber, self.nevents-1),
                                       0)
                self.reader.read(self.eventNumber)
                self.fillDataCache()

        if self.eventNumber <= 0 or self.eventNumber >= self.nevents-1:
            self.stopPlayer()

        # Force a re-drawing of pages of notebook when a page is made
        # visible
        keys = self.noteBook.pages.keys()
        for key in keys:
            self.noteBook.pages[key].redraw = True

        self.debug("end:readEvent")

    
    def initDataCache(self):
        from copy import copy
        # -------------------------------------------------------------
        # create a histogram for each sensor
        # Note: in offline, layers start at 1
        # -------------------------------------------------------------
        self.cells = {}
        for l in xrange(len(self.sensitive)):
            layer = l + 1
            # we assume the cells for each layer to be identical
            self.cells[layer] = copy(self.cellmap.cells(layer))
            cells = self.cells[layer] # make an alias

            #from pprint import PrettyPrinter
            #pp = PrettyPrinter()
            #pp.pprint(self.geometry)
            #print self.sensitive[layer]

            element = self.geometry[self.sensitive[layer]]
            if not element.has_key('cellsize'):
                sys.exit('** keyword cellsize not found - check %s' % \
                             geometryModule)

            if not element.has_key('side'):
                sys.exit('** keyword side not found - check %s' % \
                             geometryModule)

            if not element.has_key('z'):
                sys.exit('** keyword z not found - check %s' % \
                             geometryModule)

            cellside= element['cellsize']
            side    = element['side']
            z       = element['z']

            poly = TH2Poly()
            poly.SetName('layer %3d' % layer)
            poly.SetTitle('layer %3d' % layer)
            poly.GetXaxis().CenterTitle()
            poly.GetXaxis().SetTitle("#font[12]{x} axis")
            poly.GetYaxis().CenterTitle()
            poly.GetYaxis().SetTitle("#font[12]{y} axis")

            # populate histogram with cells
            for ii in xrange(cells.size()):
                cells[ii].z = z
                xv, yv = computeBinVertices(cellside, cells[ii])
                poly.AddBin(len(xv), xv, yv)

            # cache sensor histogram
            self.hist.append(poly)

    def fillDataCache(self):
        # -------------------------------------------------------------
        if not self.accumulate:
            for h in self.hist:
                h.ClearBinContents()

        self.hits = getHits(self, self.cellmap, self.sensitive)
        if self.hits == None: return

        # fill sensor histograms
        layers = self.hits.keys()
        layers.sort()
        for layer in layers:
            for hit in self.hits[layer]:
                adc, u, v, x, y, z = hit
                self.hist[layer-1].Fill(x, y, adc)
                
                #record ="cell(%3d,%3d,%3d|%6.2f,%6.2f): %d" % \
                #    (layer, u ,v, x, y, adc)
                #print record

        # copy histogram counts into cell objects
        for l, h in enumerate(self.hist):
            layer = l + 1
            cells = self.cells[layer] # make an alias
            for ii in xrange(cells.size()):
                cell = cells[ii]
                cell.count = h.GetBinContent(ii+1)

        self.maxCount = -1
        for h in self.hist:
            y = h.GetMaximum()
            if y > self.maxCount:
                self.maxCount = y

        # set all histograms to min/max values
        for h in self.hist:
            h.SetMinimum(self.ADCmin)
            if self.setMaxAll > 0:
                h.SetMaximum(self.maxCount)
            else:
                h.SetMaximum()

    def setADCmin(self):
        from string import atof
        dialog = Dialog(self.root, self.main)
        self.ADCmin = atof(dialog.GetInput('enter min[ADC] count', 
                                           '%d' % self.ADCmin))
        self.statusBar.SetText('min[ADC] set to: %d' % self.ADCmin, 1)	

 
    def setDelay(self):
        from string import atof
        dialog = Dialog(self.root, self.main)
        seconds= atof(dialog.GetInput('Enter delay in seconds', 
                                      '%10.3f' % self.Delay))
        self.Delay = seconds
        self.DELAY = max(MINDELAY, int(1000*seconds))
        self.statusBar.SetText('delay set to: %8.2f s' % seconds, 1)


    def setStyle(self):
        self.style = TStyle("Pub", "Pub")
        style = self.style
        #style.SetPalette(kRainBow)
        style.SetPalette(1)

        # For the canvases
        style.SetCanvasBorderMode(0)
        style.SetCanvasColor(kWhite)

        # For the pads
        style.SetPadBorderMode(0)
        style.SetPadColor(kWhite)
        style.SetPadGridX(kFALSE)
        style.SetPadGridY(kFALSE)
        style.SetGridColor(kGreen)
        style.SetGridStyle(3)
        style.SetGridWidth(1)

        # For the frames
        style.SetFrameBorderMode(0)
        style.SetFrameBorderSize(1)
        style.SetFrameFillColor(0)
        style.SetFrameFillStyle(0)
        style.SetFrameLineColor(1)
        style.SetFrameLineStyle(1)
        style.SetFrameLineWidth(1)

        # For the histograms
        style.SetHistLineColor(kBlack)
        style.SetHistLineStyle(0)
        style.SetHistLineWidth(2)

        style.SetEndErrorSize(2)
        #style.SetErrorX(0.)

        style.SetMarkerSize(0.4)
        style.SetMarkerStyle(20)

        # For the fit/function:
        style.SetOptFit(1)
        style.SetFitFormat("5.4g")
        style.SetFuncColor(2)
        style.SetFuncStyle(1)
        style.SetFuncWidth(1)

        # For the date:
        style.SetOptDate(0)

        # For the statistics box:
        style.SetOptFile(0)
        style.SetOptStat("")
        # To display the mean and RMS:
        # style.SetOptStat("mr") 
        style.SetStatColor(kWhite)
        style.SetStatFont(42)
        style.SetStatFontSize(0.03)
        style.SetStatTextColor(1)
        style.SetStatFormat("6.4g")
        style.SetStatBorderSize(1)
        style.SetStatH(0.2)
        style.SetStatW(0.3)

        # Margins:
        style.SetPadTopMargin(0.05)
        style.SetPadBottomMargin(0.16)
        style.SetPadLeftMargin(0.18)
        style.SetPadRightMargin(0.18)

        # For the Global title:
        style.SetOptTitle(0) 
        style.SetTitleFont(42)
        style.SetTitleColor(1)
        style.SetTitleTextColor(1)
        style.SetTitleFillColor(10)
        style.SetTitleFontSize(0.05)

        # For the axis titles:
        style.SetTitleColor(1, "XYZ")
        style.SetTitleFont(42, "XYZ")
        style.SetTitleSize(0.05, "XYZ")
        style.SetTitleXOffset(1.25)
        style.SetTitleYOffset(1.40)

        # For the axis labels:
        style.SetLabelColor(1, "XYZ")
        style.SetLabelFont(42, "XYZ")
        style.SetLabelOffset(0.020, "XYZ")
        style.SetLabelSize(0.05, "XYZ")

        # For the axis:
        style.SetAxisColor(1, "XYZ")
        style.SetStripDecimals(kTRUE)
        style.SetTickLength(0.03, "XYZ")
        style.SetNdivisions(510, "XYZ")
        # To get tick marks on the opposite side of the frame
        style.SetPadTickX(1)  
        style.SetPadTickY(1)

        # Change for log plots:
        style.SetOptLogx(0)
        style.SetOptLogy(0)
        style.SetOptLogz(0)

        # Postscript options:
        style.SetPaperSize(20.,20.)
        style.cd()
#------------------------------------------------------------------------------
def main():
    if len(sys.argv) > 1:
        geometry = sys.argv[1]
    else:
        sys.exit('''
Usage:
     TBEventDisplay.py <geometry-file> [root-file]
''')

    if len(sys.argv) > 2:
        filename = sys.argv[2]
    else:
        filename = None

    display = TBEventDisplay('CMS HGCAL Test Beam Event Display',
                             geometry, filename)
    display.run()
#------------------------------------------------------------------------------
try:
    main()
except KeyboardInterrupt:
    print 'ciao!'

