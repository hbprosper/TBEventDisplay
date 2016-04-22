#-----------------------------------------------------------------------------
# File:        TBUtil.py
# Description: TB 2016 simple HGC test beam event display utilities
# Created:     10-Apr-2016 Jeremy Thomas, Harrison B. Prosper
#-----------------------------------------------------------------------------
import sys, os, re
from string import atof, lower, replace, strip, split, joinfields, find
from array import array
from math import *
from ROOT import *
#------------------------------------------------------------------------------
def getValue(record):
    return atof(split(record)[0])

def getColor(f):
    gStyle.SetPalette(kDarkBodyRadiator)
    ncolors = TColor.GetNumberOfColors()
    ii = int(0.99*(1.0-f)*ncolors)
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
def computeSquareVertices(side):
    # construct (x,y) vertices of a hexagon centered at the origin
    S = side
    H = S/2  # center to side distance
    x = array('d')
    y = array('d')
    x.append(-H); y.append(-H)
    x.append(-H); y.append( H)
    x.append( H); y.append( H)
    x.append( H); y.append(-H)
    return (x, y)
#------------------------------------------------------------------------------
def getHits(parent, cellmap, sensitive, keyname="SKIROC2DataFrame"):
    try:
        skiroc = parent.reader(keyname)
    except:
        return (None, None)

    maxval=-1.0
    hits  = []
    for ii in xrange(skiroc.size()):
        digi = SKIROC2DataFrame(skiroc[ii])
        nsamples = digi.samples()
        detid    = digi.detid()
        sensor_u = detid.sensorIU()
        sensor_v = detid.sensorIV()
        l  = detid.layer()
        u  = detid.iu()
        v  = detid.iv()
        xy = cellmap(u, v)
        x  = xy.first
        y  = xy.second
        z  = sensitive[l]['z']
        adc= digi[0].adcHigh()
        #record ="cell(%3d,%3d,%3d): %d" % (l, u ,v, adc)
        #print record
        hits.append((adc, l, u, v, x, y, z))
        if adc > maxval: maxval = adc
    return (maxval, hits)
#------------------------------------------------------------------------------
def createGeometry(geometry="TBGeometry_2016_04"):
    from copy import copy
    cmd = 'from HGCal.TBStandaloneSimulator.%s import Components, Geometry'\
        % geometry
    exec(cmd)

    tprev = 0.0
    layer = 0
    z = 0.0
    geometry  = []
    sensitive = {}
    for part in Geometry:
        print part
        comp = copy(Components[part])
        # check for modules
        if type(comp) == type([]):
            for subpart in comp:
                print '\t%s' % subpart
                component = copy(Components[subpart])
                t    = component['thickness']
                side = component['side']
                z += (t + tprev)/2
                component['z'] = z
                tprev = t
                if component.has_key('sensitive'):
                    layer += 1
                    component['layer'] = layer
                    sensitive[layer] = component
                geometry.append(component)
        else:
            t    = comp['thickness']
            side = comp['side']
            z += (t + tprev)/2
            comp['z'] = z
            tprev = t
            geometry.append(comp)
    return (geometry, sensitive)
#------------------------------------------------------------------------------
def main():
    # get test beam geometry
    geom, sensitive  = createGeometry(geometry="TBGeometry_2016_04")
    from pprint import PrettyPrinter
    pp = PrettyPrinter()
    pp.pprint(geom)

if __name__ == "__main__": main()
