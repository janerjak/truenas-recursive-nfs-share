from dataclasses import dataclass

@dataclass
class NFSShare:
	id: int
	path: str
	aliases: list[str]
	comment: str
	hosts: list[str]
	ro: bool
	maproot_user: str
	maproot_group: str
	mapall_user: str
	mapall_group: str
	security: list
	enabled: bool
	networks: list[str]
	locked: bool