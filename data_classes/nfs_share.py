from dataclasses import dataclass
from json import loads
from requests import Response

from helpers.constants import AUTOCREATE_COMMENT_SUFFIX

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

	@classmethod
	def list_from_api_response(cls, api_response: Response):
		dataset_json_array = api_response.json()
		return [cls.from_json_dict(dataset_json_dict) for dataset_json_dict in dataset_json_array]

	@classmethod
	def from_json_dict(cls, json_dict: dict):
		return cls(**json_dict)
	
	@property
	def path_name(self):
		mount_prefix = "/mnt/"
		return self.path[len(mount_prefix):] if self.path.startswith(mount_prefix) else self.path
	
	def is_automatically_created(self):
		return self.comment.endswith(AUTOCREATE_COMMENT_SUFFIX)
	
	def is_relevant(self, relevant_datasets_list: list[str]):
		return self.path_name in relevant_datasets_list
	
	def set_comment_for_automatically_created_flag(self, comment: str):
		self.comment = f"{comment} {AUTOCREATE_COMMENT_SUFFIX}"