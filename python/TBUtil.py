#!/usr/bin/env python
#-----------------------------------------------------------------------------
# File:        TBUtil.py
# Description: TB 2016 simple HGC test beam event display utilities
# Created:     10-Apr-2016 Jeremy Thomas, Harrison B. Prosper
#-----------------------------------------------------------------------------
import sys, os, re
from ROOT import *
from string import atof, lower, replace, strip, split, joinfields, find
from array import array
from math import *
from HGCal.TBEventDisplay.Util    import root
#------------------------------------------------------------------------------
def getValue(record):
    return atof(split(record)[0])

def getColor(f):
    ncolors = root.SetSpectrumPalette()
    ii = int(0.99*(1-f)*ncolors)
    return TColor.GetColorPalette(ii)

def computeBinVertices(side, cellmap, cell):
    pos, posid = cell.first, cell.second
    u, v = pos.first, pos.second
    pos  = cellmap(u, v)
    x0,y0= pos.first, pos.second

    # construct (x,y) vertices of a hexagon or half-hexagon, 
    # centered at (x0,y0)
    S = float(side)
    H = S*sqrt(3.0)/2  # center to side distance
    x = array('d')
    y = array('d')
    if   posid == 0:
        x.append(x0-S/2); y.append(y0-H)
        x.append(x0-S);   y.append(y0)
        x.append(x0-S/2); y.append(y0+H)
        x.append(x0+S/2); y.append(y0+H)
        x.append(x0+S);   y.append(y0)
        x.append(x0+S/2); y.append(y0-H)
    elif posid == 1:
        x.append(x0-S/2); y.append(y0-H)
        x.append(x0-S);   y.append(y0)
        x.append(x0-S/2); y.append(y0+H)
        x.append(x0+S/2); y.append(y0-H)
    elif posid == 2:
        x.append(x0-S/2); y.append(y0-H)
        x.append(x0-S);   y.append(y0)
        x.append(x0+S);   y.append(y0)
        x.append(x0+S/2); y.append(y0-H)
    elif posid == 3:
        x.append(x0-S/2); y.append(y0-H)
        x.append(x0+S/2); y.append(y0+H)
        x.append(x0+S);   y.append(y0)
        x.append(x0+S/2); y.append(y0-H)
    elif posid == 4:
        x.append(x0-S/2); y.append(y0+H)
        x.append(x0+S/2); y.append(y0+H)
        x.append(x0+S);   y.append(y0)
        x.append(x0+S/2); y.append(y0-H)
    elif posid == 5:
        x.append(x0-S);   y.append(y0)
        x.append(x0-S/2); y.append(y0+H)
        x.append(x0+S/2); y.append(y0+H)
        x.append(x0+S);   y.append(y0)
    elif posid == 6:
        x.append(x0-S/2); y.append(y0-H)
        x.append(x0-S);   y.append(y0)
        x.append(x0-S/2); y.append(y0+H)
        x.append(x0+S/2); y.append(y0+H)    
    return (x, y)
#------------------------------------------------------------------------------
def computeHexVertices(side):
    # construct (x,y) vertices of a hexagon centered at the origin
    S = side
    H = S*sqrt(3)/2  # center to side distance
    x = array('d')
    y = array('d')
    x.append(-S/2); y.append(-H)
    x.append(-S);   y.append(0)
    x.append(-S/2); y.append( H)
    x.append( S/2); y.append( H)
    x.append( S);   y.append(0)
    x.append( S/2); y.append(-H)
    return (x, y)
#------------------------------------------------------------------------------
    def getHits(parent, cellmap, keyname="TBRecHit"):
        try:
            rechits = parent.reader(keyname)
        except:
            return (None, None)

        maxenergy =-1.0
        hits = []
        wafer= {}
        for ii in xrange(rechits.size()):
            energy = rechits[ii].energy()
            cellid = rechits[ii].id()
            l = cellid.layer()
            u = cellid.iu()
            v = cellid.iv()
            pos = cellmap(u, v)
            x = pos.first
            y = pos.second
            #record ="cell(%3d,%3d,%3d): %8.3f GeV" % (l, u ,v, energy)
            #print record

            if not wafer.has_key(l):
                parent.debug("begin new wafer")
                # silicon wafer is last sub-layer of layer (aka module)
                module  = self.design[l]
                element = module[-1]
                z    = getValue(element['z'])
                cellside = getValue(element['cellside'])
                wafer[l] = (z, cellside)

            z, cellside = wafer[l]
            hits.append((energy, l, u, v, x, y, z, cellside))
            if energy > maxenergy: maxenergy = energy

        return (maxenergy, hits)
