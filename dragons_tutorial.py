#!/usr/bin/env python

import glob


import astrodata

import gemini_instruments

from recipe_system.reduction.coreReduce import Reduce

from gempy.adlibrary import dataselect

from gempy.utils import logutils

#this will be print to the directory in which you are working
logutils.config(file_name='gmosls_tutorial.log')

dataroot = '/Users/grudnick/Code/Dragons/Tutorials/gmosls_tutorial'

#set up calibration services
# You can manually add processed calibrations with caldb.add_cal(<filename>),
# list the database content with caldb.list_files(), and caldb.remove_cal(<filename>) to remove a file from the database (it will not remove the file on disk.)

from recipe_system import cal_service

caldb = cal_service.set_local_database()

#only initialize the database if it hasn't been initialized
try:
     caldb.init()
except:
     print("cal database already exists")
     caldb.list_files()

all_files = glob.glob(dataroot + '/playdata/example1/*.fits')

all_files.sort()
print(all_files)

#set up lists of bias files.  Start with all files
all_biases = dataselect.select_data(all_files, ['BIAS'])

for bias in all_biases:
    ad = astrodata.open(bias)
    print(bias, '  ', ad.detector_roi_setting())

#No split up the biases into full frame and the central spectrum
biasstd = dataselect.select_data(
    all_files,
    ['BIAS'],
    [],
    dataselect.expr_parser('detector_roi_setting=="Central Spectrum"')
)

biassci = dataselect.select_data(
    all_files,
    ['BIAS'],
    [],
    dataselect.expr_parser('detector_roi_setting=="Full Frame"')
)
