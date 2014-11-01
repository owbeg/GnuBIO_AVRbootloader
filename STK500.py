import serial
import time

# STK Response constants
Resp_STK_OK, Resp_STK_FAILED, Resp_STK_UNKNOWN, Resp_STK_NODEVICE, Resp_STK_INSYNC, Resp_STK_NOSYNC = (
        0x10, 0x11, 0x12, 0x13, 0x14, 0x15)

Resp_ADC_CHANNEL_ERROR, Resp_ADC_MEASURE_OK, Resp_PWM_CHANNEL_ERROR, Resp_PWM_ADJUST_OK =(
        0x16, 0x17, 0x18, 0x19)

# STK Special constants
Sync_CRC_EOP = 0x20

# Command constants
Cmnd_STK_GET_SYNC, Cmnd_STK_GET_SIGN_ON = (0x30, 0x31)

Cmnd_STK_SET_PARAMETER, Cmnd_STK_GET_PARAMETER, Cmnd_STK_SET_DEVICE, Cmnd_STK_SET_DEVICE_EXT = (
        0x40, 0x41, 0x42, 0x45)
#       -     *     *      *

Cmnd_STK_ENTER_PROGMODE  =  0x50 # -
Cmnd_STK_LEAVE_PROGMODE  =  0x51 # -
Cmnd_STK_CHIP_ERASE      =  0x52
Cmnd_STK_CHECK_AUTOINC   =  0x53
Cmnd_STK_LOAD_ADDRESS    =  0x55 # *
Cmnd_STK_UNIVERSAL       =  0x56 # *
Cmnd_STK_UNIVERSAL_MULTI =  0x57

Cmnd_STK_PROG_FLASH    =    0x60
Cmnd_STK_PROG_DATA     =    0x61
Cmnd_STK_PROG_FUSE     =    0x62
Cmnd_STK_PROG_LOCK     =    0x63
Cmnd_STK_PROG_PAGE     =    0x64 # *
Cmnd_STK_PROG_FUSE_EXT =    0x65         

Cmnd_STK_READ_FLASH      =  0x70
Cmnd_STK_READ_DATA       =  0x71
Cmnd_STK_READ_FUSE       =  0x72
Cmnd_STK_READ_LOCK       =  0x73
Cmnd_STK_READ_PAGE       =  0x74 # *
Cmnd_STK_READ_SIGN       =  0x75 # *
Cmnd_STK_READ_OSCCAL     =  0x76
Cmnd_STK_READ_FUSE_EXT   =  0x77         
Cmnd_STK_READ_OSCCAL_EXT =  0x78     

# STK Parameter constants
Parm_STK_HW_VER         =   0x80  # R
Parm_STK_SW_MAJOR       =   0x81  # R
Parm_STK_SW_MINOR       =   0x82  # R
Parm_STK_LEDS           =   0x83  # R/W
Parm_STK_VTARGET        =   0x84  # R/W
Parm_STK_VADJUST        =   0x85  # R/W
Parm_STK_OSC_PSCALE     =   0x86  # R/W
Parm_STK_OSC_CMATCH     =   0x87  # R/W
Parm_STK_RESET_DURATION =   0x88  # R/W
Parm_STK_SCK_DURATION   =   0x89  # R/W
Parm_STK_BUFSIZEL       =   0x90  # R/W, Range {0..255}
Parm_STK_BUFSIZEH       =   0x91  # R/W, Range {0..255}
Parm_STK_DEVICE         =   0x92  # R/W, Range {0..255}
Parm_STK_PROGMODE       =   0x93  # 'P' or 'S'
Parm_STK_PARAMODE       =   0x94  # TRUE or FALSE
Parm_STK_POLLING        =   0x95  # TRUE or FALSE
Parm_STK_SELFTIMED      =   0x96  # TRUE or FALSE

# STK status bit definitions
Stat_STK_INSYNC         =   0x01  # INSYNC status bit, '1' - INSYNC
Stat_STK_PROGMODE       =   0x02  # Programming mode,  '1' - PROGMODE
Stat_STK_STANDALONE     =   0x04  # Standalone mode,   '1' - SM mode
Stat_STK_RESET          =   0x08  # RESET button,      '1' - Pushed
Stat_STK_PROGRAM        =   0x10  # Program button, '   1' - Pushed
Stat_STK_LEDG           =   0x20  # Green LED status,  '1' - Lit
Stat_STK_LEDR           =   0x40  # Red LED status,    '1' - Lit
Stat_STK_LEDBLINK       =   0x80  # LED blink ON/OFF,  '1' - Blink

# {MCU Name: Signature bytes, Page size in words, Number of pages}
AVRInfo = {
  "atmega48a":  ( 0x1e9205, 32,  64 ),
  "atmega48pa": ( 0x1e920a, 32,  64 ),
  "atmega88a":  ( 0x1e930a, 32, 128 ),
  "atmega88pa": ( 0x1e930f, 32, 128 ),
  "atmega168a": ( 0x1e9406, 64, 128 ),
  "atmega168pa":( 0x1e940b, 64, 128 ),
  "atmega328":  ( 0x1e9514, 64, 256 ),
  "atmega328p": ( 0x1e950f, 64, 256 )
}

class STK500Error(Exception):
    pass

class STK500Protocol:
    def __init__(self, pCOMPort, pBaud, pMCU):
        # open serial port in non-blocking mode
        self.m_comport = serial.Serial(pCOMPort, pBaud, timeout=0)
        self.m_MCU = pMCU
        if not pMCU in AVRInfo.keys():
            raise STK500Error('Unknown MCU: %s' % pMCU)
        self.m_deviceSignature = AVRInfo[pMCU][0]
        self.m_pageSize = AVRInfo[pMCU][1] # page size in words
        self.m_numOfPages = AVRInfo[pMCU][2] # size of flash in pages
    
    def putc(self, pChar):
        pass

    def getc(self):
        pass

    def getSynchronization(self):
        # tries to sync during 1 sec, if Resp_STK_INSYNC+Resp_STK_OK or Resp_STK_NOSYNC is received than exit immidiatelly
        # returns Resp_STK_INSYNC, Resp_STK_NOSYNC, or -1(?) for timeout
        print "In stk500.getSynchronization()..."
        self.m_comport.write(chr(Cmnd_STK_GET_SYNC)+chr(Sync_CRC_EOP))
        self.m_comport.flush()
        return self.waitResponse()

    def waitResponse(self, pTimeoutSec=1):
        # wait for responce from bootloader - Resp_STK_INSYNC/Resp_STK_OK or Resp_STK_NOSYNC
        # pTimeoutSec - timeout in seconds (can be with floating point), defualt is 1 second
        t0 = time.clock()
        state = 0 # 0 - wait for Resp_STK_INSYNC or Resp_STK_NOSYNC, 1 - wait for Resp_STK_OK after Resp_STK_INSYNC
        while time.clock()-t0<=pTimeoutSec:
            resp = self.m_comport.read()
            if len(resp)>=1:
                if state==0:
                    if resp[0]==chr(Resp_STK_NOSYNC):
                        return Resp_STK_NOSYNC
                    elif resp[0]==chr(Resp_STK_INSYNC):
                        state=1
                elif state==1:
                    if resp[0]==chr(Resp_STK_OK):
                        return Resp_STK_INSYNC
                    else:
                        state=0 # start waiting for Resp_STK_INSYNC/Resp_STK_NOSYNC again
        return -1

    def waitResponseWithData(self, pDataSize, pTimeoutSec=1):
        # wait for responce from bootloader - Resp_STK_INSYNC/Resp_STK_OK/Resp_STK_FAILED or Resp_STK_NOSYNC
        # pDataSize - size of data block (in bytes) which expect to receive from device
        # pTimeoutSec - timeout in seconds (can be with floating point), defualt is 1 second
        t0 = time.clock()
        state = 0 # 0 - wait for Resp_STK_INSYNC or Resp_STK_NOSYNC, 1 - wait for Resp_STK_OK/Resp_STK_FAILED after reading N bytes
        #           2 - receiving data
        dataReceived = []
        bytesReceived = 0
        while time.clock()-t0<=pTimeoutSec:
            resp = self.m_comport.read()
            if len(resp)>=1:
                respn = ord(resp[0])
                if state==0:
                    if respn==Resp_STK_NOSYNC:
                        return [Resp_STK_NOSYNC, []]
                    elif respn==Resp_STK_INSYNC:
                        state=2
                elif state==2:
                    dataReceived.append(respn)
                    bytesReceived = bytesReceived+1
                    if bytesReceived>=pDataSize:
                        state=1
                elif state==1:
                    if respn==Resp_STK_OK or respn==Resp_STK_FAILED:
                        return [respn, dataReceived]
                    else:
                        return [Resp_STK_NOSYNC, []]
        return [-1, []]

    def enterProgramMode(self):
        # enterProgramMode
        # returns Resp_STK_INSYNC, Resp_STK_NOSYNC, or -1(?) for timeout
        print "In stk500.enterProgramMode()..."
        self.m_comport.write(chr(Cmnd_STK_ENTER_PROGMODE)+chr(Sync_CRC_EOP))
        self.m_comport.flush()
        return self.waitResponse()


    def leaveProgramMode(self):
        # leaveProgramMode
        # returns Resp_STK_INSYNC, Resp_STK_NOSYNC, or -1(?) for timeout
        print "In stk500.leaveProgramMode()..."
        self.m_comport.write(chr(Cmnd_STK_LEAVE_PROGMODE)+chr(Sync_CRC_EOP))
        self.m_comport.flush()
        return self.waitResponse()

    def loadAddress(self, pAddress):
        # load Address before read/write memory operation
        # pAddress - in bytes (not words), but it transfered to bootloader in words
        # for address greater 128K we need send "universal command" 0x49
        #print "In stk500.loadAddress()..."
        addr_low = pAddress & 0xFF
        addr_high = (pAddress & 0xFF00)>>8
        self.m_comport.write(chr(Cmnd_STK_LOAD_ADDRESS)+chr(addr_low)+chr(addr_high)+chr(Sync_CRC_EOP))
        self.m_comport.flush()
        return self.waitResponse()

    def universalCommand(self, pBytes):
        # universal command
        # pBytes - list of 4 bytes to pass to the board via universal command
        print "In stk500.universalCommand()..."
        s = ''.join([a for a in pBytes])
        self.m_comport.write(chr(Cmnd_STK_UNIVERSAL)+s[0:4]+chr(Sync_CRC_EOP))
        self.m_comport.flush()
        return self.waitResponse()

    def readSignature(self):
        print "In stk500.readSignature()..."
        self.m_comport.write(chr(Cmnd_STK_READ_SIGN)+chr(Sync_CRC_EOP))
        self.m_comport.flush()
        t0 = time.clock()
        while time.clock()-t0<=1:
            if self.m_comport.inWaiting()>=5: break
        resp = self.m_comport.read(5)
        bytesInBuf = len(resp)
        if bytesInBuf==5:
            return (ord(resp[1])<<16) | (ord(resp[2])<<8) | ord(resp[3])
        else:
            print "readsignature - read only %d bytes" % bytesInBuf
            return 0

    def readPage(self):
        # currently only reads flash
        # returns list in format [response code, [byte list]]
        #print "In stk500.readPage()..."
        pageSizeBytes = self.m_pageSize<<1 # from word to bytes
        size_low = pageSizeBytes & 0xFF
        size_high = (pageSizeBytes & 0xFF00)>>8
        self.m_comport.write(chr(Cmnd_STK_READ_PAGE)+chr(size_high)+chr(size_low)+'F'+chr(Sync_CRC_EOP))
        self.m_comport.flush()
        resp = self.waitResponseWithData(pageSizeBytes)
        return resp

    def closeLink(self):
        self.m_comport.close()

if __name__=="__main__":
    print "To create class instance - STK500Protocol('comport',baud)"
