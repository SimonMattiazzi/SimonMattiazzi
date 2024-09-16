"""
This is a program that takes the input array of director angles
in [0, pi] and converts it to the corresponding output,
suitable for upload to SLM.

It takes care of:
    - importing the input (either .csv or .npy)
    - transformation of angles [0, pi] or [0, 2pi], measured from cartesian point (1,0) in counter-clockwise direction
        to graylevel [0-255]
    - resizing in case of wrong array sizes at all levels (special care about interpolation!)
    - mapping the graylevels to the SLM phase outputs according to the 
    chosen map (dictionary) from the manual calibration. Possible options:
        a) 2pi average over the whole sensor (the relation is quasi linear)
        b) 2pi pixel by pixel raw
        c) 2pi pixel by pixel filtered (gaussian convolution))
        d) 4pi average over the whole sensor (the relation is quasi linear)
        e) 4pi pixel by pixel raw
        f) 4pi pixel by pixel filtered (gaussian convolution))
    
    * if you use 2pi map, you must set SLM range to [0, 2.2 pi], 454 nm
    * if you use 4pi map, you must set SLM range to [0, 5 pi], 454 nm
    
    - saving the output array to the correct format for SLM
        (axes ticks in both directions, number format,
        correct size and shape, CSV file format),
        overwrite prevention with automatic numbering "_i"
    - plotting 6 images:
        - input angles,
        - what you should see on pol. camera
        - calculated output for SLM,
        - inverse output from inverse dictionaty in angles 
        - inverse output as seen on pol. camera
        - difference between inverse and input in angles

It is now a GUI.    

Author: Simon
"""


import tkinter as tk
from tkinter import filedialog, ttk
import os 
import numpy as np
import SLM_module as SLM
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from SLM_module import resize, dimX_final, dimY_final



#----------------------------------------------------#
# JUST RUN THIS FILE (F5 in Spyder)
# do not change anything below


# it may open a new window in the background!
#----------------------------------------------------#







































    

def import_map(maptype):
    
    """
    Imports the appropriate calibration map and its inverse based on the selected map type. 
    The function updates the UI label to reflect the progress and the selected map type.
    The global variable to control the transform from (0, pi) or (0, 2pi) is set.
    """    
    
    mapselect_label.config(text=f"Please wait ...", bg="orangered1")
    root.update_idletasks()
    if maptype:
        mapselect_label.config(text=f"Map type selected: {maptype}", bg="palegreen4")
        
    dict_maps = {"2pi pixel-by-pixel raw": "SLM_maps/map_pix_res4_raw.npy",
                 "2pi pixel-by-pixel filtered": "SLM_maps/map_pix_res4_filt20.npy",
                 "2pi average": "SLM_maps/map_avg_res4.npy", 
                 "4pi pixel-by-pixel raw": "SLM_maps/map_pix_res4_raw_4pi.npy",
                 "4pi pixel-by-pixel filtered": "SLM_maps/map_pix_res4_filt20_4pi.npy",
                 "4pi average": "SLM_maps/map_avg_res4_4pi.npy"}
                
    inv_dict_maps = {"2pi pixel-by-pixel raw": "SLM_maps/map_pix_inv_res4_raw.npy",
                     "2pi pixel-by-pixel filtered": "SLM_maps/map_pix_inv_res4_filt20.npy",
                     "2pi average": "SLM_maps/map_avg_inv_res4.npy",
                     "4pi pixel-by-pixel raw": "SLM_maps/map_pix_inv_res4_raw_4pi.npy",
                     "4pi pixel-by-pixel filtered": "SLM_maps/map_pix_inv_res4_filt20_4pi.npy",
                     "4pi average": "SLM_maps/map_avg_inv_res4_4pi.npy"}
    
    global map1
    global map_inv
    global transform_mode
    
    if maptype in ["4pi pixel-by-pixel raw", "4pi pixel-by-pixel filtered", "4pi average"]:
        transform_mode = "4pi"
    else:
        transform_mode = "2pi"
    print("transform mode set to: ", transform_mode)
    
    if maptype  in ["2pi average", "4pi average"]:
        map1 = (np.load(dict_maps[maptype], allow_pickle=True)).item()
        map_inv = (np.load(inv_dict_maps[maptype], allow_pickle=True)).item()
    
    else:
        map1 = np.load(dict_maps[maptype])
        map_inv = np.load(inv_dict_maps[maptype])



# Function to import file
def import_file():
    """
    Opens a file dialog for the user to select a file, imports the selected file 
    (different procedures for a CSV or NPY format),
    and processes the data to be compatible with the map where inputs match the
    camera readings in AOLP [0-255].
    The selected file path is stored in `in_file_path` global variable.
    The function also updates a UI label to reflect the status of the import process.
    
    """
    in_file_path = filedialog.askopenfilename()
    global in_file
    
    if in_file_path:
        in_file_label.config(text=f"Please wait ...", bg="orangered1")
        root.update_idletasks()
        in_file_name, extension = os.path.splitext(os.path.split(in_file_path)[1])
        in_file_label.config(text=f"Imported file: {in_file_name}", bg="palegreen4")

        if extension == ".csv":
            in_file = np.loadtxt(in_file_path, delimiter=",")
        elif extension == ".npy":
            in_file = np.load(in_file_path) 
            
        in_file = in_file 





def confirm_out(name):
    """
    Confirms and formats the output file name for saving data, adding a `.csv` 
    extension if it is not yet present. It is stored as a global variable.
    The function also updates a UI label to display the confirmed output name.
    """
    
    global output_name
    output_name = os.path.join("SLM_outputs",name)
    if os.path.splitext(output_name)[1]!=".csv": # if not .csv extension
        output_name = os.path.splitext(output_name)[0] + ".csv"
    outname_label.config(text=f"Output name: {output_name}", bg="palegreen4")


def calculate():
    """
    Calculate the output and show all 4 plots for testing. It also manipulates
    the UI label to show the proces status.
    """
    calc_label.config(text="Please wait ...", bg="orangered1")
        
    
    # show input in ANGLES:
    fig = Figure(figsize = (4, 2.5), dpi = 120)
    plot1 = fig.add_subplot(111)
    plot1.set_title(r"input in angles [0, $2\pi$] rad") 
    img = plot1.imshow(in_file, cmap="Greys_r", clim=(0, 2*np.pi))
    #img = plot1.imshow(SLM.transform_input_inv(in_file, transform_mode=transform_mode), cmap="Greys_r", clim=(0, 2*np.pi))
    fig.colorbar(img, ax=plot1, fraction=0.036, pad=0.04)
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master = root) 
    canvas.draw() 
    canvas.get_tk_widget().grid(row=5, column=0, pady=(0, 0), padx=(10, 0), sticky="w") 


    # show how you see input with pol. cam:
    fig12 = Figure(figsize = (4, 2.5), dpi = 120)
    plot12 = fig12.add_subplot(111)
    #plot12.set_title(r"transf. input [0, $\pi$] $\Rightarrow$ [0, 255]") 
    plot12.set_title(r"Input as seen on polarizing camera")  
    
    if transform_mode == "4pi":
        print("in 4pi mode")
        #razdeli v 2 
        pol_cam_0 = SLM.transform_input(in_file, transform_mode=transform_mode) * 2
        pol_cam = np.where(pol_cam_0 > 255, pol_cam_0 - 255, pol_cam_0)
        img12 = plot12.imshow(pol_cam, cmap="Greys_r", clim=(0, 255))

    else:
        img12 = plot12.imshow(SLM.transform_input(in_file, transform_mode=transform_mode), cmap="Greys_r", clim=(0, 255))
        
    fig12.colorbar(img12, ax=plot12, fraction=0.036, pad=0.04)
    fig12.tight_layout()
    canvas = FigureCanvasTkAgg(fig12, master = root) 
    canvas.draw() 
    canvas.get_tk_widget().grid(row=5, column=1, pady=(0, 0), padx=(10, 0), sticky="w") 
    
    
    # show mapped output in [0, 1023]:
    root.update_idletasks()
    fig2 = Figure(figsize = (4, 2.5),  dpi = 120)
    plot2 = fig2.add_subplot(111)
    global map_calibration
    map_calibration = SLM.mapping(SLM.transform_input(in_file, transform_mode=transform_mode), map1)
    plot2.set_title("Output for SLM [0-1023]")
    img2=plot2.imshow(map_calibration, cmap="Greys_r")
    fig2.colorbar(img2, ax=plot2, fraction=0.036, pad=0.04)
    fig2.tight_layout()
    canvas2 = FigureCanvasTkAgg(fig2, master = root) 
    canvas2.draw() 
    canvas2.get_tk_widget().grid(row=5, column=2, pady=(0, 0), padx=(10, 0), sticky="w")
    
    
    # show simulation in graylevels (what you will see on camera):
    fig3 = Figure(figsize = (4, 2.5),  dpi = 120)
    plot3 = fig3.add_subplot(111)
    sim = SLM.mapping(map_calibration, map_inv)
    
    if transform_mode == "4pi":
        print("in 4pi mode")
        pol_cam_sim_0 = sim * 2
        pol_cam_sim = np.where(pol_cam_sim_0 > 255, pol_cam_sim_0 - 255, pol_cam_sim_0)
        img3 = plot3.imshow(pol_cam_sim, cmap="Greys_r", clim=(0,255))
    else:    
        img3 = plot3.imshow(sim, cmap="Greys_r", clim=(0,255))
        
    plot3.set_title("Inverse simulation as seen on pol. cam.")
    fig3.colorbar(img3, ax=plot3, fraction=0.036, pad=0.04)
    fig3.tight_layout()
    canvas3 = FigureCanvasTkAgg(fig3, master = root) 
    canvas3.draw() 
    canvas3.get_tk_widget().grid(row=6, column=1, pady=(0, 0), padx=(10, 0), sticky="w")
    
    
    
    # show inverse simulation in angles
    fig32 = Figure(figsize = (4, 2.5),  dpi = 120)
    plot32 = fig32.add_subplot(111)
    sim_angles = SLM.transform_input_inv(sim, transform_mode=transform_mode)
    
    img32 = plot32.imshow(sim_angles, cmap="Greys_r", clim=(0,2*np.pi))
        
    plot32.set_title("Inverse simulation: angles [rad]")
    fig32.colorbar(img32, ax=plot32, fraction=0.036, pad=0.04)
    fig32.tight_layout()
    canvas32 = FigureCanvasTkAgg(fig32, master = root) 
    canvas32.draw() 
    canvas32.get_tk_widget().grid(row=6, column=0, pady=(0, 0), padx=(10, 0), sticky="w")
    
    
    
    # show difference between input and simulation in ANGLES:
    fig4 = Figure(figsize = (4, 2.5),  dpi = 120)
    plot4 = fig4.add_subplot(111)
    plot4.set_title("Difference input-sim in angles [rad]")
    img4 = plot4.imshow(resize(in_file, (dimY_final, dimX_final), preserve_range=True, order=1)-sim_angles, cmap="Greys_r")
    fig4.colorbar(img4, ax=plot4, fraction=0.036, pad=0.04)
    fig4.tight_layout()
    canvas4 = FigureCanvasTkAgg(fig4, master = root) 
    canvas4.draw() 
    canvas4.get_tk_widget().grid(row=6, column=2, pady=(0, 0), padx=(10, 0), sticky="w")

    calc_label.config(text="Finished. Don't forget to save.", bg="palegreen4")
    
    
def save_output():
    SLM.nparray_to_csv(map_calibration, filename = output_name)
    save_label.config(text="Output saved", bg="palegreen4")



# Create the main window
root = tk.Tk()
root.title("SLM converter")
root.geometry("1500x900")
root.grid_propagate(False)


# Dropdown menu for map selection
map_label = tk.Label(root, text="Select Map:")
map_label.grid(row=0, column=0, pady=(10, 0), padx=(10, 0), sticky="w")
map_options = ["2pi pixel-by-pixel raw", "2pi pixel-by-pixel filtered", "2pi average", "4pi pixel-by-pixel raw", "4pi pixel-by-pixel filtered", "4pi average"]
map_var = tk.StringVar()
map_dropdown = ttk.Combobox(root, textvariable=map_var, values=map_options)
map_dropdown.grid(row=0, column=0, pady=(10, 0), padx=(80, 0), sticky="w")

# Confirm button for map selection and label to display output
confirm_btn = tk.Button(root, text="Confirm", command=lambda: import_map(map_var.get()))
confirm_btn.grid(row=0, column=0, pady=(10, 0), padx=(230, 0), sticky="w")
mapselect_label = tk.Label(root, text="")
mapselect_label.grid(row=0, column=1, pady=(10, 0), padx=(10, 0), sticky="w")

# Import file button and label and label to display output
map_label = tk.Label(root, text="(must be .csv or .npy. Angles range [0, pi] for 2pi and [0, 2pi] for 4pi map.)")
map_label.grid(row=1, column=0, pady=(10, 0), padx=(120, 0), sticky="e")
import_btn = tk.Button(root, text="Import Input File ", command=import_file)
import_btn.grid(row=1, column=0, pady=(10, 0), padx=(10, 0), sticky="w")
in_file_label = tk.Label(root, text="")
in_file_label.grid(row=1, column=1, pady=(10, 0), padx=(10, 0), sticky="w")

# Output filename entry and label
output_label = tk.Label(root, text="Output Filename:")
output_label.grid(row=2, column=0, pady=(10, 0), padx=(10, 0), sticky="w")
output_entry = tk.Entry(root)
output_entry.grid(row=2, column=0, pady=(10, 0), padx=(120, 0), sticky="w")

# Confirm button for output filename and label to display output
confirm_out_btn = tk.Button(root, text="Confirm", command=lambda: confirm_out(output_entry.get()))
confirm_out_btn.grid(row=2, column=0, pady=(10, 0), padx=(230, 0), sticky="w")
outname_label = tk.Label(root, text=f"")
outname_label.grid(row=2, column=1, pady=(10, 0), padx=(10, 0), sticky="w")

# Calculate button
calc_btn = tk.Button(root, text="CALCULATE", command=calculate)
calc_btn.grid(row=3, column=0, pady=(10, 0), padx=(10, 0), sticky="w")
calc_label = tk.Label(root, text=f"")
calc_label.grid(row=3, column=1, pady=(10, 0), padx=(10, 0), sticky="w")

# Save output button
save_btn = tk.Button(root, text="Save Output", command=save_output)
save_btn.grid(row=4, column=0, pady=(10, 0), padx=(10, 0), sticky="w")
save_label = tk.Label(root, text=f"")
save_label.grid(row=4, column=1, pady=(10, 0), padx=(10, 0), sticky="w")

# Start the main event loop
root.mainloop()
