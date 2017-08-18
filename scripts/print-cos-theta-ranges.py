
from calibration.GeometryInterface import *
import argparse

parser = argparse.ArgumentParser("Running energy calibration:",
                                     formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("--compactFile", action="store", default="",
                        help="The compact XML file", required = True)

parsed = parser.parse_args()

geo = GeometryInterface(parsed.compactFile)

ebmin, ebmax = geo.getEcalBarrelCosThetaRange()
print "Ecal barrel cos theta range : [{0},{1}]".format(ebmin, ebmax)

eemin, eemax = geo.getEcalEndcapCosThetaRange()
print "Ecal endcap cos theta range : [{0},{1}]".format(eemin, eemax)

hbmin, hbmax = geo.getHcalBarrelCosThetaRange()
print "Hcal barrel cos theta range : [{0},{1}]".format(hbmin, hbmax)

hemin, hemax = geo.getHcalEndcapCosThetaRange()
print "Hcal endcap cos theta range : [{0},{1}]".format(hemin, hemax)

#