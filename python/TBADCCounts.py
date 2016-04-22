#!/usr/bin/env python
#-----------------------------------------------------------------------------
# File:        TBADCCounts.py
# Description: TB 2016 - display of ADC distribution
# Created:     10-Apr-2016 Jeremy Thomas, Harrison B. Prosper
#-----------------------------------------------------------------------------
import sys, os, re
from string import atof, lower, replace, strip, split, joinfields, find
from HGCal.TBEventDisplay.TBUtil import *
from math import *
from ROOT import *
#------------------------------------------------------------------------------
class ADCCounts:

    def __init__(self, parent, page):
        self.cellmap = parent.cellmap
        self.geometry, self.sensitive = parent.geometry
        self.canvas  = page.canvas

        # try to figure out an arrangement of plots on the
        # canvas
        self.nlayers= len(self.sensitive)
        n = int(sqrt(self.nlayers+1))
        xdiv = n
        ydiv = n
        if xdiv*ydiv < self.nlayers: ydiv += 1
        nplots = min(xdiv*ydiv, self.nlayers)
        self.canvas.Divide(xdiv, ydiv)

        # create a histogram for each sensor
        nbins = 4000
        xmin  = 0
        xmax  = 4000

        self.hist = []
        for layer in xrange(nplots):
            name = 'ADClayer%3d' % (layer+1)
            h = TH1F(name, "", nbins, xmin, xmax)
            h.SetFillStyle(3001)
            h.SetFillColor(kBlue)
            h.GetXaxis().CenterTitle()
            h.GetXaxis().SetTitle("ADC count")
            h.GetYaxis().CenterTitle()
            h.GetYaxis().SetTitle("count")
            h.SetMinimum(parent.ADCcut)
            self.hist.append(h)

    def __del__(self):
        pass

    def Draw(self, parent):
        if not parent.accumulate:
            for h in self.hist:
                h.Reset()

        maxADC, hits = getHits(parent, self.cellmap, self.sensitive)
        if maxADC == None: return

        # fill sensor histogram (layers start at one)
        for ii,(adc, layer, u, v, x, y, z) in enumerate(hits):
            self.hist[layer-1].Fill(adc)

        # now plot
        gStyle.SetOptStat("mr") 
        for ii, h in enumerate(self.hist):
            layer = ii + 1
            self.canvas.cd(layer)
            h.Draw()
        self.canvas.Update()

        if parent.shutterOpen:
            filename = "adccounts%5.5d.png" % parent.eventNumber
            self.canvas.SaveAs(filename)

        gStyle.SetOptStat("") 
