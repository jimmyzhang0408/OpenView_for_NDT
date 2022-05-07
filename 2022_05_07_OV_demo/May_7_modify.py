#coding:utf-8
# 导入必要的模块
from inspect import formatargvalues
import clr
import ctypes
from tkinter.constants import BOTTOM, TRUE, W
import matplotlib
from pyqtgraph.functions import colorDistance
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtCore, QtWidgets,QtGui
import matplotlib.pyplot as plt
import sys,math
import pyqtgraph.opengl as gl
import csv,json,os
import pandas as pd
from pyqtgraph.Qt import QtCore,QtGui
import pyqtgraph as pg
from pandas._config.config import describe_option
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


clr.FindAssembly("OlympusNDT.Storage.NET.dll")
clr.AddReference('OlympusNDT.Storage.NET')
from OlympusNDT.Storage.NET import IAscanData,IReadOnlyAscanBuffer,ICscanData,StorageSWIG,Utilities



class My_Main_window(QtWidgets.QMainWindow):

    def __init__(self,parent=None):
        super(My_Main_window,self).__init__(parent)
        # 重新调整大小
        self.resize(1440, 810)
        # 添加菜单中的按钮        
        self.menu2 = QtWidgets.QMenu("Import Files")
 
        self.menu_action3 = QtWidgets.QAction("Corrosion...",self.menu2)
        self.menu_action4 = QtWidgets.QAction("Bolt defect...",self.menu2)

        self.menu2.addAction(self.menu_action3)
        self.menu2.addAction(self.menu_action4)
        self.menuBar().addMenu(self.menu2)

        # 添加事件
        self.menu_action3.triggered.connect(self.on_openFileNameDialog)
        self.menu_action4.triggered.connect(self.on_openFileNameDialog2)     
        self.setCentralWidget(QtWidgets.QWidget())

        

        self.result_info_window = QTextEdit()
        self.result_info_window.setWordWrapMode(QTextOption.WordWrap)
        self.result_info_window.setFontPointSize(10)
        self.result_info_window.setMinimumHeight(50)
        self.result_info_window.setMinimumWidth(210)
        self.result_info_window.setMaximumWidth(270)


        self.make_plot_button = QPushButton('PLOT')
        self.apply_gate_button = QPushButton("Apply Gate")
        self.reset_gate_button = QPushButton('Load/Reset Default')
        #============================================================#


        #============================================================#       
        self.w = gl.GLViewWidget()
        self.data_layout = QHBoxLayout()
        # self.data_layout.addWidget(self.result_info_window)
        self.data_layout.addWidget(self.w)
        #============================================================#
        self.info_layout = QVBoxLayout()
        self.info_layout.addWidget(self.result_info_window)
        self.info_layout.addWidget(self.apply_gate_button)
        self.info_layout.addWidget(self.reset_gate_button)
        self.info_layout.addWidget(self.make_plot_button)
        





        #============================================================#
        #Put them together

        
        #max_log_length = 250
        hbox = QHBoxLayout()    

        hbox.addLayout(self.info_layout)
        hbox.addLayout(self.data_layout)


        self.main_frame = QWidget()
        self.main_frame.setLayout(hbox)

        self.setCentralWidget(self.main_frame)
        #============================================================#
        #Connect pushbutton or other stuff

        # self.make_plot_button.clicked.connect(self.plot_3)
        self.make_plot_button.clicked.connect(self.make_plot)

        # self.make_plot_button.clicked.connect(self.display_defect)
        self.apply_gate_button.clicked.connect(self.apply_gate)
        self.reset_gate_button.clicked.connect(self.reset_gate)

        
    def on_openFileNameDialog(self):
      options = QFileDialog.Options()
      options |= QFileDialog.DontUseNativeDialog
      fileName, _ = QFileDialog.getOpenFileName(self,"OpenFileName()","","fpd Files (*fpd);;odat Files (*.odat)", options=options)
      if fileName:
            print(fileName)
            self.fpdfilename = fileName
            self.loading_file_type = 'Corrosion'
            message = f'Scan File Opened:  {fileName.split("/")[-1]}'
            self.result_info_window.append(fileName)
            self.result_info_window.append(message)



    def on_openFileNameDialog2(self):
      options = QFileDialog.Options()
      options |= QFileDialog.DontUseNativeDialog
      fileName, _ = QFileDialog.getOpenFileName(self,"OpenFileName()","","odat Files (bolt*odat)", options=options)
      if fileName:
            print(fileName)
            self.fpdfilename = fileName
            self.loading_file_type = 'Bolt'
            message = f'Bolt file Opened:  {fileName.split("/")[-1]}'
            self.result_info_window.append(fileName)
            self.result_info_window.append(message)

    def OpenView_bolt(self):
        Utilities.ResolveDependenciesPath()
        datafile = StorageSWIG.OpenDataFile(self.fpdfilename)
        data = datafile.GetData()
        # if self.loaded_statud == 'Bolt':
        datafile = StorageSWIG.OpenDataFile(self.fpdfilename)
        data = datafile.GetData()
        defect_group = []
        A_BufferKeys = data.GetAscanBufferKeys()
        m = 0
        for m in range(A_BufferKeys.GetCount()):
        # for m in range(1):
            key = A_BufferKeys.GetBufferKey(m)  
            AScanBuffer = data.GetAscanBuffer(key)
            A_Descriptor = AScanBuffer.GetDescriptor()
            print(f"DataType? : {AScanBuffer.GetDataType()}")    #Turns out to be USHORT

            Velocity = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetVelocity()
            Velocity = Velocity * 1e3  #Convert to mm/s
            Current_gain = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetGain()
            AScanCompressionFactor = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetDigitizingSettings().GetTimeSettings().GetAscanCompressionFactor()
            AscanSamplingResolution = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetDigitizingSettings().GetTimeSettings().GetAscanSamplingResolution()
            Velocity_in_mm_per_ns = Velocity * 1e-9
            AmplitudeAxis = A_Descriptor.GetAmplitudeAxis()
            AmplitudeSamplingAxis = A_Descriptor.GetAmplitudeSamplingAxis()
            SampleQty = AScanBuffer.GetSampleQuantity()
            IndxQty = AScanBuffer.GetIndexCellQuantity()
            ScnQty = AScanBuffer.GetScanCellQuantity()
            IndxQty_Resol = A_Descriptor.GetIndexAxis().GetResolution()
            ScnQty_Resol = A_Descriptor.GetScanAxis().GetResolution()
            AScanX_axis_limit = Velocity_in_mm_per_ns * AscanSamplingResolution * SampleQty * 0.5
            j = 0
            k = 0
            ARead = AScanBuffer.Read(j,k)
            ascan_ptr = ARead.GetData()
            newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_ushort))
            DataBytes = ()
            DataBytes = np.ctypeslib.as_array(newpnt,(SampleQty,)) #Raw Amplitude array (unit in samplings)
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
            if (X_axis_processed.size != 0 ) and (amp_axis_processed.size != 0):
                the_index = int(((np.where(amp_axis_processed == np.amax(amp_axis_processed)))[0])[0])

                defect_point = [m,X_axis_processed[the_index],amp_axis_processed[the_index]]
                defect_group.append(defect_point)
            else:
                print("This point good")
        defect_group = np.array(defect_group)
        lines_index_list = self.split_and_process_raw_defect(defect_group)
        self.line_group = []
        for probe_no_line in lines_index_list:
            probe_no_line = np.array(probe_no_line)
            the_line = []
            for n in probe_no_line:
                index_to_keep = np.where(defect_group[:,0] == n)
                the_line.append((defect_group[index_to_keep]).tolist()[0])
            self.line_group.append(the_line)
        self.result_info_window.append("Bolt Dataframe loaded")

    def split_and_process_raw_defect(self,defect_group):
        import more_itertools as mit
        thelist = defect_group[:,0]
        grplist = [list(group) for group in mit.consecutive_groups(thelist)]
        print(grplist)
        return (grplist)




    def OpenView_data(self):
        print("load")
        Utilities.ResolveDependenciesPath()
        datafile = StorageSWIG.OpenDataFile(self.fpdfilename)
        data = datafile.GetData()
        if self.loading_file_type == 'Corrosion':
            self.thickness_setup = float(datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetThickness())
            self.Length_setup = datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetLength()
            self.width_setup = datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetWidth()
            # #============================================#
            A_BufferKeys = data.GetAscanBufferKeys()
            m = 0
            key = A_BufferKeys.GetBufferKey(m)  
            AScanBuffer = data.GetAscanBuffer(key)
            A_Descriptor = AScanBuffer.GetDescriptor()
            Velocity = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetVelocity()
            Velocity = Velocity * 1e3  #Convert to mm/s
            Current_gain = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetGain()
            AScanCompressionFactor = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetDigitizingSettings().GetTimeSettings().GetAscanCompressionFactor()
            AscanSamplingResolution = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetDigitizingSettings().GetTimeSettings().GetAscanSamplingResolution()
            Velocity_in_mm_per_ns = Velocity * 1e-9
            AmplitudeAxis = A_Descriptor.GetAmplitudeAxis()
            AmplitudeSamplingAxis = A_Descriptor.GetAmplitudeSamplingAxis()
            SampleQty = AScanBuffer.GetSampleQuantity()
            IndxQty = AScanBuffer.GetIndexCellQuantity()
            ScnQty = AScanBuffer.GetScanCellQuantity()
            IndxQty_Resol = A_Descriptor.GetIndexAxis().GetResolution()
            ScnQty_Resol = A_Descriptor.GetScanAxis().GetResolution()
            AScanX_axis_limit = Velocity_in_mm_per_ns * AscanSamplingResolution * SampleQty * 0.5
            self.X,self.Y,self.D,self.A = [],[],[],[]
            # if self.gate_apply_status == False:
            #     self.threshold = 20
            # elif self.gate_apply_status == True:
            #     self.threshold = 90
            # else:
            #     self.result_info_window.append("Uncessful")
            for j in range(ScnQty):
                for k in range(IndxQty):
                    ARead = AScanBuffer.Read(j,k)
                    ascan_ptr = ARead.GetData()
                    location_index = [j,k]
                    actual_coordinate = [location_index[0]*ScnQty_Resol,location_index[1]*IndxQty_Resol]
                    try:
                        if self.fpdfilename.split(".")[1] == 'fpd':
                            newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_ubyte))
                        elif  self.fpdfilename.split(".")[1] == 'odat':
                            newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_ushort))
                        DataBytes = ()
                        DataBytes = np.ctypeslib.as_array(newpnt,(SampleQty,)) #Raw Amplitude array (unit in samplings)
                        errormessage = False
                    except:
                        errormessage = True
                    
                    if errormessage == False:
                        #========================Get the raw amplitude and thickness X-axis reading======================================#
                        AScan_multiply_reading = DataBytes * np.array([float(AmplitudeAxis.GetResolution())])   #Convert to percent
                        self.AScan_multiply_reading = DataBytes * np.array([float(AmplitudeAxis.GetResolution())])   #Convert to percent
                        self.X_axis = np.linspace(0,AScanX_axis_limit,SampleQty)  #get the Thickness reading for the X-axis
                        X_axis = np.linspace(0,AScanX_axis_limit,SampleQty)  #get the Thickness reading for the X-axis
                        #===================================================================================#
                        """Process the array with the given gate"""
                        """Apply gate threshold for both x-axis and amplitude in the ascan"""
                        """Defaul gate setting up below"""
                        amp_gate_lower_limit = self.threshold
                        Xaxis_lower_limit = self.X_axis_threshold

                        xaxis_index_processed_arr = np.array(np.where(X_axis > Xaxis_lower_limit))[0]
                        amp_index_processed_arr = np.array(np.where(AScan_multiply_reading > amp_gate_lower_limit))[0]
                        overlapping_process_index_arr = np.intersect1d(xaxis_index_processed_arr,amp_index_processed_arr)

                        X_axis_processed = X_axis[overlapping_process_index_arr]
                        amp_axis_processed = AScan_multiply_reading[overlapping_process_index_arr]

                        if (X_axis_processed.size != 0 ) and (amp_axis_processed.size != 0):
                            the_index = int(((np.where(amp_axis_processed == np.amax(amp_axis_processed)))[0])[0])
                            self.D.append(X_axis_processed[the_index])
                            self.A.append(amp_axis_processed[the_index])
                            self.X.append(actual_coordinate[0])
                            self.Y.append(actual_coordinate[1])
            self.result_info_window.append("File Dataframe loaded")
            self.loaded_statud = True  # Can used as a pointer to disable the plot button during loading or before loading
            self.X = np.array(self.X)
            self.Y = np.array(self.Y)
            self.A = np.array(self.A)
            self.D = np.array(self.D)
            return (self.D,self.A,self.X,self.Y)



    def apply_gate(self):
        print("lol")
        # self.gate_apply_status = True
        if self.loading_file_type == 'Corrosion':
            self.threshold = 90
            self.X_axis_threshold = 5
            self.OpenView_data()


    def reset_gate(self):
        # self.gate_apply_status = False
        self.threshold = 20
        print("application type:", self.loading_file_type)
        if self.loading_file_type == 'Corrosion':
            if self.fpdfilename.split('.')[1] == 'fpd':
                self.X_axis_threshold = 3
            else:
                self.X_axis_threshold = 2
            self.OpenView_data()
                    
        elif self.loading_file_type == 'Bolt':
            self.OpenView_bolt()

    def make_plot(self):
        if self.loading_file_type == "Corrosion":
            self.w.clear()
            self.plot_3()
        elif self.loading_file_type == 'Bolt':
            self.w.clear()
            self.display_defect()


    def display_defect(self):
        self.w.clear()
        self.w.opts['distance'] = 800
        self.w.setBackgroundColor((160,160,160,0.1))#set background color
        # ==========================================================================
        # making a base
        verts = np.array([\
            [-50, -50, 0],
            [+50, -50, 0],
            [+50, +50, 0],
            [-50, +50, 0],
            [-50, -50, +1],
            [+50, -50, +1],
            [+50, +50, +1],
            [-50, +50, +1]])
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
        self.w.addItem(m1)
        #############################################################
        radius = 35*0.5 # mm
        header_length = 22
        header_radius = 60*0.5
        total_length = 227
        height = total_length - header_length  # mm
        probe_count = 64
        rad_each = 360 / probe_count
        stuff = self.line_group
        #=========================Cylinder model =================================================
        md = gl.MeshData.cylinder(rows=2, cols=20, radius=[radius, radius], length=height,offset=True)
        # md._vertexes[:, 2] = md._vertexes[:, 2] - 10  
        #########################################
        ## set color based on z coordinates
        # color_map = pg.colormap.get("CET-L10")
        # color_map = pg.colormap.get("viridis")
        h = md.vertexes()[:, 2]

        h = (h) * 0 + 0.2
        viridis = cm.get_cmap('viridis',256)
        colors = viridis(h)
        # colors = color_map.map(h, mode="float")
        md.setFaceColors(colors)    
        #########################################
        m = gl.GLMeshItem(meshdata=md,smooth=True)
        # m.setColor((125,5,5,1))
        self.w.addItem(m)
        
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
        # print(h_vert)

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
        self.w.addItem(m1)
        # ==========================================================================
        if len(self.line_group) > 0:
            for line in stuff:
                eachline = []        
                for polar_point in line:
                    theta = rad_each * math.pi / 180 * int(polar_point[0]) 
                    x = radius * math.cos(theta)
                    y = radius * math.sin(theta)
                    z = total_length - polar_point[1]
                    the_amp = polar_point[2]

                    eachline.append([x,y,z,the_amp])
                # print(eachline)
                # print("~~~???~~~")
                eachline = np.array(eachline)
                pltt = gl.GLLinePlotItem(pos=eachline[:,:-1], color='red', width=3, antialias=True,mode= "line_strip")
                # pltt = gl.GLLinePlotItem(pos=eachline, olor='yellow', width=1, antialias=True,mode= "line_strip")

                self.w.addItem(pltt)
        pass    

    def plot_3(self):
        fposs = np.stack((self.X, self.Y,self.D), axis=-1)
        pinglv = self.A / self.A.max()       
        self.w.clear()
        self.w.opts['distance'] = 500
        self.w.setBackgroundColor((5,5,5,1))#set background color
        viridis = cm.get_cmap('hsv',256)
        #['viridis', 'plasma', 'inferno', 'magma', 'cividis','gist_ncar']
        yanse_new = viridis(pinglv)
        size = []
        for s in range(len(pinglv)):
            size.append(1)
        size= np.array(size)
        print('~~~~~'*10)
        print(fposs.shape)
        print(pinglv.shape)
        print(size.shape)
        print('~~~~~'*10)
        sp1 = gl.GLScatterPlotItem(pos=fposs, size=size, color=yanse_new, pxMode=False)
        self.w.addItem(sp1)

        if self.Length_setup > self.width_setup:
            grdx = int(self.Length_setup/100)*100+50
            grdy = int(self.width_setup/100)*100+50
            # grdz = 50
        
        elif self.Length_setup < self.width_setup:
            grdx = int(self.width_setup/100)*100+50
            grdy = int(self.Length_setup/100)*100+50
            # grdz = 50
        
        else:
            self.result_info_window.append("LMAO")
            grdx = 350
            grdy = 150
        
        # grdz = 50
        if self.thickness_setup > 50:
            if int(self.thickness_setup/100) == 0:
                grdz = self.thickness_setup
            elif self.thickness_setup > 100:
                grdz = int(self.thickness_setup/10) * 10 + 20
        else:
            grdz = 50

        self.result_info_window.append(f'grdx {grdx}\ngrdy {grdy}')

        grid1 = gl.GLGridItem()
        grid1.setSize(x=grdx,y=grdy)
        grid1.setSpacing(x=10, y=10)
        grid1.translate(dx = 0.5 * grdx, dy= 0.5*grdy, dz=0)
        # grid1.setColor((0,255,0,255))
        self.w.addItem(grid1)
        grid2 = gl.GLGridItem()
        grid2.setSize(x= grdx, y= grdz)
        grid2.setSpacing(x=10,y=10)
        grid2.rotate(90,1,0,0)
        grid2.translate(dx= 0.5 * grdx, dy=0, dz = 0.5 * grdz )
        # grid2.setColor((0,255,255,255))
        self.w.addItem(grid2)

        grid3 = gl.GLGridItem()
        grid3.setSize(x= grdz, y= grdy, z=0)
        grid3.setSpacing(x=10,y=10)
        grid3.rotate(90,0,1,0)
        grid3.translate(dx=0, dy = 0.5*grdy, dz =  0.5*grdz)
        self.w.addItem(grid3)
        print("~End~"*10)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = My_Main_window()
    main_window.show()
    app.exec()
