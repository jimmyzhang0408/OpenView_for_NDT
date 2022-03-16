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
import sys
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
        self.menu2 = QtWidgets.QMenu("Files")
 
        self.menu_action3 = QtWidgets.QAction("Import Olympus...",self.menu2)
        self.menu2.addAction(self.menu_action3)
        self.menuBar().addMenu(self.menu2)

        # 添加事件
        self.menu_action3.triggered.connect(self.on_openFileNameDialog)     
        self.setCentralWidget(QtWidgets.QWidget())

        

        self.result_info_window = QTextEdit()
        self.result_info_window.setWordWrapMode(QTextOption.WordWrap)
        self.result_info_window.setFontPointSize(10)
        self.result_info_window.setMinimumHeight(50)
        self.result_info_window.setMinimumWidth(210)
        self.result_info_window.setMaximumWidth(270)


        self.make_plot_button = QPushButton('PLOT')
        self.apply_gate_button = QPushButton("Apply Gate")
        self.reset_gate_button = QPushButton('RESET/Default')
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
        self.make_plot_button.clicked.connect(self.plot_3)
        self.apply_gate_button.clicked.connect(self.apply_gate)
        self.reset_gate_button.clicked.connect(self.reset_gate)




    def on_menu_action3_clicked(self):
        pass
        # self.on_openFileNameDialog
        # self.OpenView_data
        
    def on_openFileNameDialog(self):
      options = QFileDialog.Options()
      options |= QFileDialog.DontUseNativeDialog
      fileName, _ = QFileDialog.getOpenFileName(self,"OpenFileName()","","fpd Files (*fpd);;odat Files (*.odat)", options=options)
      if fileName:
            print(fileName)
            self.fpdfilename = fileName
            message = f'Scan File Opened:  {fileName.split("/")[-1]}'
            self.result_info_window.append(fileName)
            self.result_info_window.append(message)
            # self.OpenView_data()
            # self.plot_3()


    def OpenView_data(self):
        print("load")
        Utilities.ResolveDependenciesPath()
        datafile = StorageSWIG.OpenDataFile(self.fpdfilename)
        data = datafile.GetData()

        self.thickness_setup = float(datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetThickness())
        self.Length_setup = datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetLength()
        self.width_setup = datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetWidth()
        # #============================================#
        A_BufferKeys = data.GetAscanBufferKeys()
        print("======"*25)
        m = 0
        key = A_BufferKeys.GetBufferKey(m)  
        AScanBuffer = data.GetAscanBuffer(key)
        A_Descriptor = AScanBuffer.GetDescriptor()
        # print(f"DataType? : {AScanBuffer.GetDataType()}")    #Turns out to be USHORT

        Velocity = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetVelocity()
        Velocity = Velocity * 1e3  #Convert to mm/s
        print('Velocity is : \n', Velocity , 'mm/s')
        Current_gain = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetGain()
        print(f"Gain is : {Current_gain} dB ")
        AScanCompressionFactor = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetDigitizingSettings().GetTimeSettings().GetAscanCompressionFactor()
        # print(f'AScan Compression Factor is: {AScanCompressionFactor}')
        AscanSamplingResolution = datafile.GetSetup().GetInspectionConfigurations().GetConfiguration(0).GetConfigurations().GetConfiguration(0).GetDigitizingSettings().GetTimeSettings().GetAscanSamplingResolution()
        # print(f'Ascan Sampling Resolution is: {AscanSamplingResolution} ns')
        Velocity_in_mm_per_ns = Velocity * 1e-9
        # print(f'Velocity in mm/ns is: {Velocity_in_mm_per_ns} mm/ns')

        print("====="*10)
        AmplitudeAxis = A_Descriptor.GetAmplitudeAxis()
        # print("Amplitude Axis Max: \n", AmplitudeAxis.GetMax())
        # print("Amplitude Axis Min: \n", AmplitudeAxis.GetMin())
        # print("Amplitude Axis Resolution: \n", AmplitudeAxis.GetResolution())
        # print("Amplitude Axis Unit: \n", AmplitudeAxis.GetUnit())
        # print("Amplitude Axis Data Type: \n", AmplitudeAxis.GetType())

        print("====="*10)
        AmplitudeSamplingAxis = A_Descriptor.GetAmplitudeSamplingAxis()
        # print("Amplitude Sampling Axis Max: \n", AmplitudeSamplingAxis.GetMax())
        # print("Amplitude Sampling Axis Min: \n", AmplitudeSamplingAxis.GetMin())
        # print("Amplitude Sampling Axis Resolution: \n", AmplitudeSamplingAxis.GetResolution())
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

        print(range(10,ScnQty))

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
        print("~~~~~~~~~~~~~~~~~")
        print(len(self.A))
        print(len(self.D))
        print(len(self.X))
        print(len(self.Y))
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
        self.threshold = 90
        self.X_axis_threshold = 5
        self.OpenView_data()


    def reset_gate(self):
        # self.gate_apply_status = False
        self.threshold = 20
        if self.fpdfilename.split('.')[1] == 'fpd':
            self.X_axis_threshold = 5
        else:
            self.X_axis_threshold = 2
        self.OpenView_data()



    def plot_3(self):
        # print(self.A)
        #np.array(list(zip(X, y)))
        # fposs = np.array(list(zip(self.X,self.Y,self.D)))
        # fposs = np.array(zip(self.X,self.Y,self.D))
        fposs = np.stack((self.X, self.Y,self.D), axis=-1)

        # fposs = np.dstack((self.X,self.Y,self.D))
        # pinglv = np.array(self.A)
        pinglv = self.A / self.A.max()
        print(fposs.shape)
        print('checking pinglv')
        print(pinglv)


        
        self.w.clear()
        self.w.opts['distance'] = 500
        self.w.setBackgroundColor((5,5,5,1))#set background color
        viridis = cm.get_cmap('brg',256)
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

        #=============================================================
        # if self.thickness_setup & self.width_setup & self.Length_setup:
        #     print('true')
        # else:
        # #     print("False")

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
        print(self.thickness_setup)
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
