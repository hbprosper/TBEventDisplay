#!/usr/bin/env python
#-----------------------------------------------------------------------------
# File:        TBHeatMap.py
# Description: TB 2016 simple heat map display of HGCal
# Created:     10-Apr-2016 Jeremy Thomas, Harrison B. Prosper
#-----------------------------------------------------------------------------
import sys, os, re
from string import atof, lower, replace, strip, split, joinfields, find
from HGCal.TBEventDisplay.TBUtil import *
from math import *
from ROOT import *
#------------------------------------------------------------------------------
class HeatMap:

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

        # construct a hexagon centered at the origin to
        # represent sensor
        layer   = 1
        element = self.sensitive[layer]
        side    = element['side']

        self.wafer = TH2Poly()
        self.wafer.SetName('wafer')
        self.wafer.SetTitle('wafer')
        self.wafer.GetXaxis().CenterTitle()
        self.wafer.GetXaxis().SetTitle("#font[12]{x} axis")
        self.wafer.GetYaxis().CenterTitle()
        self.wafer.GetYaxis().SetTitle("#font[12]{y} axis")
        xv, yv  = computeHexVertices(side)
        self.wafer.AddBin(len(xv), xv, yv)

        # create a histogram for each sensor
        self.hist = []
        cellside  = element['cellside']
        cells = self.cellmap.cells()
        for layer in xrange(nplots):
            poly = TH2Poly()
            poly.SetName('layer %3d' % (layer+1))
            poly.SetTitle('layer %3d' % (layer+1))
            poly.GetXaxis().CenterTitle()
            poly.GetXaxis().SetTitle("#font[12]{x} axis")
            poly.GetYaxis().CenterTitle()
            poly.GetYaxis().SetTitle("#font[12]{y} axis")
            poly.SetMinimum(0)
            self.hist.append(poly)

            # populate with cells
            for ii in xrange(cells.size()):
                xv,yv = computeBinVertices(cellside, self.cellmap, cells[ii])
                poly.AddBin(len(xv), xv, yv)
            self.canvas.cd(layer+1)
            self.wafer.Draw()
        self.canvas.Update()

    def __del__(self):
        pass

    def Draw(self, parent):
        if not parent.accumulate:
            for h in self.hist:
                h.ClearBinContents()

        maxADC, hits = getHits(parent, self.cellmap, self.sensitive)
        if maxADC == None: return

        # fill sensor histograms
        # layers start at zero
        for ii,(adc, layer, u, v, x, y, z) in enumerate(hits):
            self.hist[layer-1].Fill(x, y, adc)

        # get maximum
        maxcount = -1.0
        for layer, h in enumerate(self.hist):
            count = h.GetMaximum()
            if count > maxcount:
                maxcount = count

        gStyle.SetOptStat("")
        # now plot
        for layer, h in enumerate(self.hist):
            self.canvas.cd(layer+1)
            h.SetMinimum(parent.ADCcut)
            #h.SetMaximum(maxcount)
            h.Draw("colz")
            self.wafer.Draw("same")
        self.canvas.Update()

        if parent.shutterOpen:
            filename = "heatmap%5.5d.png" % parent.eventNumber
            self.canvas.SaveAs(filename)

