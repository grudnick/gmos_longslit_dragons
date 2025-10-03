#!/usr/bin/env python

# import glob

# from recipe_system.reduction.coreReduce import Reduce

# from gempy.utils import logutils

# from gempy.adlibrary import dataselect

from recipe_system import cal_service

caldb = cal_service.set_local_database()

try:
    caldb.init()
except LocalManagerError:
    print("cal database already exists")
    caldb.list_files()

# You can manually add processed calibrations with caldb.add_cal(<filename>),
# list the database content with caldb.list_files(), and caldb.remove_cal(<filename>) to remove a file from the database (it will not remove the file on disk.)

