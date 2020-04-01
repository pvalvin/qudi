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

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Definition and initialisation of the GUI.
        """

        # connect the logic module from the declared connector
        self._spectrum_logic = self.spectrumlogic()

        # setting up the window
        self._mw = HirondelleWindow()
        self._mw.centralwidget.hide()
        self._mw.setDockNestingEnabled(True)


        # giving the plots names allows us to link their axes together
        self._spec = self._mw.spectrumPlot
        self._spec_item = self._spec.plotItem

        # create a new ViewBox, link the right axis to its coordinate system
        self._right_axis = pg.ViewBox() # Create a ViewBox right axis
        self._spec_item.showAxis('right') # Show the right axis of plotItem
        self._spec_item.scene().addItem(self._right_axis) # associate the ViewBox right axis to the plotItem
        self._spec_item.getAxis('right').linkToView(self._right_axis) # link this right axis to the ViewBox
        self._right_axis.setXLink(self._spec_item) # link the ViewBox object to the plotItem x axis

        # create a new ViewBox, link the top axis to its coordinate system (same procedure)
        self._top_axis = pg.ViewBox()
        self._spec_item.showAxis('top')
        self._spec_item.scene().addItem(self._top_axis)
        self._spec_item.getAxis('top').linkToView(self._top_axis)
        self._top_axis.setYLink(self._spec_item)
        self._top_axis.invertX(b=True) # We force the x axis to be rightward

        # label plot axis :

        self._spec.setLabel('left', 'Fluorescence', units='counts/s')
        self._spec.setLabel('right', 'Number of Points', units='#')
        self._spec.setLabel('bottom', 'Wavelength', units='m')
        self._spec.setLabel('top', 'Relative Frequency', units='Hz')

        # Create 2 empty plot curve to be filled later, set its pen (curve style)
        self._curve1 = self._spec.plot()
        self._curve1.setPen(palette.c1, width=2)

        # Connect signals :
        # Action (spectro):
        self._mw.actionRun.triggered.connect(self.run_spectrum_acquisition)
        self._mw.actionStop_Run.triggered.connect(self.stop_spectrum_acquisition)
        # Button (image):
        self._mw.runImageButton.clicked.connect(self.run_image_acquisition())
        self._mw.stopImageButton.clicked.connect(self.stop_image_acquisition())

        self.show()

        self._save_PNG = True

    def read_settings(self):

        self._center_wavelength = self._spectrum_logic.center_wavelength
        self._detector_offset = self._spectrum_logic.detector_offset
        self._grating = self._spectrum_logic.grating
        self._input_slit = self._spectrum_logic.input_slit
        self._input_slit_width = self._spectrum_logic.input_slit_width
        self._output_slit = self._spectrum_logic.output_slit
        self._output_slit_width = self._spectrum_logic.output_slit_width
        self._min_wavelength, self._max_wavelength = self._spectrum_logic.wavelength_limits

        # Initialize widgets slots :
        self._mw.wavelengthDSpin.setValue(self._center_wavelength)
        self._mw.detectorOffsetSpin.setValue(self._detector_offset)
        self._mw.gratingNumCombo.setCurrentIndex(self._grating)
        self._mw.inputSlitCombo.setCurrentIndex(self._input_slit)
        self._mw.inputSlitWidthDSpin.setValue(self._input_slit_width)
        self._mw.outputSlitCombo.setCurrentIndex(self._output_slit)
        self._mw.outputSlitWidthDSpin.setValue(self._output_slit_width)


    def update_settings(self):

        self._center_wavelength = self._mw.wavelengthDSpin.value()
        self._detector_offset = self._mw.detectorOffsetSpin.value()
        self._grating = self._mw.gratingNumCombo.currentIndex()
        self._input_slit = self._mw.inputSlitCombo.currentIndex()
        self._input_slit_width = self._mw.inputSlitWidthDSpin.value()
        self._output_slit = self._mw.outputSlitCombo.currentIndex()
        self._output_slit_width = self._mw.outputSlitWidthDSpin.value()

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

    def run_spectrum_acquisition(self):
        """Run the spectrum acquisition called from actionRun
        and plot the spectrum data obtained.
        """
        self.update_settings()
        self._spectrum_logic.start_acquisition()
        data = self._spectrum_logic._spectrum_data
        wavelength = np.linspace(self._min_wavelength,self._max_wavelength,len(self.data))
        self._curve1.setData(wavelength,data)

    def stop_spectrum_acquisition(self):
        """Stop the spectrum acquisition called from actionStop_Run
        """
        self._spectrum_logic.stop_acquisition()

    def run_image_acquisition(self):
        """Run the image acquisition called from runImageButton
        and plot the spectrum data obtained.
        """
        self.update_settings()
        self._spectrum_logic.read_mode('IMAGE')
        self._spectrum_logic.start_acquisition()
        data = self._spectrum_logic._spectrum_data