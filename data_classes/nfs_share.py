from dataclasses import asdict, dataclass, field
from json import loads
from typing import Self
from requests import Response

import helpers.global_fields as g

from helpers.constants import AUTOCREATE_COMMENT_SUFFIX, MOUNT_PREFIX

@dataclass
class NFSShare:
	path: str
	id: int = None
	aliases: list[str] = field(default_factory=list)
	comment: str = None
	hosts: list[str] = field(default_factory=list)
	ro: bool = False
	maproot_user: str | None = None
	maproot_group: str | None = None
	mapall_user: str | None = None
	mapall_group: str | None = None
	security: list = field(default_factory=list)
	enabled: bool = True
	networks: list[str] = field(default_factory=list)
	locked: bool | None = None

	@classmethod
	def list_from_api_response(cls: Self, api_response: Response) -> list[Self]:
		dataset_json_array = api_response.json()
		return [cls.from_json_dict(dataset_json_dict) for dataset_json_dict in dataset_json_array]

	@classmethod
	def from_json_dict(cls: Self, json_dict: dict) -> Self:
		return cls(**json_dict)
	
	@classmethod
	def from_config_options(cls: Self, path_without_prefix: str) -> Self:
		path = f"{MOUNT_PREFIX}{path_without_prefix}"
		custom_options_dict = g.config.share_options.custom.get(path_without_prefix)

		options_dict = {}
		if custom_options_dict is None:
			options_dict = g.config.share_options.default
		else:
			options_dict = dict(custom_options_dict)
			for default_option_key, default_option_value in g.config.share_options.default.items():
				if default_option_key not in options_dict.keys():
					options_dict[default_option_key] = default_option_value

		new_share = cls(path=path, **options_dict)
		new_share.set_comment_for_automatically_created_flag(new_share.comment)
		return new_share
	
	@property
	def path_name(self):
		return self.path[len(MOUNT_PREFIX):] if self.path.startswith(MOUNT_PREFIX) else self.path
	
	def as_dict(self):
		return asdict(self)
	
	def as_create_dict(self):
		limited_dict = self.as_dict()
		keys_to_remove = [
			"id",
			"locked"
		]
		for key_to_remove in keys_to_remove:
			del limited_dict[key_to_remove]
		return limited_dict
	
	def is_automatically_created(self):
		return self.comment.endswith(AUTOCREATE_COMMENT_SUFFIX)
	
	def is_relevant(self, relevant_datasets_list: list[str]):
		return self.path_name in relevant_datasets_list
	
	def set_comment_for_automatically_created_flag(self, comment: str = None):
		self.comment = f"{comment} {AUTOCREATE_COMMENT_SUFFIX}" if comment else AUTOCREATE_COMMENT_SUFFIX