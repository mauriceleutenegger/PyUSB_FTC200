import serial
import timeit

# Utility functions

def CalculateChecksum (command) :
    checksum = command[0]
    for i in range (1, len (command)) :
        checksum = checksum ^ command[i]        
    return checksum

def PrepareCommand (command) :
    checksum = CalculateChecksum (command)
    full_command = bytearray ([27])
    full_command += command
    full_command.append (checksum)
    return full_command

# this is meant to be used only with numbers having a single decimal place
def SplitToWholeDecimal (number) :
    temp = number * 10
    whole = int (temp // 10)
    decimal = int (temp % 10)
    return whole, decimal

class FTC200 :

    def __init__ (self, device_path) :
        self.device_path = device_path
        self.baudrate = 9600
        self.serial_connection = serial.Serial \
            (self.device_path, baudrate=self.baudrate,
             timeout=0.2, write_timeout=0.2)
        self.data = None # buffer for status data
        # status data:
        self.SerialNumber = None
        self.FirmwareVersion = None
        # not sure why sometimes they use HV and sometimes voltage
        self.MinimumHV = None # this is in kV
        self.MaximumVoltage = None # I think this is also kV
        self.VoltageSetpointWhole = None
        self.VoltageSetpointDecimal = None # only one sig fig 0-9
        self.VoltageSetpoint = None # float
        self.MinimumEmissionCurrent = None # currents are all microamps
        self.MaximumEmissionCurrent = None
        self.ControlVoltageValue = None
        self.EmissionCurrentSetpointWhole = None
        self.EmissionCurrentSetpointDecimal = None
        self.EmissionCurrentSetpoint = None
        self.MonitoredVoltage = None
        self.MonitoredVoltageWhole = None
        self.MonitoredVoltageDecimal = None
        self.MonitoredEmissionCurrent = None
        self.MonitoredEmissionCurrentWhole = None
        self.MonitoredEmissionCurrentDecimal = None
        self.InterlockStatus = None
        self.HighVoltageState = None
        return
        
    def __del__ (self) :
        self.serial_connection.close ()
        return

    def WaitToSendData (self, delay=0.2) :
        timeout = timeit.default_timer () + delay
        while (True) :
            if self.serial_connection.out_waiting == 0 :
                return 0 # success
            if timeit.default_timer () > timeout :
                if self.debug : print ("Writing timed out")
                return 1 # failure
        return 2 # should not get here

    def ReceiveData (self, nbytes_r, delay=0.2) :
        data = bytearray ()
        timeout = timeit.default_timer () + delay
        while (True) :
            if self.serial_connection.in_waiting > 0 :
                byte = self.serial_connection.read (1)
                data += byte
                timeout = timeit.default_timer () + delay # reset clock
            if timeit.default_timer () > timeout :
                if self.debug : print ("Writing timed out")
                return 1 # failure
            if len (data) == nbytes_r + 3 :
                self.data = data
                return 0
        return 2 # should not get here

    def CheckData (self, commandbyte) :
        if self.data[0] != 27 :
            print ("Received data packet did not begin correctly")
            return 1
        checksum = CalculateChecksum (self.data[1:-1])
        if checksum != self.data[-1] :
            print ("Received data packet had incorrect checksum")
            return 1
        if commandbyte != self.data[1] :
            print ("Received data packet had incorrect command")
            return 1
        return 0

    def SendCommandAndGetReply (self, commandbyte, nbytes_t, data, nbytes_r) :
        command = bytearray ([commandbyte])
        command.append (nbytes_t)
        if data :
            command += data
        command = PrepareCommand (command)
        self.serial_connection.write (command)
        stat = self.WaitToSendData ()
        if stat :
            print ("Error Sending Command")
            return 1
        stat = self.ReceiveData (nbytes_r)
        if stat :
            print ("Error Receiving Data")
            return 1
        stat = self.CheckData (commandbyte)
        if stat :
            print ("Error in data checks")

    # intentionally omitting SetSerialNumber
    
    def GetSerialNumber (self) :
        commandbyte = 0x43
        nbytes_t = 1
        nbytes_r = 7
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        # decode to ASCII
        self.SerialNumber = self.data[4:9].decode ()
        return 0

    def GetFirmwareVersion (self) :
        commandbyte = 0x44
        nbytes_t = 1
        nbytes_r = 6
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        # decode to ASCII
        self.FirmwareVersion = self.data[4:8].decode ()
        return 0

    # did not implement SetTubeTypePreset
    # did not implement GetTubeTypePreset

    # did not implement SetMinimumHV
    
    def GetMinimumHV (self) :
        commandbyte = 0x48
        nbytes_t = 1
        nbytes_r = 3
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.MinimumHV = self.data[4]
        return 0

    # did not implement SetMaximumVoltage
    
    def GetMaximumVoltage (self) :
        commandbyte = 0x4A
        nbytes_t = 1
        nbytes_r = 3
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.MaximumVoltage = self.data[4]
        return 0

    # did not implement SetVoltageScaleFactor
    # did not implement GetControlVoltageForVoltage

    # TODO
    # change argument to float (units are kV)
    # add check for argument range
    def SetVoltageSetpoint (self, voltage) :
        if voltage > self.MaximumVoltage :
            print ("Requested voltage exceeds maximum allowed.")
            return 1
        if voltage < self.MinimumHV :
            print ("Requested voltage is lower than minimum allowed.")
            return 1
        voltage_whole, voltage_decimal = SplitToWholeDecimal (voltage)
        commandbyte = 0x4D
        nbytes_t = 3
        nbytes_r = 4
        data = bytearray ([voltage_whole, voltage_decimal])
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.UpdateVoltageSetpoint ()
        return 0
    
    def GetVoltageSetpoint (self) :
        commandbyte = 0x4E
        nbytes_t = 1
        nbytes_r = 4
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.UpdateVoltageSetpoint ()
        return 0

    def UpdateVoltageSetpoint (self) :
        self.VoltageSetpointWhole = self.data[4]
        self.VoltageSetpointDecimal = self.data[5]
        self.VoltageSetpoint = self.VoltageSetpointWhole + \
            self.VoltageSetpointDecimal / 10.0
        return
    
    # did not implement SetMinimumEmissionCurrent

    def GetMinimumEmissionCurrent (self) :
        commandbyte = 0x50
        nbytes_t = 1
        nbytes_r = 4
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.MinimumEmissionCurrent = int.from_bytes (self.data[4:6], "big")
        return 0

    # did not implement SetMaximumEmissionCurrent

    def GetMaximumEmissionCurrent (self) :
        commandbyte = 0x52
        nbytes_t = 1
        nbytes_r = 4
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.MaximumEmissionCurrent = int.from_bytes (self.data[4:6], "big")
        return 0
    
    # did not implement SetEmissionCurrentScaleFactor
    def GetControlVoltageForEmissionCurrent (self) :
        commandbyte = 0x54
        nbytes_t = 1
        nbytes_r = 4 # according to the documentation this should be 3
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.ControlVoltageValue = self.data[4] # should be between 1-5
        # there is an undocumented value in data[5];
        # I'm not sure what it is
        return 0  

    # TODO
    # use float argument
    # check argument value
    def SetEmissionCurrentSetpoint (self, current) :
        if current > self.MaximumEmissionCurrent :
            print ("Requested current exceeds maximum allowed.")
            return 1
        if current < self.MinimumEmissionCurrent :
            print ("Requested current is lower than minimum allowed.")
            return 1
        commandbyte = 0x55
        nbytes_t = 4
        nbytes_r = 5
        current_whole, current_decimal = SplitToWholeDecimal (current)
        data = [current_whole//256]
        data.append (current_whole%256)
        data.append (current_decimal)
        data = bytearray (data)
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.UpdateEmissionCurrentSetpoint ()
        return 0
    
    def GetEmissionCurrentSetpoint (self) :
        commandbyte = 0x56
        nbytes_t = 1
        nbytes_r = 5
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.UpdateEmissionCurrentSetpoint ()
        return 0

    def UpdateEmissionCurrentSetpoint (self) :
        self.EmissionCurrentSetpointWhole = \
            int.from_bytes (self.data[4:6], "big")
        self.EmissionCurrentSetpointDecimal = self.data[6]
        self.EmissionCurrentSetpoint = self.EmissionCurrentSetpointWhole + \
            self.EmissionCurrentSetpointDecimal / 10.0
        return
        
    def GetMonitoredVoltage (self) :
        commandbyte = 0x57
        nbytes_t = 1
        nbytes_r = 4
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.MonitoredVoltageWhole = self.data[4]
        self.MonitoredVoltageDecimal = self.data[5]
        self.MonitoredVoltage = self.MonitoredVoltageWhole + \
            self.MonitoredVoltageDecimal / 10.0
        return 0
    
    def GetMonitoredEmissionCurrent (self) :
        commandbyte = 0x58
        nbytes_t = 1
        nbytes_r = 5
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.MonitoredEmissionCurrentWhole = \
            int.from_bytes (self.data[4:6], "big")
        self.MonitoredEmissionCurrentDecimal = self.data[6]
        self.MonitoredEmissionCurrent = self.MonitoredEmissionCurrentWhole + \
            self.MonitoredEmissionCurrentDecimal / 10.0
        return 0

    def GetInterlockStatus (self) :
        commandbyte = 0x59
        nbytes_t = 1
        nbytes_r = 3
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.InterlockStatus = bool (self.data[4]) # True = closed = 1
        return 0

    # turn on HV
    def SetHighVoltageState (self, state) :
        commandbyte = 0x5A
        nbytes_t = 2
        nbytes_r = 3
        data = 1 if state else 0
        data = bytearray ([data])
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.HighVoltageState = bool (self.data[4]) # True = on = 1
        return 0
    
    def GetHighVoltageState (self) :
        commandbyte = 0x5B
        nbytes_t = 1
        nbytes_r = 3
        data = None
        stat = self.SendCommandAndGetReply \
               (commandbyte, nbytes_t, data, nbytes_r)
        if stat :
            return stat
        commandstat = self.data[3]
        if commandstat :
            print ("FTC200 status error")
            return commandstat
        self.HighVoltageState = bool (self.data[4]) # True = on = 1
        return 0


    # did not implement SetHighVoltageRestoreOnPowerUp
    # did not implement GetHighVoltageRestoreOnPowerUp 

    # did not implement ClearRemoteStatus

    # did not implement WriteEEProm
    # did not implement ReadEEProm

    # did not implement SetPSInputVoltage
    # did not implement GetPSInputVoltage

    
    def UpdateStatusFull (self) :
        self.GetSerialNumber ()
        self.GetFirmwareVersion ()
        self.GetMinimumHV ()
        self.GetMaximumVoltage ()
        self.GetVoltageSetpoint ()
        self.GetMinimumEmissionCurrent ()
        self.GetMaximumEmissionCurrent ()
        self.GetControlVoltageForEmissionCurrent ()
        self.GetEmissionCurrentSetpoint ()
        self.GetMonitoredVoltage ()
        self.GetMonitoredEmissionCurrent ()
        self.GetInterlockStatus ()
        self.GetHighVoltageState ()
        return

    def UpdateStatus (self) :
        self.GetMonitoredVoltage ()
        self.GetMonitoredEmissionCurrent ()
        return

    # print status to command line for diagnostic purposes
    def PrintStatus (self) :
        print ("Serial number:\t{}".format (self.SerialNumber))
        print ("Firmware version:\t{}".format (self.FirmwareVersion))
        print ("Minimum HV:\t{} kV".format (self.MinimumHV))
        print ("Maximum Voltage:\t{}".format (self.MaximumVoltage))
        print ("MinimumEmissionCurrent:\t{}".format \
            (self.MinimumEmissionCurrent))
        print ("MaximumEmissionCurrent:\t{}".format \
               (self.MaximumEmissionCurrent))
        print ("Control voltage value:\t{}".format (self.ControlVoltageValue))
        print ("Voltage setpoint:\t{:.1f} kV".format (self.VoltageSetpoint))
        print ("Emission current setpoint:\t{:.1f} uA".format \
               (self.EmissionCurrentSetpoint))
        print ("Monitored voltage:\t{:.1f} kV".format (self.MonitoredVoltage))
        print ("Monitored emission current:\t{:.1f} uA".format \
               (self.MonitoredEmissionCurrent))
        istat = "closed" if self.InterlockStatus else "open"
        print ("Interlock status:\t{}".format (istat))
        hvstat = "on" if self.HighVoltageState else "off"
        print ("High voltage state:\t{}".format (hvstat))
        return

    def ClearError (self) :
        self.serial_connection.reset_input_buffer ()
        self.serial_connection.reset_output_buffer ()
        return
