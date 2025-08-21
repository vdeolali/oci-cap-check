# oci-cap-check
This is a flask application i.e. you access it in your browser at localhost:5000. The UI is just a form that collects inputs to query the backend for capacity. 

# How to run
Run the app: python app.py
Open the webpage in your browser (http://127.0.0.1:5000).
Fill out the form and click "Check Capacity".

## Troubleshooting
The most common point of failure for a script like this is authentication. The environment where you run python app.py might not have the same access to your OCI config as your normal user terminal.
Config File Path: The default path is ~/.oci/config. The ~ symbol refers to the home directory of the user running the script. If you are using a different user or a virtual environment, this path might not be correct. Try using the full, absolute path to your config file in the web form (e.g., /Users/yourname/.oci/config or C:\Users\yourname\.oci\config).
Permissions: Ensure the config file and the key file it references are readable by the user running the Flask app.

<img width="1265" height="838" alt="image" src="https://github.com/user-attachments/assets/cf21c775-99a4-4a49-8cc6-28abb9f2e234" />

