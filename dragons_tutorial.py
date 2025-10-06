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
#The syntax for select_data is
#select_data(inputs, tags=[], xtags=[], expression='True')
#where tags and xtags are tags to include or exclude respectively.
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

#select files of differen types
#flats - The default recipe does not
#stack the flats. This allows us to use only one list of the
#flats. Each will be reduced individually, never interacting with the
#others.
flats = dataselect.select_data(all_files, ['FLAT'])

#arcs - The default recipe does not stack the arcs. This allows us to use
#only one list of arcs. Each will be reduce individually, never
#interacting with the others.
arcs = dataselect.select_data(all_files, ['ARC'])

#If a spectrophotometric standard is recognized as such by DRAGONS, it
#will receive the Astrodata tag STANDARD. To be recognized, the name
#of the star must be in a lookup table. All spectrophotometric
#standards normally used at Gemini are in that table.
stdstar = dataselect.select_data(all_files, ['STANDARD'])

#this prints all the data not flagged as a calibration file.  This
#could include daytime calibrations with daycal flag
all_science = dataselect.select_data(all_files, [], ['CAL'])
for sci in all_science:
    ad = astrodata.open(sci)
    print(sci, '  ', ad.object())

scitarget = dataselect.select_data(
    all_files,
    [],
    ['CAL'],
    dataselect.expr_parser('object=="J2145+0031"')
)
print('scitarget = ', scitarget)

#load bad pixel maps to the database.  this has to be downloaded
#separately from the database
for bpm in dataselect.select_data(all_files, ['BPM']):
    caldb.add_cal(bpm)


#make master bias from full frames and standard frames
reduce_biasstd = Reduce()
reduce_biassci = Reduce()
reduce_biasstd.files.extend(biasstd)
reduce_biassci.files.extend(biassci)
reduce_biasstd.runr()
reduce_biassci.runr()

#reduce master flat fields
#GMOS longslit flat fields are normally obtained at night along with
#the observation sequence to match the telescope and instrument
#flexure. The matching flat nearest in time to the target observation
#is used to flat field the target

#We can send all the flats, regardless of characteristics, to Reduce
#and each will be reduce individually. When a calibration is needed,
#in this case, a master bias, the best match will be obtained
#automatically from the local calibration manager.
reduce_flats = Reduce()
reduce_flats.files.extend(flats)

#The primitive normalizeFlat, used in the recipe, has an interactive
#mode. To activate the interactive mode.  Comment out this line to not
#run interactively
#reduce_flats.uparms = dict([('interactive', True)])
reduce_flats.runr()


#reduce arcs.  As for spectroscopic flats, these images are not stacked
reduce_arcs = Reduce()
reduce_arcs.files.extend(arcs)

#comment out to not run interactively
#reduce_arcs.uparms = dict([('interactive', True)])
reduce_arcs.runr()
