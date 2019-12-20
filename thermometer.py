import numpy as np
from PySide2 import QtCore, QtGui, QtSvg, QtWidgets

# import the whole module so pyqtgraph catches it
import PySide2
import pyqtgraph as pg
import MLX90640 as cam
import threading

class Thermometer(QtWidgets.QMainWindow):
    """
    Window that
        * displays output from a mlx90640 sensor
        * lets you select an ROI and threshold to measure from
        * gives a history and numerical readout of temp
    """

    def __init__(self, fps=32):
        super(Thermometer, self).__init__()
        self.frame = None
        self.fps = fps
        self.capture_thread = None

        self.init_ui()
        self.init_sensor()
        self.main()

    def main(self):
        try:
            while True:
                # refresh image
                self.img.setImage(self.frame)
                # get value of temps within roi
                # update line plot
                # update numerical temp
        except KeyboardInterrupt:
            print('quitting!')




    def init_ui(self):
        self.layout = QtWidgets.QGridLayout()

        # raw output of thermal sensor
        self.img = pg.ImageView()
        roi = pg.ROI([0, 0], [1, 1], pen=pg.mkPen('r', width=2))
        self.img.addItem(roi)
        roi.sigRegionChanged.connect(self.getcoordinates)

        # timeseries of temps
        self.plot = pg.PlotWidget()

        # numerical temperature
        self.temp = QtWidgets.QLabel()

    def init_sensor(self):
        cam.setup(self.fps)
        self.capture_thread = threading.Thread(target=self._sensor)
        self.capture_thread.setDaemon(True)
        self.capture_thread.start()

    def _sensor(self):
        try:
            while True:
                self.frame = np.array(cam.get_frame()).reshape((32, 24), order="F")
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







