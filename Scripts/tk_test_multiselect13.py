import os
import tkinter as tk
from tkinter import filedialog as fd
#from tkinter import ttk

# Learning Tkinter GUI
# Simple listbox with multiple choices
# Version 1.0

# variable prefixes and object type
# ******************************************************************
# window : menu
# frm : frame
# cbx : checkbox
# ent : text entry
# lbl  : label text
# lbx : listbox
# txt  : text box entry allows multiple lines, etc.
# tab : tab
# ?
#

# tkinter.filedialog.askdirectory()

# ******************************************************************
def ShowSelected(event):
    surveyAreas = []
    selectedSet = lbxDownloads.curselection()

    if len(selectedSet) > 0:
        print("")
    
    for i in selectedSet:
        subFolder = lbxDownloads.get(i)
        surveyAreas.append(subFolder)
        
    for val in surveyAreas:
        print("\t", val)

    msgCount = str(len(surveyAreas)) + " survey areas selected for processing"
    print("\n", str(len(surveyAreas)), "survey areas selected for processing")
    lblCount.config(text=msgCount)

    return

# ******************************************************************
def SelectClear(event):
    surveyAreas = []
    lbxDownloads.selection_clear(0, tk.END)
    selectedSet = lbxDownloads.curselection()

    if len(selectedSet) == 0:
        msgCount = "No survey areas selected for processing"

    else:
        msgCount = str(len(selectedSet)) + " survey areas selected for processing"
      
    lblCount.config(text=msgCount)
    #print("Cleared set count: ", str(len(surveyAreas)))
    
    return

# ******************************************************************
def SelectAll(event):
    States = []
    lbxDownloads.focus_set()
    cnt = lbxDownloads.size()
    lbxDownloads.select_set(0, tk.END)
    selectedSet = lbxDownloads.curselection()
    print("Selected set count: ", str(len(selectedSet)))
    msgCount = str(len(selectedSet)) + " survey areas selected for processing"
    lblCount.config(text=msgCount)

    return

# ******************************************************************
def ValidateFilter(event):
    # Once the entFilter has been populated, make sure characters are valid
    # alpha-numeric or asterik. Do I need to add underscore or dash?
    wildCard = entFilter.get().upper()
    inputFolder = entFolder.get()
    
    newWildCard = ""

    for c in wildCard:
        num = ord(c)
        
        if num == 42 or num in range(48, 58) or num in range(65, 91) or num in range(97, 123):
            newWildCard += c
          
    entFilter.delete(0, tk.END)
    entFilter.insert(0, newWildCard)

    if newWildCard and inputFolder:
        GetDownloads()

    return
  
# ******************************************************************
def GetFolder(event):
    # Get local folder where SSURGO downloads are stored
    inputFolder = fd.askdirectory()
    sLen = max(30, int(round( (1.25 * len(inputFolder)), 0)))
    wildCard = entFilter.get().upper()
    
    #print("SSURGO Download Folder: '" + inputFolder + "'")
    entFolder.delete(0, tk.END)
    entFolder.configure(width=sLen)
    entFolder.insert(0, inputFolder)
    #print("entFolder state: '" + entFolder["state"])

    if inputFolder and wildCard:
        print("Getting download list")
        GetDownloads()
    
    return

# ******************************************************************
def GetDownloads():
    # Once the entFilter and entFolder have been populated,
    # try to get a listing of subfolders

    surveyList = list()  # list of download folder names
    matchedList = list() # list of 
    inputFolder = entFolder.get()

    color = "#ecedf3" # light gray
    color = "#bdc1d6" # medium gray
    color = "#ffa500" # orange
    color = "#00daff" # cyan
    color = "#00cc84" # medium green

    if not inputFolder:
        return

    dirList = os.listdir(inputFolder)
    dupList = list()

    # Check each subfolder to make sure it is a valid SSURGO dataset
    # validation: has 'soil_' prefix and contains a spatial folder and a soilsmu_a shapefile
    # and matches one of the AREASYMBOL values in the legend table

    # To list all SSURGO downloads, the user can enter a single asterik.
    wildCard = entFilter.get().replace("*", "")

    # 
    if wildCard == "":
      # Return any folder that contains spatial and tabular subfolders
      for subFolder in dirList:
        areasym = subFolder[-5:].upper()
      
        if os.path.isdir( os.path.join( inputFolder, os.path.join( subFolder, "spatial" ) ) ) and  \
          os.path.isdir( os.path.join( inputFolder, os.path.join( subFolder, "tabular" ) ) ):
          # Found the first and hopefully the only matching SSURGO download folder

          if not areasym in matchedList:
            # Found the first and hopefully the only matching SSURGO download folder.
            # Add the foldername to the import list
            matchedList.append(areasym)
            surveyList.append(subFolder)

          else:
            # Found another matching SSURGO download folder. 
            # Must be a different folder naming convention?
            # Skip downloading this version, but let the user know there is more than one match.
            dupList.append(subFolder)
            
    else:
      # Using wildcard filter on subdirectory name
      for subFolder in dirList:
        areasym = subFolder[-5:].upper()
        
        # Found another matching SSURGO download folder. 
        # Must be a different folder naming convention?
        # Skip downloading this version, but let the user know there is more than one match.
          
        if areasym.startswith(wildCard) and \
          os.path.isdir( os.path.join( inputFolder, os.path.join( subFolder, "spatial" ) ) ) and  \
          os.path.isdir( os.path.join( inputFolder, os.path.join( subFolder, "tabular" ) ) ):
          # Found the first and hopefully the only matching SSURGO download folder

          if not areasym in matchedList:
            # Found the first and hopefully the only matching SSURGO download folder.
            # Add the foldername to the import list
            matchedList.append(areasym)
            surveyList.append(subFolder)

          else:
            # Found another matching SSURGO download folder. 
            # Must be a different folder naming convention?
            # Skip downloading this version, but let the user know there is more than one match.
            dupList.append(subFolder)

    #if len(dupList) > 0:
    #  self.params[3].value = "Warning. Possible duplicate downloads found: " + ", ".join(dupList) 

    if len(surveyList) > 0:
      #self.params[2].filter.list = surveyList
      lbxDownloads.delete(0, tk.END)

      # Add the list of values to the listbox
      for item in range(len(surveyList)): 
          lbxDownloads.insert(tk.END, surveyList[item]) 
          lbxDownloads.itemconfig(item, bg=color)

      if len(surveyList) == 1:
          #self.params[2].values = surveyList

          # Add the list of values to the listbox
          for item in range(len(surveyList)): 
              lbxDownloads.insert(tk.END, countryList[item]) 
              lbxDownloads.itemconfig(item, bg=color)  # supposed to be gray

    else:
        lbxDownloads.insert(tk.END, "No Data")

    if len(dupList) > 0:
        msgDups = str(len(dupList)) + " apparent duplicate downloads found: " + ", ".join(dupList)
        #dupWidth = int(round((1.2 * len(msgDups)), 0))
        dupWidth = len(msgDups)
        lblDups.config(text=msgDups, width=dupWidth)

    else:
        lblDups.config(text="")

    btnFolder.configure(relief=tk.RAISED, state=tk.ACTIVE)
    print("btnFolder raised")
    
    del surveyList, matchedList, dupList, subFolder

    return
  
# ******************************************************************
def Close(event):
    window.destroy()
    
    return
  
# ******************************************************************
# ******************************************************************
# main
# ******************************************************************

window = tk.Tk()                       # Menu frame
window.title('Python Guides')          # Title bar for menu
window.geometry('500x500')             # Menu size
var = tk.StringVar()                   # Not sure how this is being used, but doesn't work without it

# Create frame top (control buttons go here)
frmTop = tk.Frame(master=window, width=150, height=40, relief=tk.RAISED, borderwidth=5)
frmTop.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Create frame second from top (entry widgets go here)
frmMiddle= tk.Frame(master=window, width=150, height=230, relief=tk.RAISED, borderwidth=5)
frmMiddle.pack(fill=tk.BOTH, expand=True)

# Create frame at the bottom (States listbox goes here)
frmBottom = tk.Frame(master=window, relief=tk.RAISED, borderwidth=5)
frmBottom.pack(fill=tk.BOTH, expand=True)

# Starting coordinates for top row buttons in top frame
row1X = 5
btnX = 1
row1Y = 1
row2Y = 60
row3Y = 150

# ******************************************************************
# Top Frame Widgets
# ******************************************************************

# Button-Print. Prints selected values to console.
btnWidth = 5
btnOK = tk.Button(master=frmTop, text="Print", height=1, width=btnWidth)
btnOK.place(x=4, y=row1Y)
btnOK.bind("<Button-1>", ShowSelected)
btnX += btnWidth

# Button-Select All. Select everything in listbox
btnWidth = 11
btnSelectAll = tk.Button(master=frmTop, text="Select All", height=1, width=btnWidth)
btnSelectAll.place(x=55, y=row1Y)
btnSelectAll.bind("<Button-1>", SelectAll)
btnX += btnWidth

# Button-Clear Selection. Deselect everything in listbox.
btnWidth = 11
btnClearSelection = tk.Button(master=frmTop, text="Clear Selection", height=1, width=btnWidth)
btnClearSelection.place(x=147, y=row1Y)
btnClearSelection.bind("<Button-1>", SelectClear)
btnX += btnWidth

# Button-Quit. Closes menu.
btnWidth = 5
btnExit = tk.Button(master=frmTop, text="Quit", height=1, width=btnWidth)
btnExit.place(x=240, y=row1Y)
btnExit.bind("<Button-1>", Close)
btnX += btnWidth

# ******************************************************************
# Middle Frame Widgets
# ******************************************************************
# Entry for areasymbol filter
entFilter = tk.Entry(master=frmMiddle, width = 20)
entFilter.place(x=5, y=15)
entFilter.bind("<FocusOut>", ValidateFilter)

# Label for areasymbol filter
lblFilter = tk.Label(master=frmMiddle, text="Enter areasymbol filter or asterik (*) for no filter")
lblFilter.place(in_=entFilter, relx=1.0, x=10, rely=0)

# Entry box for input folder
entFolder = tk.Entry(master=frmMiddle, width = 40)
entFolder.place(x=5, y=65)

# Label for input folder box
lblFolder = tk.Label(master=frmMiddle, text="Folder containing SSURGO downloads")
#lblFolder.place(in_=entFolder, relx=0.0, x=0, y=2.0, rely=0.0, anchor='sw')
lblFolder.place(in_=entFolder, relx=0.0, x=0, y=2.0, rely=0.0, anchor='sw', bordermode=tk.OUTSIDE)

# Button-Browser for input folder
folderIcon = tk.PhotoImage(file="folder_icon.png")
btnFolder = tk.Button(master=frmMiddle, image=folderIcon, relief=tk.RAISED)
btnFolder.place(in_=entFolder, relx=1.0, x=5, rely=0)
btnFolder.bind("<ButtonRelease-1>", GetFolder)

# Label for selection count
lblCount = tk.Label(master=frmMiddle, text="No survey areas selected", anchor="w", width=30)
lblCount.place(x=2, y=165)

# Label for duplicate downloads (different folder names, same areasymbol)
lblDups = tk.Label(master=frmMiddle, text="", anchor="w", width=40)
lblDups.place(x=2, y=185)

# ******************************************************************
# Bottom Frame Widgets
# ******************************************************************

# Create the text label at the top of the second frame
# , font=("Helvetica", 12)
lblShow = tk.Label(master=frmBottom, text = "Select SSURGO Downloads to Import", padx=2, pady=2)
lblShow.place(x=5, y=5)

# Create listbox in the bottom frame
downloadList = tk.StringVar()
lbxDownloads = tk.Listbox(master=frmBottom, listvariable=downloadList, height=20, selectmode='multiple')
lbxDownloads.pack(padx=5, pady=35, expand=True, fill="both")
lbxDownloads.bind("<FocusOut>", ShowSelected)



window.mainloop() 
