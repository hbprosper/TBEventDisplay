# TBEventDisplay
Temporary home of HGCal test beam 3D event display. This has been tested with CMSSW_8_0_0, slc6_amd64_gcc493, running within a CERNVM virtual machine on a mac. It should work on lxplus and cmslpc-sl6.

# Installation
```linux
  cd HGCal
  git clone https://github.com/hbprosper/TBEventDisplay.git
  cd TBEventDisplay
  cmsenv
  scram b
  scram b (do scram b a second time, if the first fails)
```
# Testing
```linux
  cd test
  TBEventDisplay.py HGCal_RecHits_4Layer.root
```
