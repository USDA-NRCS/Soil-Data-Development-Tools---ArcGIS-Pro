# Not sure how this is supposed to work, but sounded interesting
from tkinter import *

class TextToolTip:

    def __init__(self, root, widget:Text, delay=0):
        
        self.parent = root
        self.delay = delay
        self.widget = widget
        
        self.top = None
        self.pos_x, self.pos_y = 0, 0

        self.i0, self.i1 = "", ""
        self.after_id = None

        self.msg=''
        
        self.bind()
        
    def bind(self):
        self.parent.bind('<Button>', self.hide)
        self.parent.bind('<Configure>', self.move)
        self.widget.tag_bind('sel', '<Enter>', self._display) #  remove this if hover tooltip is not necessary
        self.widget.tag_bind('sel', '<Leave>', self.tempHide)
                

    def tempHide(self, event):
        # similar to hide method the only difference is that this does't reset self.i0 and self.i1
        if self.top:
            self.top.destroy()
            self.top = None

    
    def hide(self, event=None):
        # destroys the top level
        if self.top:
            self.top.destroy()
            self.top = None
      
        self.i0, self.i1 = "", ""

    def move(self, event):
        # moves the tooltip along with the window
        if self.top:
            x, y = self.calcPos()
            if x and y:
                self.top.wm_geometry(f"+{x}+{y}")
                
            else:
                self.hide()

    def _display(self, event=None):
        # creates the tool tip
        if self.top is None:
            self.top = Toplevel(self.parent)
            self.top.wm_overrideredirect(True)
            
            label = Label(self.top, text=self.msg, justify='left',
                           background="black", foreground='white',
                          relief='solid', borderwidth=1)

            label.pack()
            
            x, y = self.calcPos()
            if x and y:
                self.top.wm_geometry(f"+{x}+{y}")
                    
            else:
                self.hide()
                return         

    def calcPos(self):  # calculates the position to display the tool tip
        
        try:
            self.widget.update_idletasks()
            b1, b2 = self.widget.bbox(self.i0), self.widget.bbox(self.i1)
            win_x, win_y = self.parent.winfo_x(), self.parent.winfo_y()
            return win_x + ((b2[0]+b1[0])//2), win_y + b1[1]

        except Exception:

            return None, None
            
    def show(self, msg, i0, i1):  
        """ pass in the index and the message (note: must pass a valid index ctrl+a might not provide
                correct index. A simple conditionl stmt to check should do the job.)"""
        if self.top:
            self.hide()

        if self.after_id:
            self.parent.after_cancel(self.after_id)
            self.after_id = None
        
        self.i0, self.i1 = i0, i1
        self.msg = msg
        self.after_id = self.parent.after(self.delay, self._display)
        
        
def print_count(event):
    if text.tag_ranges('sel'):
        global s0 , s1
        s0 = text.index("sel.first")
        s1 = text.index("sel.last")
        countstringstart = s0.split('.')[1]
        countstringend = s1.split('.')[1]

        waitshowballon(countstringstart, countstringend)

    else:
        tooltip.hide()    

    
root = Tk()

text = Text(root)
text.bind('<<Selection>>', print_count)
text.pack()

tooltip = TextToolTip(root, text, 500)  # pass in the rot, text widget and delay


def waitshowballon(cs, ce):
 
    tooltip.show(f"{cs}-{ce}", s0, s1)

root.mainloop()
