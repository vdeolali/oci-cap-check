from flask import Flask, render_template, request
from oci_runner import run_capacity_check
from modules.identity import init_authentication
import oci

app = Flask(__name__)

def get_oci_tenancy_regions(identity_client):
    """Fetches the list of regions the tenancy is subscribed to."""
    try:
        regions = oci.pagination.list_call_get_all_results(identity_client.list_regions).data
        region_names = [region.name for region in regions]
        return sorted(region_names)
    except Exception as e:
        print(f"!!! ERROR inside get_oci_tenancy_regions: {e}")
        return [f"Error fetching regions"]

def get_oci_shapes(config, signer):
    """Fetches a list of all available compute shapes for a tenancy."""
    try:
        compute_client = oci.core.ComputeClient(config=config, signer=signer)
        compartment_id = config["tenancy"]
        list_shapes_response = oci.pagination.list_call_get_all_results(
            compute_client.list_shapes,
            compartment_id=compartment_id
        )
        shape_names = [shape.shape for shape in list_shapes_response.data]
        return sorted(shape_names)
    except Exception as e:
        print(f"!!! ERROR inside get_oci_shapes: {e}")
        return ["Error fetching shapes"]

@app.route('/', methods=['GET', 'POST'])
def index():
    report_output = ""
    error_message = ""
    oci_regions = []
    shape_list = []
    form_data = request.form

    if request.method == 'POST':
        auth_params = {
            'user_auth': form_data.get('user_auth'),
            'config_file_path': form_data.get('config_file_path'),
            'config_profile': form_data.get('config_profile')
        }
        action = form_data.get('action')

        if action == 'load_data':
            try:
                config, signer, tenancy, _, _ = init_authentication(**auth_params)
                if not all([config, signer, tenancy]):
                    raise ValueError("Authentication function returned incomplete credentials.")
                
                identity_client = oci.identity.IdentityClient(config, signer=signer)
                oci_regions = get_oci_tenancy_regions(identity_client)
                shape_list = get_oci_shapes(config, signer)

            except Exception as e:
                error_message = f"Failed to connect and load data. Please check credentials.\nError: {e}"

        elif action == 'run_report':
            try:
                # Re-fetch data to keep dropdowns populated on the results page
                config, signer, tenancy, _, _ = init_authentication(**auth_params)
                if not all([config, signer, tenancy]):
                    raise ValueError("Authentication function returned incomplete credentials for report run.")

                identity_client = oci.identity.IdentityClient(config, signer=signer)
                oci_regions = get_oci_tenancy_regions(identity_client)
                shape_list = get_oci_shapes(config, signer)

                # Now, run the report with the new parameters from the second form
                report_params = {
                    'target_region': form_data.get('target_region'),
                    'shape': form_data.get('shape'),
                    'ocpus': int(form_data.get('ocpus')) if form_data.get('ocpus') else None,
                    'memory': int(form_data.get('memory')) if form_data.get('memory') else None,
                    'compartment': form_data.get('compartment'),
                    'su': 'su' in form_data,
                    'drcc': 'drcc' in form_data
                }
                report_output = run_capacity_check(auth_params, report_params)
            except Exception as e:
                 error_message = f"Failed to run report. Please check parameters.\nError: {e}"


    return render_template('index.html',
                           report_output=report_output,
                           form_data=form_data,
                           oci_regions=oci_regions,
                           shape_list=shape_list,
                           error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)
