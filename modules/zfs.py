from colorama import Fore
from halo import Halo
from sys import stdin

import helpers.global_fields as g

from data_classes.nfs_share import NFSShare
from helpers.cli_utility import is_input_prompt_positive
from helpers.spinner import spinner, spinner_generator

def obtain_zfs_list_output() -> list[str]:
    if g.args.datasets_file is not None:
        with open(g.args.datasets_file, "r") as dataset_file_handle, Halo(f"Reading dataset list from '{g.args.datasets_file}'"):
            return dataset_file_handle.readlines()
    elif g.args.stdin:
        print("Attempting to read from STDIN...\nPass in a file, or enter content manually and confirm with Ctrl+D (Ctrl+Z, then Enter on Windows)")
        return stdin.readlines()
    else:
        return None

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

def get_list_of_relevant_datasets_for_dataset_list(dataset_list: list[str]) -> list[str]:
    def is_dataset_relevant(dataset: str):
        return any(dataset.startswith(requested_recursive_share) for requested_recursive_share in g.config.shares)
    relevant_datasets = [dataset for dataset in dataset_list if is_dataset_relevant(dataset)]
    print(f"{len(relevant_datasets)} of {len(dataset_list)} datasets require shares with the current config:")
    for dataset in relevant_datasets:
        print(f"\t- {dataset}")
    return relevant_datasets

def get_list_of_relevant_datasets_for_list_output(zfs_list_output: list[str]) -> list[str]:
    all_datasets = obtain_list_of_all_datasets(zfs_list_output)
    return get_list_of_relevant_datasets_for_dataset_list(all_datasets)

def obtain_list_of_relevant_datasets() -> list[str]:
    zfs_list_output = obtain_zfs_list_output()
    if zfs_list_output is None:
        # No data retrieved from datasets file or STDIN. Falling back to API request
        datasets_query_response = g.api_manager.get_available_datasets_query_response()
        if datasets_query_response.status_code != 200:
            print(f"{Fore.RED}Could not gather available datasets from any applicable source. Please refer to the help page.{Fore.RED}")
            return None
        datasets_response_json = datasets_query_response.json()
        all_datasets = [dataset_info["id"] for dataset_info in datasets_response_json]
        all_datasets.sort()
        return get_list_of_relevant_datasets_for_dataset_list(all_datasets)
    else:    
        return get_list_of_relevant_datasets_for_list_output(zfs_list_output)

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
                
def delete_irrelevant_automatically_created_shares(all_shares: list[NFSShare], relevant_datasets: list[str]) -> bool:
    automatically_created_shares = [share for share in all_shares if share.is_automatically_created()]
    number_of_automatically_created_shares = len(automatically_created_shares)
    if number_of_automatically_created_shares <= 0:
        return True
    
    print(f"{Fore.CYAN}Note: There are {number_of_automatically_created_shares} automatically created shares already present")

    # Filter for relevant shares that should only be updated, instead of deleted
    irrelevant_automatically_created_shares = [share for share in automatically_created_shares if share.path_name not in relevant_datasets]
    number_of_shares_to_delete = len(irrelevant_automatically_created_shares)

    if number_of_shares_to_delete <= 0:
        return True

    print(f"{Fore.YELLOW}Warning: The following {number_of_shares_to_delete} automatically created shares that are no longer relevant:")
    for automatic_share in irrelevant_automatically_created_shares:
        print(automatic_share)
    print(f"{Fore.YELLOW}Warning: Above automatically created shares ({number_of_shares_to_delete}) will be deleted.\n{Fore.RESET}")

    delete_automatic_shares_response = input("\nDo you want to delete these automatically created shares? y/[n]: ")
    should_delete_automatic_shares = is_input_prompt_positive(delete_automatic_shares_response)
    if not should_delete_automatic_shares:
        return False
    
    remaining_number_of_shares_to_delete = number_of_shares_to_delete
    def get_spinner_text(share: NFSShare):
        f"Removing automatically created shares ({share.path_name}, {remaining_number_of_shares_to_delete} remaining)..."

    with spinner_generator() as spinner:
        for automatic_share in automatically_created_shares:
            spinner.start(get_spinner_text(automatic_share))
            g.api_manager.delete_share(automatic_share)
            remaining_number_of_shares_to_delete -= 1

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