import math
import pyqtgraph.examples
# pyqtgraph.examples.run()
from matplotlib import cm
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
import pandas as pd
# Create a GL View widget to display data
app = pg.mkQApp("Welding Plate Example")
w = gl.GLViewWidget()
w.show()
w.setWindowTitle('Welding Plate')
w.setCameraPosition(distance=200)

#########################################################################################

#Setting up all the lines for the welding plate
line1_point = np.array([\
    [0,0,-15],[-130,0,-15],[-130,0,0],
    [-15*np.tan(30*np.pi/180),0,0],[0,0,-15],[15*np.tan(30*np.pi/180),0,0],
    [130,0,0],[130,0,-15],[0,0,-15]
    ])
line_face1 = gl.GLLinePlotItem(pos=line1_point, color='red', width=1, antialias=True,mode= "line_strip")
w.addItem(line_face1)

line2_point = np.array([\
    [-15*np.tan(30*np.pi/180),0,0],[-15*np.tan(30*np.pi/180),260,0],
    [0,260,-15],[15*np.tan(30*np.pi/180),260,0],[15*np.tan(30*np.pi/180),0,0]
    ])
line_face2 = gl.GLLinePlotItem(pos=line2_point, color='red', width=1, antialias=True,mode= "line_strip")
w.addItem(line_face2)

line3 = np.array([[0,0,-15],[0,260,-15]])
line_3 = gl.GLLinePlotItem(pos=line3, color='red', width=1, antialias=True,mode= "line_strip")
w.addItem(line_3)

line4_point = np.array([\
    [130,0,-15],[130,0,0],[130,260,0],[130,260,-15],[130,0,-15]
    ])
line_face4 = gl.GLLinePlotItem(pos=line4_point, color='red', width=1, antialias=True,mode= "line_strip")
w.addItem(line_face4)

line5_point = np.array([\
    [-130,0,-15],[-130,0,0],[-130,260,0],[-130,260,-15],[-130,0,-15]
    ])
line_face5= gl.GLLinePlotItem(pos=line5_point, color='red', width=1, antialias=True,mode= "line_strip")
w.addItem(line_face5)

line6_point = np.array([\
    [0,260,-15],[-130,260,-15],[-130,260,0],
    [-15*np.tan(30*np.pi/180),260,0],[0,260,-15],[15*np.tan(30*np.pi/180),260,0],
    [130,260,0],[130,260,-15],[0,260,-15]
    ])
line_face6 = gl.GLLinePlotItem(pos=line6_point, color='red', width=1, antialias=True,mode= "line_strip")
w.addItem(line_face6)

welding_radius = 15 / (np.cos(30 * np.pi /180))
fan_shape_front = []
fan_shape_back = []
for i in range(60,121,1):
    fan_shape_front.append([welding_radius*np.cos(i * np.pi /180),0,welding_radius * np.sin(i * np.pi / 180)-15])
    fan_shape_back.append([welding_radius*np.cos(i * np.pi /180),260,welding_radius * np.sin(i * np.pi / 180)-15])
fan_shape_front = np.array(fan_shape_front)
fan_shape_back = np.array(fan_shape_back)
fan_line_1 = gl.GLLinePlotItem(pos = fan_shape_front,color = 'green',width = 1,antialias=True,mode= "line_strip")
fan_line_2 = gl.GLLinePlotItem(pos = fan_shape_back,color = 'green',width = 1,antialias=True,mode= "line_strip")
w.addItem(fan_line_1)
w.addItem(fan_line_2)




with open('defects_group_find_peaks_Aug1.csv','r') as readfile:
    f= pd.read_csv(readfile,header=None)
f.columns=['x(mm)','scan(mm)','depth(mm)','amplitude(%)','beam_angle(°)','Lower Limit','Higher Limit',"Ascan Defect",'L']
filtered = f.loc[(f['amplitude(%)']>35)]
print(filtered)

X = np.array(filtered['x(mm)'].to_list())
Y = np.array(filtered['scan(mm)'].to_list())
D = np.array(filtered['depth(mm)'].to_list())
A = np.array(filtered['amplitude(%)'].to_list())

fposs = np.stack((X,Y,D), axis=-1)
pinglv = A / 300       
# w.clear()
w.opts['distance'] = 600
# w.setBackgroundColor((5,5,5,1))#set background color
viridis = cm.get_cmap('hsv',512)
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
w.addItem(sp1)



if __name__ == '__main__':
    pg.exec()
