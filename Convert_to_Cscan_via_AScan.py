import os
import numpy as np
import clr
import sys
import ctypes
import json
import pandas as pd
import matplotlib.pyplot as plt
from pyqtgraph.Qt import QtCore,QtGui
from pyqtgraph.graphicsItems.PlotDataItem import dataType
import pyqtgraph.opengl as gl
import pyqtgraph as pg
from matplotlib import cm
import datetime
# import scipy

clr.FindAssembly("OlympusNDT.Storage.NET.dll")
clr.AddReference('OlympusNDT.Storage.NET')
clr.FindAssembly("OlympusNDT.Instrumentation.NET.dll")
clr.AddReference('OlympusNDT.Instrumentation.NET')
import OlympusNDT.Storage.NET
import OlympusNDT.Instrumentation.NET
from OlympusNDT.Storage.NET import StorageSWIG,Utilities
current_path = os.getcwd()
address = f"{current_path}\\LAM21-705-CPZ.odat"
# address = f"{current_path}\\rollerform.fpd"
# address = f"{current_path}\\TF_Corrosion.odat"
Utilities.ResolveDependenciesPath()
datafile = StorageSWIG.OpenDataFile(address)
data = datafile.GetData()
#============================================#
thickness_setup = float(datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetThickness())
#============================================#
C_BufferKeys = data.GetCscanBufferKeys()
A_BufferKeys = data.GetAscanBufferKeys()
print("======"*25)
# print(f'A_BufferKeys.GetCount(): {A_BufferKeys.GetCount()}')
m = 0
key = A_BufferKeys.GetBufferKey(m)  
AScanBuffer = data.GetAscanBuffer(key)
A_Descriptor = AScanBuffer.GetDescriptor()
print(f"DataType? : {AScanBuffer.GetDataType()}")    #Turns out to be USHORT

Velocity = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetVelocity()
Velocity = Velocity * 1e3  #Convert to mm/s
print('Velocity is : \n', Velocity , 'mm/s')
# Current_gain = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).SetGain(25)

Current_gain = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetGain()
print(f"Gain is : {Current_gain} dB ")
print("=-=-"*20)
AScanCompressionFactor = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetDigitizingSettings().GetTimeSettings().GetAscanCompressionFactor()
print(f'AScan Compression Factor is: {AScanCompressionFactor}')
AscanSamplingResolution = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetDigitizingSettings().GetTimeSettings().GetAscanSamplingResolution()
print(f'Ascan Sampling Resolution is: {AscanSamplingResolution} ns')
Velocity_in_mm_per_ns = Velocity * 1e-9
print(f'Velocity in mm/ns is: {Velocity_in_mm_per_ns} mm/ns')


CKey = C_BufferKeys.GetBufferKey(1) #Gate A  
CScanBuffer = data.GetCscanBuffer(CKey)






print("====="*10)
AmplitudeAxis = A_Descriptor.GetAmplitudeAxis()
print("Amplitude Axis Max: \n", AmplitudeAxis.GetMax())
# print("Amplitude Axis Min: \n", AmplitudeAxis.GetMin())
print("Amplitude Axis Resolution: \n", AmplitudeAxis.GetResolution())
# print("Amplitude Axis Unit: \n", AmplitudeAxis.GetUnit())
# print("Amplitude Axis Data Type: \n", AmplitudeAxis.GetType())

print("====="*10)
AmplitudeSamplingAxis = A_Descriptor.GetAmplitudeSamplingAxis()
print("Amplitude Sampling Axis Max: \n", AmplitudeSamplingAxis.GetMax())
# print("Amplitude Sampling Axis Min: \n", AmplitudeSamplingAxis.GetMin())
print("Amplitude Sampling Axis Resolution: \n", AmplitudeSamplingAxis.GetResolution())
# print("Amplitude Sampling Axis Unit: \n", AmplitudeSamplingAxis.GetUnit())
# print("Amplitude Sampling Axis Data Type: \n", AmplitudeSamplingAxis.GetType())
print("====="*10)
SampleQty = AScanBuffer.GetSampleQuantity()
print("Sample Qty is : ", SampleQty)
IndxQty = AScanBuffer.GetIndexCellQuantity()
print(f'IndxQty:',IndxQty)
ScnQty = AScanBuffer.GetScanCellQuantity()
print(f'ScnQty:',ScnQty)
print("====="*10)
IndxQty_Resol = A_Descriptor.GetIndexAxis().GetResolution()
ScnQty_Resol = A_Descriptor.GetScanAxis().GetResolution()
print(f'ScanQty_resol: {ScnQty_Resol} mm')
print(f'IndexQty_resol: {IndxQty_Resol} mm')
AScanX_axis_limit = Velocity_in_mm_per_ns * AscanSamplingResolution * SampleQty * 0.5
print(f"Ascan plot X limit is : {AScanX_axis_limit} mm")
X,Y,D,A = [],[],[],[]
for j in range(ScnQty):
      for k in range(IndxQty):
            ARead = AScanBuffer.Read(j,k)
            CRead = CScanBuffer.Read(j,k)
            ascan_ptr = ARead.GetData()
            location_index = [j,k]
            actual_coordinate =  [location_index[0]*ScnQty_Resol,location_index[1]*IndxQty_Resol]

            newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_ushort))
            # newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_ubyte))
            DataBytes = ()
            try:
                  DataBytes = np.ctypeslib.as_array(newpnt,(SampleQty,)) #Raw Amplitude array (unit in samplings)
                  
                  #=================
                  #From CScan
                  raw_amplitude_reading = CRead.GetAmplitude()
                  processed_amplitude_reading = raw_amplitude_reading * float(AmplitudeAxis.GetResolution())
                  #=================
                  if raw_amplitude_reading in DataBytes:
                        AScan_multiply_reading = DataBytes * np.array([float(AmplitudeAxis.GetResolution())])
                        tango = np.where(DataBytes == raw_amplitude_reading)   #to find the index
                        X_axis = np.linspace(0,AScanX_axis_limit,SampleQty)
                        # print('T: ',X_axis[tango],' mm')
                        Depth = X_axis[tango]
                        D.append(float(Depth))
                        Amplitude_in_pct = [AScan_multiply_reading[tango]][0]
                        A.append(Amplitude_in_pct[0])
                        X.append(actual_coordinate[0])
                        Y.append(actual_coordinate[1])
                  # elif raw_amplitude_reading not in DataBytes:
                  #       print('Amplitude reading from CScan not match with the reading from AScan')

            except:
                  Depth = 0
            # Distance = (CRead.GetPosition() * 1.0e-9) * Velocity * 0.5

print(len(X))
print(len(Y))
print(len(D),' ',len(A))
print(D[-1])
print(A[-1])






#===================================
fig = plt.figure()
ax = plt.axes(projection ="3d")
my_cmap = plt.get_cmap('hsv')
# Creating plot
sctt = ax.scatter3D(X, Y, D,
                    alpha = 0.8,
                    c = A,
                    cmap = my_cmap,
                    marker ='.')
 
plt.title("simple 3D scatter plot")
ax.set_xlabel('X-axis', fontweight ='bold')
ax.set_ylabel('Y-axis', fontweight ='bold')
ax.set_zlabel('Z-axis', fontweight ='bold')
fig.colorbar(sctt, ax = ax, shrink = 0.5, aspect = 5)
 
# show plot
plt.show()



print("~END~END~END~END~END~")

