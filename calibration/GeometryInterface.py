

from math import *
import os
from calibration.XmlTools import etree
import subprocess

class GeometryInterface(object) :
    def __init__(self, compactFile):
        self._compactFile = compactFile
        self._gearFile = self._convertToGear(self._compactFile)
        parser = etree.XMLParser(remove_blank_text=True)
        self._xmlTree = etree.parse(self._gearFile, parser)
    
    """ Convert the compact file to gear file using 'convertToGear' binary
    """
    def _convertToGear(self, compactFile, force=False) :
        gearFile = "gear_" + os.path.split(compactFile)[1]

        if os.path.isfile(gearFile) and not force:
            return gearFile

        args = ['convertToGear', 'default', compactFile, gearFile]
        process = subprocess.Popen(args = args)
        if process.wait() :
            raise RuntimeError("Couldn't convert compact file to gear file")
        return gearFile
    
    def _getGearDetector(self, dname, dtype) :
        elements = self._xmlTree.xpath("//gear/detectors/detector[@name='{0}'][@geartype='{1}']".format(dname, dtype))
        return None if not len(elements) else elements[0] 
    
    def getDetectorDimmensions(self, dname, dtype) :
        detector = self._getGearDetector(dname, dtype)
        if detector is not None :
            return detector.find("dimensions")
        return None
    
    def getDetectorInnerR(self, dname, dtype) :
        dimensions = self.getDetectorDimmensions(dname, dtype)
        if dimensions is not None :
            return dimensions.get("inner_r")
    
    def getDetectorOuterR(self, dname, dtype) :
        dimensions = self.getDetectorDimmensions(dname, dtype)
        if dimensions is not None :
            outerR = dimensions.get("outer_r")
            if outerR is not None :
                return float(outerR)
            else :
                innerR = float(self.getDetectorInnerR(dname, dtype))
                layers = dimensions.getparent().findall("layer")
                outerR = innerR
                for l in layers :
                    repeat = int(l.get("repeat"))
                    thickness = float(l.get("thickness"))
                    outerR = outerR + repeat*thickness
                return outerR
        return None
    
    def getDetectorInnerZ(self, dname, dtype) :
        dimensions = self.getDetectorDimmensions(dname, dtype)
        if dimensions is not None :
            return dimensions.get("inner_z")
        
    def getDetectorOuterZ(self, dname, dtype) :
        dimensions = self.getDetectorDimmensions(dname, dtype)
        if dimensions is not None :
            outerZ = dimensions.get("outer_z")
            if outerZ is not None :
                return float(outerZ)
            else :
                innerZ = float(self.getDetectorInnerZ(dname, dtype))
                layers = dimensions.getparent().findall("layer")
                outerZ = innerZ
                for l in layers :
                    repeat = int(l.get("repeat"))
                    thickness = float(l.get("thickness"))
                    outerZ = outerZ + repeat*thickness
                return outerZ
        return None

    def getEcalBarrelCosThetaRange(self) :
        ecalBarrelOuterR = float(self.getDetectorOuterR("EcalBarrel", "CalorimeterParameters"))
        ecalBarrelOuterZ = float(self.getDetectorOuterZ("EcalBarrel", "CalorimeterParameters"))
        maxCosTheta = cos(atan( ecalBarrelOuterR / ecalBarrelOuterZ ))
        return 0.05, maxCosTheta
    
    def getEcalEndcapCosThetaRange(self) :
        ecalEndcapOuterR = float(self.getDetectorOuterR("EcalEndcap", "CalorimeterParameters"))
        ecalEndcapOuterZ = float(self.getDetectorOuterZ("EcalEndcap", "CalorimeterParameters"))
        ecalEndcapInnerR = float(self.getDetectorInnerR("EcalEndcap", "CalorimeterParameters"))
        ecalEndcapInnerZ = float(self.getDetectorInnerZ("EcalEndcap", "CalorimeterParameters"))
        minCosTheta = cos(atan( ecalEndcapOuterR / ecalEndcapOuterZ ))
        maxCosTheta = cos(atan( ecalEndcapInnerR / ecalEndcapInnerZ ))
        return minCosTheta, maxCosTheta

    def getHcalBarrelCosThetaRange(self) :
        hcalBarrelOuterR = float(self.getDetectorOuterR("HcalBarrel", "CalorimeterParameters"))
        hcalBarrelOuterZ = float(self.getDetectorOuterZ("HcalBarrel", "CalorimeterParameters"))
        maxCosTheta = cos(atan( hcalBarrelOuterR / hcalBarrelOuterZ ))
        return 0.05, maxCosTheta

    def getHcalEndcapCosThetaRange(self) :
        hcalEndcapOuterR = float(self.getDetectorOuterR("HcalEndcap", "CalorimeterParameters"))
        hcalEndcapOuterZ = float(self.getDetectorOuterZ("HcalEndcap", "CalorimeterParameters"))
        hcalEndcapInnerR = float(self.getDetectorInnerR("HcalEndcap", "CalorimeterParameters"))
        hcalEndcapInnerZ = float(self.getDetectorInnerZ("HcalEndcap", "CalorimeterParameters"))
        minCosTheta = cos(atan( hcalEndcapOuterR / hcalEndcapOuterZ ))
        maxCosTheta = cos(atan( hcalEndcapInnerR / hcalEndcapInnerZ ))
        return minCosTheta, maxCosTheta
        
#