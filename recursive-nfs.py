from colorama import Fore

import helpers.global_fields as g

from data_classes.nfs_share import NFSShare
from helpers.args import obtain_args
from helpers.config_loader import obtain_config, obtain_config
from modules.api import APIManager
from modules.zfs import create_recursive_shares, delete_automatically_created_shares, handle_non_automatic_relevant_shares, obtain_list_of_relevant_datasets

def main(_args, _config) -> bool:
    g.config = _config
    g.args = _args

    # Extract relevant datasets from output of zfs list -o POOL_NAME
    relevant_datasets = obtain_list_of_relevant_datasets()

    # Connect to the API
    g.api_manager = APIManager()
    
    # Check if API is available
    g.api_manager.check_api_availability()
    
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

    # Remove all automatically created shares (do not care if they are relevant)
    # NOTE: This is for removing outdated shares that no longer are required, or even broken
    if not delete_automatically_created_shares(all_shares):
        return False

    # Create all relevant shares
    if not create_recursive_shares(relevant_datasets):
        return False
    
    return True

if __name__ == "__main__":
    _args = obtain_args()
    _config = obtain_config(_args)
    if main(_args, _config):
        print(f"{Fore.GREEN}Done.{Fore.RESET}")
    else:
        print(f"{Fore.RED}Terminating.{Fore.RESET}")