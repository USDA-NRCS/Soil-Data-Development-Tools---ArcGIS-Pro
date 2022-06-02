# gSSURGO_CreateSoilMaps.py
#
# Batch-mode. Creates Soil Data Viewer-type maps using only the default settings. Designed to run in batch-mode.

## ===================================================================================
class MyError(Exception):
    pass

## ===================================================================================
def errorMsg():
    try:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        theMsg = tbinfo + " \n" + str(sys.exc_type)+ ": " + str(sys.exc_value) + " \n"
        PrintMsg(theMsg, 2)

    except:
        PrintMsg("Unhandled error in attFld method", 2)
        pass

## ===================================================================================
def PrintMsg(msg, severity=0):
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
            if severity == 0:
                arcpy.AddMessage(string)

            elif severity == 1:
                arcpy.AddWarning(string)

            elif severity == 2:
                arcpy.AddError(" \n" + string)

    except:
        pass

## ===================================================================================
def Number_Format(num, places=0, bCommas=True):
    try:
    # Format a number according to locality and given places
        locale.setlocale(locale.LC_ALL, "")
        if bCommas:
            theNumber = locale.format("%.*f", (places, num), True)

        else:
            theNumber = locale.format("%.*f", (places, num), False)
        return theNumber

    except:
        errorMsg()

        return "???"

## ===================================================================================
def elapsedTime(start):
    # Calculate amount of time since "start" and return time string
    try:
        # Stop timer
        #
        end = time.time()

        # Calculate total elapsed seconds
        eTotal = end - start

        # day = 86400 seconds
        # hour = 3600 seconds
        # minute = 60 seconds

        eMsg = ""

        # calculate elapsed days
        eDay1 = eTotal / 86400
        eDay2 = math.modf(eDay1)
        eDay = int(eDay2[1])
        eDayR = eDay2[0]

        if eDay > 1:
          eMsg = eMsg + str(eDay) + " days "
        elif eDay == 1:
          eMsg = eMsg + str(eDay) + " day "

        # Calculated elapsed hours
        eHour1 = eDayR * 24
        eHour2 = math.modf(eHour1)
        eHour = int(eHour2[1])
        eHourR = eHour2[0]

        if eDay > 0 or eHour > 0:
            if eHour > 1:
                eMsg = eMsg + str(eHour) + " hours "
            else:
                eMsg = eMsg + str(eHour) + " hour "

        # Calculate elapsed minutes
        eMinute1 = eHourR * 60
        eMinute2 = math.modf(eMinute1)
        eMinute = int(eMinute2[1])
        eMinuteR = eMinute2[0]

        if eDay > 0 or eHour > 0 or eMinute > 0:
            if eMinute > 1:
                eMsg = eMsg + str(eMinute) + " minutes "
            else:
                eMsg = eMsg + str(eMinute) + " minute "

        # Calculate elapsed secons
        eSeconds = "%.1f" % (eMinuteR * 60)

        if eSeconds == "1.00":
            eMsg = eMsg + eSeconds + " second "
        else:
            eMsg = eMsg + eSeconds + " seconds "

        return eMsg

    except:
        errorMsg()
        return ""

## ===================================================================================
## MAIN
## ===================================================================================

# Import system modules
import arcpy, sys, string, os, traceback, locale, time, sqlite3

# Create the environment
from arcpy import env

try:

    inputLayer = arcpy.GetParameterAsText(0)       # Input mapunit polygon layer
    sdvAtts = arcpy.GetParameter(1)                # SDV Attribute
    top = arcpy.GetParameter(2)                    # Top Depth, default = 0
    bot = arcpy.GetParameter(3)                     # Bottom Depth, default = 1

    num = 0
    badList = list()
    PrintMsg(" \n", 0)
    import gSSURGO_CreateSoilMap

    # Turn off display of the inputLayer to reduce potential screen redraws
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = mxd.activeDataFrame
    layers = arcpy.mapping.ListLayers(mxd, inputLayer, df)
    
    if len(layers) == 1:
        soilLayer = layers[0]
        soilLayer.visible = False
        del soilLayer

    del mxd, df, layers

    # Get gSSURGO Db behind inputLayer
    desc = arcpy.Describe(inputLayer)
    
    if desc.dataType.lower() == "featurelayer":
        fc = desc.featureclass.catalogPath
        gdb = os.path.dirname(fc)

    elif desc.dataType.lower() == "rasterlayer":
        gdb = os.path.dirname(desc.catalogPath)

    aggMethod = ""
    primCst = ""
    secCst = ""
    begMo = "January"
    endMo = "December"
    bZero = True
    cutOff = 0
    bFuzzy = False
    bNulls = True
    tieBreaker = ""
    sRV = "Representative"

    newAtts = list()
    
    for sdvAtt in sdvAtts:
        # Choice list in menu was modified to include folder names and tabbed attributenames. Need
        # to clean up the list before processing.
        if not sdvAtt.startswith("* "):
            newAtts.append(sdvAtt.strip())
            
    PrintMsg(" \nCreating a series of " + str(len(newAtts)) + " soil maps", 0)
    arcpy.SetProgressor("step", "Creating series of soil maps...", 1, len(newAtts), 1)
    num = 0
    
    for sdvAtt in newAtts:
        if not sdvAtt.startswith("* "):
            sdvAtt = sdvAtt.strip()
            num += 1
            msg = "Creating map number " + str(num) + ":  " + sdvAtt
            #arcpy.SetProgressorLabel(msg)
            PrintMsg(" \n" + msg, 0)
            time.sleep(2)

            # Trying here to enter default values for most parameters and to modify CreateSoilMap.CreateSoilMap to use default aggregation method (aggMethod) when it is passed an empty string
            bSoilMap = gSSURGO_CreateSoilMap.CreateSoilMap(inputLayer, sdvAtt, aggMethod, primCst, secCst, top, bot, begMo, endMo, tieBreaker, bZero, cutOff, bFuzzy, bNulls, sRV) # external script
            #arcpy.SetProgressorPosition()
            
            if bSoilMap == 2:
                badList.append(sdvAtt)

            elif bSoilMap == 0:
                #PrintMsg("\tbSoilMap returned 0", 0)
                badList.append(sdvAtt)
            
    del bSoilMap
    arcpy.RefreshActiveView()
    
    if len(badList) > 0:
        if len(badList) == 1:
            PrintMsg(" \nUnable to create the following soil map layer: '" + badList[0] + "' \n ", 1)

        else:
            PrintMsg(" \nUnable to create the following soil map layers: '" + "', '".join(badList) + "' \n ", 1)

    else:
        PrintMsg(" \nCreateSoilMaps finished \n ", 0)

    del badList

except:
    errorMsg()

finally:
    try:
        del mxd, df

    except:
        pass
