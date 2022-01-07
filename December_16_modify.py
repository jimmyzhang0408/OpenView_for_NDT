#coding:utf-8
# 导入必要的模块
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
        self.reset_gate_button = QPushButton('RESET')
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
        #Oh Fuck I cannot use Bing starting from Dec 16.
        #Shit Shit Shit        
        
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
        self.on_openFileNameDialog
        self.OpenView_data
        
    def on_openFileNameDialog(self):
      options = QFileDialog.Options()
      options |= QFileDialog.DontUseNativeDialog
      fileName, _ = QFileDialog.getOpenFileName(self,"OpenFileName()", "","fpd Files (*.fpd);;odat Files (*.odat)", options=options)
      if fileName:
            print(fileName)
            self.fpdfilename = fileName
            message = f'Scan File Opened:  {fileName.split("/")[-1]}'
            self.result_info_window.append(fileName)
            self.result_info_window.append(message)

            self.OpenView_data()
            # self.plot_3()


    def OpenView_data(self):
        print("load")
        Utilities.ResolveDependenciesPath()
        datafile = StorageSWIG.OpenDataFile(self.fpdfilename)
        data = datafile.GetData()
        self.coordinate = []
        self.overall = []
        self.Amplitude = []


        self.thickness_setup = float(datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetThickness())
        print(f"thickness_setup is {self.thickness_setup}")
        print(dir(datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry()))
        self.Length_setup = datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetLength()
        print(f'Lengh_setup is: {self.Length_setup}')
        self.width_setup = datafile.GetSetup().GetScanPlan().GetSpecimen().GetGeometry().GetWidth()
        print(f'width_setup is {self.width_setup}')


        X =[]
        Y =[]
        
        BufferKeys = data.GetCscanBufferKeys()
        print(BufferKeys.GetCount())
        print("======"*25)
        C_BufferKeys = data.GetCscanBufferKeys()
        A_BufferKeys = data.GetAscanBufferKeys()

        key = A_BufferKeys.GetBufferKey(0)  
        AScanBuffer = data.GetAscanBuffer(key)
        A_Descriptor = AScanBuffer.GetDescriptor()
        AmplitudeAxis = A_Descriptor.GetAmplitudeAxis()
        coefficient_to_amplitude_pct = float(AmplitudeAxis.GetResolution())
        Velocity = A_Descriptor.GetUltrasoundVelocity() * (1.0e3)  #Convert to mm/s
        print('Velocity is : \n', Velocity , 'mm/s')

        try:
            CKey = C_BufferKeys.GetBufferKey(1) #Gate A  
        except:
            CKey = C_BufferKeys.GetBufferKey(0) #Gate A
        CScanBuffer = data.GetCscanBuffer(CKey)

        if CScanBuffer.GetScanCellQuantity() == AScanBuffer.GetScanCellQuantity() and CScanBuffer.GetIndexCellQuantity() == AScanBuffer.GetIndexCellQuantity():
            print("====="*20)
            print("Cscan Scan and Index Qty. == AScan Scan and Index Qty.")
            ScanQty = CScanBuffer.GetScanCellQuantity()
            IndexQty = CScanBuffer.GetIndexCellQuantity()
            print("====="*20)
            ScanQty_resol = CScanBuffer.GetDescriptor().GetScanAxis().GetResolution()
            IndexQty_resol = CScanBuffer.GetDescriptor().GetIndexAxis().GetResolution()

        for j in range(ScanQty):
            for k in range(IndexQty):
                CRead = CScanBuffer.Read(j,k)
                raw_position = CRead.GetPosition()
                distance = (raw_position * 1.0e-9) * Velocity
                thickness = distance / 2
                raw_amplitude = CRead.GetAmplitude()
                amplitude_in_pct = raw_amplitude * coefficient_to_amplitude_pct
                self.coordinate.append([j*ScanQty_resol,k*IndexQty_resol,thickness])
                self.overall.append([j*ScanQty_resol,k*IndexQty_resol,thickness,raw_amplitude])
                self.Amplitude.append(amplitude_in_pct)
        self.dff=pd.DataFrame(self.overall)
        print(self.dff[2].max())
        print("Show the maximum number above")
        
        self.result_info_window.append(f"Got the origonal dataframe")
        print("Got the origonal dataframe")
        self.coordinate = np.array(self.coordinate)
        self.Amplitude = np.array(self.Amplitude)
        self.gate_position = np.array([])
        self.gate_amplitude = np.array([])

        return self.coordinate, self.Amplitude

    def reset_gate(self):
        self.gate_position = np.array([]) 
        self.gate_amplitude = np.array([])

    def apply_gate(self):
        """
        Then it will be added the gate percentage ONLY later
        gate default number will be set to 0 if no input is added (That is what to be designed)
        """ 
        self.gate_position = 50
        self.gate_amplitude = 50

        if (self.dff).empty:
            print(f'Did not optain the dataframe')
            self.result_info_window.append(f"Did not optain the dataframe")           
        else:
            #==============================================#
            """
            The following section may need to be changed entirely while confiming to co-workers
            to make sure such applies method is accurate or worth trying
            """
            postion_threshold = self.gate_position * 0.01 * self.dff[2].max()
            position_condidtion = self.dff[2] > postion_threshold
            amplitude_threshold = self.gate_amplitude * 0.01 * self.dff[3].max()
            amplitude_condition = self.dff[3] > amplitude_threshold
            #The next line is what the magin happens
            self.dff_filter = self.dff[position_condidtion & amplitude_condition] #Apply threholds and get a new dataframe
            #==============================================#
            self.threshold_coordinate = (self.dff_filter.drop(3,axis=1)).to_numpy()
            self.threshold_pinglv = (self.dff_filter.drop([0,1,2],axis=1)).to_numpy()
            print(self.threshold_coordinate.shape)
            print(self.threshold_pinglv.shape)

        return self.threshold_coordinate, self.threshold_pinglv

    def plot_3(self):
        pinglv = []
        self.result_info_window.append(f'Width is {self.width_setup}')
        self.result_info_window.append(f'Length is {self.Length_setup}')
        self.result_info_window.append(f'Thickness is {self.thickness_setup}')
        #===========================================#
        if np.any(self.gate_position) and np.any(self.gate_amplitude):
            fposs = self.threshold_coordinate
            pinglv = (self.threshold_pinglv)/ (self.threshold_pinglv.max())
            print('With threshold',fposs.shape, "\n")
            print('With threshold',len(pinglv), '\n', type(pinglv))

        else:
            fposs = self.coordinate    
            pinglv = np.array((self.Amplitude) / (self.Amplitude.max()))
            # pinglv = np.array(self.Amplitude)
            print("No threshold",type(fposs))
            print("No threshold",type(pinglv))

        #===========================================#
                
        self.w.clear()
        self.w.opts['distance'] = 500
        self.w.setBackgroundColor((5,5,5,1))#set background color
        viridis = cm.get_cmap('brg',256)
        #['viridis', 'plasma', 'inferno', 'magma', 'cividis','gist_ncar']
        yanse_new = viridis(pinglv)
        size = []
        for s in range(len(fposs)):
            size.append(1)
        size= np.array(size)
        col = yanse_new
        print('~~~~~'*10)
        print(fposs.shape)
        print(pinglv.shape)
        print(size.shape)
        print('~~~~~'*10)
        sp1 = gl.GLScatterPlotItem(pos=fposs, size=size, color=col, pxMode=False)
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
