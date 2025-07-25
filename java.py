import tkinter as tk
from tkinter import filedialog, messagebox
import os
from urllib.parse import urlparse
import re

# Define the base output directory for the Java files
OUTPUT_BASE_DIR = r"E:\Notes\Macros\Cyber Security\Projects\scripts\Java_Downloader"

def _write_java_file_content(url, selected_method, filename, execute_after_download, java_file_path):
    """
    Helper function to generate and write the .java file content.
    """
    # Sanitize filename for use within Java strings (Windows paths)
    sanitized_filename_for_java = filename.replace("\\", "\\\\").replace("'", "\\'")

    java_content = f'''
// Java Download Script generated by Python Tkinter App
// This script is designed to be compiled and run on Windows.
// URL: {url}
// Method: {selected_method}
// Output File: {filename}

import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.net.HttpURLConnection;
import java.nio.channels.Channels;
import java.nio.channels.ReadableByteChannel;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.awt.Desktop; // For opening files after download (requires AWT/Swing environment)
import java.net.URI;
import java.net.URISyntaxException;
import java.util.concurrent.TimeUnit; // For ProcessBuilder timeout
import java.io.BufferedReader;
import java.io.InputStreamReader;

'''
    if selected_method == "Apache HttpClient (External Library)":
        java_content += '''import org.apache.http.HttpEntity;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
'''

    java_content += f'''
public class Downloader {{

    public static void main(String[] args) {{
        String urlString = "{url}";
        String outputFileName = "{sanitized_filename_for_java}";
        boolean executeAfterDownload = {str(execute_after_download).lower()}; // Python boolean to Java boolean

        System.out.println("Attempting to download '" + urlString + "' to '" + outputFileName + "' using '{selected_method}'...");

        try {{
'''

    if selected_method == "java.net.URL & InputStream (Built-in)":
        java_content += f'''
            URL url = new URL(urlString);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.connect();

            if (connection.getResponseCode() != HttpURLConnection.HTTP_OK) {{
                throw new IOException("Server returned HTTP " + connection.getResponseCode()
                        + " " + connection.getResponseMessage());
            }}

            try (InputStream in = connection.getInputStream();
                 FileOutputStream out = new FileOutputStream(outputFileName)) {{
                byte[] buffer = new byte[4096];
                int bytesRead;
                while ((bytesRead = in.read(buffer)) != -1) {{
                    out.write(buffer, 0, bytesRead);
                }}
            }} finally {{
                if (connection != null) {{
                    connection.disconnect();
                }}
            }}
'''
    elif selected_method == "java.nio.channels.Channels (Built-in, Efficient)":
        java_content += f'''
            URL url = new URL(urlString);
            ReadableByteChannel rbc = Channels.newChannel(url.openStream());
            try (FileOutputStream fos = new FileOutputStream(outputFileName)) {{
                fos.getChannel().transferFrom(rbc, 0, Long.MAX_VALUE);
            }} finally {{
                rbc.close();
            }}
'''
    elif selected_method == "Apache HttpClient (External Library)":
        java_content += f'''
            // This method requires Apache HttpClient library.
            // You need to add the dependency to your project (e.g., Maven, Gradle)
            // or include the JARs in your classpath when compiling/running.
            // Example Maven dependency:
            // <dependency>
            //     <groupId>org.apache.httpcomponents</groupId>
            //     <artifactId>httpclient</artifactId>
            //     <version>4.5.13</version> <!-- Use a recent version -->
            // </dependency>

            try (CloseableHttpClient httpClient = HttpClients.createDefault()) {{
                HttpGet request = new HttpGet(urlString);
                try (CloseableHttpResponse response = httpClient.execute(request)) {{
                    HttpEntity entity = response.getEntity();
                    if (entity != null) {{
                        try (InputStream in = entity.getContent();
                             FileOutputStream out = new FileOutputStream(outputFileName)) {{
                            byte[] buffer = new byte[4096];
                            int bytesRead;
                            while ((bytesRead = in.read(buffer)) != -1) {{
                                out.write(buffer, 0, bytesRead);
                            }}
                        }}
                    }} else {{
                        throw new IOException("No content received from URL.");
                    }}
                }}
            }}
'''
    elif selected_method == "Curl (via ProcessBuilder)":
        java_content += f'''
            ProcessBuilder processBuilder = new ProcessBuilder("curl", "-L", "-o", outputFileName, urlString);
            processBuilder.redirectErrorStream(true); // Merge stdout and stderr
            Process process = processBuilder.start();

            // Read output from the process
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {{
                String line;
                while ((line = reader.readLine()) != null) {{
                    System.out.println("Curl output: " + line);
                }}
            }}

            boolean finished = process.waitFor(5, TimeUnit.MINUTES); // Wait up to 5 minutes
            if (!finished) {{
                process.destroyForcibly();
                throw new IOException("Curl process timed out.");
            }}

            int exitCode = process.exitValue();
            if (exitCode != 0) {{
                throw new IOException("Curl command failed with exit code: " + exitCode);
            }}
'''
    elif selected_method == "Wget (via ProcessBuilder)":
        java_content += f'''
            ProcessBuilder processBuilder = new ProcessBuilder("wget", "--no-check-certificate", "-O", outputFileName, urlString);
            processBuilder.redirectErrorStream(true); // Merge stdout and stderr
            Process process = processBuilder.start();

            // Read output from the process
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {{
                String line;
                while ((line = reader.readLine()) != null) {{
                    System.out.println("Wget output: " + line);
                }}
            }}

            boolean finished = process.waitFor(5, TimeUnit.MINUTES); // Wait up to 5 minutes
            if (!finished) {{
                process.destroyForcibly();
                throw new IOException("Wget process timed out.");
            }}

            int exitCode = process.exitValue();
            if (exitCode != 0) {{
                throw new IOException("Wget command failed with exit code: " + exitCode);
            }}
'''
    else:
        raise ValueError(f"Unknown download method selected: {selected_method}")

    java_content += f'''
            System.out.println("Download complete: " + outputFileName);

            // --- Execute after download ---
            if (executeAfterDownload) {{
                File downloadedFile = new File(outputFileName);
                if (downloadedFile.exists()) {{
                    System.out.println("Executing downloaded file: " + outputFileName);
                    try {{
                        // Desktop.getDesktop().open() is a cross-platform way to open files
                        // It requires a GUI environment (even if just a console app is running)
                        // For a purely headless server, you might use Runtime.getRuntime().exec()
                        if (Desktop.isDesktopSupported()) {{
                            Desktop.getDesktop().open(downloadedFile);
                            System.out.println("Execution command sent.");
                        }} else {{
                            System.out.println("Desktop API not supported. Cannot execute file automatically.");
                            // Fallback for non-GUI environments (Windows specific example)
                            // Runtime.getRuntime().exec("cmd /c start " + downloadedFile.getAbsolutePath());
                        }}
                    }} catch (IOException e) {{
                        System.err.println("Failed to execute '" + outputFileName + "': " + e.getMessage());
                    }}
                }} else {{
                    System.out.println("Cannot execute: Downloaded file not found at " + outputFileName + ".");
                }}
            }}

        }} catch (IOException | URISyntaxException e) {{
            System.err.println("An error occurred during download: " + e.getMessage());
            e.printStackTrace(); // Print full stack trace for debugging
            System.exit(1); // Exit with an error code
        }} catch (Exception e) {{
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }}
    }}
}}
'''

    # Write the content to the .java file
    with open(java_file_path, 'w') as f:
        f.write(java_content)

def generate_single_java_file():
    """
    Generates a single .java file for the selected method, prompting for save location.
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
    
    # Specific warnings for methods that might not handle all URL types well
    if ("Apache HttpClient" in selected_method) and url.startswith("ftp://"):
        messagebox.showwarning("Method Warning", f"{selected_method} is primarily for HTTP/HTTPS. FTP support is not direct.")
    
    if ("Curl" in selected_method or "Wget" in selected_method) and url.startswith("ftp://"):
        messagebox.showwarning("External Tool Warning", f"{selected_method} might have limited or no direct support for FTP URLs. Consider HTTP/HTTPS.")

    try:
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        filename = path_segments[-1] if path_segments[-1] else "downloaded_file"
        if '.' not in filename:
            filename += ".dat"

        # Sanitize filename for Windows path compatibility
        filename = re.sub(r'[\\/:*?"<>|]', '_', filename)

        java_file_path = filedialog.asksaveasfilename(
            defaultextension=".java",
            filetypes=[("Java Source Files", "*.java")],
            initialfile=f"Downloader_{selected_method.split(' ')[0].lower()}.java",
            title="Save .java File As"
        )

        if not java_file_path:
            return

        _write_java_file_content(url, selected_method, filename, execute_after_download, java_file_path)

        messagebox.showinfo(
            "Success",
            f"'{os.path.basename(java_file_path)}' created successfully!\n"
            f"You can find it at: {java_file_path}\n\n"
            f"**Next Steps:**\n"
            f"1. Compile: javac {os.path.basename(java_file_path)} (add -cp if using Apache HttpClient)\n"
            f"2. Run: java Downloader (add -cp if using Apache HttpClient)"
        )

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def create_all_java_files():
    """
    Creates a .java file for each download method in the specified output directory.
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
        os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        base_filename = path_segments[-1] if path_segments[-1] else "downloaded_file"
        if '.' not in base_filename:
            base_filename += ".dat"
        
        # Sanitize base_filename for Windows path compatibility
        base_filename = re.sub(r'[\\/:*?"<>|]', '_', base_filename)

        created_files_count = 0
        failed_methods = []

        for method in download_methods:
            # Specific warnings/skips for methods that might not handle all URL types well
            if ("Apache HttpClient" in method) and url.startswith("ftp://"):
                failed_methods.append(f"{method} (Primarily for HTTP/HTTPS)")
                continue
            
            if ("Curl" in method or "Wget" in method) and url.startswith("ftp://"):
                failed_methods.append(f"{method} (Limited/no direct support for FTP URLs)")
                continue

            # Sanitize method name for filename
            sanitized_method_name = re.sub(r'[\\/:*?"<>|()]', '', method).replace(' ', '_').replace('.', '').replace('&', '')
            
            # Construct the filename for the output java file
            java_filename = f"Downloader_{sanitized_method_name}.java"
            java_file_path = os.path.join(OUTPUT_BASE_DIR, java_filename)

            try:
                _write_java_file_content(url, method, base_filename, execute_after_download, java_file_path)
                created_files_count += 1
            except Exception as e:
                failed_methods.append(f"{method} ({e})")

        success_message = f"Successfully created {created_files_count} .java files in:\n{OUTPUT_BASE_DIR}"
        if failed_methods:
            success_message += "\n\nFailed to create files for the following methods:\n" + "\n".join(failed_methods)
            messagebox.showwarning("Partial Success", success_message)
        else:
            messagebox.showinfo("Success", success_message)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while creating all files: {e}")

# --- GUI Setup ---
app = tk.Tk()
app.title("Java (.java) Downloader Generator")
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
    "java.net.URL & InputStream (Built-in)",
    "java.nio.channels.Channels (Built-in, Efficient)",
    "Apache HttpClient (External Library)",
    "Curl (via ProcessBuilder)",
    "Wget (via ProcessBuilder)"
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
generate_button = tk.Button(app, text="Generate Single .JAVA File", command=generate_single_java_file)
generate_button.grid(row=3, column=0, columnspan=2, pady=10)

create_all_button = tk.Button(app, text="Create All Methods", command=create_all_java_files)
create_all_button.grid(row=4, column=0, columnspan=2, pady=10)

# Run the application
app.mainloop()
