# ConvertShapefilesToSQLite.py

# Use SSURGO export files (.shp) to build the spatial schema for an SQLite database.
#
# Using an existing SSURGO-SQLite that already has the tabular schema, but lacks the geometry tables
#
# ArcGIS Pro 2.7
#
# Steve Peaslee, National Soil Survey Center, Lincoln, Nebraska
#
# python libraries for shapefile:  fiona, shapely, ogr, import shapefile?
#
# Extents methods:
#    import ogr; ds = ogr.Open(<shapefile>); layer = ds.GetLayer(),
#    extentTuple = layer.GetExtent()

## ===================================================================================
class MyError(Exception):
    # Custom error

    def __init__(self, *args):

        if args:
            self.message = args[0]

        else:
            self.message = None

    def __str__(self):

        if self.message:
            return self.message
            #return 'Message passed through MyError: {0}'.format(self.message)

        else:
            return 'MyError has been raised'

## ===================================================================================
def MyWarning(msg):
    # If I use sys.exit(1), the script will drop down to the exception clause where usually errorMsg1 is called.
    # Do I need to clear the traceback when MyError is called?
    PrintMsg(msg, 1)
    return

## ===================================================================================
def errorMsg1(excInfo):
    # Capture system error from traceback and then exit
    # Should I be passing in the value for sys.exc_info()?
    try:
        # sys.tracebacklimit = 1

        # excInfo object is a tuple that should contain 3 values
        # 0: type gets the type of the exception being handled (a subclass of BaseException)
        # 1: value gets the exception instance (an instance of the exception type)
        # 2: traceback gets a traceback object which encapsulates the call stack at the point where the exception originally occurred

        if not excInfo is None:

            PrintMsg(70 * "=", 2)
            exc_type, exc_value, exc_tb = sys.exc_info()

            for tb_info in traceback.extract_tb(exc_tb):
                filename, linenum, funcname, source = tb_info
                errInfo = str(sys.exc_info()[1])

                if funcname != '<module>':
                    funcname = funcname + '()'

                if source.strip().startswith("raise MyError"):
                    # raised error
                    PrintMsg(errInfo + " (function " + sys._getframe().f_code.co_name + ")", 2)

                else:
                    # arcpy.Execute error
                    PrintMsg("Error '" + errInfo + "' in " + os.path.basename(filename) + \
                         " at line number " + str(linenum) + ":" + "\n" + source, 2)

            PrintMsg(70 * "=", 2)
            return

    except MyError as e:
        PrintMsg(str(e), 2)

    except:
        errorMsg1(sys.exc_info())

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

    except MyError as e:
        PrintMsg(str(e), 2)
        return False

    except:
        errorMsg1(sys.exc_info())
        return False

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


    except MyError as e:
        PrintMsg(str(e), 2)
        return "???"

    except:
        errorMsg1(sys.exc_info())
        return "???"

## ===================================================================================

# Import system modules
import arcpy, sys, string, os, traceback, locale, time, datetime, sqlite3
sys.tracebacklimit = 1

from arcpy import env

try:
    if __name__ == "__main__":
        outputDB = arcpy.GetParameterAsText(0)        # Test to see if I can sort the ssaLayer when using the 'Create gSSURGO DB by Map' tool
        inputFolder = arcpy.GetParameterAsText(1)     # location of a SSURGO dataset path (including spatial folder)

        if not inputFolder.endswith("spatial"):
            raise MyError("Looking for a 'spatial' folder containing SSURGO shapefiles")

        if not arcpy.Exists(inputFolder):
            raise MyError("Input folder (" + inputFolder + ") not found")

        # Set current workspace to the 'spatial' folder
        env.workspace = inputFolder

        shapefiles = arcpy.ListFiles("soil*.shp")  # Please note. These should be empty shapefiles.
        shpCnt = len(shapefiles)

        if shpCnt != 6:
            if shpCnt == 0:
                raise MyError("No SSURGO shapefiles found in folder: " + inFolder)

            else:
                raise MyError("Need 6 SSURGO shapefiles, found " + str(shpCnt) + " in folder: " + inFolder)

        env.workspace = outputDB

        # Check data type for mapunit.mukey
        # if mukey is integer, make the featureclasses match
        # for all fields that end in 'key' and are 30 character
        mapunitFields = arcpy.Describe("main.mapunit").fields
        bInteger = False

        for fld in mapunitFields:
            #PrintMsg(".\tChecking mapunit field " + fld.name.lower() + " with data type of '" + fld.type + "'", 1)

            if fld.name.lower() == "mukey":
                if fld.type.lower() in ("integer", "long", "oid"):
                    PrintMsg(".\tSetting all key fields to long integer...", 0)
                    bInteger = True
                    break

                else:
                    PrintMsg(".\tSetting all key fields to text because mapunit.mukey is '" + fld.type.lower() + "'...", 0)
                    #raise MyError("EARLY OUT BECAUSE THIS NEEDS TO BE INTEGER")

        dbName, dbExt = os.path.splitext(os.path.basename(outputDB))

        dShapefiles = dict()
        dFields = dict()
        featuresList = ["sapolygon", "mupolygon", "muline", "mupoint", "featline", "featpoint"]

        for shp in shapefiles:
            # parse the shapefile names and use the standard SSURGO filenaming convention to assign geometry type
            dFields[shp] = arcpy.Describe(os.path.join(inputFolder, shp)).fields
            typeString = shp[4:8]

            if typeString == "mu_a":
                 dShapefiles["mupolygon"] = (shp, "POLYGON")

            elif typeString == "mu_l":
                dShapefiles["muline"] = (shp, "POLYLINE")

            elif typeString == "mu_p":
                dShapefiles["mupoint"] = (shp, "POINT")

            elif typeString == "sa_a":
                dShapefiles["sapolygon"] = (shp, "POLYGON")

            elif typeString == "sf_l":
                dShapefiles["featline"] = (shp, "POLYLINE")

            elif typeString == "sf_p":
                dShapefiles["featpoint"] = (shp, "POINT")

        for tbl in featuresList:
            shp, geomType = dShapefiles[tbl]
            sr = arcpy.Describe(os.path.join(inputFolder, shp)).spatialReference
            PrintMsg(".\tCreating new SQLite geometry table: " + tbl, 0)

            # Here we are using arcpy to create the new spatial tables. Would prefer SQL if that can be figured out.
            # arcpy.management.CreateFeatureclass(outputDB, tbl, geomType, os.path.join(inputFolder, shp), "DISABLED", "DISABLED", sr)
            arcpy.management.CreateFeatureclass(outputDB, tbl.lower(), geomType, "", "DISABLED", "DISABLED", sr)

            for fld in dFields[shp]:
                #if not fld.type in ("OID", "Geometry"):
                if not fld.type in ("OID", "Geometry"):
                    field_name = fld.name.lower()
                    field_type = fld.type
                    field_precision = fld.precision
                    field_scale = fld.scale
                    field_length = fld.length
                    field_alias = fld.aliasName
                    field_is_nullable = fld.isNullable
                    field_is_required = fld.required

                    if field_name[-3:] == "key" and fld.length == 30:
                        # This is a primary or foreign key in SSURGO
                        if bInteger:
                            field_type = "Long"
                            field_length = 0

                    PrintMsg(".\tCreating " + field_name + " as '" + field_type + "' data type", 1)
                    arcpy.management.AddField(tbl, field_name=field_name.lower(), field_type=field_type, \
                    field_precision=field_precision, field_scale=field_scale, field_length=field_length, \
                    field_alias=field_alias, field_is_nullable=field_is_nullable, field_is_required=field_is_required)

        # Create spatial views based upon 'mupolygon' and

        # Begin spatial views
        if 1 == 1:  # Turned on
            # Make sure to test the SQL for any view before creating them. Silent error if they fail.
            conn = sqlite3.connect(outputDB, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
            liteCur = conn.cursor()

            # Adding spatial view for mupolygon-muaggatt table
            time.sleep(1.0)
            PrintMsg(".", 0)
            PrintMsg(".\tAdding spatial view for map unit name", 0)
            queryMunameView = """CREATE VIEW view_muname AS SELECT
            M.objectid, M.shape, M.areasymbol, M.spatialver, M.musym, M.mukey, R.muname
            FROM MUPOLYGON M
            INNER JOIN mapunit R ON M.mukey = R.mukey
            ORDER BY M.objectid ASC;"""
            liteCur.execute(queryMunameView)
            conn.commit


            ##Add spatial view for mupolygon-muaggatt table
            PrintMsg(".\tAdding spatial view of selected muaggatt data", 0)
            queryMuaggattView = """CREATE VIEW view_mupolyextended AS SELECT
            M.objectid, M.shape, M.areasymbol, M.spatialver, M.musym, M.mukey, G.muname,
            G.slopegradwta, G.brockdepmin, G.aws025wta, G.drclassdcd, G.hydgrpdcd, G.niccdcd, G.hydclprs
            FROM MUPOLYGON M
            INNER JOIN muaggatt G ON M.mukey = G.mukey
            ORDER BY M.objectid ASC;"""
            liteCur.execute(queryMuaggattView)
            conn.commit  # Do I need to commit if I'm just reading records?
            ## End of spatial views


            if dbExt == ".gpkg":
                # ["sapolygon", "mupolygon", "muline", "mupoint", "featline", "featpoint"]
                PrintMsg(".\tRegistering spatial layers to the database", 0)

                # Get table info including name, alias, description for use in registering tables to geopackage
                sqlTableInfo = "SELECT tabphyname, tablabel, tabdesc " + \
                               "FROM mdstattabs WHERE tabphyname IN " + str(tuple(featuresList)) + " " +\
                               "ORDER BY tabphyname ;"

                tblValues = list()

                for rec in liteCur.execute(sqlTableInfo):
                    if tblName in featuresList:
                        # These records should already exists in the gpkg_contents table, but
                        # will be used to update
                        tblName, tblAlias, tblDesc = rec
                        tnta = (tblName, tblAlias, tblDesc, tblName)
                        tblValues.append(tnta)

                #conn.commit()

                # Update existing records
                #for tnta in tblValues:
                sqlUpdate = "UPDATE gpkg_contents SET table_name=?, data_type='attributes', identifier=?, description=? WHERE table_name=?"
                liteCur.executemany(sqlUpdate, tblValues)

                conn.commit()


                # Register these spatial views
                # Note to self. Could probably use tblValues from above to update the featureclass information as well
                # Those will contain the feature classes as well.
                #
                # Reset tblValues for just the views that will need new records
                tblValues = list()
                tblValues.append(("View_Muname", "features", "View_Muname", "Map unit polgyons with mapunit name (mun)ame) attached"))
                tblValues.append(("View_MupolyExtended", "features", "View_MupolyExtended", "Map unit polgyons with selected attributes from muaggatt table"))

                if len(tblValues) > 0:
                    #
                    queryRegisterTables = "INSERT INTO gpkg_contents (table_name, data_type, identifier, description) VALUES(?, ?, ?, ?)"
                    liteCur.executemany(queryRegisterTables, tblValues)
                    conn.commit()

            #elif dbExt == ".sqlite":
            #    pass



            conn.close()
            del conn

except MyError as e:
    PrintMsg(str(e), 2)

except:
    errorMsg1(sys.exc_info())
