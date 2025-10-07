#!/usr/bin/env python


'''

Gregory Rudnick
6-Oct-2025

DESCRIPTION

Python reduction script using reduce class.  Works on Dragons tutorial
data.

COMMAND LINE PARAMETERS

makebias:  default=True; make master bias

makeflats: default=True; make flatfields

makearcs:  default=True; reduce arcs and determine wavelength solution

makestd:   default=True; reduce standard and make sensitivity correction

makesci:   default=True; reduce science frames and extract 1D spectrum

interactive default=True; perform all reductions interactively

plotspec   default=True; plot spectra

INPUT

You need to specify the path "dataroot" that locates the input data.

EXAMPLE USAGE

python dragons_tutorial.py --makebias False --makeflats True

OUTPUT

Reduced data will be deposited in execution directory

'''


import glob
import astrodata
import gemini_instruments
from recipe_system.reduction.coreReduce import Reduce
from gempy.adlibrary import dataselect
from gempy.utils import logutils
import argparse
from gempy.adlibrary import plotting
import matplotlib.pyplot as plt

# This needs to be set to the root for the data. 
dataroot = '/Users/grudnick/Code/Dragons/Tutorials/gmosls_tutorial'

#initialize variables that govern which parts of the script to execute
makebias = True
makeflats = True
makearcs = True
makestd = True
makesci = True
interactive = True
plotspec = True

#parse command line options
parser = argparse.ArgumentParser(description="This is a reduction script using Dragons for longslit spectra")
parser.add_argument("--makebias", help="default=True; make master bias")
parser.add_argument("--makeflats", help="default=True; make flatfields")
parser.add_argument("--makearcs", help="default=True; reduce arcs and determine wavelength solution")
parser.add_argument("--makestd", help="default=True; reduce standard and make sensitivity correction")
parser.add_argument("--makesci", help="default=True; reduce science frames and extract 1D spectrum")
parser.add_argument("--interactive", help="default=True; perform all reductions interactively")
parser.add_argument("--plotspec", help="default=True; plot spectra")

args = parser.parse_args()

if args.makebias is not None:
    makebias = args.makebias
if args.makeflats is not None:
    makeflats = args.makeflats
if args.makearcs is not None:
    makearcs = args.makearcs
if args.makestd is not None:
    makestd = args.makestd
if args.makesci is not None:
    makesci = args.makesci
if args.interactive is not None:
    interactive = args.interactive
if args.makesci is not None:
    plotspec = args.plotspec

print(f"makebias={makebias}, makeflats={makeflats}, makearcs={makearcs}, makestd={makestd}, makesci={makesci}, interactive={interactive}, plotspec={plotspec}")


#this will be print to the directory in which you are working
logutils.config(file_name='gmosls_tutorial.log')


#set up calibration services You can manually add processed
# calibrations with caldb.add_cal(<filename>), list the database
# content with caldb.list_files(), and caldb.remove_cal(<filename>) to
# remove a file from the database (it will not remove the file on
# disk.)

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
print('#############################################')
print('collect file names')
print('#############################################')

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
if makebias==True:
    print('#############################################')
    print('make master bias')
    print('#############################################')
    reduce_biasstd = Reduce()
    reduce_biasstd.files.extend(biasstd)
    reduce_biasstd.runr()

    reduce_biassci = Reduce()
    reduce_biassci.files.extend(biassci)
    reduce_biassci.runr()
else:
    print('#############################################')
    print('Skipping master bias construction')
    print('#############################################')



#reduce master flat fields
#GMOS longslit flat fields are normally obtained at night along with
#the observation sequence to match the telescope and instrument
#flexure. The matching flat nearest in time to the target observation
#is used to flat field the target

#We can send all the flats, regardless of characteristics, to Reduce
#and each will be reduce individually. When a calibration is needed,
#in this case, a master bias, the best match will be obtained
#automatically from the local calibration manager.
if makeflats==True:
    print('#############################################')
    print('make master flats')
    print('#############################################')

    reduce_flats = Reduce()
    reduce_flats.files.extend(flats)

    #The primitive normalizeFlat, used in the recipe, has an interactive
    #mode. 
    if interactive==True:
        reduce_flats.uparms = dict([('interactive', True)])

    reduce_flats.runr()
else:
    print('#############################################')
    print('Skipping master flat construction')
    print('#############################################')

#reduce arcs.  As for spectroscopic flats, these images are not stacked
if makearcs==True:
    print('#############################################')
    print('make arcs and determine wavelength solution')
    print('#############################################')
    reduce_arcs = Reduce()
    reduce_arcs.files.extend(arcs)

    #you can use an interactive feature to fit the arcs
    if interactive==True:
        reduce_arcs.uparms = dict([('interactive', True)])

    reduce_arcs.runr()
else:
    print('#############################################')
    print('Skipping arc procession and wavelength solution determination')
    print('#############################################')
    

#sensitivity functiion.  This is performed at only one spectroscopic
#dither as it has been found that differences of ~10nm does not
#significantly affect spectrophotometric calibration
if makestd==True:
    print('#############################################')
    print('reduce standard and calculate sensitivity correction')
    print('#############################################')

    reduce_std = Reduce()
    reduce_std.files.extend(stdstar)

    #comment out to run in non-interactive mode for all the reduction.
    #This includes for sky subtraction and tracing the spectrum.
    #Standards are bright so this probably won't be needed
    #reduce_std.uparms = dict([('interactive', True)])

    #this is just to do the sensitivity function interactively.
    if interactive==True: 
        reduce_std.uparms = dict([('calculateSensitivity:interactive', True)])

    reduce_std.runr()

    #this will plot the spectrum in aperture 1
    plotspec=False
    if plotspec==True:
        ad = astrodata.open(reduce_std.output_filenames[0])
        plt.ioff()
        plotting.dgsplot_matplotlib(ad, 1)
        plt.ion()
else:
    print('#############################################')
    print('skip making sensitivity correction')
    print('#############################################')


#reduce science images.
#This makes a 2-D spectrum and an extracted 1D spectrum.  The 1D
#spectrum is flux calibrated with the sensitivity function
if makesci==True:
    print('#############################################')
    print('reduce science images')
    print('#############################################')
    reduce_science = Reduce()
    reduce_science.files.extend(scitarget)

    if interactive==True:
        #reduce_science.uparms = dict([('findApertures:interactive', True)])
        #reduce_science.uparms = dict([('skyCorrectFromSlit:interactive', True)])
        #reduce_science.uparms = dict([('traceApertures:interactive', True)])
        reduce_science.uparms = dict([('interactive', True)])
        
    reduce_science.runr()

    display = Reduce()
    display.files = ['S20171022S0087_2D.fits']
    display.recipename = 'display'
    display.runr()

    plotspec=False
    if plotspec==True:
        ad = astrodata.open(reduce_science.output_filenames[0])
        plt.ioff()
        plotting.dgsplot_matplotlib(ad, 1)
        plt.ion()
else:
    print('#############################################')
    print('skip reducing science images')
    print('#############################################')
