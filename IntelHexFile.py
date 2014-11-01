import sys

class IntelHexFile:
    """
    parsing Intel hex file - resulting data in self.mBinData variable
    """
    def __init__(self,pFileName):
        self.mFileName = pFileName
        self.mBinData = [];     # list of dict. {"startaddr":x,"endaddr":x,"data":x}
        self.mStartAddress = 0; # start address - from record type 03
        self.mOffset = 0;       # offset to support more 64K memory - from record type 02 or 04

    def loadFile(self):
        """
        parse file and fill mBinData
        """
        fhex = open(self.mFileName,'r')
        for l in fhex.readlines():
            rec = self.parseRecord(l)
            if rec[0]==0: # data record
                self.processRecord(rec)
            elif rec[0]==1: # end of file
                break  
            elif rec[0]==3: # start address; Start Segment Address Record
                self.mStartAddress = rec[1]
            elif rec[0]==2: # Extended Segment Address Record
                self.mOffset = (rec[3][0]<<8+rec[3][1]) << 4
            elif rec[0]==4: # Extended Linear Address Record
                self.mOffset = rec[3][0]<<8+rec[3][1] << 16
        print len(self.mBinData)
        for elem in self.mBinData:
            print elem["startaddr"],elem["endaddr"]
        fhex.close()
        
    def parseRecord(self,pLine):
        """
        returns parsed line as list [<record type>, <start address>, <bytes number>, <LIST of bytes>]
        all elements as integers
        """
        dataLen = int(pLine[1:3],16)
        addr = int(pLine[3:7],16)
        recType = int(pLine[7:9],16)
        idxCrc = 9+dataLen*2 # position in line of start CRC
        crc = int(pLine[idxCrc:idxCrc+2],16)
        dataBytes = []
        for i in range(9,idxCrc,2):
            dataBytes.append(int(pLine[i:i+2],16))
        print dataLen,len(dataBytes),crc
        return [recType, addr, dataLen, dataBytes]
    
    def processRecord(self,pRecord):
        """
        fill self.mBinData with new record, join different records if it is possible
        list self.mBinData is must be ORDERED by <start address> attribute
        """
        i = 0
        n = len(self.mBinData)
        vStartAddr = pRecord[1]
        vEndAddr = vStartAddr+pRecord[2]
        vNewRec = {}
        vNewRec["startaddr"] = vStartAddr
        vNewRec["endaddr"] = vEndAddr
        vNewRec["data"] = pRecord[3]
        if n==0: # first record
            self.mBinData.append(vNewRec)
        else:
            # loop over records list and insert newrec in correct place or merge with existing records
            while i<n:
                currRec = self.mBinData[i]
                if vEndAddr<currRec["startaddr"]: #
                    self.mBinData.insert(i,vNewRec)
                    print "inserting",i,vStartAddr
                    break
                elif currRec["endaddr"]<vStartAddr and i==n-1:
                    self.mBinData.append(vNewRec)
                    print "appending",i,vStartAddr
                    break
                elif currRec["endaddr"]==vStartAddr: # merge new and current records
                    currRec["data"].extend(vNewRec["data"])
                    currRec["endaddr"] = vEndAddr
                    if i<n-1 and self.mBinData[i+1]["startaddr"]==vEndAddr:
                        #merge with the next record
                        currRec["data"].extend(self.mBinData[i+1]["data"])
                        currRec["endaddr"] = self.mBinData[i+1]["endaddr"]
                        del self.mBinData[i+1]
                        n = n-1
                    break
                elif currRec["startaddr"]==vEndAddr:
                    # merge new and current records 2 (new before current)
                    vNewRec["data"].extend(currRec["data"])
                    currRec["data"] = vNewRec["data"] 
                    currRec["startaddr"] = vStartAddr
                    break
                i=i+1

    def saveFile(self):
        """
        save file
        """
        fhex = open(self.mFileName,'w')
        for elem in self.mBinData:
            startAddr = elem["startaddr"]
            currAddr = startAddr
            endAddr = elem["endaddr"]
            bytes = elem["data"]
            while currAddr<endAddr:
                recBytes = bytes[currAddr-startAddr:currAddr-startAddr+16]
                fhex.write(':10'+("%04x" % currAddr)+'00'+''.join("%02x" % b for b in recBytes) + 'xx\n')
                currAddr = currAddr+16
        fhex.close()

if __name__=="__main__":
    #ihf = IntelHexFile("optiboot_atmega328.hex")
    ihf = IntelHexFile("optiboot_atmega328_NOTORD.hex")
    #ihf = IntelHexFile("complex.hex")
    ihf.loadFile()
    print "done."