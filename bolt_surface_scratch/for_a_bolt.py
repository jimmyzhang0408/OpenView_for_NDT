import os
import numpy as np
import clr
import sys,math
import ctypes
import json
import pandas as pd
import matplotlib.pyplot as plt
from pyparsing import And
from scipy.signal import find_peaks
from PyQt5.QtWidgets import QApplication
from pyqtgraph.opengl import GLViewWidget, MeshData, GLMeshItem
from stl import mesh

import pyqtgraph.opengl as gl
import pyqtgraph as pg


# from Convert_to_Cscan_via_AScan import DataBytes

clr.FindAssembly("OlympusNDT.Storage.NET.dll")
clr.AddReference('OlympusNDT.Storage.NET')
clr.FindAssembly("OlympusNDT.Instrumentation.NET.dll")
clr.AddReference('OlympusNDT.Instrumentation.NET')

import OlympusNDT.Storage.NET
import OlympusNDT.Instrumentation.NET
from OlympusNDT.Storage.NET import StorageSWIG,Utilities
current_path = os.getcwd()
# address = f"{current_path}\\LAM21-705-CPZ.odat"
# address = f"{current_path}\\rollerform.fpd"
# address = f"{current_path}\\TF_Corrosion.odat"

def get_defect(file_address):
    address = file_address
    # address = f"{current_path}\\bolt_5_7.odat"
    Utilities.ResolveDependenciesPath()
    datafile = StorageSWIG.OpenDataFile(address)
    data = datafile.GetData()
    print(data)
    #============================================#




    # #============================================#
    thickness_setup = float(datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetThickness())
    # #============================================#
    C_BufferKeys = data.GetCscanBufferKeys()
    A_BufferKeys = data.GetAscanBufferKeys()

    obverall = dict()
    defect_group = []
    print("======"*25)
    # print(f'A_BufferKeys.GetCount(): {A_BufferKeys.GetCount()}')
    m = 0
    for m in range(A_BufferKeys.GetCount()):
    # for m in range(1):
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
        j = 0
        k = 0
        ARead = AScanBuffer.Read(j,k)
        ascan_ptr = ARead.GetData()
        newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_ushort))
        DataBytes = ()
        DataBytes = np.ctypeslib.as_array(newpnt,(SampleQty,)) #Raw Amplitude array (unit in samplings)
        # print(DataBytes)
        #========================Get the raw amplitude and thickness X-axis reading======================================#
        AScan_multiply_reading = DataBytes * np.array([float(AmplitudeAxis.GetResolution())])   #Convert to percent
        X_axis = np.linspace(0,AScanX_axis_limit,SampleQty)  #get the Thickness reading for the X-axis
        #================================================================================================================#
        amp_gate_lower_limit = 45
        amp_gate_higher_limit = 100
        Xaxis_lower_limit = 26
        Xaxis_higher_limit = 120   
        """Apply gate threshold for both x-axis and amplitude in the ascan"""
        xaxis_index_processed_arr = np.array(np.where((X_axis > Xaxis_lower_limit) & (X_axis < Xaxis_higher_limit)))[0]
        #amp_index_processed_arr = np.array(np.where((AScan_multiply_reading>amp_gate_lower_limit)&(AScan_multiply_reading<amp_gate_higher_limit)))[0]
        amp_index_processed_arr = np.array(np.where(AScan_multiply_reading > amp_gate_lower_limit))
        overlapping_process_index_arr = np.intersect1d(xaxis_index_processed_arr,amp_index_processed_arr)

        X_axis_processed = X_axis[overlapping_process_index_arr]
        amp_axis_processed = AScan_multiply_reading[overlapping_process_index_arr]

        print("~~~~~~~~~~~~~~~~~~~~~~~")
        # result = dict()
        # result['No_of_probe'] = m
        if (X_axis_processed.size != 0 ) and (amp_axis_processed.size != 0):
            the_index = int(((np.where(amp_axis_processed == np.amax(amp_axis_processed)))[0])[0])
            # print(X_axis_processed[the_index])
            # print(amp_axis_processed[the_index])
            # print(m)
            defect_point = [m,X_axis_processed[the_index],amp_axis_processed[the_index]]
            defect_group.append(defect_point)
        else:
            print("This point good")
        print("~~~~~~~~~~~~~~~~~~~~~~~")


    # print(f"amp_gate_lower_limit {amp_gate_lower_limit}")
    # print('[No.Probe, Defect Depth, Max. Amplitude]')
    # print(np.array(defect_group)[:,:])
    # print("get all list")
    defect_group = np.array(defect_group)
    lines_index_list = split_and_process_raw_defect(defect_group)
    # print(lines_index_list)
    line_group = []
    for probe_no_line in lines_index_list:
        probe_no_line = np.array(probe_no_line)
        # print(probe_no_line)
        # indexes_to_keep = np.where(defect_group[:,0] in probe_no_line)
        # print(indexes_to_keep)
        the_line = []
        for n in probe_no_line:
            index_to_keep = np.where(defect_group[:,0] == n)
            # print(index_to_keep)
            # print(defect_group[index_to_keep])
            the_line.append((defect_group[index_to_keep]).tolist()[0])
        # print(np.array(the_line).shape)
        # print(the_line)
        line_group.append(the_line)


    # print("Line Group")
    # print(line_group)
    # print(len(line_group))

    display_defect(line_group)

    return (line_group)

def split_and_process_raw_defect(defect_group):
    import more_itertools as mit
    # thelist = [2, 13, 4, 5, 6, 13, 14, 15, 6, 7, 8]
    thelist = defect_group[:,0]
    grplist = [list(group) for group in mit.consecutive_groups(thelist)]
    # print(grplist)
    return (grplist)




def display_defect (line_group):
    #======================================================================================
    app = pg.mkQApp("GLLinePlotItem Example")
    w = gl.GLViewWidget()
    w.show()
    w.setWindowTitle('pyqtgraph example: GLLinePlotItem')
    # w.setCameraPosition(distance=200)
    w.opts['distance'] = 600
    w.setBackgroundColor((160,160,160,0.1))#set background color
    # grdx = 100
    # grdy = 100
    # grdz = 200
    gx = gl.GLGridItem()
    gx.rotate(90, 0, 1, 0)
    gx.translate(0, 0, 0)
    # gx.setSize(x=10,y=10)
    # w.addItem(gx)
    gy = gl.GLGridItem()
    gy.rotate(90, 1, 0, 0)
    # gy.setSize( x = 10 , y = 100)
    gy.translate(0, 0, 0)
    # w.addItem(gy)
    gz = gl.GLGridItem()
    gz.translate(0, 0, 0)
    # gz.setSize(x = 25 , y= 25)
    # w.addItem(gz)
    """
    """
    verts = np.array([\
        [-50, -50, 0],
        [+50, -50, 0],
        [+50, +50, 0],
        [-50, +50, 0],
        [-50, -50, +1],
        [+50, -50, +1],
        [+50, +50, +1],
        [-50, +50, +1]])
    # Define the 12 triangles composing the cube
    faces = np.array([\
        [0,3,1],
        [1,3,2],
        [0,4,7],
        [0,7,3],
        [4,5,6],
        [4,6,7],
        [5,1,2],
        [5,2,6],
        [2,3,6],
        [3,7,6],
        [0,1,5],
        [0,5,4]])
    colors = np.array([\
        [1, 0, 0, 0.1],
        [1, 0, 0, 0.1],
        [1, 0, 0, 0.1],
        [1, 0, 0, 0.1],
        [1, 0, 0, 0.1],
        [1, 0, 0, 0.1],
        [1, 0, 0, 0.1],
        [1, 0, 0, 0.1],
        [1, 0, 0, 0.1],
        [1, 0, 0, 0.1],
        [1, 0, 0, 0.1],
        [1, 0, 0, 0.1]
    ])
    m1 = gl.GLMeshItem(vertexes=verts, faces=faces, faceColors=colors,smooth=False)
    # m1.translate(5, 5, 0)
    m1.setGLOptions('opaque')
    w.addItem(m1)
    #############################################################
    radius = 35*0.5 # mm
    header_length = 22
    header_radius = 60*0.5
    total_length = 227
    height = total_length - header_length  # mm
    probe_count = 64
    rad_each = 360 / probe_count
    stuff = line_group
    #=========================Cylinder model =================================================
    md = gl.MeshData.cylinder(rows=2, cols=20, radius=[radius, radius], length=height,offset=True)
    # md._vertexes[:, 2] = md._vertexes[:, 2] - 10  
    #########################################
    ## set color based on z coordinates
    # color_map = pg.colormap.get("CET-L10")
    color_map = pg.colormap.get("viridis")
    h = md.vertexes()[:, 2]
    print('~~~~~~~~~~~~~~~~~~~~~~~~~====================================')
    print(h *0)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~====================================')
    # remember these
    h = (h) * 0 + 0.2
    colors = color_map.map(h, mode="float")
    md.setFaceColors(colors)    
    #########################################
    m = gl.GLMeshItem(meshdata=md,smooth=True)
    # m.setColor((125,5,5,1))
    w.addItem(m)
    # =========================================================================================
    # mdd = gl.MeshData.cylinder(rows=20, cols=20, radius=[header_radius, header_radius], length=header_length)
    # mdd._vertexes[:, 2] = mdd._vertexes[:, 2] + height  
    # #########################################
    # ## set color based on z coordinates
    # # color_map = pg.colormap.get("CET-L10")
    # color_map = pg.colormap.get("viridis")
    # hh = mdd.vertexes()[:, 2]
    # # remember these
    # hh_max, hh_min = hh.max(), hh.min()
    # hh = (hh - hh_min) / (hh_max - hh_min) * 0 + 0.1
    # colorsss = color_map.map(hh, mode="float")
    # mdd.setFaceColors(colorsss)    
    # mm = gl.GLMeshItem(meshdata=mdd, smooth=True)
    # w.addItem(mm)
    #########################################
    r = header_radius

    h_vert = np.array([\
        [r*np.cos(2 * np.pi * 1 / 6), r * np.sin(2 * np.pi * 1 / 6), header_length + height],
        [r*np.cos(2 * np.pi * 2 / 6), r * np.sin(2 * np.pi * 2 / 6), header_length + height],
        [r*np.cos(2 * np.pi * 3 / 6), r * np.sin(2 * np.pi * 3 / 6), header_length + height],
        [r*np.cos(2 * np.pi * 4 / 6), r * np.sin(2 * np.pi * 4 / 6), header_length + height],
        [r*np.cos(2 * np.pi * 5 / 6), r * np.sin(2 * np.pi * 5 / 6), header_length + height],
        [r*np.cos(2 * np.pi * 6 / 6), r * np.sin(2 * np.pi * 6 / 6), header_length + height],
        [r*np.cos(2 * np.pi * 1 / 6), r * np.sin(2 * np.pi * 1 / 6), 0 + height],
        [r*np.cos(2 * np.pi * 2 / 6), r * np.sin(2 * np.pi * 2 / 6), 0 + height],
        [r*np.cos(2 * np.pi * 3 / 6), r * np.sin(2 * np.pi * 3 / 6), 0 + height],
        [r*np.cos(2 * np.pi * 4 / 6), r * np.sin(2 * np.pi * 4 / 6), 0 + height],
        [r*np.cos(2 * np.pi * 5 / 6), r * np.sin(2 * np.pi * 5 / 6), 0 + height],
        [r*np.cos(2 * np.pi * 6 / 6), r * np.sin(2 * np.pi * 6 / 6), 0 + height],
    ])
    print(h_vert)

    h_face = np.array([\
        [0,1,6],[1,7,6],
        [1,2,7],[2,8,7],
        [2,3,8],[3,8,9],
        [3,9,10],[3,10,4],
        [4,10,11],[4,11,5],
        [5,11,6],[5,6,0],
        [0,1,2],[0,2,3],[0,3,4],[0,4,5],
        [6,7,8],[6,8,9],[6,9,10],[6,10,11]
        ])
    h_colors = np.array([
        [1, 1, 0, 0.1],[1, 1, 0, 0.1],
        [1, 1, 0, 0.1],[1, 1, 0, 0.1],
        [1, 1, 0, 0.1],[1, 1, 0, 0.1],
        [1, 1, 0, 0.1],[1, 1, 0, 0.1],
        [1, 1, 0, 0.1],[1, 1, 0, 0.1],
        [1, 1, 0, 0.1],[1, 1, 0, 0.1],
        [1, 1, 0, 0.1],[1, 1, 0, 0.1],[1, 1, 0, 0.1],[1, 1, 0, 0.1],
        [1, 1, 0, 0.1],[1, 1, 0, 0.1],[1, 1, 0, 0.1],[1, 1, 0, 0.1]
    ])
    
    hh_color = []
    for i in range(len(h_face)):
        hh_color.append(colors[0])
    hh_color = np.array(hh_color)


    meshdd = gl.MeshData(vertexes= h_vert,faces = h_face, faceColors = hh_color)
    m1 = gl.GLMeshItem(meshdata= meshdd,smooth = False)
    # m1 = gl.GLMeshItem(vertexes = h_vert, faces=h_face, faceColors = h_colors, smooth=True)
    m1.setGLOptions('opaque')
    w.addItem(m1)

    for line in stuff:
        eachline = []        
        for polar_point in line:
            theta = rad_each * math.pi / 180 * int(polar_point[0]) 
            x = radius * math.cos(theta)
            y = radius * math.sin(theta)
            z = total_length - polar_point[1]
            the_amp = polar_point[2]

            eachline.append([x,y,z,the_amp])
        print(eachline)
        print("~~~???~~~")
        eachline = np.array(eachline)
        pltt = gl.GLLinePlotItem(pos=eachline[:,:-1], color='red', width=3, antialias=True,mode= "line_strip")
        # pltt = gl.GLLinePlotItem(pos=eachline, olor='yellow', width=1, antialias=True,mode= "line_strip")

        w.addItem(pltt)
        # print(line)




if __name__ == '__main__':
    
    target_address = f"{current_path}\\bolt_5_7.odat"
    get_defect(target_address)
    pg.exec()
    print("EndEndEndEndEndEndEndEndEndEndEndEndEndEndEndEndEndEnd")

