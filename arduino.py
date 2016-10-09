from pyfirmata import *
import time
import database
class Arduinocon(object):
    """docstring for Arduino."""
    def __init__(self, port = ["/dev/ttyACM0", "/dev/ttyUSB1", "/dev/ttyUSB0", "/dev/ttyAMA0" ]):
        if type(port) == str:
            self.port = port
            self.board = Arduino(self.port)
        else:
            for aPort in port:
                try:
                    self.port = aPort
                    self.board = Arduino(self.port)

                    break
                except: pass

        self.i1 = {'G': 13, 'Y': 12, 'R': 11}
        self.i2 = {'G': 10, 'Y': 9, 'R': 8}
        self.i3 = {'G': 7, 'Y': 6, 'R': 5}
        self.i4 = {'G': 4, 'Y': 3, 'R': 2}

    def setPin(self, pin, value = 1):
        self.board.digital[pin].write(value)

    def getSetPins(self,printer_id, G, Y, R):
        if printer_id == 1:
            self.setPin(self.i1['G'], G)
            self.setPin(self.i1['Y'], Y)
            self.setPin(self.i1['R'], R)
        elif printer_id == 2:
            self.setPin(self.i2['G'], G)
            self.setPin(self.i2['Y'], Y)
            self.setPin(self.i2['R'], R)
        elif printer_id == 3:
            self.setPin(self.i3['G'], G)
            self.setPin(self.i3['Y'], Y)
            self.setPin(self.i3['R'], R)
        else:
            self.setPin(self.i4['G'], G)
            self.setPin(self.i4['Y'], Y)
            self.setPin(self.i4['R'], R)

    def ledOff(self, printer_id):
        self.getSetPins(printer_id, 0, 0, 0)
        time.sleep(0.1)

    def ledReady(self, printer_id):
        self.getSetPins(printer_id, 1, 0, 0)
        time.sleep(0.1)

    def ledPrinting(self, printer_id, val):
        self.getSetPins(printer_id, val, 0, 0)
        time.sleep(0.1)



    def ledEnded(self, printer_id):
        self.getSetPins(printer_id, 0, 1, 0)
        time.sleep(0.1)


    def ledError(self, printer_id,val):
        self.getSetPins(printer_id, 0, 0, val)
        time.sleep(0.1)


    def ledMaintenance(self, printer_id):
        self.getSetPins(printer_id, 0, 0, 1)
        time.sleep(0.1)



if __name__ == '__main__':
    print('Connecting to Arduino!')
    myconn = Arduinocon()
    print('Arduino Connected!')

    #########################
    while True:
        db = database.DataBase(user='control', passwd='controlhack', host='10.193.115.148', db="imp3d")
        printers = db.read("SELECT * FROM {0}".format('printers'))
        all_status = []
        for printer in printers:
            all_status.append([int(printer[0]), int(printer[3])])

        for i in range(6):
            for status in all_status:
                if status[1] == 0:
                    myconn.ledOff(status[0])
                elif status[1] == 1:
                    myconn.ledReady(status[0])
                elif status[1] == 2:
                    myconn.ledPrinting(status[0],1)
                elif status[1] == 3:
                    myconn.ledEnded(status[0])
                elif status[1] == 4:
                    myconn.ledError(status[0],1)
                elif status[1] == 5:
                    myconn.ledMaintenance(status[0])
            for status in all_status:
                if status[1] == 0:
                    myconn.ledOff(status[0])
                elif status[1] == 1:
                    myconn.ledReady(status[0])
                elif status[1] == 2:
                    myconn.ledPrinting(status[0],0)
                elif status[1] == 3:
                    myconn.ledEnded(status[0])
                elif status[1] == 4:
                    myconn.ledError(status[0],0)
                elif status[1] == 5:
                    myconn.ledMaintenance(status[0])
