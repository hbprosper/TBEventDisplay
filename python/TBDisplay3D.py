#!/usr/bin/env python
#-----------------------------------------------------------------------------
# File:        TBDisplay3D.py
# Description: TB 2016 simple 3D display of HGCal
# Created:     10-Apr-2016 Jeremy Thomas, Harrison B. Prosper
#-----------------------------------------------------------------------------
import sys, os, re
from ROOT import *
from string import atof, lower, replace, strip, split, joinfields, find
from array import array
from math import *
from HGCal.TBEventDisplay.TBUtil import *
#------------------------------------------------------------------------------
COLOR = {'W':   kRed,
         'Cu':  kYellow+2,  
         'WCu': kOrange, 
         'PCB': kBlue, 
         'Si':  kWhite}
#------------------------------------------------------------------------------
class Display3D:

    def __init__(self, parent, page):

        self.cellmap = parent.cellmap
        # this is a 2-tuple: (geometry_description, sensitive_elements)
        self.geometry, self.sensitive = parent.geometry
        self.page    = page
        self.first   = True
        self.transparency = 99

        # some shapes might be pickable
        self.pickables = Pickable()
        self.connections = []
        self.connections.append(Connection(self.pickables, 
                                           "Selected(int)",
                                           self, "selected"))
        self.connections.append(Connection(self.pickables, 
                                           "Cleared()",
                                           self, "cleared"))
    def __del__(self):
        pass

    def Show(self):
        if self.first:
            self.first = False
            gEve.Redraw3D(kTRUE)
        else:
            gEve.Redraw3D(kFALSE)
 
    def selected(self, idd):
        element = self.pickables[idd]
        # todo

    def cleared(self):
        # todo
        pass

    #----------------------------------------------------------------------
    # Draw wafer and hits
    #----------------------------------------------------------------------
    def Draw(self, parent):	

        # either add more objects to existing
        # picture or refresh
        if not parent.accumulate:
            self.page.elements.DestroyElements()

        # clear all pickables from the list
        # of selected pickables
        self.pickables.Clear()

        # draw HGC modules
        if self.first:
            self.drawGeometry(parent)

        # draw hits
        self.drawHits(parent)

        #shape = TEveText('#font[12]{The Time Has Come}')
        #shape.SetMainColor(kBlack)
        #shape.SetFontSize(14)
        #shape.RefMainTrans().SetPos(12, 12, 20)
        #elements.AddElement(shape)

        self.Show()
        if parent.shutterOpen:
            filename = "display3d%5.5d.png" % parent.eventNumber
            self.page.viewer.SaveAs(filename)

    def drawGeometry(self, parent):
        for ii in xrange(len(self.geometry)):
            element = self.geometry[ii]
            material = element['material']
            if material == 'Air': continue

            # construct (x,y) vertices of a hexagon/square 
            # centered at the origin use first sensitive layer
            shape     = element['shape']
            side      = element['side']
            thickness = element['thickness']
            if shape == 'hexagon':
                x, y = computeHexVertices(side)
            else:
                x, y = computeSquareVertices(side)
            o = TGeoXtru(2)
            o.DefinePolygon(len(x), x, y)
            # args: z-section-number, z
            o.DefineSection(0,-thickness/2)
            o.DefineSection(1, thickness/2)
 
            name = '%s_%d' % (material, ii)
            shape= TEveGeoShape(name)
            shape.SetShape(o)
            shape.SetMainColor(COLOR[material])
            shape.SetMainTransparency(self.transparency)

            # move to correct position
            xpos = element['x']
            ypos = element['y']
            zpos = element['z']
            shape.RefMainTrans().SetPos(xpos, ypos, zpos)
 
            if material == 'Si':
                shape.SetPickable(1)
                self.pickables.AddElement(shape)
            self.page.fixedelements.AddElement(shape)
            self.page.shapes.append(shape)

    def drawHits(self, parent):
        maxADC, hits = getHits(parent, 
                               self.cellmap, 
                               self.sensitive)
        if maxADC == None: return
        
        for ii,(adc, layer, u, v, x, y, z) in enumerate(hits):
            if adc < parent.ADCcut: continue

            name = 'hit%d_%d_%d_%d' % (parent.eventNumber, layer, u, v)
            p = TEvePointSet(name)
            p.SetNextPoint(x, y, z)
            p.SetPointId(TNamed(name, name))
            p.SetMarkerStyle(4)
            p.SetMarkerSize(2.0)
            color = getColor(float(adc)/maxADC)
            print '\t%d\tcolor = %d' % (adc, color)
            p.SetMarkerColor(color)
            p.SetPickable(1)
            self.pickables.AddElement(p)
            self.page.elements.AddElement(p)
