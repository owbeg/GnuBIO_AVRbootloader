import IntelHexFile
from STK500 import STK500Protocol
import STK500
import sys
import argparse
import serial.tools.list_ports
import serial

board_MCU = {'Uno':'atmega328p','Mega':'atmega2560','Leonardo':'atmega32u4','Nano':'atmega328','Mini':'atmega328'}

if __name__=="__main__":
    pparser = argparse.ArgumentParser(description="Atmel AVR MCU flasher for GnuBIO")
    group = pparser.add_mutually_exclusive_group(required=True)
    group.add_argument('-a','--arduino', dest='pBoard', metavar='board name',help='name of Arduino board',choices=['Uno','Mega','Leonardo','Nano','Mini'])
    group.add_argument('-m','--mcu', dest='pMCU', metavar='MCU name',help='name of Atmel AVR MCU',choices=['atmega328p','atmega2560','atmega32u4','atmega168'])
    pparser.add_argument('-p','--port', dest='pPort', metavar='PORT',help='serial port to communicate with master board',required=True)
    pparser.add_argument('-b','--baud', dest='pBaud', metavar='BAUD',help='serial port baud', type=int,required=True)
    pparser.add_argument('-d','--mode', dest='pMode', metavar='MODE',help='choose mode master/serial board', choices=['master','slave'],default='master')
    pparser.add_argument('-i','--address', dest='pTwiAddr', metavar='i2c address',help='address of slave board', type=int)
    pparser.add_argument('fn', metavar='FILENAME',help='HEX file', nargs=1)
    args = pparser.parse_args()
    if args.pMCU is None:
        args.pMCU = board_MCU[args.pBoard]
    print args.pBoard, args.pMCU

    port_list = list(serial.tools.list_ports.comports())
    port_list_nameonly = [name for name,descr,hwaddr in port_list]
    if not (args.pPort in port_list_nameonly):
        pparser.error('Port %s not exists. Available ports: (%s)' % (args.pPort,', '.join(port_list_nameonly)))

    try:
        stk500 = STK500Protocol(args.pPort,args.pBaud, args.pMCU)
        print "stk500"
    except Exception, e:
        print 'ERROR: %s. Exiting...' % e.message
    else:
        try:
            syncCnt = 0
            for i in range(5):
              reply = stk500.getSynchronization()
              print "getSynchronization %d" % reply
              if reply==STK500.Resp_STK_INSYNC:
                  syncCnt = syncCnt+1
            print "syncCnt = %d" % syncCnt
            if syncCnt>=3:
                print "synced"
                hexfile = IntelHexFile.IntelHexFile("avr_pages.hex")
                rc = stk500.enterProgramMode()
                print "device signature %06x" % stk500.readSignature()
                addr = 0
                for ipg in range(stk500.m_numOfPages):
                    rc = stk500.loadAddress(addr)
                    resp = stk500.readPage()
                    nonFFbytes = [a for a in resp[1] if a!=0xff]
                    if len(nonFFbytes)>0:
                        print "non empty block %04x %d" % (addr<<1,len(resp[1]))
                        # !!! address in words!
                        hexfile.processRecord([0,addr<<1,len(resp[1]),resp[1]])
                    # !!! address in words!
                    addr = addr + (len(resp[1])>>1)
                rc = stk500.leaveProgramMode()
                print "readpage return code ",resp[0]
                for elem in hexfile.mBinData:
                    print elem["startaddr"],elem["endaddr"]
                hexfile.saveFile()
                #f = open("avr_pages.bin","wb")
                #for b in resp[1]:
                #    f.write(chr(b))
                #f.close()
            else:
                print "NO sync"
        except Exception, e:
            print 'ERROR: %s. Exiting...' % e.message
        finally:
            stk500.closeLink()
