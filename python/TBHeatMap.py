#!/usr/bin/env python
#-----------------------------------------------------------------------------
# File:        TBHeatMap.py
# Description: TB 2016 simple heat map display of HGCal
# Created:     10-Apr-2016 Jeremy Thomas, Harrison B. Prosper
#-----------------------------------------------------------------------------
import sys, os, re
from string import atof, lower, replace, strip, split, joinfields, find
from array import array
from HGCal.TBEventDisplay.Util import Connection, root
from HGCal.TBEventDisplay.TBUtil import *
from math import *
from ROOT import *
#------------------------------------------------------------------------------
class HeatMap:

    def __init__(self, parent, page):
        self.cellmap = parent.cellmap
        self.geometry= parent.geometry
        self.canvas  = page.canvas
        self.first   = True

        # try to figure out an arrangement of plots on the
        # canvas
        self.nlayers= len(self.geometry)
        n = int(sqrt(self.nlayers+1))
        xdiv = n
        ydiv = n
        if xdiv*ydiv < self.nlayers: ydiv += 1
        nplots = min(xdiv*ydiv, self.nlayers)
        self.canvas.Divide(xdiv, ydiv)

        # construct (x,y) vertices of a hexagon centered at the origin
        module  = self.geometry[0]
        element = module[-1] # silicon layer
        side    = getValue(element['side'])
        cellside= getValue(element['cellside'])

        gStyle.SetPalette(1)
        gStyle.SetOptStat("")

        # create a histogram for each sensor
        self.hist = []

        cells = self.cellmap.cells()
        for layer in xrange(nplots):
            poly = TH2Poly()
            poly.SetName('layer %3d' % layer)
            poly.SetTitle('layer %3d' % layer)
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
            poly.Draw("colz")

        self.canvas.Update()

    def __del__(self):
        pass

    def Draw(self, parent):
        if not parent.accumulate:
            for h in self.hist:
                h.ClearBinContents()
        try:
            rechits = parent.reader("TBRecHit")
        except:
            return 

        maxenergy, hits = getHits(parent, self.cellmap, self.geometry)
        if maxenergy == None: return

        # fill sensor histograms
        for ii,(energy, layer, u, v, x, y, z, size) in enumerate(hits):
            self.hist[layer].Fill(x, y, energy)

        # now plot
        for layer, h in enumerate(self.hist):
            self.canvas.cd(layer+1)
            h.SetMinimum(parent.energyCut)
            h.SetMaximum(maxenergy)
            h.Draw("colz")
        self.canvas.Update()
        if parent.shutterOpen:
            filename = "heatmap%5.5d.png" % parent.eventNumber
            self.canvas.SaveAs(filename)

