#!/usr/bin/env python
#-----------------------------------------------------------------------------
# File:        TBLego.py
# Description: TB 2016 simple lego display of HGCal
# Created:     10-Apr-2016 Jeremy Thomas, Harrison B. Prosper
#-----------------------------------------------------------------------------
import sys, os, re
from string import atof, lower, replace, strip, split, joinfields, find
from HGCal.TBEventDisplay.TBUtil import *
from HGCal.TBStandaloneSimulator.TBGeometryUtil import *
from math import *
from ROOT import *
#------------------------------------------------------------------------------
class Lego:

    def __init__(self, parent, page):
        self.parent  = parent
        self.page    = page
        self.canvas  = page.canvas
        self.cellmap = parent.cellmap
        self.geometry  = parent.geometry
        self.sensitive = parent.sensitive

        # try to figure out an arrangement of plots on the
        # canvas
        self.nlayers = len(self.sensitive)
        self.nplots  = divideCanvas(self.nlayers, self.canvas)

        # construct a 2D histogram
        layer   = 1
        element = self.geometry[self.sensitive[layer]]
        side    = element['side']
        ii      = int(float(side) / 10)+1
        hwid    = ii * 10

        self.nbinx   = 80
        self.xmin    =-hwid
        self.xmax    = hwid
        self.xstep   = (self.xmax-self.xmin)/self.nbinx

        self.nbiny   = 80
        self.ymin    =-hwid
        self.ymax    = hwid
        self.ystep   = (self.ymax-self.ymin)/self.nbiny

        # create a 2D plot for each sensor
        self.wafer = []
        for l in xrange(self.nplots):
            layer = l + 1
            hname = 'wafer%3.3d' % layer
            wafer = TH2F(hname, "", 
                         self.nbinx, 
                         self.xmin, 
                         self.xmax, 
                         self.nbiny, 
                         self.ymin, 
                         self.ymax)

            wafer.GetXaxis().CenterTitle()
            wafer.GetXaxis().SetTitle("#font[12]{x} axis")
            wafer.GetXaxis().SetTitleOffset(1.5)
            wafer.SetNdivisions(505, "X")

            wafer.GetYaxis().CenterTitle()
            wafer.GetYaxis().SetTitle("#font[12]{y} axis")
            wafer.GetYaxis().SetTitleOffset(1.5)
            wafer.SetNdivisions(505, "Y")
            self.wafer.append(wafer)

    def __del__(self):
        pass

    def Draw(self, parent):
        if parent.hits == None: return

        gStyle.SetOptStat("")        

        for l in xrange(self.nplots):
            layer = l + 1
            cells = parent.cells[layer]

            for ii in xrange(cells.size()):
                cell = cells[ii]
                if cell.count < parent.ADCmin: continue

                binx = int((cell.x - self.xmin)/self.xstep) + 1
                biny = int((cell.y - self.ymin)/self.ystep) + 1

                self.wafer[l].SetBinContent(binx, biny, cell.count)

            self.canvas.cd(layer)
            self.wafer[l].Draw("LEGO2Z")
        self.canvas.Update()

        if parent.shutterOpen:
            filename = "lego%5.5d.png" % parent.eventNumber
            self.canvas.SaveAs(filename)

