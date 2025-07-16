import tkinter as tk
from tkinter import filedialog, messagebox
import os
from urllib.parse import urlparse
import re # Import regex for sanitizing filenames
import datetime # For potential future date/time handling

# Define the output directory
OUTPUT_DIR = r"E:\Notes\Macros\Cyber Security\Projects\scripts\Downloader\output"

def _write_bat_file_content(url, selected_method, filename, execute_after_download, task_scheduler_enabled, schedule_interval_type, bat_file_path):
    """
    Helper function to generate and write the .bat file content.
    """
    # Sanitize method name for task scheduler name
    sanitized_method_for_task = re.sub(r'[\\/:*?"<>|()\s-]', '', selected_method).replace(' ', '')

    # Construct the content for the .bat file based on the selected method
    bat_content = f'@echo off\n' \
                  f'echo Downloading {url} using {selected_method}...\n'

    # Determine command based on selected method
    if selected_method == "Curl (Recommended)":
        bat_content += f'curl -L -o "{filename}" "{url}"\n'
    elif selected_method == "Bitsadmin (Older Windows)":
        bat_content += f'bitsadmin /transfer "DownloadJob" /download /priority HIGH "{url}" "{filename}"\n'
    elif selected_method == "PowerShell (Invoke-WebRequest)":
        bat_content += f'powershell -Command "Invoke-WebRequest -Uri \'{url}\' -OutFile \'{filename}\'"\n'
    elif selected_method == "Certutil (Windows Built-in)":
        bat_content += f'certutil -urlcache -f "{url}" "{filename}"\n'
    elif selected_method == "Wget (Requires Installation)":
        bat_content += f'wget -O "{filename}" "{url}"\n'
    elif selected_method == "FTP (Native Windows Client)":
        parsed_url = urlparse(url)
        ftp_script_name = "ftp_download_script.txt"
        ftp_script_content = f"open {parsed_url.hostname}\n" \
                             f"anonymous\n" \
                             f"anonymous\n" \
                             f"bin\n" \
                             f"get {parsed_url.path} \"{filename}\"\n" \
                             f"quit\n"
        bat_content += f'echo {ftp_script_content} > "{ftp_script_name}"\n' \
                       f'ftp -s:"{ftp_script_name}"\n' \
                       f'del "{ftp_script_name}"\n'
    elif selected_method == "PowerShell (WebClient)":
        bat_content += f'powershell -Command "$wc = New-Object System.Net.WebClient; $wc.DownloadFile(\'{url}\', \'{filename}\')"\n'
    elif selected_method == "MSHTA (HTA Application)":
        hta_filename = "temp_download.hta"
        hta_content = f'''
        <HTML>
        <HEAD>
        <HTA:APPLICATION WINDOWSTATE="minimize" SHOWINTASKBAR="no" SYSMENU="no" CAPTION="no" BORDER="none"/>
        <SCRIPT LANGUAGE="VBScript">
        Set objHTTP = CreateObject("WinHttp.WinHttpRequest.5.1")
        objHTTP.Open "GET", "{url}", False
        objHTTP.Send
        If objHTTP.Status = 200 Then
            Set objStream = CreateObject("ADODB.Stream")
            objStream.Open
            objStream.Type = 1 'adTypeBinary
            objStream.Write objHTTP.ResponseBody
            objStream.SaveToFile "{filename}", 2 'adSaveCreateOverWrite
            objStream.Close
            Set objStream = Nothing
        End If
        Set objHTTP = Nothing
        window.close
        </SCRIPT>
        </HEAD>
        </HTML>
        '''
        bat_content += f'echo {hta_content} > "{hta_filename}"\n' \
                       f'mshta "{hta_filename}"\n' \
                       f'del "{hta_filename}"\n'
    elif selected_method == "VBScript (Windows Native)":
        vbs_filename = "temp_download.vbs"
        vbs_content = f'''
Dim xHttp: Set xHttp = CreateObject("Microsoft.XMLHTTP")
Dim bStrm: Set bStrm = CreateObject("ADODB.Stream")
xHttp.Open "GET", "{url}", False
xHttp.Send

const adTypeBinary = 1
bStrm.Type = adTypeBinary
bStrm.Open
bStrm.Write xHttp.ResponseBody
bStrm.SaveToFile "{filename}", 2 ' 1 = no overwrite, 2 = overwrite
Set bStrm = Nothing
Set xHttp = Nothing
WScript.Quit
        '''
        bat_content += f'echo {vbs_content} > "{vbs_filename}"\n' \
                       f'cscript //NoLogo "{vbs_filename}"\n' \
                       f'del "{vbs_filename}"\n'
    elif selected_method == "SCP (Requires OpenSSH/Client)":
        bat_content += f'echo IMPORTANT: SCP requires OpenSSH client installed on Windows and an SSH server on the remote machine.\n' \
                       f'echo Usage: scp [user@]remote_host:[remote_path] "{filename}"\n' \
                       f'echo You will need to manually edit this .bat file with the correct SCP command.\n' \
                       f'echo Example (replace user, remote_host, and remote_path):\n' \
                       f'echo scp user@example.com:/path/to/remote/file.zip "{filename}"\n' \
                       f'REM Pause for user to read the message if run directly\n'
    else:
        raise ValueError(f"Unknown download method selected: {selected_method}")

    # Add post-download execution and error handling
    bat_content += f'if %errorlevel% equ 0 (\n' \
                   f'    echo Download complete: "{filename}"\n'
    
    if execute_after_download:
        bat_content += f'    echo Executing downloaded file...\n' \
                       f'    start "" "{filename}"\n' # Use start to run the file
    
    bat_content += f') else (\n' \
                   f'    echo Error during download. Check your internet connection or URL.\n' \
                   f'    echo Note: "Curl" requires Windows 10+ or separate installation.\n' \
                   f'    echo "Bitsadmin" might be blocked by some network policies.\n' \
                   f'    echo "PowerShell" requires PowerShell 3.0+.\n' \
                   f'    echo "Certutil" might have limitations with large files or certain server configurations.\n' \
                   f'    echo "Wget" requires Wget to be installed and in your system PATH.\n' \
                   f'    echo "FTP" requires an FTP server and correct URL. May not work with all FTP configurations.\n' \
                   f'    echo "WebClient" is a PowerShell method, similar to Invoke-WebRequest.\n' \
                   f'    echo "MSHTA" is an advanced method, often flagged by security software. Use with caution.\n' \
                   f'    echo "VBScript" uses native Windows scripting, may be blocked by some security settings.\n' \
                   f'    echo "SCP" requires OpenSSH client and server, and correct syntax for remote path.\n' \
                   f')\n' \
                   f'pause\n' # Pause to keep the window open after execution for inspection

    # Add Task Scheduler command if enabled
    if task_scheduler_enabled:
        task_name = f"DownloadTask_{sanitized_method_for_task}"
        
        schedule_command = ""
        if schedule_interval_type == "5_minutes":
            schedule_command = '/SC MINUTE /MO 5'
        elif schedule_interval_type == "1_hour":
            schedule_command = '/SC HOURLY /MO 1'
        elif schedule_interval_type == "daily":
            schedule_command = '/SC DAILY /MO 1'
        else:
            # Fallback or error if an unknown interval is selected
            raise ValueError(f"Unknown schedule interval type: {schedule_interval_type}")

        # Get the full path of the current batch file to schedule it
        # %~dp0 is the drive and path of the batch file
        # %~nx0 is the file name and extension of the batch file
        task_action = f'cmd /c "{os.path.basename(bat_file_path)}"' # Schedule the batch file itself
        
        # Start time (optional, but good for recurring tasks to define a start)
        # Using current time for simplicity, but can be made customizable
        current_time_str = datetime.datetime.now().strftime("%H:%M")

        bat_content += f'\nREM --- Task Scheduler Setup ---\n' \
                       f'echo Setting up scheduled task "{task_name}"...\n' \
                       f'schtasks /create /TN "{task_name}" /TR "{task_action}" {schedule_command} /ST {current_time_str} /RL HIGHEST /F\n' \
                       f'if %errorlevel% equ 0 (\n' \
                       f'    echo Task "{task_name}" scheduled successfully.\n' \
                       f'    echo The task will run "{schedule_interval_type.replace("_", " ")}" starting from today at {current_time_str}.\n' \
                       f'    echo NOTE: This batch file might need to be run as Administrator once to create the task.\n' \
                       f') else (\n' \
                       f'    echo Failed to schedule task "{task_name}". This usually requires Administrator privileges.\n' \
                       f'    echo Please run this batch file as Administrator and try again.\n' \
                       f')\n' \
                       f'pause\n' # Pause again after task scheduler attempt

    # Write the content to the .bat file
    with open(bat_file_path, 'w') as f:
        f.write(bat_content)

def generate_single_bat_file():
    """
    Generates a single .bat file for the selected method, prompting for save location.
    """
    url = url_entry.get()
    selected_method = method_var.get()
    execute_after_download = execute_var.get()
    task_scheduler_enabled = task_scheduler_var.get()
    schedule_interval_type = schedule_interval_var.get() if task_scheduler_enabled else ""

    if not url:
        messagebox.showwarning("Input Error", "Please enter a valid URL.")
        return

    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("ftp://")):
        messagebox.showwarning("Invalid URL", "URL must start with http://, https://, or ftp://")
        return

    if selected_method == "FTP (Native Windows Client)" and not url.startswith("ftp://"):
        messagebox.showwarning("Invalid URL for FTP", "FTP method requires an FTP URL (ftp://...).")
        return
    
    if task_scheduler_enabled and not schedule_interval_type:
        messagebox.showwarning("Scheduling Error", "Please select a scheduling interval.")
        return

    try:
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        filename = path_segments[-1] if path_segments[-1] else "downloaded_file"
        if '.' not in filename:
            filename += ".dat"

        bat_file_path = filedialog.asksaveasfilename(
            defaultextension=".bat",
            filetypes=[("Batch Files", "*.bat")],
            initialfile="download_file.bat",
            title="Save .bat File As"
        )

        if not bat_file_path:
            return

        _write_bat_file_content(url, selected_method, filename, execute_after_download, task_scheduler_enabled, schedule_interval_type, bat_file_path)

        messagebox.showinfo(
            "Success",
            f"'{os.path.basename(bat_file_path)}' created successfully!\n"
            f"You can find it at: {bat_file_path}\n\n"
            f"Double-click the .bat file to start the download."
        )

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def create_all_bat_files():
    """
    Creates a .bat file for each download method in the specified output directory.
    """
    url = url_entry.get()
    execute_after_download = execute_var.get()
    task_scheduler_enabled = task_scheduler_var.get()
    schedule_interval_type = schedule_interval_var.get() if task_scheduler_enabled else ""

    if not url:
        messagebox.showwarning("Input Error", "Please enter a valid URL to create all files.")
        return

    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("ftp://")):
        messagebox.showwarning("Invalid URL", "URL must start with http://, https://, or ftp://")
        return
    
    if task_scheduler_enabled and not schedule_interval_type:
        messagebox.showwarning("Scheduling Error", "Please select a scheduling interval before creating all files.")
        return

    try:
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        base_filename = path_segments[-1] if path_segments[-1] else "downloaded_file"
        if '.' not in base_filename:
            base_filename += ".dat"

        created_files_count = 0
        failed_methods = []

        for method in download_methods:
            # Skip FTP method if URL is not FTP
            if method == "FTP (Native Windows Client)" and not url.startswith("ftp://"):
                failed_methods.append(f"{method} (URL not FTP)")
                continue

            # Sanitize method name for filename
            sanitized_method_name = re.sub(r'[\\/:*?"<>|()]', '', method).replace(' ', '_').replace('.', '')
            
            # Construct the filename for the output bat file
            bat_filename = f"download_{sanitized_method_name}.bat"
            bat_file_path = os.path.join(OUTPUT_DIR, bat_filename)

            try:
                _write_bat_file_content(url, method, base_filename, execute_after_download, task_scheduler_enabled, schedule_interval_type, bat_file_path)
                created_files_count += 1
            except Exception as e:
                failed_methods.append(f"{method} ({e})")

        success_message = f"Successfully created {created_files_count} .bat files in:\n{OUTPUT_DIR}"
        if failed_methods:
            success_message += "\n\nFailed to create files for the following methods:\n" + "\n".join(failed_methods)
            messagebox.showwarning("Partial Success", success_message)
        else:
            messagebox.showinfo("Success", success_message)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while creating all files: {e}")

def toggle_task_scheduler_options():
    """
    Shows/hides task scheduler interval options based on checkbox state.
    """
    if task_scheduler_var.get():
        task_scheduler_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")
    else:
        task_scheduler_frame.grid_forget()

# --- GUI Setup ---
app = tk.Tk()
app.title("BAT File Downloader Generator")
app.geometry("700x600") # Increased size to accommodate new options
app.resizable(False, False)

# Configure grid for better layout
for i in range(7): # Adjust rows for new widgets
    app.grid_rowconfigure(i, weight=1)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=3)

# URL Label
url_label = tk.Label(app, text="Enter File URL:")
url_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

# URL Entry
url_entry = tk.Entry(app, width=60)
url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
url_entry.focus_set()

# Download Method Label
method_label = tk.Label(app, text="Select Download Method:")
method_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

# Download Method Dropdown (OptionMenu)
download_methods = [
    "Curl (Recommended)",
    "Bitsadmin (Older Windows)",
    "PowerShell (Invoke-WebRequest)",
    "Certutil (Windows Built-in)",
    "Wget (Requires Installation)",
    "FTP (Native Windows Client)",
    "PowerShell (WebClient)",
    "MSHTA (HTA Application - Advanced)",
    "VBScript (Windows Native)",
    "SCP (Requires OpenSSH/Client)"
]
method_var = tk.StringVar(app)
method_var.set(download_methods[0]) # Set default value

method_dropdown = tk.OptionMenu(app, method_var, *download_methods)
method_dropdown.config(width=40) # Adjust width
method_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="w")

# Execute After Download Checkbox
execute_var = tk.BooleanVar() # Variable to store checkbox state
execute_checkbox = tk.Checkbutton(app, text="Execute after download", variable=execute_var)
execute_checkbox.grid(row=2, column=1, padx=10, pady=5, sticky="w") # Place below dropdown

# Task Scheduler Checkbox
task_scheduler_var = tk.BooleanVar()
task_scheduler_checkbox = tk.Checkbutton(app, text="Add to Task Scheduler", variable=task_scheduler_var, command=toggle_task_scheduler_options)
task_scheduler_checkbox.grid(row=3, column=1, padx=10, pady=5, sticky="w")

# Task Scheduler Options Frame (initially hidden)
task_scheduler_frame = tk.Frame(app, bd=2, relief="groove", padx=5, pady=5)
# It will be gridded when the checkbox is checked

schedule_interval_var = tk.StringVar(app)
schedule_interval_var.set("1_hour") # Default schedule

tk.Label(task_scheduler_frame, text="Run every:").pack(anchor="w")
tk.Radiobutton(task_scheduler_frame, text="5 Minutes", variable=schedule_interval_var, value="5_minutes").pack(anchor="w")
tk.Radiobutton(task_scheduler_frame, text="1 Hour", variable=schedule_interval_var, value="1_hour").pack(anchor="w")
tk.Radiobutton(task_scheduler_frame, text="Daily", variable=schedule_interval_var, value="daily").pack(anchor="w")

# Buttons
generate_button = tk.Button(app, text="Generate Single .BAT File", command=generate_single_bat_file)
generate_button.grid(row=5, column=0, columnspan=2, pady=10)

create_all_button = tk.Button(app, text="Create All Methods", command=create_all_bat_files)
create_all_button.grid(row=6, column=0, columnspan=2, pady=10)

# Run the application
app.mainloop()