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
def getColor(y, ymax):
    f  = float(min(y, ymax))/ymax
    ii = int(0.99*f*TColor.GetNumberOfColors())
    return TColor.GetColorPalette(ii)
#------------------------------------------------------------------------------
def getHits(parent, cellmap, sensitive, keyname="SKIROC2DataFrame"):
    try:
        skiroc = parent.reader(keyname)
    except:
        return None

    hits = {}
    for ii in xrange(skiroc.size()):
        digi = SKIROC2DataFrame(skiroc[ii])
        nsamples = digi.samples()
        detid    = digi.detid()
        sensor_u = detid.sensorIU()
        sensor_v = detid.sensorIV()
        l  = detid.layer()
        u  = detid.iu()
        v  = detid.iv()
        xy = cellmap.uv2xy(u, v)
        x  = xy.first
        y  = xy.second
        z  = sensitive[l]['z']
        adc= digi[0].adcHigh()
        if not hits.has_key(l): hits[l] = []
        hits[l].append((adc, u, v, x, y, z))
    return hits
