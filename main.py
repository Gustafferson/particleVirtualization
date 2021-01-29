# import dependencies
import time
import os
import numpy as np
import serial
from harvesters.core import Harvester
from harvesters.util.pfnc import mono_location_formats
import png

# Get the date and time in yymmddHHMMSS format for file naming
Time = time.strftime("%y%m%d%H%M%S")

imageDir = str("/home/gus/Particles/"+str(Time)+"/")
# create the directory for image saving
try:  
    os.mkdir(imageDir)
except OSError as error:  
    print(error)   

print('opening gigE-vis platform')
# open the GeniCam API
h = Harvester()
# import the GenTL cti file
# h.add_file('/opt/baumer-gapi-sdk/lib/libbgapi2_gige.cti')
h.add_file('/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti')

# update Harvester to use the GenTL file
h.update()
# display the list of detected GigE cameras
print(h.device_info_list)

# activates cam, light green
ia = h.create_image_acquirer(0)
# set the camera settings in the node_map
ia.remote_device.node_map.acquisitionFrameRateControlMode = 'Programmable'
ia.remote_device.node_map.ExposureMode.value = 'Timed'
ia.remote_device.node_map.ExposureTime.value = 200024
ia.remote_device.node_map.AcquisitionFrameRate = 0.06
ia.remote_device.node_map.exposureAlignment = 'Synchronous'
ia.remote_device.node_map.Width = 4112
ia.remote_device.node_map.Height = 3008
ia.remote_device.node_map.autoBrightnessMode = 'Off'
ia.remote_device.node_map.devicePacketResendBufferSize = 11
ia.remote_device.node_map.DeviceLinkThroughputLimitMode	= 'On'
ia.remote_device.node_map.DeviceLinkThroughputLimit = 5500000 # I removed a 0 now it works
ia.remote_device.node_map.GevSCPSPacketSize	= 576
ia.remote_device.node_map.GevStreamChannelSelector = 0

# create a function to communicate over Serial 
def query(serialPort,string):
    command="#1"+string+"\r"
    ser.write(bytes(command, 'utf-8'))
    stri = ser.read_until(b"\r")
    print(stri)
    return stri


ser = serial.Serial('/dev/ttyS4',baudrate=115200,
                         bytesize=serial.EIGHTBITS,
                         parity=serial.PARITY_NONE,
                         stopbits=serial.STOPBITS_ONE,
                         timeout=20)
#ser.open()

ia.start_acquisition(run_in_background=True)


# create n number of stops per revolution
n=8

# on the serial connection: 
print('opening serial connection')
query(ser,"J1") # open connection
query(ser,"s+"+str(int(2560000/n))) # step by total steps per rev/n
query(ser,"o+32000") # set speed
print("s+"+str(int(2560000/n))) 
for step in range(n):
    print('stop %d of %s' % (step+1,n))
    query(ser,"p1")
    query(ser,"A")
    ser.read_until(b"\r")

    # Perhaps add error handling, try fetch, if fail, repeat twice else exit
    # Take Image Here
    buffer = ia.fetch_buffer()
    # if np.mean(buffer) > 1:
    #     print('Buffer filled! '+str(step)+' of '+str(n))
    # else:
    #     print('Buffer error! '+str(step)+' of '+str(n))
    
    # get the buffer 1D array and reshape onto height and width
    payload = buffer.payload
    component = payload.components[0]
    width = component.width
    height = component.height
    content = component.data.reshape(height, width)
    
    # from png module, save array to png
    filename = str(str(Time)+"_"+str(step).zfill(3)+".png")
    png.from_array(content,'L').save(imageDir+filename)

    buffer.queue()

ia.stop_acquisition()
ia.destroy()

h.reset()


query(ser,"S")
    