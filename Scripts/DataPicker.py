# This version of Data Picker will filter SSURGO downloads by a given list of areasymbol values.
# This code is simple enough that it could be imbedded in the UI.

import os
import DataLoader

# There are four input parameters
# 1. InputFolder containing SSURGO downloads (browser, datatype=folder)
# 2. List of areasymbols for the desired SSURGO datasets to be imported. This may be user input or derived values.
# 3. outputCoordinateSystem - EPSG code or some other way to identify the desired output coordinate system.
# 4. 


# SSURGO Downloads folder (input parameter, fullpath, datatype=folder)
inputFolder = r"D:\Geodata\2021\SSURGO_Downloads"

# Unique list of survey areas to search for by areasymbol.
areasymboList = ['NE139', 'KS023']
areasymbolList = list(set(areasymbolList))


# Output coordinate system (input parameter, integer)
outputCoordinateSystem = 4326

# List of matching SSURGO datasets. (derived input parameter subfolder name, datatype=string)
# If any were not found, let the user know and prevent the tool from executing.

# Get list of subfolders (top level only) in the inputFolder
dirList = os.listdir(inputFolder)

# Initialize list of matched SSURGO downloads
surveyList = list()

# Initialize list of matched areasymbols
matchedList = list()

# Initialize list of duplicate SSURGO downloads?
dupList = list()

for folderName in dirList:
    # Assume that the last five characters of the foldername would be an 
    # areasymbol in either upper or lowercase format.
    # this would not be true for WSS-AOI downloads
    areaSym = folderName[-5:].upper()

    if (areaSym in areasymbolList) and (\
      os.path.isdir( os.path.join( inputFolder, os.path.join( folderName, "spatial" ) ) ) and  \
      os.path.isdir( os.path.join( inputFolder, os.path.join( folderName, "tabular" ) ) ) ) ) ]
    # Found the first and hopefully the only matching SSURGO download folder.

      if not areaSym in matchedList:
        # Found the first and hopefully the only matching SSURGO download folder.
        # Add the foldername to the import list
        matchedList.append(areaSym)
        surveyList.append(folderName)

      else:
        # Found another matching SSURGO download folder. 
        # Must be a different folder naming convention?
        # Skip downloading this version, but let the user know there is more than one match.
        dupList.append(folderName)

diff = len(areasymbolList) - len(surveyList)
        
if diff > 0:
    print("Warning. You are missing " + str(diff) + " survey area datasets in your SSURGO Data Cache")

# Run Data Loader
# 
bImported = DataLoader(inputFolder, surveyList, outputCoordinateSystem, surveyList)

