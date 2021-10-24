import FTC200

import tkinter as tk
import os, fnmatch

def find_files(directory, pattern):
    print (directory, pattern)
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename

muchar = "\u03BC"
# mu is in unicode : \u03BC

class moxtek_control_GUI (tk.Frame) :

    def __init__ (self, master) :
        self.IsConnected = False # needs an indicator
        self.ftc = None # don't initialize til dev is supplied
        self.device = "null"

        
        # Initializes the frame
        tk.Frame.__init__(self, master)

        # add a ticker to indicate aliveness
        self.tick_value = 0
        self.TickerVar = tk.StringVar ()
        self.TickerVar.set (self.tick_value)
        self.TickerLabel = \
            tk.Label (self.master, textvariable=self.TickerVar)
        self.TickerLabel.grid (row=0,column=5,sticky=tk.W)
        self.UpdateTicker ()

        # add a field for error handling
        self.ErrorText = "N/A"
        self.Error_Var = tk.StringVar ()
        self.Error_Var.set ("---")
        self.Error_Label = tk.Label (self.master, textvariable=self.Error_Var)
        self.Error_Label.grid (row=13, column=5, columnspan=4, rowspan=3,
                               sticky=tk.W)
        self.UpdateErrorText ()

        # run a routine to guess device
        # should give access to the arguments in a better way, hard code for now
        self.GuessDevice ('/dev/', 'cu.usbserial-[0-9]*')
        print ("device = ", self.device)
        
        # buttons
        ConnectButton = tk.Button(
            self.master, text = 'Connect', command=self.Connect)
        ConnectButton.grid(row=0, column=2)

        DisconnectButton = tk.Button(
            self.master, text = 'Disconnect', command=self.Disconnect)
        DisconnectButton.grid(row=0, column=3)

        HVControlButton = tk.Button (
            self.master, text='HV on/off', command=self.ToggleHV)
        HVControlButton.grid (row=1, column=0)

        # make an indicator to show if we are connected
        canvas_y = 18
        self.ConnectedCanvas = tk.Canvas (self.master, width=150, height=30)
        self.ConnectedCanvas.create_text (50,canvas_y,text='Connected')
        self.ConnectedCanvas.grid (row=0, column=4)
        self.LEDcolor = 'red'
        button_r = 10
        button_y0 = canvas_y - button_r
        button_y1 = canvas_y + button_r
        button_x = 105
        button_x0 = button_x - button_r
        button_x1 = button_x + button_r
        self.ConnectedLED = \
            self.ConnectedCanvas.create_oval \
            (button_x0,button_y0,button_x1,button_y1, fill=self.LEDcolor)
        self.ConnectedCanvas.after (1000, self.UpdateStatus)

        # make an indicator to show if HV is on
        # reuse canvas/button parameters from connected indicator
        self.HVStatusCanvas = tk.Canvas (self.master, width=150, height=30)
        self.HVStatusCanvas.create_text (50,canvas_y,text='HV Status')
        self.HVStatusCanvas.grid (row=1, column=1)
        self.HVLEDcolor = 'red'
        self.HVStatusLED = \
            self.HVStatusCanvas.create_oval \
            (button_x0,button_y0,button_x1,button_y1, fill=self.HVLEDcolor)
        self.HVStatusCanvas.after (1000, self.UpdateStatus)
        # also one for interlock
        self.InterlockStatusCanvas = tk.Canvas \
            (self.master, width=150, height=30)
        self.InterlockStatusCanvas.create_text \
            (50,canvas_y,text='Interlock')
        self.InterlockStatusCanvas.grid (row=1, column=2)
        self.InterlockLEDcolor = 'red'
        self.InterlockStatusLED = \
            self.InterlockStatusCanvas.create_oval \
            (button_x0,button_y0,button_x1,button_y1,\
             fill=self.InterlockLEDcolor)
        self.InterlockStatusCanvas.after (1000, self.UpdateStatus)
        
        
        # button to set device path
        SetDeviceButton = tk.Button (self.master, text='Set Device',\
                                     command=self.SetDevice)
        SetDeviceButton.grid (row=0, column=0)

        # and entry field
        self.DeviceEntry = tk.Entry (self.master, width=30)
        self.DeviceEntry.grid (row=0, column=1)
        print ("device = ", self.device)
        self.DeviceEntry.insert ('end', self.device)

        # buttons to set HV and current
        SetHVButton = tk.Button (self.master, text='Set HV (kV)',\
                                 command=self.SetHV)
        SetHVButton.grid (row=3, column=2)
        SetEmissionCurrentButton = tk.Button \
            (self.master, text='Set Iem ({}A)'.format (muchar),\
             command=self.SetEmissionCurrent)
        SetEmissionCurrentButton.grid (row=4, column=2)

        self.RangeLabel = tk.Label (self.master, text="Range")
        self.RangeLabel.grid (row=2, column=3)
        self.NewSetpointLabel = tk.Label (self.master, text="New setpoint")
        self.NewSetpointLabel.grid (row=2, column=4)
        self.SetpointLabel = tk.Label (self.master, text="Setpoint")
        self.SetpointLabel.grid (row=2, column=5)
        self.MonitorLabel = tk.Label (self.master, text="Monitor")
        self.MonitorLabel.grid (row=2, column=6)

        # entry fields for HV and current
        self.HVEntry = tk.Entry (self.master, width=5)
        self.HVEntry.grid (row=3, column=4)
        self.HVEntry.insert ('end', 10) # hardcode for now
        self.EmissionCurrentEntry = tk.Entry (self.master, width=5)
        self.EmissionCurrentEntry.grid (row=4, column=4)
        self.EmissionCurrentEntry.insert ('end', 0)
        # print setpoints
        self.HVVar = tk.StringVar ()
        self.HVVar.set ("-1")
        self.HVValue = tk.Label \
            (self.master, textvariable=self.HVVar)
        self.HVValue.grid (row=3,column=5)
        self.EmissionCurrentVar = tk.StringVar ()
        self.EmissionCurrentVar.set ("-1")
        self.EmissionCurrentValue = tk.Label \
            (self.master, textvariable=self.EmissionCurrentVar)
        self.EmissionCurrentValue.grid (row=4, column=5)
        
        QuitButton = tk.Button(
            master,
            text = 'Quit',
            command=master.quit,
            width=15
        )
        QuitButton.grid(row=0, column=10)

        # print status values

        self.SerialNumberVar = tk.StringVar ()
        self.SerialNumberVar.set ("-1")
        self.SerialNumberValue = tk.Label \
            (self.master, textvariable=self.SerialNumberVar)
        self.SerialNumberValue.grid (row=10,column=10) # fix me
        self.FirmwareVersionVar = tk.StringVar ()
        self.FirmwareVersionVar.set ("-1")
        self.FirmwareVersionValue = tk.Label \
            (self.master, textvariable=self.FirmwareVersionVar)
        self.FirmwareVersionValue.grid (row=11,column=10) # fix me

        # these all need to be associated to setpoints
        #self.MinimumHVVar = tk.StringVar ()
        #self.MinimumHVVar.set ("-1")
        #self.MaximumHVVar = tk.StringVar ()
        #self.MaximumHVVar.set ("-1")
        self.MinMaxHVVar = tk.StringVar ()
        self.MinMaxHVVar.set ("-1")
        
        self.MinMaxHVValue = tk.Label \
            (self.master, textvariable=self.MinMaxHVVar)
        self.MinMaxHVValue.grid (row=3,column=3)
        #self.MinimumHVValue = tk.Label \
        #    (self.master, textvariable=self.MinimumHVVar)
        #self.MinimumHVValue.grid (row=3,column=2)

        #self.MinimumEmissionCurrentVar = tk.StringVar ()
        #self.MinimumEmissionCurrentVar.set ("-1")
        #self.MaximumEmissionCurrentVar = tk.StringVar ()
        #self.MaximumEmissionCurrentVar.set ("-1")

        self.MinMaxIemVar = tk.StringVar ()
        self.MinMaxIemVar.set ("-1")
        self.MinMaxIemValue = tk.Label \
            (self.master, textvariable=self.MinMaxIemVar)
        self.MinMaxIemValue.grid (row=4, column=3)
        
        self.MonitoredVoltageVar = tk.StringVar ()
        self.MonitoredVoltageVar.set ("-1")
        self.MonitoredVoltageValue = tk.Label \
            (self.master, textvariable=self.MonitoredVoltageVar)
        self.MonitoredVoltageValue.grid (row=3, column=6)
        self.MonitoredEmissionCurrentVar = tk.StringVar ()
        self.MonitoredEmissionCurrentVar.set ("-1")
        self.MonitoredEmissionCurrentValue = tk.Label \
            (self.master, textvariable=self.MonitoredEmissionCurrentVar)
        self.MonitoredEmissionCurrentValue.grid (row=4, column=6)
        # need to make fields in the right places to display them
        
    def GuessDevice (self, deviceDirectory, deviceRootName) :
        devices = []
        for filename in find_files (deviceDirectory, deviceRootName):
            devices.append (filename)
        print ("devices : ", devices)
        if len (devices) == 1 :
            self.device = devices[0]
            return
        elif len (devices) == 0:
            self.ErrorText = "Can't find device"
            self.UpdateErrorText ()
            return
        else :
            self.device = devices[0]
            self.ErrorText = "More than one device, using first one as guess"
            self.UpdateErrorText ()
            return
        return

    def SetDevice (self) :
        self.device = self.DeviceEntry.get ()
        # not implementing device path validation for now
        return

    def SetHV (self) :
        # should validate input
        try :
            self.ftc.SetVoltageSetpoint (float (self.HVEntry.get ()))
        except :
            self.ErrorText = "Error setting HV"
            self.UpdateErrorText ()
            return
        # should add a status update (or maybe it's just updating a lot)
        return

    def SetEmissionCurrent (self):
        # should validate input
        try :
            stat = self.ftc.SetEmissionCurrentSetpoint \
                (float (self.EmissionCurrentEntry.get()))
        except :
            self.ErrorText = "Error setting emission current"
            self.UpdateErrorText ()
            return
        # status update
        return
    
    def Connect (self) :
        try :
            self.ftc = FTC200.FTC200 (self.device)
        except :
            self.ErrorText = "Error connecting to serial port"
            self.UpdateErrorText ()
            return
        self.IsConnected = True
        print ("Connected!")
        stat = self.ftc.UpdateStatusFull ()
        if stat :
            self.ErrorText = "Error getting status update"
            return
        self.SetStatusVariables ()
        return

    def Disconnect (self) :
        if self.ftc :
            self.ftc.disconnect () # this still needs to be implemented in FTC200
            self.IsConnected = False
            print ("Disconnected!")
        return

    def SetStatusVariables (self) :
        self.HVVar.set ("{} kV".format (self.ftc.VoltageSetpoint))

        self.EmissionCurrentVar.set \
            ("{} {}A".format (self.ftc.EmissionCurrentSetpoint, muchar))
        self.SerialNumberVar.set \
            ("Serial Number:\t{}".format (self.ftc.SerialNumber))
        self.FirmwareVersionVar.set \
            ("Firmware Version:\t{}".format (self.ftc.FirmwareVersion))
        #self.MinimumHVVar.set (self.ftc.MinimumHV)
        #self.MaximumHVVar.set (self.ftc.MaximumVoltage)
        self.MinMaxHVVar.set \
            ("{} - {} kV".format (self.ftc.MinimumHV, self.ftc.MaximumVoltage))
        #self.MinimumEmissionCurrentVar.set (self.ftc.MinimumEmissionCurrent)
        #self.MaximumEmissionCurrentVar.set (self.ftc.MaximumEmissionCurrent)
        self.MinMaxIemVar.set \
            ("{} - {} {}A".format (self.ftc.MinimumEmissionCurrent,\
                                   self.ftc.MaximumEmissionCurrent, muchar))
        self.MonitoredVoltageVar.set \
            ("{} kV".format (self.ftc.MonitoredVoltage))
        self.MonitoredEmissionCurrentVar.set \
            ("{} {}A".format (self.ftc.MonitoredEmissionCurrent, muchar))
        return
    
    def ToggleHV (self) :
        if not self.IsConnected :
            self.ErrorText = "Not connected"
            self.UpdateErrorText ()
            return
        if self.ftc.HighVoltageState :
            try :
                self.TurnHVOff ()
            except :
                self.ErrorText = "Error turning off HV"
                return
        else :
            try :
                self.TurnHVOn ()
            except :
                self.ErrorText = "Error turning on HV"
                return
        return

    def TurnHVOn (self) :
        stat = self.ftc.SetHighVoltageState (True)
        if stat :
            raise IOError
        stat = self.ftc.UpdateStatusFull ()
        if stat :
            raise IOError
        self.UpdateStatusVariables ()
        return

    def TurnHVOff (self) :
        stat = self.ftc.SetHighVoltageState (False)
        if stat :
            raise IOError
        stat = self.ftc.UpdateStatusFull ()
        if stat :
            raise IOError
        self.UpdateStatusVariables ()
        return
    
    def UpdateStatus (self):
        #print ("Updating Status")
        if self.IsConnected :
            self.LEDcolor = "green"
        else :
            self.LEDcolor = "red"
        if self.IsConnected :
            if self.ftc.HighVoltageState :
                self.HVLEDcolor = "green"
            else :
                self.HVLEDcolor = "red"
            if self.ftc.InterlockStatus :
                self.InterlockLEDcolor = "green"
            else :
                self.InterlockLEDcolor = "red"
        self.ConnectedCanvas.itemconfig(self.ConnectedLED, fill=self.LEDcolor)
        self.HVStatusCanvas.itemconfig(self.HVStatusLED, fill=self.HVLEDcolor)
        self.InterlockStatusCanvas.itemconfig\
            (self.InterlockStatusLED, fill=self.InterlockLEDcolor)

        if self.IsConnected :
            self.ftc.UpdateStatus ()
            self.SetStatusVariables ()
        self.master.after (1000, self.UpdateStatus)

    def UpdateTicker (self) :
        self.tick_value += 1
        self.TickerVar.set ("Tick:\t{}".format (self.tick_value))
        self.master.after (1000, self.UpdateTicker)
        return
    
    def UpdateErrorText (self) :
        #print (self.ErrorText) # print to command line, serves as a log
        self.Error_Var.set ("Most recent error: {}".format(self.ErrorText))

if __name__ == "__main__":

    root = tk.Tk()
    root.title("Moxtek x-ray source control")
    app = moxtek_control_GUI(root)

    app.mainloop()

