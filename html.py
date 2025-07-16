import tkinter as tk
from tkinter import filedialog, messagebox
import os
from urllib.parse import urlparse
import re

# Define the base output directory for the HTML files
OUTPUT_BASE_DIR = r"E:\Notes\Macros\Cyber Security\Projects\scripts\HTML_Downloader"

def _write_html_file_content(url, selected_method, filename, html_file_path):
    """
    Helper function to generate and write the .html file content.
    """
    # Sanitize filename for use within JavaScript strings (HTML attributes)
    sanitized_filename_for_js = filename.replace("\\", "\\\\").replace("'", "\\'")

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTML File Downloader</title>
    <!-- Tailwind CSS CDN for styling -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{
            font-family: "Inter", sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-color: #f0f4f8;
        }}
        .container {{
            background-color: #ffffff;
            padding: 2.5rem;
            border-radius: 1rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            text-align: center;
            max-width: 500px;
            width: 90%;
        }}
        .button {{
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.2s;
            display: inline-block;
            margin-top: 1rem;
        }}
        .button-primary {{
            background-color: #4f46e5;
            color: white;
        }}
        .button-primary:hover {{
            background-color: #4338ca;
            transform: translateY(-2px);
        }}
        .input-field {{
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #d1d5db;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }}
        .status-text {{
            margin-top: 1.5rem;
            font-size: 1.125rem;
            color: #4b5563;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-3xl font-bold text-gray-800 mb-6">HTML File Downloader</h1>
        <p class="text-gray-600 mb-4">URL: <span class="font-medium text-blue-600">{url}</span></p>
        <p class="text-gray-600 mb-6">Method: <span class="font-medium text-green-600">{selected_method}</span></p>

        <button id="downloadButton" class="button button-primary">Start Download</button>
        <p id="status" class="status-text">Status: Ready</p>
    </div>

    <script>
        const downloadUrl = '{url}';
        const outputFileName = '{sanitized_filename_for_js}';
        const statusElement = document.getElementById('status');
        const downloadButton = document.getElementById('downloadButton');

        function updateStatus(message) {{
            statusElement.textContent = `Status: ${{message}}`;
        }}

        downloadButton.addEventListener('click', () => {{
            updateStatus('Initiating download...');
            try {{
                {selected_method.replace(" ", "_").replace("(", "").replace(")", "").lower()}_download(downloadUrl, outputFileName);
            }} catch (e) {{
                updateStatus(`Error: ${{e.message || e}}`);
                console.error('Download error:', e);
            }}
        }});

        // --- Download Methods ---
'''

    if selected_method == "Anchor Tag (Direct Download)":
        html_content += f'''
        function anchor_tag_direct_download(url, fileName) {{
            const link = document.createElement('a');
            link.href = url;
            link.download = fileName; // Suggests filename for download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            updateStatus('Download initiated via Anchor Tag.');
            // Note: Browser security might prevent direct download prompt if not same-origin.
            // User might need to confirm download.
        }}
'''
    elif selected_method == "window.location.href (Redirect)":
        html_content += f'''
        function window_location_href_redirect(url, fileName) {{
            // This method redirects the current page to the download URL.
            // It's simple but navigates away from the current page.
            window.location.href = url;
            updateStatus('Redirecting to download URL. Page might navigate away.');
        }}
'''
    elif selected_method == "Fetch API (Blob & Object URL)":
        html_content += f'''
        async function fetch_api_blob_object_url_download(url, fileName) {{
            try {{
                const response = await fetch(url);
                if (!response.ok) {{
                    throw new Error(`HTTP error! status: ${{response.status}}`);
                }}
                const blob = await response.blob();
                const blobUrl = URL.createObjectURL(blob);

                const link = document.createElement('a');
                link.href = blobUrl;
                link.download = fileName;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(blobUrl); // Clean up the object URL

                updateStatus('Download complete via Fetch API.');
            }} catch (error) {{
                updateStatus(`Download failed via Fetch API: ${{error.message}}`);
                console.error('Fetch API download error:', error);
            }}
        }}
'''
    elif selected_method == "XMLHttpRequest (XHR Blob)":
        html_content += f'''
        function xmlhttprequest_xhr_blob_download(url, fileName) {{
            const xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.responseType = 'blob'; // Request a Blob response

            xhr.onload = function() {{
                if (xhr.status === 200) {{
                    const blob = xhr.response;
                    const blobUrl = URL.createObjectURL(blob);

                    const link = document.createElement('a');
                    link.href = blobUrl;
                    link.download = fileName;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    URL.revokeObjectURL(blobUrl); // Clean up the object URL

                    updateStatus('Download complete via XHR.');
                }} else {{
                    updateStatus(`Download failed via XHR. Status: ${{xhr.status}}`);
                    console.error('XHR download failed. Status:', xhr.status);
                }}
            }};

            xhr.onerror = function() {{
                updateStatus('Network error during XHR download.');
                console.error('XHR network error.');
            }};

            xhr.send();
        }}
'''
    elif selected_method == "Hidden IFrame":
        html_content += f'''
        function hidden_iframe_download(url, fileName) {{
            // This method creates a hidden iframe and sets its src to the download URL.
            // It can trigger downloads without navigating the main page.
            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = url;
            document.body.appendChild(iframe);
            // Optionally, remove the iframe after a delay if it's not needed for tracking
            // setTimeout(() => document.body.removeChild(iframe), 5000);
            updateStatus('Download initiated via Hidden IFrame.');
        }}
'''
    else:
        raise ValueError(f"Unknown download method selected: {selected_method}")

    html_content += f'''
    </script>
</body>
</html>
'''

    # Write the content to the .html file
    with open(html_file_path, 'w') as f:
        f.write(html_content)

def generate_single_html_file():
    """
    Generates a single .html file for the selected method, prompting for save location.
    """
    url = url_entry.get()
    selected_method = method_var.get()

    if not url:
        messagebox.showwarning("Input Error", "Please enter a valid URL.")
        return

    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("ftp://")):
        messagebox.showwarning("Invalid URL", "URL must start with http://, https://, or ftp://")
        return
    
    # Specific warnings for methods that might not handle all URL types well
    if ("Fetch API" in selected_method or "XMLHttpRequest" in selected_method) and url.startswith("ftp://"):
        messagebox.showwarning("Method Warning", f"{selected_method} is primarily for HTTP/HTTPS. FTP support is not direct in browsers.")
    
    if selected_method == "Anchor Tag (Direct Download)" and url.startswith("ftp://"):
        messagebox.showwarning("Method Warning", "Anchor tag downloads for FTP URLs might behave differently across browsers.")

    try:
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        filename = path_segments[-1] if path_segments[-1] else "downloaded_file"
        if '.' not in filename:
            filename += ".dat"

        # Sanitize filename for HTML/JS compatibility
        filename = re.sub(r'[\\/:*?"<>|]', '_', filename)

        html_file_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html")],
            initialfile=f"downloader_{selected_method.split(' ')[0].lower()}.html",
            title="Save .html File As"
        )

        if not html_file_path:
            return

        _write_html_file_content(url, selected_method, filename, html_file_path)

        messagebox.showinfo(
            "Success",
            f"'{os.path.basename(html_file_path)}' created successfully!\n"
            f"You can find it at: {html_file_path}\n\n"
            f"Open this .html file in any web browser to use the downloader."
        )

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def create_all_html_files():
    """
    Creates .html files for each download method in the specified output directory.
    """
    url = url_entry.get()

    if not url:
        messagebox.showwarning("Input Error", "Please enter a valid URL to create all files.")
        return

    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("ftp://")):
        messagebox.showwarning("Invalid URL", "URL must start with http://, https://, or ftp://")
        return

    try:
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        base_filename = path_segments[-1] if path_segments[-1] else "downloaded_file"
        if '.' not in base_filename:
            base_filename += ".dat"
        
        # Sanitize base_filename for HTML/JS compatibility
        base_filename = re.sub(r'[\\/:*?"<>|]', '_', base_filename)

        created_files_count = 0
        failed_methods = []

        for method in download_methods:
            # Specific warnings/skips for methods that might not handle all URL types well
            if ("Fetch API" in method or "XMLHttpRequest" in method) and url.startswith("ftp://"):
                failed_methods.append(f"{method} (Primarily for HTTP/HTTPS)")
                continue
            
            if method == "Anchor Tag (Direct Download)" and url.startswith("ftp://"):
                failed_methods.append(f"{method} (FTP behavior varies)")
                continue

            # Sanitize method name for filename
            sanitized_method_name = re.sub(r'[\\/:*?"<>|()]', '', method).replace(' ', '_').replace('.', '').replace('&', '')
            
            # Construct the filename for the output html file
            html_filename = f"downloader_{sanitized_method_name}.html"
            html_file_path = os.path.join(OUTPUT_BASE_DIR, html_filename)

            try:
                _write_html_file_content(url, method, base_filename, html_file_path)
                created_files_count += 1
            except Exception as e:
                failed_methods.append(f"{method} ({e})")

        success_message = f"Successfully created {created_files_count} .html files in:\n{OUTPUT_BASE_DIR}"
        if failed_methods:
            success_message += "\n\nFailed to create files for the following methods:\n" + "\n".join(failed_methods)
            messagebox.showwarning("Partial Success", success_message)
        else:
            messagebox.showinfo("Success", success_message)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while creating all files: {e}")

# --- GUI Setup ---
app = tk.Tk()
app.title("HTML (.html) Downloader Generator")
app.geometry("750x480") # Adjusted size
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
url_entry.insert(0, "https://www.example.com/sample.zip") # Default URL

# Download Method Label
method_label = tk.Label(app, text="Select Download Method:")
method_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

# Download Method Dropdown (OptionMenu)
download_methods = [
    "Anchor Tag (Direct Download)",
    "window.location.href (Redirect)",
    "Fetch API (Blob & Object URL)",
    "XMLHttpRequest (XHR Blob)",
    "Hidden IFrame"
]
method_var = tk.StringVar(app)
method_var.set(download_methods[0]) # Set default value

method_dropdown = tk.OptionMenu(app, method_var, *download_methods)
method_dropdown.config(width=40) # Adjust width
method_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="w")

# Note: "Execute after download" is not directly applicable for HTML/browser downloads
# as the browser handles file saving. The user would typically open the file manually.
execute_var = tk.BooleanVar() # Variable to store checkbox state
execute_checkbox = tk.Checkbutton(app, text="Execute after download (N/A for browser)", variable=execute_var, state=tk.DISABLED)
execute_checkbox.grid(row=2, column=1, padx=10, pady=5, sticky="w")

# Buttons
generate_button = tk.Button(app, text="Generate Single .HTML File", command=generate_single_html_file)
generate_button.grid(row=3, column=0, columnspan=2, pady=10)

create_all_button = tk.Button(app, text="Create All Methods", command=create_all_html_files)
create_all_button.grid(row=4, column=0, columnspan=2, pady=10)

# Run the application
app.mainloop()
