import os,math,csv
from queue import Full
from sqlite3 import DatabaseError
from ssl import AlertDescription
from tabnanny import check
from matplotlib.axis import XAxis
from matplotlib.patches import Wedge
import numpy as np
import clr
import sys
import ctypes
import json
import pandas as pd
import matplotlib.pyplot as plt
from pyqtgraph.Qt import QtCore,QtGui
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


# ================================================================
with open('welding_different_angle.json','r') as filein:
    ff = json.load(filein)
print(ff)
total_point_group = []
# ================================================================

current_path = os.getcwd()
address = f"{current_path}\\5l16_caokong_90.opd"
# address = f"{current_path}\\rollerform.fpd"
# address = f"{current_path}\\TF_Corrosion.odat"

# address = f"{current_path}\\bolt_5_7.odat"
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
#============================================#
A_BufferKeys = data.GetAscanBufferKeys()
print("======"*20)
# print(f'A_BufferKeys.GetCount(): {A_BufferKeys.GetCount()}')


Velocity = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetVelocity()
# Velocity = Velocity  #Convert to mm/s
print('Velocity is : \n', Velocity , 'mm/s')

Current_gain = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetGain()
# print(f"Gain is : {Current_gain} dB ")
AScanCompressionFactor = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetDigitizingSettings().GetTimeSettings().GetAscanCompressionFactor()
print(f'AScan Compression Factor is: {AScanCompressionFactor}')
AscanSamplingResolution = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetDigitizingSettings().GetTimeSettings().GetAscanSamplingResolution()
print(f'Ascan Sampling Resolution is: {AscanSamplingResolution} ns')
Velocity_in_mm_per_ns = Velocity * 1e-6
# print(f'Velocity in mm/ns is: {Velocity_in_mm_per_ns} mm/ns')
probe_offset = (-1) * 30 # Unit: mm  CL左侧，所以认为坐标是负数
#Get the parameters for each beam/ascan buffer key

welding_part_left_limit = 0 - 15 / np.tan( 60 * (np.pi/180))   #焊接部分左侧边界 （距离CL的长度）

print("=-=-"*20)

for m in range(A_BufferKeys.GetCount()):
# for m in range(1): #for testing should comment out
    # m = 25 #for testing should comment out
    key = A_BufferKeys.GetBufferKey(m)

    SetUp = datafile.GetSetup()
    GetInspectionConfigurations = SetUp.GetInspectionConfigurations()
    InspectionGetConfiguration = GetInspectionConfigurations.GetConfiguration(0)
    Configuration = InspectionGetConfiguration.GetConfigurations().GetConfiguration(0)
    # total_i = Configuration.GetBeamCount() #total of 36 in the example case
    the_beam = Configuration.GetBeam(m)
    # ==================================================================
    #确认一次波是否cover焊接部分
    Angle = the_beam.GetRefractedAnglePrimary() #获得当前beam的角度
    ExitPoint_offset = (-1) * the_beam.GetExitPointPrimary() #获得beam射入工件和楔块的位置
    distance_to_CL = (probe_offset + ExitPoint_offset) # beam射入工件到中心线CL的位置距离



    # ==================================================================
    print("~~~~")
    AScanBuffer = data.GetAscanBuffer(key)
    A_Descriptor = AScanBuffer.GetDescriptor()
    IndxQty_Resol = A_Descriptor.GetIndexAxis().GetResolution()
    ScnQty_Resol = A_Descriptor.GetScanAxis().GetResolution()
    SampleQty = AScanBuffer.GetSampleQuantity()
    Total_sound_path_distance = AscanSamplingResolution * SampleQty * Velocity_in_mm_per_ns
    print(f"The total sound path should be: {Total_sound_path_distance} mm")
    print(f'Datatype is {AScanBuffer.GetDataType()}')
    # =================================================================
    #获取各种Axis的信息
    UltrasoundAxis = A_Descriptor.GetUltrasoundAxis()
    UT_axis_min = UltrasoundAxis.GetMin()
    UT_axis_max = UltrasoundAxis.GetMax()
    UT_axis_resolution = UltrasoundAxis.GetResolution()
    UT_axis_unit = UltrasoundAxis.GetUnit()
    # print("UT axis min ",UT_axis_min)
    # print("UT axis max ",UT_axis_max)
    # print("UT axis resilution ", UT_axis_resolution)
    # print('UT axis unit ', UT_axis_unit)  #nanosecond as unit
    Amplitude_Axis = A_Descriptor.GetAmplitudeAxis()
    Amp_axis_min = Amplitude_Axis.GetMin()
    Amp_axis_max = Amplitude_Axis.GetMax()
    Amp_axis_resolution = Amplitude_Axis.GetResolution()
    Amp_axis_unit = Amplitude_Axis.GetUnit()
    # print('Amplitude Axis min',Amp_axis_min)
    # print('Amplitude Axis max',Amp_axis_max)
    # print('Amplitude Axis resolution',Amp_axis_resolution)
    # print('Amplitude Axis unit',Amp_axis_unit)

    #==================================================================
    #开始读取A扫原始数据
    IndxQty = AScanBuffer.GetIndexCellQuantity()
    print(IndxQty)
    ScnQty = AScanBuffer.GetScanCellQuantity()
    print(ScnQty)
    for j in range(ScnQty):
    # for k in [0]:
        i = 0
        # j = 192
        
        ScanLocation = ScnQty_Resol * j  #Scan 坐标值
        print(f'Scanlocation is {ScanLocation}')

        AScanRead = AScanBuffer.Read(j,i)
        ascan_ptr = AScanRead.GetData()
        try:
            newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_ushort))
            DataBytes = ()
            DataBytes = np.ctypeslib.as_array(newpnt,(SampleQty,)) #Raw Amplitude array (unit in samplings)
            # print(DataBytes)
            # print("Conver the amplitude to the percent")
            Amplitude_in_percentage = DataBytes * Amp_axis_resolution
            UT_axis_in_ns = np.linspace(UT_axis_min,UT_axis_max,SampleQty)
            UT_axis_in_sound_path = UT_axis_in_ns * Velocity_in_mm_per_ns
            # print(Angle,ff[str(Angle)])
            # UT_axis_fixed = np.linspace(8.74,52.95,SampleQty)
            UT_axis_fixed = np.linspace(ff[str(Angle)][0],ff[str(Angle)][0]+ff[str(Angle)][1],SampleQty)
            #==================================================================================================
            #开始获取深度信息，并得到相对CL的位置来确定缺陷的空间位置，只考虑每个A扫查中的最大peak
            # print(f'max amplitude is {np.max(Amplitude_in_percentage)}')
            # Depth_index = np.where(Amplitude_in_percentage == np.max(Amplitude_in_percentage))
            # Defect_point_depth = UT_axis_fixed[int(Depth_index[0][0])]  #确认缺陷所对应的深度值(相对于A扫的X轴的值)
            L = distance_to_CL #Beam射入点距离CL的位置
            print(f"L is {L} mm")
            # ==================================================================================
            # 尝试使用find peaks来定位多个peak的问题，确认大致算法后再测试这个算法
            peak_id, peak_property = find_peaks(Amplitude_in_percentage,height=10)
            peak_depth = UT_axis_fixed[peak_id]
            print("////////////////////////////////////////")
            print(f'peak_depth {peak_depth}')
            peak_amplitude = peak_property['peak_heights']
            print(peak_amplitude)
            print("////////////////////////////////////////")

            # =======================================================
            # 画plot确认peak值
            # if len(peak_depth) >0:
            #     plt.plot(UT_axis_fixed,Amplitude_in_percentage)
            #     for kkk in range(len(peak_amplitude)):
            #         plt.scatter(peak_depth[kkk],peak_amplitude[kkk], s =2 , c= 'red')
            #     # plt.ylim((0,300))
            #     plt.title(f'At {Angle} °, Scanlocation{ScanLocation}')
            #     plt.savefig(f'D:\\NDT_stuff\\2022\\WELDING\\find_peaks_plots\Scan_{ScanLocation}_{Angle}.jpg')
            #     plt.close()
            #     # plt.show()
            # =======================================================


            #以顶面为高度的0面
            for depth_index in range(len(peak_depth)):

                print(peak_depth[depth_index])
                print(peak_amplitude[depth_index])
                Defect_point_depth = peak_depth[depth_index]
                Corrsponding_amplitude = peak_amplitude[depth_index]
                ##每个A扫信号上面有多个peak，逐一获取对应深度值并且再进行转换

                if Defect_point_depth > thickness_setup and Defect_point_depth < (2*thickness_setup):  #考虑一次反射之后
                    Actual_defect_depth = Defect_point_depth - (2*thickness_setup)  # 实际深度
                    print(f'Actual_defect_depth = {Actual_defect_depth}')
                    Defect_x_location =L+\
                        thickness_setup*np.tan(Angle*np.pi/180)+\
                        np.absolute(np.tan(Angle*np.pi/180)*(thickness_setup-np.absolute(Actual_defect_depth)))
                    print(Defect_x_location)
                    print('point information')
                    print(f'x_coordinate:{Defect_x_location}, y_coordinate:{Actual_defect_depth},Amplitude:{np.max(Amplitude_in_percentage)}')
                    point_info=[Defect_x_location,ScanLocation,Actual_defect_depth,Corrsponding_amplitude,Angle,15,30,Defect_point_depth,L]
                    # total_point_group.append(point_info)


                elif Defect_point_depth > (2*thickness_setup) and Defect_point_depth < (3*thickness_setup):  #考虑二次反射之后 （底波 + 顶波）
                    print("hello")
                    print(f"Defect_point_depth is {Defect_point_depth}")
                    Actual_defect_depth =  (2*thickness_setup) -Defect_point_depth #实际深度
                    print(f"Persumed actual defect depth:{Actual_defect_depth}")
                    Defect_x_location = L + \
                        (2* thickness_setup * np.tan(Angle * np.pi/180)) + \
                        (np.tan(Angle * np.pi/180)* np.absolute(Actual_defect_depth))
                    print('point information')
                    print(f'x_coordinate:{Defect_x_location}, y_coordinate:{Actual_defect_depth},Amplitude:{np.max(Amplitude_in_percentage)}')
                    point_info=[Defect_x_location,ScanLocation,Actual_defect_depth,Corrsponding_amplitude,Angle,30,45,Defect_point_depth,L]
                    # total_point_group.append(point_info)

                #     pass
                elif Defect_point_depth > (3*thickness_setup) and Defect_point_depth < (4*thickness_setup): #考虑三次反射后缺陷（底+顶+底）
                    print('LOL')
                    print(f"Defect_point_depth is {Defect_point_depth}")
                    Actual_defect_depth = Defect_point_depth -4*thickness_setup #实际深度\
                    print(f"Persumed actual defect depth:{Actual_defect_depth}")
                    Defect_x_location =L+\
                        3*thickness_setup*np.tan(Angle*np.pi/180)+\
                        np.absolute((thickness_setup-np.absolute(Actual_defect_depth))*np.tan(Angle*np.pi/180))
                    point_info=[Defect_x_location,ScanLocation,Actual_defect_depth,Corrsponding_amplitude,Angle,45,60,Defect_point_depth,L]
                    # total_point_group.append(point_info)

                elif Defect_point_depth < (1*thickness_setup):
                    print('first half')
                    print(f"Defect_point_depth is {Defect_point_depth}")
                    Actual_defect_depth = (-1) * Defect_point_depth
                    print(f"Persumed actual defect depth:{Actual_defect_depth}")
                    Defect_x_location = L + np.absolute(Actual_defect_depth)* np.tan(Angle*np.pi/180)
                    point_info = [Defect_x_location,ScanLocation,Actual_defect_depth,Corrsponding_amplitude,Angle,0,15,Defect_point_depth,L]
                    # total_point_group.append(point_info)
                    print(point_info)


                # else:
                #     print("do later")
                #     pointinfo = [0,ScanLocation,0,Angle]


                # if  point_info[3] > 30:
                total_point_group.append(point_info)


                


        except:
            pass
            # print("something is wroong")

print(total_point_group)
print(len(total_point_group))

#================
# 整理所有的缺陷点

with open("defects_group_find_peaks_Aug1.csv",'w',newline='') as fileout:
# with open("to double check.csv",'w',newline='') as fileout:

    csvwriter = csv.writer(fileout)
    csvwriter.writerows(total_point_group)
