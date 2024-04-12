from halo import Halo
from munch import munchify
from yaml import safe_load

from helpers.spinner import spinner

def obtain_config(args):
    with Halo(text=f"Loading config from {args.config}"):
        with open(args.config, "r") as file_handle:
            yaml_dict = safe_load(file_handle)
        return munchify(yaml_dict)