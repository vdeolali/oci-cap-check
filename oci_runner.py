import oci
import io
import sys
from contextlib import redirect_stdout
from modules.utils import green, print_info
from modules.identity import init_authentication, get_region_subscription_list, validate_region_connectivity, get_home_region, set_user_compartment
from modules.capacity import denseio_flex_shapes, process_region, set_denseio_shape_ocpus, set_user_shape_name, set_user_shape_ocpus, set_user_shape_memory

def run_capacity_check(auth_params, report_params):
    """
    This function encapsulates the logic of the OCI Capacity Report script.
    It captures and returns all printed output.
    """
    # Use an in-memory text buffer to capture the script's print output
    output_buffer = io.StringIO()
    with redirect_stdout(output_buffer):
        try:
            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            # Init OCI authentication from provided params
            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            config, signer, tenancy, auth_name, details = init_authentication(
                auth_params['user_auth'], 
                auth_params['config_file_path'], 
                auth_params['config_profile']
            )

            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            # Start print script info
            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            print(green(f"\n{'*'*94:94}"))
            print_info(green, 'Login', 'success', auth_name)
            print_info(green, 'Login', 'profile', details)
            print_info(green, 'Tenancy', tenancy.name, f'home region: {tenancy.home_region_key}')
            
            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            # Init oci service client
            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            identity_client=oci.identity.IdentityClient(config=config, signer=signer)
            tenancy_id=config['tenancy']

            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            # Set target regions
            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            regions_to_analyze=get_region_subscription_list(
                identity_client,
                tenancy_id,
                report_params['target_region']
            )
            regions_validated=validate_region_connectivity(
                regions_to_analyze,
                config,
                signer
            )

            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            # End print script info
            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            if report_params['shape']:
                print_info(green, 'Shape', 'analyzed', report_params['shape'])
            if report_params['ocpus']:
                print_info(green, 'oCPUs', 'amount', f"{report_params['ocpus']} cores")
            if report_params['memory']:
                print_info(green, 'Memory', 'amount', f"{report_params['memory']} gbs")

            print(green(f"{'*'*94:94}\n"))

            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            # Set report variables from params
            # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            class Args:
                su = report_params['su']
                compartment = report_params['compartment']

            user_compartment = set_user_compartment(identity_client, Args, tenancy_id)
            user_shape_name = report_params['shape']
            user_shape_ocpus = report_params['ocpus']
            user_shape_memory = report_params['memory']
            
            # --- This is the core logic from your main() function ---
            if not user_shape_name:
                 print("\nError: Shape name is a required field for the web UI.")
                 return output_buffer.getvalue()

            if user_shape_name in denseio_flex_shapes:
                user_shape_ocpus = float(set_denseio_shape_ocpus(user_shape_name))

            elif ".Flex" not in user_shape_name or user_shape_name.startswith('BM.'):
                user_shape_ocpus = 0
                user_shape_memory = 0
            
            else:
                user_shape_ocpus = set_user_shape_ocpus(user_shape_name) if not user_shape_ocpus else user_shape_ocpus
                user_shape_memory = set_user_shape_memory(user_shape_name) if not user_shape_memory else user_shape_memory
                
            header = f"\n{'REGION':<20} {'AVAILABILITY_DOMAIN':<30} {'FAULT_DOMAIN':<20} {'SHAPE':<25} {'OCPU':<10} {'MEMORY':<10}"
            if report_params['drcc']:
                header += f" {'AVAILABLE_COUNT':<16}"
            header += f" {'AVAILABILITY'}\n"

            print(header)

            for region in regions_validated:
                config['region']=region.region_name
                process_region(region, config, signer, user_compartment, user_shape_name, user_shape_ocpus, user_shape_memory, report_params['drcc'])

        except Exception as e:
            # Print any errors to the buffer as well
            print(f"\n\nAn error occurred:\n{str(e)}")

    # Get the content of the buffer and return it
    report_output = output_buffer.getvalue()
    return report_output
