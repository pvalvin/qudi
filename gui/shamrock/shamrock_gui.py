# -*- coding: utf-8 -*-
"""
This module contains a GUI for operating the spectrum logic module.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

import os
import pyqtgraph as pg
import numpy as np

from core.connector import Connector
from core.statusvariable import StatusVar
from core.util import units

from gui.colordefs import QudiPalettePale as palette
from gui.guibase import GUIBase
from qtpy import QtCore
from qtpy import QtWidgets
from qtpy import uic


class HirondelleWindow(QtWidgets.QMainWindow):

    def __init__(self):
        """ Create the laser scanner window.
        """
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_hirondelle200.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()


class HirondelleGui(GUIBase):
    """
    """

    # declare connectors
    spectrumlogic = Connector(interface='ShamrockLogic')

    # Import last spectrum and background or initialize :
    _spectrum_data = StatusVar('spectrum_data', np.empty((2, 0)))
    _background_data = StatusVar('background_data', np.empty((2, 0)))

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Definition and initialisation of the GUI.
        """

        # connect the logic module from the declared connector
        self._spectrum_logic = self.spectrumlogic()

        # setting up the window
        self._mw = HirondelleWindow()


        # giving the plots names allows us to link their axes together
        self._plot = self._mw.plotWidget
        self._plot_item = self._plot.plotItem

        # create a new ViewBox, link the right axis to its coordinate system
        self._right_axis = pg.ViewBox() # Create a ViewBox right axis
        self._plot_item.showAxis('right') # Show the right axis of plotItem
        self._plot_item.scene().addItem(self._right_axis) # associate the ViewBox right axis to the plotItem
        self._plot_item.getAxis('right').linkToView(self._right_axis) # link this right axis to the ViewBox
        self._right_axis.setXLink(self._plot_item) # link the ViewBox object to the plotItem x axis

        # create a new ViewBox, link the top axis to its coordinate system (same procedure)
        self._top_axis = pg.ViewBox()
        self._plot_item.showAxis('top')
        self._plot_item.scene().addItem(self._top_axis)
        self._plot_item.getAxis('top').linkToView(self._top_axis)
        self._top_axis.setYLink(self._plot_item)
        self._top_axis.invertX(b=True) # We force the x axis to be rightward

        # label plot axis :

        self._plot.setLabel('left', 'Fluorescence', units='counts/s')
        self._plot.setLabel('right', 'Number of Points', units='#')
        self._plot.setLabel('bottom', 'Wavelength', units='m')
        self._plot.setLabel('top', 'Relative Frequency', units='Hz')

        # Create 2 empty plot curve to be filled later, set its pen (curve style)
        self._curve1 = self._plot.plot()
        self._curve1.setPen(palette.c1, width=2)

        # Connect signals
        self._mw.runButton.clicked.connect(self.run_acquisition)
        self._mw.stopButton.clicked.connect(self.stop_acquisition)

        self._center_wavelength = self._spectrum_logic.center_wavelength
        self._detector_offset = self._spectrum_logic.detector_offset
        self._grating = self._spectrum_logic.grating
        self._input_slit = self._spectrum_logic.input_slit
        self._input_slit_width = self._spectrum_logic.input_slit_width
        self._output_slit = self._spectrum_logic.output_slit
        self._output_slit_width = self._spectrum_logic.output_slit_width
        self._min_wavelength, self._max_wavelength = self._spectrum_logic.wavelength_limits

        # Initialize widgets slots :
        self._mw.centerWavelength.setValue(self._center_wavelength)
        self._mw.detectorOffset.setValue(self._detector_offset)
        self._mw.gratingNum.setCurrentIndex(self._grating)
        self._mw.inputSlit.setCurrentIndex(self._input_slit)
        self._mw.inputSlitWidth.setValue(self._input_slit_width)
        self._mw.outputSlit.setCurrentIndex(self._output_slit)
        self._mw.outputSlitWidth.setValue(self._output_slit_width)

        self.show()

        self._save_PNG = True

    def update_settings(self):

        self._center_wavelength = self._mw.centerWavelength.value()
        self._detector_offset = self._mw.detectorOffset.value()
        self._grating = self._mw.gratingNum.currentIndex()
        self._input_slit = self._mw.inputSlit.currentIndex()
        self._input_slit_width = self._mw.inputSlitWidth.value()
        self._output_slit = self._mw.outputSlit.currentIndex()
        self._output_slit_width = self._mw.outputSlitWidth.value()

        self._spectrum_logic.center_wavelength = self._center_wavelength
        self._spectrum_logic.detector_offset = self._detector_offset
        self._spectrum_logic.grating = self._grating
        self._spectrum_logic.input_slit = self._input_slit
        self._spectrum_logic.input_slit_width = self._input_slit_width
        self._spectrum_logic.output_slit = self._output_slit
        self._spectrum_logic.output_slit_width = self._output_slit_width

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """

        self._mw.close()

    def show(self):
        """Make window visible and put it above all other windows.
        """
        QtWidgets.QMainWindow.show(self._mw)
        self._mw.activateWindow()
        self._mw.raise_()

    def run_acquisition(self):
        """Run the spectrum acquisition called from run_acquisition_Action
        and plot the spectrum data obtained.
        """
        self.update_settings()
        self._spectrum_logic.acquire_spectrum()
        data = self._spectrum_logic._spectrum_data
        _wavelength_axis = np.linspace(self._min_wavelength,self._max_wavelength,len(self.data))
        self._curve1.setData(_wavelength_axis,data)

    def stop_acquisition(self):
        """Stop the spectrum acquisition called from run_acquisition_Action
        """
        pass