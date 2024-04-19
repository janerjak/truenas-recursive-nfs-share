from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from os.path import basename

from helpers.spinner import spinner

parser = ArgumentParser(
    description="truenas-recursive-nfs-share: Pseudo-recursive NFS share creation for TrueNAS. Copy config-example.yaml to config.yaml and make appropriate changes. This tool expects the list of present datasets via STDIN. Sample invocation: zfs list -o name > python3 truenas-recursive-nfs-share.py",
    formatter_class=ArgumentDefaultsHelpFormatter,
)

task_group = parser.add_argument_group("io", description="Arguments to specify I/O")
task_group.add_argument("--config", "-c", type=str, metavar="file", default="./config.yaml", help="path to the config file to read")
task_group.add_argument("--datasets-file", "-d", type=str, metavar="file", default=None, help="path to the file containing output of 'zfs list -o name'. If None is provided, it is instead read from STDIN")

misc_group = parser.add_argument_group("misc", "Miscellaneous arguments")

def obtain_args():
    return parser.parse_args()