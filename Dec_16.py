#coding:utf-8
# 导入必要的模块
import clr
import ctypes
from tkinter.constants import W
import matplotlib
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
        self.resize(800, 659)
        # 添加菜单中的按钮
        # self.menu = QtWidgets.QMenu("绘图")
        # self.menu_action = QtWidgets.QAction("绘制",self.menu)
        # self.menu.addAction(self.menu_action)
        # self.menuBar().addMenu(self.menu)
        
        self.menu2 = QtWidgets.QMenu("Files")
        # self.menu_action2 = QtWidgets.QAction("Import Files...",self.menu2)
        # self.menu2.addAction(self.menu_action2)
        # self.menuBar().addMenu(self.menu2)

        self.menu_action3 = QtWidgets.QAction("Import Olympus...",self.menu2)
        self.menu2.addAction(self.menu_action3)
        self.menuBar().addMenu(self.menu2)
        # 添加事件
        # self.menu_action.triggered.connect(self.plot_)
        # self.menu_action2.triggered.connect(self.plot_2)
        self.menu_action3.triggered.connect(self.on_openFileNameDialog)
        
        self.setCentralWidget(QtWidgets.QWidget())
    
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
            print('yes')
            self.OpenView_proress_and_collect_data()
            self.make_plot_()
      return self.fpdfilename

    def OpenView_proress_and_collect_data(self):

        Utilities.ResolveDependenciesPath()
        datafile = StorageSWIG.OpenDataFile(self.fpdfilename)
        data = datafile.GetData()
        C_BufferKeys = data.GetCscanBufferKeys()
        A_BufferKeys = data.GetAscanBufferKeys()
        key = A_BufferKeys.GetBufferKey(0)  
        AScanBuffer = data.GetAscanBuffer(key) #Obtain AScan
        A_Descriptor = AScanBuffer.GetDescriptor()
        AmplitudeAxis = A_Descriptor.GetAmplitudeAxis()
        Velocity = A_Descriptor.GetUltrasoundVelocity() * (1.0e3)  #Convert to mm/s
        CKey = C_BufferKeys.GetBufferKey(1) #Gate A  
        CScanBuffer = data.GetCscanBuffer(CKey) #Obtain CScan
        self.df = pd.DataFrame()

        if CScanBuffer.GetScanCellQuantity() == AScanBuffer.GetScanCellQuantity() and CScanBuffer.GetIndexCellQuantity() == AScanBuffer.GetIndexCellQuantity():
            print("yes")
            ScanQty = CScanBuffer.GetScanCellQuantity()   #Find the Scan Qty (length)
            IndexQty = CScanBuffer.GetIndexCellQuantity() #Find the index Qty (width)
            ScanQty_resol = CScanBuffer.GetDescriptor().GetScanAxis().GetResolution() #Obtain each axes's resolution
            IndexQty_resol = CScanBuffer.GetDescriptor().GetIndexAxis().GetResolution()
            for j in range(ScanQty):
                    for k in range(IndexQty):
                        CRead = CScanBuffer.Read(j,k)
                        raw_position = CRead.GetPosition()
                        distance = (raw_position * 1.0e-9) * Velocity
                        raw_amplitude = CRead.GetAmplitude()
                        temp_df = pd.DataFrame()
                        temp_dict = {"X":[j*ScanQty_resol],'Y':[k*IndexQty_resol],"Position": [distance], "Amplitude":[raw_amplitude]}
                        temp_df = temp_df.from_dict(temp_dict)
                        self.df = self.df.append(temp_df,ignore_index=True)
            print("Dataframe created")
        return (self.df)
            


    def OpenView_data(self):
        threshold = 0 # in percent %
        if self.df.empty:
            print('WTF')
        else:

            condition = self.df['Position']  > (0.01 * threshold * self.df["Position"].max())
            self.df_filter = self.df[condition]

            df_X = self.df_filter["X"].values.tolist()
            df_Y = self.df_filter['Y'].values.tolist()
            df_Position = self.df_filter['Position'].values.tolist()
            df_Amplitude = self.df_filter['Amplitude'].values.tolist()

            self.coordiante_numpy = (self.df_filter.drop(['Amplitude'],axis=1)).to_numpy()
        return self.coordiante_numpy , self.df_filter
        
    


    
    # 绘图方法
    def make_plot_(self):
        
        self.w = gl.GLViewWidget()
        self.w.opts['distance'] = 500
        self.w.setBackgroundColor((5,5,5,1))#set background color

        #~~~~~~~~~~~~~~~~~~~~~~~~#
        XX = np.array(self.df_filter["X"].values.tolist())
        YY = np.array(self.df_filter['Y'].values.tolist())
        ZZ = np.array(self.df_filter['Position'].values.tolist())
        #~~~~~~~~~~~~~~~~~~~~~~~~#
        grdx = 350
        grdy = 150
        grdz = 75
        grid1 = gl.GLGridItem()
        grid1.setSize(x=grdx,y=grdy)
        grid1.setSpacing(x=10, y=10)
        grid1.translate(dx = 0.5 * grdx, dy= 0.5*grdy, dz=0)
        # grid1.setColor((0,255,0,255))
        self.w.addItem(grid1)

        grid2 = gl.GLGridItem()
        grid2.setSize(x= grdx, y= grdy)
        grid2.setSpacing(x=10,y=10)
        grid2.rotate(90,1,0,0)
        grid2.translate(dx= 0.5 * grdx, dy=0, dz = 0.5 * grdy)
        # grid2.setColor((0,255,255,255))
        self.w.addItem(grid2)

        grid3 = gl.GLGridItem()
        grid3.setSize(x= grdy, y= grdy, z=0)
        grid3.setSpacing(x=10,y=10)
        grid3.rotate(90,0,1,0)
        grid3.translate(dx=0, dy = 0.5*grdy, dz =  0.5*grdy)
        self.w.addItem(grid3)

        fposs = np.array(self.coordiante_numpy)
        print(fposs)
        viridis = cm.get_cmap('brg',64)
        #['viridis', 'plasma', 'inferno', 'magma', 'cividis','gist_ncar']
        pinglv =[]
        pinglv = np.array(self.df_filter['Amplitude'].values.tolist())/np.array(self.df_filter['Amplitude'].values.tolist()).max()
        yanse_new = viridis(pinglv)
        size = []
        for s in self.coordiante_numpy:
            size.append(1.5)
        size= np.array(size)
        col = yanse_new
        sp1 = gl.GLScatterPlotItem(pos=fposs, size=size, color=col, pxMode=False)
        self.w.addItem(sp1)
        self.setCentralWidget(self.w)


        print("~End~"*10)

        









if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = My_Main_window()
    main_window.show()
    app.exec()
