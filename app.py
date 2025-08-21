from flask import Flask, render_template, request
from oci_runner import run_capacity_check
import oci

app = Flask(__name__)

def get_oci_regions():
    """
    Fetches a list of all OCI region names using an anonymous signer.
    Returns a sorted list of region names.
    """
    try:
        # Use an anonymous signer since fetching region list doesn't require user credentials
        signer = oci.signer.AnonymousSigner()
        identity_client = oci.identity.IdentityClient(config={}, signer=signer)
        # The list_regions() call gets all publicly available regions
        regions = identity_client.list_regions()
        # Extract the region name (e.g., "us-ashburn-1") from each region object
        region_names = [region.name for region in regions.data]
        return sorted(region_names)
    except Exception as e:
        print(f"Error fetching OCI regions: {e}")
        # Return a fallback list in case the API call fails
        return ["us-ashburn-1", "us-phoenix-1", "eu-frankfurt-1", "uk-london-1"]

@app.route('/', methods=['GET', 'POST'])
def index():
    report_output = ""
    form_data = request.form 
    
    # Fetch the list of OCI regions to populate the dropdown
    oci_regions = get_oci_regions()

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
            'su': 'su' in form_data,
            'drcc': 'drcc' in form_data
        }

        # Run the refactored script logic and get the output
        report_output = run_capacity_check(auth_params, report_params)

    # Pass the list of regions to the template
    return render_template('index.html', 
                           report_output=report_output, 
                           form_data=form_data, 
                           oci_regions=oci_regions)

if __name__ == '__main__':
    app.run(debug=True)

