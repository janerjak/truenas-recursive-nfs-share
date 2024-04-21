from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

parser = ArgumentParser(
    description="truenas-recursive-nfs-share: Pseudo-recursive NFS share creation for TrueNAS. Copy config-example.yaml to config.yaml and make appropriate changes. This tool expects the list of present datasets via STDIN. Sample invocation: zfs list -o name > python3 truenas-recursive-nfs-share.py",
    formatter_class=ArgumentDefaultsHelpFormatter,
)

task_group = parser.add_argument_group("io", description="Arguments to specify I/O")
task_group.add_argument("--config", "-c", type=str, metavar="file", default="./config.yaml", help="path to the config file to read")

datasets_source_group = parser.add_argument_group("datasets-source", description="Arguments to specify the source from which dataset information is gathered. The default source is a (slow) API query")
datasets_source_group.add_argument("--stdin", "-s", action="store_true", default=False, help="flag to specify that the dataset source is the output of zfs list -o name piped or manually entered into the STDIN handle. If neither this nor --datasets-file is provided, the API endpoint is used as a default")
datasets_source_group.add_argument("--datasets-file", "-d", type=str, metavar="file", default=None, help="path to the file containing output of 'zfs list -o name'. If neither a file nor --stdin is provided, the API endpoint is used as a default")

def obtain_args():
    return parser.parse_args()