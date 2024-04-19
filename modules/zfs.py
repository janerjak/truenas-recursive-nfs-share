# TEMP
import curlify

from colorama import Fore
from halo import Halo
from sys import stdin

import helpers.global_fields as g

from data_classes.nfs_share import NFSShare
from helpers.cli_utility import is_input_prompt_positive
from helpers.spinner import spinner, spinner_generator

def obtain_zfs_list_output() -> list[str]:
    if g.args.datasets_file is None:
        print("Attempting to read from STDIN...\nPass in a file, or enter content manually and confirm with Ctrl+D (Ctrl+Z, then Enter on Windows)")
        return stdin.readlines()
    else:
        with open(g.args.datasets_file, "r") as dataset_file_handle, Halo(f"Reading dataset list from '{g.args.datasets_file}'"):
            return dataset_file_handle.readlines()

@spinner("Extracting list of datasets")
def obtain_list_of_all_datasets(zfs_list_output) -> list[str]:
    filtered_list_output = [line.strip() for line in zfs_list_output if len(line.strip()) > 0]
    
    if not isinstance(filtered_list_output, list) or len(filtered_list_output) < 1:
        raise Exception("No list of datasets was received (via STDIN or the datasets-file).\nPlease see the quick guide for reference on how to use this tool")
    
    expected_list_header = filtered_list_output[0]
    if expected_list_header != "NAME":
        raise Exception("Expected list header 'NAME' from 'zfs list -o name' invocation. Terminating for safety.")
    
    list_without_header = filtered_list_output[1:]
    print(f"Found {len(list_without_header)} datasets in total")
    return list_without_header

def get_list_of_relevant_datasets_for(zfs_list_output: list[str]) -> list[str]:
    def is_dataset_relevant(dataset: str):
        return any(dataset.startswith(requested_recursive_share) for requested_recursive_share in g.config.shares)
    all_datasets = obtain_list_of_all_datasets(zfs_list_output)
    relevant_datasets = [dataset for dataset in all_datasets if is_dataset_relevant(dataset)]
    print(f"{len(relevant_datasets)} of {len(all_datasets)} datasets require shares with the current config:")
    for dataset in relevant_datasets:
        print(f"\t- {dataset}")
    return relevant_datasets

def obtain_list_of_relevant_datasets() -> list[str]:
    zfs_list_output = obtain_zfs_list_output()
    return get_list_of_relevant_datasets_for(zfs_list_output)

def handle_non_automatic_relevant_shares(non_automatic_relevant_shares: list[NFSShare]):
    number_of_problematic_shares = len(non_automatic_relevant_shares)
    print(f"{Fore.YELLOW}Warning: There are {number_of_problematic_shares} active relevant NFS shares that have not been automatically created:{Fore.RESET}")
    print("\n".join(
        str(share) for share in non_automatic_relevant_shares)
    )
    delete_non_automatic_shares_response = input("\nDo you want to delete them? y/[n]: ")
    should_delete_non_automatic_shares = is_input_prompt_positive(delete_non_automatic_shares_response)

    if should_delete_non_automatic_shares:
        with spinner_generator(f"Removing {number_of_problematic_shares} present manual shares"):
            for non_automatic_share in non_automatic_relevant_shares:
                g.api_manager.delete_share(non_automatic_share)
                
def delete_automatically_created_shares(all_shares: list[NFSShare]) -> bool:
    automatically_created_shares = [share for share in all_shares if share.is_automatically_created()]
    number_of_automatically_created_shares = len(automatically_created_shares)
    if number_of_automatically_created_shares <= 0:
        return True
    
    print(f"{Fore.CYAN}Note: There are {number_of_automatically_created_shares} automatically created shares present that will be deleted:{Fore.RESET}")
    for automatic_share in automatically_created_shares:
        print(automatic_share)
    print(f"{Fore.CYAN}Note: Above automatically created shares ({number_of_automatically_created_shares}) will be deleted.\n{Fore.RESET}")

    delete_automatic_shares_response = input("\nDo you want to delete these automatically created shares? y/[n]: ")
    should_delete_automatic_shares = is_input_prompt_positive(delete_automatic_shares_response)
    if not should_delete_automatic_shares:
        return False
    
    with spinner_generator(f"Removing {number_of_automatically_created_shares} automatically created shares"):
        for automatic_share in automatically_created_shares:
            g.api_manager.delete_share(automatic_share)

    return True

def create_recursive_shares(relevant_datasets: list[str]) -> bool:
    shares_to_create = [
        NFSShare.from_config_options(relevant_dataset_path_name)
        for relevant_dataset_path_name in relevant_datasets
    ]
    number_of_shares_to_create = len(shares_to_create)
    if number_of_shares_to_create <= 0:
        print(f"{Fore.RED}Note: There are no relevant datasets available to create shares for\n{Fore.RESET}")
        return False
    
    print(f"{Fore.CYAN}Warning: Attempting to create the following ({number_of_shares_to_create}) NFS shares:{Fore.RESET}")
    print("\n".join(
        str(share) for share in shares_to_create)
    )
    print(f"{Fore.CYAN}Warning: Attempting to create the above ({number_of_shares_to_create}) NFS shares{Fore.RESET}")
    create_automatic_shares_response = input("\nDo you want to create them? [y]/n: ")
    should_create_automatic_shares = (not create_automatic_shares_response) or is_input_prompt_positive(create_automatic_shares_response)

    if not should_create_automatic_shares:
        return False
    
    number_of_remaining_shares = number_of_shares_to_create
    def get_spinner_text(share: NFSShare):
        return f"Creating share {share.path_name} ({number_of_remaining_shares} remaining)..."
    starting_spinner_text = f"Creating {number_of_shares_to_create} shares..."
    with spinner_generator(starting_spinner_text) as spinner:
        for automatic_share in shares_to_create:
            spinner.start(get_spinner_text(automatic_share))
            creation_response = g.api_manager.create_share(automatic_share)
            if creation_response.status_code != 200:
                raise Exception(f"Error ({creation_response.reason}):\n{creation_response.text}")
            number_of_remaining_shares -= 1
        spinner.start(starting_spinner_text)
        spinner.succeed(f"Created {number_of_shares_to_create} shares")

    return True