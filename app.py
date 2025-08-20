from flask import Flask, render_template, request
from oci_runner import run_capacity_check

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    report_output = ""
    form_data = request.form 
    
    if request.method == 'POST':
        # --- Authentication Parameters ---
        auth_params = {
            'user_auth': form_data.get('user_auth'),
            'config_file_path': form_data.get('config_file_path', '~/.oci/config'),
            'config_profile': form_data.get('config_profile', 'DEFAULT')
        }

        # --- Report/Script Parameters ---
        report_params = {
            'target_region': form_data.get('target_region', 'all_regions'),
            'shape': form_data.get('shape'),
            'ocpus': int(form_data.get('ocpus')) if form_data.get('ocpus') else None,
            'memory': int(form_data.get('memory')) if form_data.get('memory') else None,
            'compartment': form_data.get('compartment'),
            'su': 'su' in form_data,  # Check if the checkbox was ticked
            'drcc': 'drcc' in form_data # Check if the checkbox was ticked
        }

        # Run the refactored script logic and get the output
        report_output = run_capacity_check(auth_params, report_params)

    # Re-render the page, passing in the output and the form data to repopulate fields
    return render_template('index.html', report_output=report_output, form_data=form_data)

if __name__ == '__main__':
    app.run(debug=True)

