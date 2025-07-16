import tkinter as tk
from tkinter import filedialog, messagebox
import os
from urllib.parse import urlparse
import re

# Define the base output directory for the Android project
OUTPUT_BASE_DIR = r"E:\Notes\Macros\Cyber Security\Projects\scripts\Android_Downloader_Project"

def _sanitize_package_name(name):
    """Sanitizes a string to be suitable for a Java package name."""
    return re.sub(r'[^a-zA-Z0-9_.]', '', name).lower()

def _sanitize_class_name(name):
    """Sanitizes a string to be suitable for a Java class name."""
    return re.sub(r'[^a-zA-Z0-9_]', '', name).replace(' ', '')

def _write_android_project_content(url, selected_method, filename, project_name, package_name, output_dir):
    """
    Helper function to generate and write the Android project structure and files.
    """
    # Sanitize inputs for file paths and code
    sanitized_project_name = _sanitize_class_name(project_name)
    sanitized_package_name = _sanitize_package_name(package_name)
    
    # Extract base filename without extension for display
    base_filename_display = os.path.splitext(filename)[0]

    java_dir = os.path.join(output_dir, sanitized_project_name, 'app', 'src', 'main', 'java', *sanitized_package_name.split('.'))
    res_dir = os.path.join(output_dir, sanitized_project_name, 'app', 'src', 'main', 'res')
    layout_dir = os.path.join(res_dir, 'layout')
    manifest_dir = os.path.join(output_dir, sanitized_project_name, 'app', 'src', 'main')
    gradle_app_dir = os.path.join(output_dir, sanitized_project_name, 'app')
    gradle_project_dir = os.path.join(output_dir, sanitized_project_name)

    # Create directories
    os.makedirs(java_dir, exist_ok=True)
    os.makedirs(layout_dir, exist_ok=True)
    os.makedirs(manifest_dir, exist_ok=True)
    os.makedirs(gradle_app_dir, exist_ok=True)
    os.makedirs(gradle_project_dir, exist_ok=True)

    # --- MainActivity.java content ---
    java_content = f'''package {sanitized_package_name};

import androidx.appcompat.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.IOException;

'''
    if selected_method == "OkHttp (Recommended)":
        java_content += '''import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
'''
    elif selected_method == "DownloadManager (System Service)":
        java_content += '''import android.app.DownloadManager;
import android.content.Context;
import android.net.Uri;
import android.os.Environment;
'''
    elif selected_method == "AsyncTask (Legacy)":
        java_content += '''import android.os.AsyncTask;
'''

    java_content += f'''
public class MainActivity extends AppCompatActivity {{

    private static final String TAG = "DownloaderApp";
    private EditText urlEditText;
    private TextView statusTextView;
    private Button downloadButton;

    private String downloadUrl = "{url}";
    private String outputFileName = "{filename}";

    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        urlEditText = findViewById(R.id.urlEditText);
        statusTextView = findViewById(R.id.statusTextView);
        downloadButton = findViewById(R.id.downloadButton);

        urlEditText.setText(downloadUrl); // Set initial URL

        downloadButton.setOnClickListener(new View.OnClickListener() {{
            @Override
            public void onClick(View v) {{
                downloadUrl = urlEditText.getText().toString();
                if (downloadUrl.isEmpty()) {{
                    Toast.makeText(MainActivity.this, "Please enter a URL", Toast.LENGTH_SHORT).show();
                    return;
                }}
                statusTextView.setText("Downloading...");
                startDownload(downloadUrl, outputFileName);
            }}
        }});
    }}

    private void startDownload(String urlString, String fileName) {{
        // Ensure the external storage directory exists
        File downloadsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
        if (!downloadsDir.exists()) {{
            downloadsDir.mkdirs();
        }}
        final File outputFile = new File(downloadsDir, fileName);

        Log.d(TAG, "Starting download of " + urlString + " to " + outputFile.getAbsolutePath());
'''

    if selected_method == "HttpURLConnection (Built-in)":
        java_content += f'''
        new Thread(new Runnable() {{
            @Override
            public void run() {{
                HttpURLConnection connection = null;
                InputStream inputStream = null;
                FileOutputStream outputStream = null;
                try {{
                    URL url = new URL(urlString);
                    connection = (HttpURLConnection) url.openConnection();
                    connection.connect();

                    if (connection.getResponseCode() != HttpURLConnection.HTTP_OK) {{
                        throw new IOException("Server returned HTTP " + connection.getResponseCode()
                                + " " + connection.getResponseMessage());
                    }}

                    inputStream = connection.getInputStream();
                    outputStream = new FileOutputStream(outputFile);

                    byte[] buffer = new byte[4096];
                    int bytesRead;
                    while ((bytesRead = inputStream.read(buffer)) != -1) {{
                        outputStream.write(buffer, 0, bytesRead);
                    }}

                    runOnUiThread(new Runnable() {{
                        @Override
                        public void run() {{
                            statusTextView.setText("Download complete: " + outputFile.getName());
                            Toast.makeText(MainActivity.this, "Download complete!", Toast.LENGTH_LONG).show();
                        }}
                    }});
                    Log.d(TAG, "Download successful: " + outputFile.getAbsolutePath());

                }} catch (IOException e) {{
                    Log.e(TAG, "Download failed: " + e.getMessage(), e);
                    runOnUiThread(new Runnable() {{
                        @Override
                        public void run() {{
                            statusTextView.setText("Download failed: " + e.getMessage());
                            Toast.makeText(MainActivity.this, "Download failed: " + e.getMessage(), Toast.LENGTH_LONG).show();
                        }}
                    }});
                }} finally {{
                    if (outputStream != null) {{
                        try {{ outputStream.close(); }} catch (IOException e) {{ /* ignore */ }}
                    }}
                    if (inputStream != null) {{
                        try {{ inputStream.close(); }} catch (IOException e) {{ /* ignore */ }}
                    }}
                    if (connection != null) {{
                        connection.disconnect();
                    }}
                }}
            }}
        }}).start();
'''
    elif selected_method == "OkHttp (Recommended)":
        java_content += f'''
        OkHttpClient client = new OkHttpClient();
        Request request = new Request.Builder().url(urlString).build();

        client.newCall(request).enqueue(new Callback() {{
            @Override
            public void onFailure(Call call, IOException e) {{
                Log.e(TAG, "OkHttp download failed: " + e.getMessage(), e);
                runOnUiThread(new Runnable() {{
                    @Override
                    public void run() {{
                        statusTextView.setText("Download failed: " + e.getMessage());
                        Toast.makeText(MainActivity.this, "Download failed: " + e.getMessage(), Toast.LENGTH_LONG).show();
                    }}
                }});
            }}

            @Override
            public void onResponse(Call call, Response response) throws IOException {{
                if (!response.isSuccessful()) {{
                    throw new IOException("Unexpected code " + response);
                }}

                InputStream inputStream = null;
                FileOutputStream outputStream = null;
                try {{
                    inputStream = response.body().byteStream();
                    outputStream = new FileOutputStream(outputFile);

                    byte[] buffer = new byte[4096];
                    int bytesRead;
                    while ((bytesRead = inputStream.read(buffer)) != -1) {{
                        outputStream.write(buffer, 0, bytesRead);
                    }}

                    runOnUiThread(new Runnable() {{
                        @Override
                        public void run() {{
                            statusTextView.setText("Download complete: " + outputFile.getName());
                            Toast.makeText(MainActivity.this, "Download complete!", Toast.LENGTH_LONG).show();
                        }}
                    }});
                    Log.d(TAG, "Download successful: " + outputFile.getAbsolutePath());

                }} catch (IOException e) {{
                    Log.e(TAG, "OkHttp stream write failed: " + e.getMessage(), e);
                    runOnUiThread(new Runnable() {{
                        @Override
                        public void run() {{
                            statusTextView.setText("Download failed: " + e.getMessage());
                            Toast.makeText(MainActivity.this, "Download failed: " + e.getMessage(), Toast.LENGTH_LONG).show();
                        }}
                    }});
                }} finally {{
                    if (outputStream != null) {{
                        try {{ outputStream.close(); }} catch (IOException e) {{ /* ignore */ }}
                    }}
                    if (inputStream != null) {{
                        try {{ inputStream.close(); }} catch (IOException e) {{ /* ignore */ }}
                    }}
                    if (response.body() != null) {{
                        response.body().close();
                    }}
                }}
            }}
        }});
'''
    elif selected_method == "AsyncTask (Legacy)":
        java_content += f'''
        new DownloadAsyncTask().execute(urlString, outputFile.getAbsolutePath());
    }}

    private class DownloadAsyncTask extends AsyncTask<String, Integer, String> {{
        @Override
        protected void onPreExecute() {{
            super.onPreExecute();
            statusTextView.setText("Downloading (AsyncTask)...");
        }}

        @Override
        protected String doInBackground(String... params) {{
            String urlString = params[0];
            String filePath = params[1];
            File outputFile = new File(filePath);

            HttpURLConnection connection = null;
            InputStream inputStream = null;
            FileOutputStream outputStream = null;
            try {{
                URL url = new URL(urlString);
                connection = (HttpURLConnection) url.openConnection();
                connection.connect();

                if (connection.getResponseCode() != HttpURLConnection.HTTP_OK) {{
                    return "Server returned HTTP " + connection.getResponseCode()
                            + " " + connection.getResponseMessage();
                }}

                inputStream = connection.getInputStream();
                outputStream = new FileOutputStream(outputFile);

                byte[] buffer = new byte[4096];
                int bytesRead;
                while ((bytesRead = inputStream.read(buffer)) != -1) {{
                    outputStream.write(buffer, 0, bytesRead);
                }}
                return "Download complete: " + outputFile.getName();

            }} catch (IOException e) {{
                return "Download failed: " + e.getMessage();
            }} finally {{
                if (outputStream != null) {{
                    try {{ outputStream.close(); }} catch (IOException e) {{ /* ignore */ }}
                }}
                if (inputStream != null) {{
                    try {{ inputStream.close(); }} catch (IOException e) {{ /* ignore */ }}
                }}
                if (connection != null) {{
                    connection.disconnect();
                }}
            }}
        }}

        @Override
        protected void onPostExecute(String result) {{
            super.onPostExecute(result);
            statusTextView.setText(result);
            Toast.makeText(MainActivity.this, result, Toast.LENGTH_LONG).show();
            Log.d(TAG, "AsyncTask result: " + result);
        }}
    }}
'''
    elif selected_method == "DownloadManager (System Service)":
        java_content += f'''
        DownloadManager.Request request = new DownloadManager.Request(Uri.parse(urlString));
        request.setDescription("Downloading {base_filename_display}")
               .setTitle("File Download");
        
        // Allow download over Wi-Fi and mobile networks
        request.setAllowedNetworkTypes(DownloadManager.Request.NETWORK_WIFI | DownloadManager.Request.NETWORK_MOBILE);
        
        // Set whether this download may proceed over a roaming connection.
        request.setAllowedOverRoaming(false);
        
        // Set the local destination for the downloaded file to a path within the public downloads directory.
        // This makes the file visible to the user and other apps.
        request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, fileName);
        
        // Set notification visibility
        request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);

        DownloadManager manager = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
        if (manager != null) {{
            long downloadId = manager.enqueue(request);
            statusTextView.setText("Download started via DownloadManager. ID: " + downloadId);
            Toast.makeText(MainActivity.this, "Download started in background.", Toast.LENGTH_SHORT).show();
            Log.d(TAG, "DownloadManager started for ID: " + downloadId);
            // You would typically use a BroadcastReceiver to listen for DownloadManager.ACTION_DOWNLOAD_COMPLETE
            // to get notified when the download finishes. For simplicity, this example doesn't include it.
        }} else {{
            statusTextView.setText("DownloadManager service not available.");
            Toast.makeText(MainActivity.this, "DownloadManager service not available.", Toast.LENGTH_LONG).show();
            Log.e(TAG, "DownloadManager service is null.");
        }}
'''
    else:
        raise ValueError(f"Unknown download method selected: {selected_method}")

    java_content += f'''
    }}
}}
'''
    # Write MainActivity.java
    with open(os.path.join(java_dir, 'MainActivity.java'), 'w') as f:
        f.write(java_content)

    # --- activity_main.xml content ---
    xml_layout_content = f'''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    xmlns:tools="http://schemas.android.com/tools"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="16dp"
    android:gravity="center_horizontal"
    tools:context=".{_sanitize_class_name(project_name)}.MainActivity">

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Android File Downloader"
        android:textSize="24sp"
        android:textStyle="bold"
        android:layout_marginBottom="24dp" />

    <EditText
        android:id="@+id/urlEditText"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="Enter URL to download"
        android:inputType="textUri"
        android:padding="12dp"
        android:background="@android:drawable/editbox_background"
        android:layout_marginBottom="16dp" />

    <Button
        android:id="@+id/downloadButton"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Start Download"
        android:paddingLeft="24dp"
        android:paddingRight="24dp"
        android:layout_marginBottom="24dp" />

    <TextView
        android:id="@+id/statusTextView"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Status: Ready"
        android:textSize="18sp"
        android:textColor="@android:color/darker_gray" />

</LinearLayout>
'''
    # Write activity_main.xml
    with open(os.path.join(layout_dir, 'activity_main.xml'), 'w') as f:
        f.write(xml_layout_content)

    # --- AndroidManifest.xml content ---
    manifest_content = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{sanitized_package_name}">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="28" />
    <!-- For Android 10 (API 29) and above, WRITE_EXTERNAL_STORAGE is largely deprecated for direct file access.
         Consider using Scoped Storage (MediaStore API) or DownloadManager for downloads.
         DownloadManager automatically handles permissions for its public directories. -->

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.{_sanitize_class_name(project_name)}"
        android:requestLegacyExternalStorage="true"> <!-- For older WRITE_EXTERNAL_STORAGE behavior on Android 10+ -->

        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>
'''
    # Write AndroidManifest.xml
    with open(os.path.join(manifest_dir, 'AndroidManifest.xml'), 'w') as f:
        f.write(manifest_content)

    # --- strings.xml (basic app name) ---
    strings_content = f'''<resources>
    <string name="app_name">{project_name}</string>
</resources>
'''
    res_values_dir = os.path.join(res_dir, 'values')
    os.makedirs(res_values_dir, exist_ok=True)
    with open(os.path.join(res_values_dir, 'strings.xml'), 'w') as f:
        f.write(strings_content)

    # --- styles.xml (basic theme) ---
    styles_content = f'''<resources>
    <!-- Base application theme. -->
    <style name="Theme.{_sanitize_class_name(project_name)}" parent="Theme.AppCompat.Light.DarkActionBar">
        <!-- Customize your theme here. -->
        <item name="colorPrimary">@color/purple_500</item>
        <item name="colorPrimaryDark">@color/purple_700</item>
        <item name="colorAccent">@color/teal_200</item>
    </style>
</resources>
'''
    # Create colors.xml with dummy colors if they don't exist
    colors_content = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="purple_200">#FFBB86FC</color>
    <color name="purple_500">#FF6200EE</color>
    <color name="purple_700">#FF3700B3</color>
    <color name="teal_200">#FF03DAC5</color>
    <color name="teal_700">#FF018786</color>
    <color name="black">#FF000000</color>
    <color name="white">#FFFFFFFF</color>
</resources>
'''
    with open(os.path.join(res_values_dir, 'styles.xml'), 'w') as f:
        f.write(styles_content)
    with open(os.path.join(res_values_dir, 'colors.xml'), 'w') as f:
        f.write(colors_content)


    # --- build.gradle (app level) ---
    gradle_app_content = f'''plugins {{
    id 'com.android.application'
}}

android {{
    compileSdk 34 // Or latest stable SDK version

    defaultConfig {{
        applicationId "{sanitized_package_name}"
        minSdk 21
        targetSdk 34 // Or latest stable SDK version
        versionCode 1
        versionName "1.0"

        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
    }}

    buildTypes {{
        release {{
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
    }}
    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }}
}}

dependencies {{
    implementation 'androidx.appcompat:appcompat:1.6.1' // Or latest stable version
    implementation 'com.google.android.material:material:1.12.0' // Or latest stable version
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4' // Or latest stable version
    testImplementation 'junit:junit:4.13.2'
    androidTestImplementation 'androidx.test.ext:junit:1.1.5'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.5.1'
'''
    if selected_method == "OkHttp (Recommended)":
        gradle_app_content += "    implementation 'com.squareup.okhttp3:okhttp:4.12.0' // Or latest stable version\n"
    
    gradle_app_content += "}\n"

    with open(os.path.join(gradle_app_dir, 'build.gradle'), 'w') as f:
        f.write(gradle_app_content)

    # --- build.gradle (project level) ---
    gradle_project_content = f'''// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {{
    id 'com.android.application' version '8.1.0' apply false // Or latest stable AGP version
    id 'com.android.library' version '8.1.0' apply false
}}
'''
    with open(os.path.join(gradle_project_dir, 'build.gradle'), 'w') as f:
        f.write(gradle_project_content)

    # --- settings.gradle ---
    settings_content = f'''pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}
dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}
rootProject.name = "{sanitized_project_name}"
include ':app'
'''
    with open(os.path.join(gradle_project_dir, 'settings.gradle'), 'w') as f:
        f.write(settings_content)
    
    # --- .gitignore (optional but good practice) ---
    gitignore_content = '''
.gradle/
/local.properties
/.idea/
.DS_Store
/build/
/captures/
.externalNativeBuild/
.cxx/
*.iml
*.ap_
*.apk
*.aab
*.aar
*.aidl
*.class
*.dex
*.jar
*.keystore
*.orig
*.pyc
*.swp
*.zip
/out/
/app/build/
/app/.cxx/
/app/.externalNativeBuild/
/app/src/main/assets/
/app/src/main/libs/
/app/src/main/obj/
/app/src/main/res/raw/
/app/src/main/res/values/
/app/src/main/res/xml/
/app/src/main/res/drawable-hdpi/
/app/src/main/res/drawable-mdpi/
/app/src/main/res/drawable-xhdpi/
/app/src/main/res/drawable-xxhdpi/
/app/src/main/res/drawable-xxxhdpi/
/app/src/main/res/mipmap-hdpi/
/app/src/main/res/mipmap-mdpi/
/app/src/main/res/mipmap-xhdpi/
/app/src/main/res/mipmap-xxhdpi/
/app/src/main/res/mipmap-xxxhdpi/
'''
    with open(os.path.join(gradle_project_dir, '.gitignore'), 'w') as f:
        f.write(gitignore_content)


def generate_android_project():
    """
    Generates an Android project with the selected download method.
    """
    url = url_entry.get()
    selected_method = method_var.get()
    project_name = project_name_entry.get()
    package_name = package_name_entry.get()

    if not url:
        messagebox.showwarning("Input Error", "Please enter a valid URL.")
        return
    if not project_name:
        messagebox.showwarning("Input Error", "Please enter a Project Name.")
        return
    if not package_name:
        messagebox.showwarning("Input Error", "Please enter a Package Name (e.g., com.example.app).")
        return

    if not (url.startswith("http://") or url.startswith("https://")):
        messagebox.showwarning("Invalid URL", "URL must start with http:// or https:// for Android download methods.")
        return
    
    try:
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        filename = path_segments[-1] if path_segments[-1] else "downloaded_file"
        if '.' not in filename:
            filename += ".dat"

        # Sanitize filename for Android file system compatibility
        filename = re.sub(r'[\\/:*?"<>|]', '_', filename)

        # Base directory for the new Android project
        project_output_dir = os.path.join(OUTPUT_BASE_DIR, _sanitize_class_name(project_name))
        
        # Ensure the base output directory exists
        os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

        _write_android_project_content(url, selected_method, filename, project_name, package_name, OUTPUT_BASE_DIR)

        messagebox.showinfo(
            "Success",
            f"Android project '{project_name}' created successfully!\n"
            f"You can find it at: {project_output_dir}\n\n"
            f"**Next Steps:**\n"
            f"1. Open Android Studio.\n"
            f"2. Select 'Open an existing Android Studio project'.\n"
            f"3. Navigate to and select the folder: '{project_output_dir}'.\n"
            f"4. Let Gradle sync. If prompted, update SDK/Gradle versions.\n"
            f"5. For 'OkHttp' method, Android Studio might prompt to add the dependency to build.gradle (app).\n"
            f"6. Run the app on an emulator or device. Grant storage permissions if prompted."
        )

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# --- GUI Setup ---
app = tk.Tk()
app.title("Android (.apk) Downloader Source Generator")
app.geometry("800x550") # Adjusted size
app.resizable(False, False)

# Configure grid for better layout
for i in range(7):
    app.grid_rowconfigure(i, weight=1)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=3)

# Project Name Label and Entry
project_name_label = tk.Label(app, text="Android Project Name:")
project_name_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
project_name_entry = tk.Entry(app, width=50)
project_name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
project_name_entry.insert(0, "MyAndroidDownloader")

# Package Name Label and Entry
package_name_label = tk.Label(app, text="Android Package Name:")
package_name_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
package_name_entry = tk.Entry(app, width=50)
package_name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
package_name_entry.insert(0, "com.example.downloader")

# URL Label
url_label = tk.Label(app, text="Enter File URL:")
url_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")

# URL Entry
url_entry = tk.Entry(app, width=50)
url_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
url_entry.focus_set()
url_entry.insert(0, "https://www.example.com/sample.zip") # Default URL

# Download Method Label
method_label = tk.Label(app, text="Select Download Method:")
method_label.grid(row=3, column=0, padx=10, pady=5, sticky="e")

# Download Method Dropdown (OptionMenu)
download_methods = [
    "HttpURLConnection (Built-in)",
    "OkHttp (Recommended)",
    "AsyncTask (Legacy)",
    "DownloadManager (System Service)"
]
method_var = tk.StringVar(app)
method_var.set(download_methods[0]) # Set default value

method_dropdown = tk.OptionMenu(app, method_var, *download_methods)
method_dropdown.config(width=40) # Adjust width
method_dropdown.grid(row=3, column=1, padx=10, pady=5, sticky="w")

# Note: "Execute after download" is typically handled within the Android app itself
# or by the user opening the downloaded file. It's not a direct post-generation step.
# I'm keeping the checkbox disabled to reflect this.
execute_var = tk.BooleanVar()
execute_checkbox = tk.Checkbutton(app, text="Execute after download (handled within Android app)", variable=execute_var, state=tk.DISABLED)
execute_checkbox.grid(row=4, column=1, padx=10, pady=5, sticky="w")


# Buttons
generate_button = tk.Button(app, text="Generate Android Project Source", command=generate_android_project)
generate_button.grid(row=5, column=0, columnspan=2, pady=20)

# Note: "Create All Methods" is less practical for Android projects due to project structure.
# A single project with selectable methods is more common. I'm omitting this button.
# create_all_button = tk.Button(app, text="Create All Methods", command=create_all_android_projects)
# create_all_button.grid(row=6, column=0, columnspan=2, pady=10)

# Run the application
app.mainloop()
