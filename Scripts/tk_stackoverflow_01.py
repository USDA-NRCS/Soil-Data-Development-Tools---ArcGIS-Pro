# TKinter GUI layout using tk.Frames and grids. Example from stackoverflow

import tkinter as tk

root = tk.Tk()
root.title('Model Definition')
root.geometry('{}x{}'.format(460, 350))

# create all of the main containers
top_frame = tk.Frame(root, bg='cyan', width=450, height=50, pady=3)
center = tk.Frame(root, bg='gray2', width=50, height=40, padx=3, pady=3)
btm_frame = tk.Frame(root, bg='white', width=450, height=45, pady=3)
btm_frame2 = tk.Frame(root, bg='lavender', width=450, height=60, pady=3)

# layout all of the main containers
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

top_frame.grid(row=0, sticky="ew")
center.grid(row=1, sticky="nsew")
btm_frame.grid(row=3, sticky="ew")
btm_frame2.grid(row=4, sticky="ew")

# create the widgets for the top tk.Frame
model_label = tk.Label(top_frame, text='Model Dimensions')
width_label = tk.Label(top_frame, text='Width:')
length_label = tk.Label(top_frame, text='Length:')
entry_W = tk.Entry(top_frame, background="pink")
entry_L = tk.Entry(top_frame, background="orange")

# layout the widgets in the top tk.Frame
model_label.grid(row=0, columnspan=3)
width_label.grid(row=1, column=0)
length_label.grid(row=1, column=2)
entry_W.grid(row=1, column=1)
entry_L.grid(row=1, column=3)

# create the center widgets
center.grid_rowconfigure(0, weight=1)
center.grid_columnconfigure(1, weight=1)

ctr_left = tk.Frame(center, bg='blue', width=100, height=190)
ctr_mid = tk.Frame(center, bg='yellow', width=250, height=190, padx=3, pady=3)
ctr_right = tk.Frame(center, bg='green', width=100, height=190, padx=3, pady=3)

ctr_left.grid(row=0, column=0, sticky="ns")
ctr_mid.grid(row=0, column=1, sticky="nsew")
ctr_right.grid(row=0, column=2, sticky="ns")

root.mainloop()
