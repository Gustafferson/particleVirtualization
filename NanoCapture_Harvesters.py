# uses the Harvesters.core module in combination with a CommonVisionBlox GenTL file 
# Issues: camera startup is troublesome, GenTL module presents errors after fetch_buffer call

import time
import numpy as np
#from genicam.genapi import NodeMap
from harvesters.core import Harvester
from harvesters.util.pfnc import mono_location_formats
import png



h = Harvester()

# h.add_file('/opt/cvb-13.02.002/drivers/genicam/libGevTL.cti')
# h.add_file('/opt/baumer-gapi-sdk/lib/libbgapi2_gige.cti')
h.add_file('/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti')

h.update()

print(h.device_info_list)

#activates cam, light green
ia = h.create_image_acquirer(0)
#print(dir(ia.remote_device.node_map))

# ia.remote_device.node_map.load_xml_from_string('/home/gus/GigE-V/xml/Teledyne DALSA/TeledyneDALSA_Nano-IMX267-304_Mono_9M-12M_40769e92_ECA18.0014.xml')

ia.remote_device.node_map.acquisitionFrameRateControlMode = 'Programmable'
ia.remote_device.node_map.AcquisitionMode.value = 'Continuous'
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



# ia.start_acquisition(0)
ia.start_acquisition(run_in_background=True)



buffer = ia.fetch_buffer()
# buffer = ia.fetch_buffer(is_raw=True)

print(buffer)
# Don't forget to queue the buffer.
# buffer.queue()
# buffer = ia.fetch_buffer(timeout=5)

#time.sleep(1)



payload = buffer.payload
component = payload.components[0]
width = component.width
height = component.height
data_format = component.data_format

# # Reshape the image so that it can be drawn on the VisPy canvas:
if data_format in mono_location_formats:
    content = component.data.reshape(height, width)

print(content)

png.from_array(content,'L').save("img.png")
# png.from_array(_2d,'L').save("img.png")

buffer.queue()
# buffer = ia.fetch_buffer()
# print(buffer+"second attempt")

ia.stop_acquisition()
ia.destroy()


h.reset()
