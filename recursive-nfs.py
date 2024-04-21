from colorama import Fore

import helpers.global_fields as g

from data_classes.nfs_share import NFSShare
from helpers.args import obtain_args
from helpers.config_loader import obtain_config, obtain_config
from modules.api import APIManager
from modules.zfs import create_recursive_shares, delete_irrelevant_automatically_created_shares, handle_non_automatic_relevant_shares, obtain_list_of_relevant_datasets, update_present_recursive_shares

def main(_args, _config) -> bool:
    g.config = _config
    g.args = _args

    # Connect to the API
    g.api_manager = APIManager()
    # Check if API is available
    g.api_manager.check_api_availability()

    # Extract relevant datasets using the API, or from output of zfs list -o POOL_NAME; See the help page for available options
    relevant_datasets = obtain_list_of_relevant_datasets()
    if relevant_datasets is None:
        return False
    
    # Obtain all current NFS shares
    shares_query_response = g.api_manager.get_shares_query_response()
    all_shares = NFSShare.list_from_api_response(shares_query_response)
    
    # Check for non-automatically created shares that are relevant
    # to query the user whether they want them deleted
    non_automatic_relevant_shares = [
        share for share in all_shares
            if share.is_relevant(relevant_datasets)
                and not share.is_automatically_created()
    ]
    if non_automatic_relevant_shares:
        handle_non_automatic_relevant_shares(non_automatic_relevant_shares)

    # Remove all automatically created shares that are no longer relevant
    # NOTE: This is both for removing outdated shares that are no longer required and those that might be broken
    deletion_succeeded, relevant_automatically_created_shares = delete_irrelevant_automatically_created_shares(all_shares, relevant_datasets)
    if not deletion_succeeded:
        return False
    
    # Update already present automatically created shares
    if not update_present_recursive_shares(relevant_automatically_created_shares):
        return False

    # Create all relevant remaining shares
    dataset_path_names_with_present_shares = [share.path_name for share in relevant_automatically_created_shares]
    datasets_needing_new_shares = [dataset for dataset in relevant_datasets if dataset not in dataset_path_names_with_present_shares]
    if not create_recursive_shares(datasets_needing_new_shares):
        return False
    
    return True

if __name__ == "__main__":
    _args = obtain_args()
    _config = obtain_config(_args)
    if main(_args, _config):
        print(f"{Fore.GREEN}Done.{Fore.RESET}")
    else:
        print(f"{Fore.RED}Terminating.{Fore.RESET}")