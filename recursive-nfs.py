from sys import stdin

import helpers.global_fields as g

from halo import Halo

from helpers.args import obtain_args
from helpers.config_loader import obtain_config, obtain_config
from helpers.spinner import spinner
from modules.api import APIManager

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

def main(_args, _config):
    g.config = _config
    g.args = _args

    relevant_datasets = obtain_list_of_relevant_datasets()

    api_manager = APIManager()
    print(api_manager.get_nfs_shares().json())

if __name__ == "__main__":
    _args = obtain_args()
    _config = obtain_config(_args)
    main(_args, _config)