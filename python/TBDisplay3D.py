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
from HGCal.TBEventDisplay.Util import Connection, root
from HGCal.TBEventDisplay.TBUtil import *
#------------------------------------------------------------------------------
COLOR = {'W':   kRed,
         'Cu':  kYellow+2,  
         'WCu': kOrange, 
         'PCB': kBlue, 
         'Si':  kWhite}

TRANSPARENCY = {'W':   99,
                'Cu':  99,
                'WCu': 99,
                'PCB': 99,
                'Si':  97}
#------------------------------------------------------------------------------
class Display3D:

    def __init__(self, page, geometry='TB2016Design'):

        self.cellmap = HGCCellMap()
        self.page = page
        self.first = True

        # some shapes might be pickable
        self.pickables = Pickable()
        self.connections = []
        self.connections.append(Connection(self.pickables, 
                                           "Selected(int)",
                                           self, "selected"))
        self.connections.append(Connection(self.pickables, 
                                           "Cleared()",
                                           self, "cleared"))

        # get test beam geometry
        exec('from HGCal.TBStandaloneSimulator.%s import Geometry' % geometry)
        self.design = Geometry
        self.nlayers= len(self.design)

        # construct (x,y) vertices of a hexagon centered at the origin
        module  = self.design[0]
        element = module[0]
        material= element['material']
        side = getValue(element['side'])
        self.x, self.y = computeHexVertices(side)

        gStyle.SetPalette(1)

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
        print "Event: %d" % parent.eventNumber

        # either add more objects to existing
        # picture or refresh
        if not parent.accumulate:
            self.page.elements.DestroyElements()

        # clear all pickables from the list
        # of selected pickables
        self.pickables.Clear()

        # draw HGC modules
        if self.first:
            for ii in xrange(self.nlayers):
                self.drawModule(parent, ii)

        # draw hits
        self.drawHits(parent)

        #shape = TEveText('#font[12]{The Time Has Come}')
        #shape.SetMainColor(kBlack)
        #shape.SetFontSize(14)
        #shape.RefMainTrans().SetPos(12, 12, 20)
        #elements.AddElement(shape)

        self.Show()

    def drawModule(self, parent, ii):
        module = self.design[ii]

        for jj, element in enumerate(module):
            material = element['material']
            if material == 'Air': continue

            o = TGeoXtru(2)
            o.DefinePolygon(6, self.x, self.y)
            # args: section-number, z, x0, y0, scale=1
            t = getValue(element['thickness'])
            o.DefineSection(0,-t/2, 0.0, 0.0)
            o.DefineSection(1, t/2, 0.0, 0.0)

            name = '%s_layer_%d_%d' % (material, ii, jj)
            shape= TEveGeoShape(name)
            shape.SetShape(o)
            shape.SetMainColor(COLOR[material])
            shape.SetMainTransparency(TRANSPARENCY[material])

            # move to correct position
            xpos = getValue(element['x'])
            ypos = getValue(element['y'])
            zpos = getValue(element['z'])
            shape.RefMainTrans().SetPos(xpos, ypos, zpos)

            shape.SetPickable(1)
            self.pickables.AddElement(shape)
            self.page.fixedelements.AddElement(shape)

    def drawHits(self, parent):
        maxenergy, hits = getHits(parent)
        if maxenergy == None: return

        for ii,(energy, layer, u, v, x, y, z, size) in enumerate(hits):
            if energy < parent.energyCut: continue

            name = 'hit%d_%d_%d_%d' % (parent.eventNumber, layer, u, v)
            p = TEvePointSet(name)
            p.SetNextPoint(x, y, z)
            p.SetPointId(TNamed(name, name))
            p.SetMarkerStyle(4)
            p.SetMarkerSize(size/2)
            color = getColor(energy/maxenergy)
            p.SetMarkerColor(color)
            p.SetPickable(1)
            self.pickables.AddElement(p)
            self.page.elements.AddElement(p)

