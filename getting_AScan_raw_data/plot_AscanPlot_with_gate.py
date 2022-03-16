import os
from sqlite3 import DatabaseError
from matplotlib.axis import XAxis
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
from scipy.signal import find_peaks

clr.FindAssembly("OlympusNDT.Storage.NET.dll")
clr.AddReference('OlympusNDT.Storage.NET')
clr.FindAssembly("OlympusNDT.Instrumentation.NET.dll")
clr.AddReference('OlympusNDT.Instrumentation.NET')
import OlympusNDT.Storage.NET
import OlympusNDT.Instrumentation.NET
from OlympusNDT.Storage.NET import StorageSWIG,Utilities
current_path = os.getcwd()
# address = f"{current_path}\\LAM21-705-CPZ.odat"
address = f"{current_path}\\rollerform.fpd"
# address = f"{current_path}\\TF_Corrosion.odat"
Utilities.ResolveDependenciesPath()
datafile = StorageSWIG.OpenDataFile(address)
data = datafile.GetData()
#============================================#
thickness_setup = float(datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetThickness())
print(f"thickness_setup is {thickness_setup}")
print(dir(datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry()))
Length_setup = datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetLength()
print(f'Lengh_setup is: {Length_setup}')
width_setup = datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetWidth()
print(f'width_setup is {width_setup}')
top_surface = datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetTopSurface()
print(top_surface)
# print(dir(top_surface))
#============================================#
C_BufferKeys = data.GetCscanBufferKeys()
A_BufferKeys = data.GetAscanBufferKeys()
print("======"*25)
# print(f'A_BufferKeys.GetCount(): {A_BufferKeys.GetCount()}')
m = 0
key = A_BufferKeys.GetBufferKey(m)  
AScanBuffer = data.GetAscanBuffer(key)
A_Descriptor = AScanBuffer.GetDescriptor()
print(f"DataType? : {AScanBuffer.GetDataType()}")    #Turns out to be USHORT FOR odat

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
print(range(10,ScnQty))
offset = 10
# for j in range(offset,ScnQty-offset):
# for j in range(ScnQty):
for j in range(1):
      # for k in range(offset,IndxQty-offset):
      # for k in range(IndxQty):
      for k in range(1):
            j = 182
            k = 36
            print("DataType")
            print(AScanBuffer.GetDataType())
            ARead = AScanBuffer.Read(j,k)
            ascan_ptr = ARead.GetData()
            print(f'ascan_ptr\n{dir(ascan_ptr)}')
            location_index = [j,k]
            actual_coordinate =  [location_index[0]*ScnQty_Resol,location_index[1]*IndxQty_Resol]

            try:
                  # newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_ushort))
                  newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_ubyte))
                  DataBytes = ()
                  DataBytes = np.ctypeslib.as_array(newpnt,(SampleQty,)) #Raw Amplitude array (unit in samplings)
                  print(DataBytes)
                  errormessage = False
            except:
                  # print("error")
                  errormessage = True
            
            if errormessage == False:
                  

                  #========================Get the raw amplitude and thickness X-axis reading======================================#
                  AScan_multiply_reading = DataBytes * np.array([float(AmplitudeAxis.GetResolution())])   #Convert to percent
                  X_axis = np.linspace(0,AScanX_axis_limit,SampleQty)  #get the Thickness reading for the X-axis
                  

                  #===================================================================================#
                  amp_gate_lower_limit = np.max(AScan_multiply_reading) *0.1
                  amp_gate_higher_limit = np.max(AScan_multiply_reading) *0.8
                  Xaxis_lower_limit = thickness_setup * 0.1
                  Xaxis_higher_limit = thickness_setup * 0.5
                  
                  """Apply gate threshold for both x-axis and amplitude in the ascan"""
                  xaxis_index_processed_arr = np.array(np.where((X_axis > Xaxis_lower_limit) & (X_axis < Xaxis_higher_limit)))[0]
                  amp_index_processed_arr = np.array(np.where((AScan_multiply_reading > amp_gate_lower_limit)&(AScan_multiply_reading < amp_gate_higher_limit)))[0]
                  overlapping_process_index_arr = np.intersect1d(xaxis_index_processed_arr,amp_index_processed_arr)
                  
                  X_axis_processed = X_axis[overlapping_process_index_arr]
                  
                  amp_axis_processed = AScan_multiply_reading[overlapping_process_index_arr]

                  plt.plot(X_axis,AScan_multiply_reading,c='g')
                  plt.plot(X_axis_processed,amp_axis_processed,c='r')
                  plt.show()
                  print(AScanX_axis_limit)
                  print(AmplitudeAxis.GetResolution())
