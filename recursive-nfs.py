from colorama import Fore
from data_classes.nfs_share import NFSShare

import helpers.global_fields as g

from helpers.args import obtain_args
from helpers.cli_utility import is_input_prompt_positive
from helpers.config_loader import obtain_config, obtain_config
from modules.api import APIManager
from modules.zfs import obtain_list_of_relevant_datasets

def main(_args, _config):
    g.config = _config
    g.args = _args

    # Extract relevant datasets from output of zfs list -o POOL_NAME
    relevant_datasets = obtain_list_of_relevant_datasets()

    # Connect to the API
    api_manager = APIManager()
    
    # Check if API is available
    # TODO
    
    # Obtain all current NFS shares
    nfs_shares_query_response = api_manager.get_nfs_shares_query_response()
    nfs_shares = NFSShare.list_from_api_response(nfs_shares_query_response)
    
    # Check for non-automatically created shares that are relevant
    # to query the user whether they want them deleted
    non_automatic_relevant_nfs_shares = [
        nfs_share for nfs_share in nfs_shares
            if nfs_share.is_relevant(relevant_datasets)
                and not nfs_share.is_automatically_created()
    ]

    if non_automatic_relevant_nfs_shares:
        print("{Fore.ORANGE}Warning: There are active relevant NFS shares that have not been automatically created:{Fore.RESET}")
        print("\n".join(non_automatic_relevant_nfs_shares))
        delete_non_automatic_shares_response = input("\nDo you want to delete them? y/[n]")
        should_delete_non_automatic_shares = is_input_prompt_positive(delete_non_automatic_shares_response)

        if should_delete_non_automatic_shares:
            for non_automatic_share in non_automatic_relevant_nfs_shares:
                non_automatic_share.delete_using_api()


if __name__ == "__main__":
    _args = obtain_args()
    _config = obtain_config(_args)
    main(_args, _config)