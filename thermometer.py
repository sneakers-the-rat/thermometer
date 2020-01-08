import numpy as np
import sys
import pdb
from datetime import datetime
import time
from collections import deque
from itertools import islice


from PySide2 import QtCore, QtGui, QtWidgets

# import the whole module so pyqtgraph catches it
import PySide2
import pyqtgraph as pg
from pyqtgraph.graphicsItems.GradientEditorItem import Gradients
import MLX90640 as cam
import threading
from scipy.interpolate import griddata
from itertools import product


class Thermometer(QtWidgets.QMainWindow):
    """
    Window that
        * displays output from a mlx90640 sensor
        * lets you select an ROI and threshold to measure from
        * gives a history and numerical readout of temp
    """

    def __init__(self, fps=64, display_average=10, read_average=100,interp=3):
        super(Thermometer, self).__init__()
        self.frame = None
        self.fps = fps
        self.capture_thread = None
        self.display_average = display_average
        self.read_average = read_average
        
        # store the past n frames in a 3d array
        
        self.frames = np.zeros((32,24,self.display_average))
        
        self.grid_y, self.grid_x = np.meshgrid(np.linspace(0,24,24*interp),
                                            np.linspace(0,32,32*interp))
        self.points = list(product(range(32),range(24)))
        
        self.frame_idx = 0

        self.init_ui()
        self.init_sensor()
        self.main()

    def main(self):
        try:
            #pdb.set_trace()

            #pdb.set_trace()

            
            self.frame = np.mean(self.frames, axis=2)
            interp = griddata(self.points, self.frame.flatten(), (self.grid_x, self.grid_y), method='cubic')
            self.img.setImage(interp)
            
            # draw history
            if len(self.img.history)>0:
                
                self.plot_curve.setData(self.img.timestamps, self.img.history)
                self.plot.setXRange(min(self.img.timestamps), max(self.img.timestamps))
                    #self.img.autoLevels()
                    
                
                end_ind   = len(self.img.history)
                start_ind = np.max([end_ind-self.read_average, 0])
                temp_slice = [self.img.history[i] for i in range(start_ind, end_ind)]
                
                temp = np.round(np.mean(temp_slice),1)
                self.temp.setText(str(temp))


                    
            
                
            
                # get value of temps within roi
                # update line plot
                # update numerical temp
        except KeyboardInterrupt:
            print('quitting!')
        
        finally:
            QtCore.QTimer.singleShot(1000.0/self.fps, self.main)




    def init_ui(self):
        # main layout inside a blank MainWidget
        self.main_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.main_widget)
        
        self.layout = QtWidgets.QVBoxLayout()
        self.main_widget.setLayout(self.layout)

        # raw output of thermal sensor
        self.img = ImageViewROI()
        roi = pg.ROI([0, 0], [1, 1], pen=pg.mkPen('r', width=2))
        self.img.addItem(roi)
        roi.sigRegionChanged.connect(self.getcoordinates)
        
        # colormap
        thermal_cmap = pg.ColorMap(*zip(*Gradients['inferno']['ticks']))
        self.img.setColorMap(thermal_cmap)

        # timeseries of temps
        self.plot = pg.PlotWidget(
            axisItems={'bottom':TimeAxis(orientation='bottom')})
        self.plot_curve = self.plot.plot()

        # numerical temperature
        self.temp = QtWidgets.QLabel()
        self.temp.setStyleSheet("QLabel { color: #ff0000; font-size: 72pt; font-weight: bold}")
        
        # combine lower elements
        self.lower_layout = QtWidgets.QHBoxLayout()
        self.lower_layout.addWidget(self.plot,2)
        self.lower_layout.addWidget(self.temp,1)
        
        # prepare for display
        self.layout.addWidget(self.img, stretch=2)
        self.layout.addLayout(self.lower_layout, stretch=1)
        #self.layout.addWidget(self.temp, 1,1)
        #self.layout.addWidget(self.img, 0,0, columnSpan=-1)
        
        #self.layout.setRowStretch(0,5)
        #self.layout.setRowStretch(1,1)
        
        #self.layout.setColumnStretch(0,2)
        #self.layout.setColumnStretch(1,1)
        self.show()

    def init_sensor(self):
        
        self.capture_thread = threading.Thread(target=self._sensor)
        self.capture_thread.setDaemon(True)
        self.capture_thread.start()

    def _sensor(self):
        cam.setup(self.fps)
        try:
            while True:
                self.frames[:,:,self.frame_idx] = np.rot90(np.array(cam.get_frame()).reshape((32, 24), order="F").T)
                self.frame_idx = (self.frame_idx+1) % self.frames.shape[2]
                
                #pdb.set_trace()
                #self.img.setImage(self.frame)
        except KeyboardInterrupt:
            pass
        finally:
            cam.cleanup()



    def getcoordinates(self, roi):
        data2, xdata = roi.getArrayRegion(self.frame,
                                          self.img.imageItem,
                                          returnMappedCoords=True)
        self.roi_val = data2
        self.roi_pos = xdata
        print(xdata)
        
class EllipseROI(pg.EllipseROI):
    def __init__(self, size):
        
        super().__init__(pos=[0,0], size=size)
        
    
    def getArrayRegion(self, arr, img=None, axes=(0, 1), **kwds):
        """
        Return the result of ROI.getArrayRegion() masked by the elliptical shape
        of the ROI. Regions outside the ellipse are set to 0.
        """
        # Note: we could use the same method as used by PolyLineROI, but this
        # implementation produces a nicer mask.
        #pdb.set_trace()
        arr = pg.ROI.getArrayRegion(self, arr, img, axes, **kwds)
        if len(arr) == 2:
            arr = arr[0]
        if arr is None or arr.shape[axes[0]] == 0 or arr.shape[axes[1]] == 0:
            return arr
        w = arr.shape[axes[0]]
        h = arr.shape[axes[1]]

        ## generate an ellipsoidal mask
        mask = np.fromfunction(lambda x,y: (((x+0.5)/(w/2.)-1)**2+ ((y+0.5)/(h/2.)-1)**2)**0.5 < 1, (w, h))
        
        # reshape to match array axes
        if axes[0] > axes[1]:
            mask = mask.T
        shape = [(n if i in axes else 1) for i,n in enumerate(arr.shape)]
        mask = mask.reshape(shape)
        
        return arr * mask
        

    
        
class ImageViewROI(pg.ImageView):
    def __init__(self, roi_history=2000, skip_time = 0):
        super(ImageViewROI, self).__init__()
        
        self.timestamps = deque(maxlen=roi_history)
        self.history = deque(maxlen=roi_history)
        
        self.ui.roiPlot.hide()
        
        self.roi = EllipseROI(10)
        self.roi.setZValue(20)
        self.view.addItem(self.roi)
        self.roi.sigRegionChanged.connect(self.roiChanged)
        
        self.skip_time = skip_time
        self.got_time = 0
        
    def roiClicked(self):
        showRoiPlot = False
        if self.ui.roiBtn.isChecked():
            showRoiPlot = True
            self.roi.show()
            #self.ui.roiPlot.show()
            #self.ui.roiPlot.setMouseEnabled(True, True)
            #self.ui.splitter.setSizes([self.height()*0.6, self.height()*0.4])
            #for c in self.roiCurves:
            #    c.show()
            self.roiChanged()
            #self.ui.roiPlot.showAxis('left')
        else:
            self.roi.hide()
            #self.ui.roiPlot.setMouseEnabled(False, False)
            #for c in self.roiCurves:
            #    c.hide()
            #self.ui.roiPlot.hideAxis('left')
            
        if self.hasTimeAxis():
            showRoiPlot = True
            mn = self.tVals.min()
            mx = self.tVals.max()
            self.ui.roiPlot.setXRange(mn, mx, padding=0.01)
            self.timeLine.show()
            self.timeLine.setBounds([mn, mx])
            self.ui.roiPlot.show()
            if not self.ui.roiBtn.isChecked():
                self.ui.splitter.setSizes([self.height()-35, 35])
        else:
            self.timeLine.hide()
            #self.ui.roiPlot.hide()
            
        #self.ui.roiPlot.setVisible(showRoiPlot)
        
    def roiChanged(self):
        if self.image is None:
            return
            
        image = self.getProcessedImage()

        # Extract image data from ROI
        axes = (self.axes['x'], self.axes['y'])

        data = self.roi.getArrayRegion(image.view(np.ndarray), self.imageItem, axes, returnMappedCoords=True)
        if data is None:
            return
            
        
        # Average data within entire ROI for each frame
        self.got_time += 1
        if self.got_time > self.skip_time:
            data = np.mean(data)
            self.history.append(data)
            self.timestamps.append(timestamp())
            self.got_time = 0
        

class TimeAxis(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLabel(text='Time', units=None)
        self.enableAutoSIPrefix(False)
        
    def tickStrings(self, values, scale, spacing):
        return [datetime.fromtimestamp(value).strftime('%H:%M:%S') for value in values]
        
def timestamp():
    #return time.mktime(datetime.now().timetuple())
    return time.time()
        



if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    #app.setGraphicsSystem("opengl")
    app.setStyle('GTK+') # Keeps some GTK errors at bay
    ex = Thermometer()
    sys.exit(app.exec_())




