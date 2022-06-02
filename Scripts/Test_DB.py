# Test_DB.py
# 2.7?
# Test python script to create a spatialite database with metadata tables and spatial tables
#
import os, sys, sqlite3

# Get paths for scripts, spatialite extensions, SQL queries
#
scriptPath = __file__      
scriptFolder = os.path.dirname(scriptPath)
basePath = os.path.dirname(scriptFolder)

# location for spatialite binaries
extFolder = os.path.join(basePath, "Extensions")

# location for queries used to build databases, import SSURGO data and query database
sqlFolder = os.path.join(basePath, "Queries")

newPaths = list()
newPaths.append(extFolder)  # add Script subfolder to system path

if len(newPaths) > 0:
    myPath = os.environ['PATH']
    pathList = myPath.split(";")
    addList = list()

    for p in newPaths:
        if not p in pathList:
            os.environ['PATH'] += ";" + p

# Note. dbName and outputFolder variables need to be changed to script parameters.
# Variable for outputdatabase name
dbName = "test_02.sqlite"

# Location for output database(s)
outputFolder = "C:/Geodata/ArcGIS_Home/scratch"

# Full path and filename for output database
db = os.path.join(outputFolder, dbName)

# Here I am using an ArcGIS Desktop DLL.
# Need to look at options that can be packaged with my application.
# I have created a reference to 
#
extPath = 'spatialite400x.dll'

sqlExtension = "SELECT load_extension('" + extPath + "');"

dbConn = sqlite3.connect(db)

# load spatialite extension needed for geometry functions
dbConn.enable_load_extension(True)

try:
    dbConn.execute(sqlExtension)

except:
    print "Failed to load spatialite extension"

# Create spatial metadata tables (this actually worked, but created a LOT of tables!)
# Need to compare the system tables created by this DLL to other options.
sqlMetadata = "SELECT InitSpatialMetaData();"  

liteCur.execute(sqlMetadata)

row = liteCur.fetchone()

if row[0] == 0:
    print "Failed to create spatial metadata tables for " + dbName

# Create test spatial table (featline)
sqlCT = """CREATE TABLE featline (
objectid INTEGER NOT NULL,
shape LINESTRING,
areasymbol TEXT(20),
spatialver MEDIUMINT,
featsym TEXT(3),
featkey INTEGER,
PRIMARY KEY(objectid AUTOINCREMENT),
FOREIGN KEY(featkey) REFERENCES featdesc(featkey) ON DELETE CASCADE,
FOREIGN KEY(areasymbol) REFERENCES sacatalog(areasymbol) ON DELETE CASCADE
); """

# Execute create table sql
liteCur.execute(sqlCT)

row = liteCur.fetchone()  # for some reason row is NULL in ArcGIS Python window, 
# but seems to be working otherwise
if row is not None:
    print "Create Table returned '" + str(row[0])

dbConn.commit()

# Enable geometry column. Returns 0, not sure why
sqlGeom1 = "SELECT AddGeometryColumn('featline', 'shape', 4326, 'LINESTRING', 2);"  

liteCur.execute(sqlGeom1)

row = liteCur.fetchone()
print "AddGeometryColumn returned '" + str(row[0])

dbConn.commit()

# Not sure why I have to run 'RGC' command and why it sometimes fails on the first attempt
sqlGeom2 = "SELECT RecoverGeometryColumn('featline', 'shape', 4326, 'LINESTRING', 2);"

liteCur.execute(sqlGeom2)

row = liteCur.fetchone()  # should return a 1
print "RecoverGeometryColumn returned '" + str(row[0])  

dbConn.commit()












