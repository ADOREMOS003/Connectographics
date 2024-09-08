#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import csv

import os
import subprocess
import sys
from datetime import datetime
import shutil

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from tkinter import filedialog
import tkinter.simpledialog as simpledialog
from PIL import Image, ImageTk


# In[2]:


os.chdir(os.getcwd())

subject_directory = ""
data_folder = ""



def create_link_files(file, brain_regions):
    matrix = pd.read_csv(file, sep=",", header=None)

    brain_regions = matrix.iloc[0, 1:].values  # First row, excluding the first cell
    matrix_values = matrix.iloc[1:, 1:].values  # Remove the first row and column

    
    flattened_data = []

    for i in range(matrix_values.shape[0]):
        for j in range(matrix_values.shape[1]):
            connection_strength = matrix_values[i, j]

            try:
                connection_strength = float(connection_strength)
            except ValueError:
                continue

            brain_region_1 = brain_regions[i]
            brain_region_2 = brain_regions[j]
            type = "0"
            if abs(connection_strength) > 0.5:
                type = "type=3,"
            elif abs(connection_strength) >= 0.3:
                type = "type=2,"
            elif abs(connection_strength) >= 0.1:
                type = "type=1,"
            else:
                type = "type=0,"

            flattened_data.append([brain_region_1, brain_region_2, type, connection_strength])

    df = pd.DataFrame(flattened_data, columns=['Region 1', 'Region 2', 'Type', 'Connection Strength'])
    
    def process_dataframe(df):
        numbers = np.arange(0, 164)
        regions = pd.read_csv("subject3.csv").drop("Unnamed: 0", axis=1).columns
        structure = pd.read_csv("structure.label.txt", sep=" ", header=None)
        codes = pd.read_csv("Regions_Codes.csv")

        
        df["Region 1"] = df["Region 1"].replace(np.arange(0, 164), regions)
        df["Region 2"] = df["Region 2"].replace(np.arange(0, 164), regions)



        df["Region 1"] = df["Region 1"].replace(regions, codes["newCode"])
        df["Region 2"] = df["Region 2"].replace(regions, codes["newCode"])

        df = df[df["Region 1"] != "ctx_lh_Unknown"]
        df = df[df["Region 2"] != "ctx_lh_Unknown"]
        df = df[df["Region 1"] != "ctx_rh_Unknown"]
        df = df[df["Region 2"] != "ctx_rh_Unknown"]
        df = df[df['Connection Strength'].astype(float) != 0]
        

        if "Type" in df.columns:
            df["Connection Strength"] = df["Type"] + "score=" + df["Connection Strength"].astype(str)
            df = df.drop("Type", axis=1)
        else:
            print("Warning: 'Type' column not found in DataFrame")
            
        df["Region 1"] = df["Region 1"].str.replace(" ", " ")
        df["Region 2"] = df["Region 2"].str.replace(" ", " ")
        df["Connection Strength"] = df["Connection Strength"].str.replace(" ", " ")

        
        
        return df


    df = process_dataframe(df)
    return df




def generateFile():
    global data_folder
    data_folder = subject_directory + "/data"
    os.makedirs(data_folder, exist_ok=True)   
    save_path = os.path.join(data_folder, "links.txt")
    

    matrix = upload_matrices()
    links = create_link_files(matrix, np.arange(0, 164))

    links.to_csv(save_path, sep="\t", header=None, index=None)
    
    print("Links file generated in: " + save_path)

    
    
    
def generate_conf_file(filename):
    content = f"""<plot>
    init_counter = heatmap:0
    #post_increment_counter = heatmap:1
    type         = heatmap
    file         = data/{filename}.txt
    color        = eval((split(",","conf(hm_colors)"))[counter(heatmap)])
    r1           = eval(sprintf("%fr",conf(hm_r)-counter(heatmap)*(conf(hm_w)+conf(hm_pad))))
    r0           = eval(sprintf("%fr",conf(hm_r)-counter(heatmap)*(conf(hm_w)+conf(hm_pad))+conf(hm_w)))

    stroke_color = white
    stroke_thickness = 3

    </plot>"""
    with open(subject_directory+"/"+str(filename)+".conf", 'w') as file:
        file.write(content)
    print(f"Configuration file '{filename}' has been generated.")
    
    conf_file = filename + ".conf"
    circos_conf_path = subject_directory + "/circos.conf"
    
    modify_circos_conf(circos_conf_path, conf_file)
    
    
def modify_circos_conf(circos_conf_path, example_conf_file):
    # Read the contents of the circos.conf file
    with open(circos_conf_path, 'r') as file:
        lines = file.readlines()
    
    # Find the <plots> section and insert the include line after it
    new_lines = []
    plots_section_found = False

    for line in lines:
        new_lines.append(line)
        
        if "<plots>" in line.strip() and not plots_section_found:
            plots_section_found = True
            # Add the include line after the <plots> section
            include_line = f"<<include {example_conf_file}>>\n"
            new_lines.append(include_line)
    
    # Write the modified content back to the circos.conf file
    with open(circos_conf_path, 'w') as file:
        file.writelines(new_lines)
    
    print(f"Modified {circos_conf_path} to include {example_conf_file} under <plots> section.")




def create_or_select_subject_folder():
    # Ask the user if they want to create a new folder or select an existing one
    response = tk.messagebox.askyesno("Select or Create Folder", "Do you want to create a new subject folder? (Click 'No' to select an existing one)")

    if response:  # User wants to create a new folder
        create_subject_folder()
    else:  # User wants to select an existing folder
        select_subject_folder()

def select_subject_folder():
    global subject_directory
    selected_dir = filedialog.askdirectory(title="Select Subject Folder")
    if selected_dir:
        subject_directory = selected_dir
        print(f"Selected folder: {subject_directory}")
        

def create_subject_folder():
    global subject_directory
    
    master_folder = "dependencies"
    
    base_dir = filedialog.askdirectory(title="Select Base Directory")
    if not base_dir:
        return 
    
    folder_name = simpledialog.askstring("Folder Name", "Enter a name for the new folder:")
    if not folder_name:
        return
    
    subject_folder = os.path.join(base_dir, folder_name)
    os.makedirs(subject_folder, exist_ok=True)
    
    subject_directory = subject_folder
    print(f"Created and selected folder: {subject_directory}")
    
    try:
        shutil.copytree(master_folder, subject_folder, dirs_exist_ok=True)
    except Exception as e:
        print(f"Error copying files: {e}")
        return

# Update all functions to use the `subject_directory` variable

def runCircos():
    #if not subject_directory:
        #tk.messagebox.showerror("Error", "Please create or select a subject folder first.")
       # return
    
    try:
        display_image("Loading.png", 750, 750)

        original_directory = os.getcwd()
        os.chdir(subject_directory)  # Use the selected/created subject folder

        process = subprocess.Popen(
            ["circos"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        for line in iter(process.stdout.readline, ''):
            if line:
                console.write(line)
                console.update_idletasks()

        for line in iter(process.stderr.readline, ''):
            if line:
                console.write(line)
                console.update_idletasks()

        process.stdout.close()
        process.stderr.close()
        process.wait()

        os.chdir(original_directory)
        generated_image_path = os.path.join(subject_directory, "circos_v9.png")
        if os.path.exists(generated_image_path):
            display_image(generated_image_path, 750, 750)
        else:
            console.write("Error: The generated image was not found.\n")

    except subprocess.CalledProcessError as e:
        console.write(f"Error while running Circos: {e}\n")
    except Exception as e:
        console.write(f"An unexpected error occurred: {e}\n")
        
        
        
def read_freesurfer_data(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    structures = []
    for line in lines:
        if line.startswith('#') or line.strip() == '':
            continue
        parts = line.split()
        if len(parts) == 10:
            structure = {
                'StructName': parts[0],
                'NumVert': int(parts[1]),
                'SurfArea': int(parts[2]),
                'GrayVol': int(parts[3]),
                'ThickAvg': float(parts[4]),
                'ThickStd': float(parts[5]),
                'MeanCurv': float(parts[6]),
                'GausCurv': float(parts[7]),
                'FoldInd': float(parts[8]),
                'CurvInd': float(parts[9])
            }
            structures.append(structure)
    return structures


def generate_heatmap(lh,rh,metric):
    lh_data= read_freesurfer_data(lh)
    rh_data = read_freesurfer_data(rh)
    lh_data = pd.DataFrame(lh_data)
    rh_data = pd.DataFrame(rh_data)
    lh_data["StructName"] = "ctx_lh_" + lh_data["StructName"]
    rh_data["StructName"] = "ctx_rh_" + rh_data["StructName"]
    combined_data = pd.concat([lh_data,rh_data],axis=0,ignore_index=True)
    combined_df = pd.DataFrame(combined_data)
    codes = pd.read_csv("Regions_Codes.csv")
    
       
    # Create a mapping dictionary for replacement
    replacement_map = codes.set_index('Region')['newCode'].to_dict()
    
    # Replace values in 'StructName' column using the replacement map
    combined_df["StructName"] = combined_df["StructName"].replace(replacement_map)
    
    
    
    output_file_path = os.path.join(data_folder, f"{metric}.txt")
    combined_df[["StructName", metric]].to_csv(output_file_path, header=None, index=False, sep="\t")


# In[3]:


class ToolTip:
    def __init__(self, widget, text, x_offset=0, y_offset=0):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self._id = None
        self.x_offset = x_offset
        self.y_offset = y_offset

        # Bind events
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.schedule_hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip or not self.text:
            return

        # Calculate the position with manual offsets
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + self.widget.winfo_width() + self.x_offset
        y += self.widget.winfo_rooty() + self.y_offset

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip, text=self.text, background="white", relief='solid', borderwidth=1, font=("Arial", 12))
        label.pack(ipadx=1)

        self.tooltip.bind("<Enter>", self.cancel_hide_tooltip)
        self.tooltip.bind("<Leave>", self.schedule_hide_tooltip)

    def schedule_hide_tooltip(self, event):
        self._id = self.widget.after(100, self.hide_tooltip)

    def cancel_hide_tooltip(self, event):
        if self._id:
            self.widget.after_cancel(self._id)
            self._id = None

    def hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class ConsoleText(tk.Text):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(state=tk.DISABLED)

    def write(self, message):
        self.config(state=tk.NORMAL)
        self.insert(tk.END, message)
        self.see(tk.END)  # Scroll to the end
        self.config(state=tk.DISABLED)

    def flush(self):
        pass            

            
def upload_matrices():
    file = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"),("TXT files", "*.txt")])
    return file

root = ctk.CTk()
root.title("Connectographics")
root.geometry("1920x1080")
my_font = ctk.CTkFont(family="Arial", size=25)
ctk.set_appearance_mode("dark")


img_refs = []



def store_csv(): #Stores the file paths of the files uploaded
    global file_path
    file_path = upload_matrices()
    if file_path:
        generateFile(file_path)
        
def display_file_info(file_paths): #Displays the path of the file selected from the upload button
    file_names = [os.path.basename(file) for file in file_paths]

    for file in file_paths:
        file_label = ctk.CTkLabel(btn_frame, text=f"Selected File:\n {file}")
        file_label.pack(pady=10, anchor="n")


def display_image(image_path, width=None, height=None):
    for widget in frame.winfo_children():
        widget.destroy()

    img = Image.open(image_path)
    if width and height:
        img = img.resize((width, height))
    img = ImageTk.PhotoImage(img)

    
    label = ctk.CTkLabel(frame, image=img, text="")
    label.image = img
    label.pack(anchor="center")

    
    img_refs.append(img)
    
selected_files = {}

def open_new_window():
    
    def store_lh_file():
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            selected_files['lh'] = file_path
            print(f"Selected LH file: {file_path}")
        else:
            messagebox.showwarning("No file selected", "Please select a left hemisphere file.")
    
    def store_rh_file():
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            selected_files['rh'] = file_path
            print(f"Selected RH file: {file_path}")
        else:
            messagebox.showwarning("No file selected", "Please select a right hemisphere file.")

    def generate_heatmap_btn():
        metric = heatmap_type_entry.get()
        if 'lh' in selected_files and 'rh' in selected_files and metric:
            generate_heatmap(selected_files['lh'], selected_files['rh'], metric)
            generate_conf_file(metric)
        else:
            messagebox.showwarning("Missing information", "Please select both hemisphere files and specify the heatmap type.")
    
    new_window = ctk.CTkToplevel(root)
    new_window.title("Generate Heatmap")
    new_window.geometry("600x500")
    new_window.resizable(False, False) 

    upload_lh_btn = ctk.CTkButton(new_window, text="Upload Left Hemisphere File", height=70, width=350, corner_radius=5, command=store_lh_file)
    upload_lh_btn.pack(pady=10)
    ToolTip(upload_lh_btn, "Upload the left hemisphere data.", x_offset=10, y_offset=0)

    upload_rh_btn = ctk.CTkButton(new_window, text="Upload Right Hemisphere File", height=70, width=350, corner_radius=5, command=store_rh_file)
    upload_rh_btn.pack(pady=10)
    ToolTip(upload_rh_btn, "Upload the right hemisphere data.", x_offset=10, y_offset=0)

    heatmap_type_label = ctk.CTkLabel(new_window, text="Heatmap Type:", height=40)
    heatmap_type_label.pack(pady=10)
    
    heatmap_type_entry = ctk.CTkEntry(new_window, width=350)
    heatmap_type_entry.pack(pady=10)
    
    generate_btn = ctk.CTkButton(new_window, text="Generate Heatmap", height=70, width=350, corner_radius=5, command=generate_heatmap_btn)
    generate_btn.pack(pady=20)
    ToolTip(generate_btn, "Creates the heatmap based on the selected files and type.\nNumVert, SurfArea, GrayVol, ThickAvg, ThickStd, MeanCurv, GausCurv, FoldInd, CurvInd", x_offset=10, y_offset=0)
    


#Renders the logo and name
logo = Image.open("logo.png")
logo = logo.resize((300, 100))
logo = ImageTk.PhotoImage(logo)

   
label = ctk.CTkLabel(root, image=logo, text="") 
label.pack(pady=20, anchor="center")

img_refs.append(logo)

upload_icon = Image.open("upload_icon.png")
upload_icon = upload_icon.resize((64, 64))
upload_icon = ImageTk.PhotoImage(upload_icon)
img_refs.append(upload_icon)


folder_icon = Image.open("folder_icon.png")
folder_icon = folder_icon.resize((64, 64))
folder_icon = ImageTk.PhotoImage(folder_icon)


link_icon = Image.open("link_icon.png")
link_icon = link_icon.resize((64, 64))
link_icon = ImageTk.PhotoImage(link_icon)


gen_icon = Image.open("generate_icon.png")
gen_icon = gen_icon.resize((64, 64))
gen_icon = ImageTk.PhotoImage(gen_icon)


circos_icon = Image.open("run_circos_icon.png")
circos_icon = circos_icon.resize((64, 64))
circos_icon = ImageTk.PhotoImage(circos_icon)


#Holds all of the button on the left side of the GUI
btn_frame = ctk.CTkFrame(master=root, width=200, height=800, corner_radius=5)
btn_frame.pack(padx=0, pady=0, side="left", anchor="nw")
btn_frame.pack_propagate(False)

#Holds the generated connectogram when it is generated
frame = ctk.CTkFrame(master=root, width=800, height= 800, corner_radius=5)
frame.pack(pady=0, padx=100, side="left", anchor="nw")
frame.pack_propagate(False)



console_frame = ctk.CTkFrame(root, width=700, height=800)
console_frame.pack(padx=0, pady=0, side="right", anchor="ne")
console_frame.pack_propagate(False)

# Console Text Widget
console = ConsoleText(console_frame, wrap=tk.WORD, fg="white", bg="black")
console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

sys.stdout = console
sys.stderr = console

bg_color = "#2b2b2b"




folder_frame = ctk.CTkFrame(btn_frame, fg_color = bg_color)
folder_frame.pack(pady=10)
folder_btn = tk.Label(master=folder_frame, image=folder_icon, cursor="hand2", bg=bg_color, highlightthickness=0)
folder_btn.pack(pady=30, anchor="center")
img_refs.append(folder_icon)
folder_btn.bind("<Button-1>", lambda event: create_or_select_subject_folder())
folder_text = tk.Label(folder_frame, text="Select/Create Folder", font=("Arial", 12), bg=bg_color, fg="white")
folder_text.pack()
ToolTip(folder_btn, "Select an existing or create a new folder for a subject.", x_offset=10, y_offset=0)




#Generate link files button
gen_frame = ctk.CTkFrame(btn_frame, fg_color = bg_color)
gen_frame.pack(pady=10)
gen_btn = tk.Label(master=gen_frame, image=link_icon, cursor="hand2", bg=bg_color, highlightthickness=0)
gen_btn.pack(pady=30, anchor="center")
img_refs.append(link_icon)
gen_btn.bind("<Button-1>", lambda event: generateFile())
gen_text = tk.Label(gen_frame, text="Generate Links", font=("Arial", 12), bg=bg_color, fg="white")
gen_text.pack()
ToolTip(gen_btn, "Generates a link file in the subject folder from the uploaded matrix.", x_offset=10, y_offset=0)




#Generate heatmaps
heatmap_frame = ctk.CTkFrame(btn_frame, fg_color = bg_color)
heatmap_frame.pack(pady=10)
heatmap_btn = tk.Label(master=heatmap_frame, image=gen_icon, cursor="hand2", bg=bg_color, highlightthickness=0)
heatmap_btn.pack(pady=30, anchor="center")
img_refs.append(gen_icon)
heatmap_btn.bind("<Button-1>", lambda event: open_new_window())
heatmap_text = tk.Label(heatmap_frame, text="Generate Heatmaps", font=("Arial", 12), bg=bg_color, fg="white")
heatmap_text.pack()
ToolTip(heatmap_btn, "Generates a heatmap with its configuration file in the subject folder.", x_offset=10, y_offset=0)





#Run circos button
cir_frame = ctk.CTkFrame(btn_frame, fg_color = bg_color)
cir_frame.pack(pady=10)
cir_btn = tk.Label(master=cir_frame, image=circos_icon, cursor="hand2", bg=bg_color, highlightthickness=0)
cir_btn.pack(pady=30)
img_refs.append(circos_icon)
cir_btn.bind("<Button-1>", lambda event: runCircos())
cir_text = tk.Label(cir_frame, text="Run Circos", font=("Arial", 12), bg=bg_color, fg="white")
cir_text.pack()
ToolTip(cir_btn, "Runs Circos in the subject folder.", x_offset=10, y_offset=0)




# Start the main loop
root.mainloop()

