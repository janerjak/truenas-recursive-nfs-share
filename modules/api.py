from requests import Response, delete, get, post, put

import helpers.global_fields as g

from data_classes.nfs_share import NFSShare
from helpers.spinner import spinner

class APIManager:
	def __init__(self):
		self.update_config_values()
		
	def update_config_values(self) -> None:
		api_config = g.config.truenas.api
		self.api_key = api_config.key
		self.request_headers = {
			"Content-Type": "application/json",
			"Authorization": f"Bearer {self.api_key}",
		}
		self.uri_prefix = f"{api_config.host}{api_config.path}"

	def get_uri(self, endpoint: str) -> str:
		return f"{self.uri_prefix}{endpoint}"

	def perform_request(self, request_method: callable, endpoint: str, json_body: dict | None = None) -> Response:
		data_kwarg = { "json": json_body } if json_body else {}
		return request_method(
			self.get_uri(endpoint),
			headers=self.request_headers,
			**data_kwarg,
		)
	
	def perform_nfs_request(self, request_method: callable, endpoint: str = "", body: dict | None = None) -> Response:
		return self.perform_request(request_method, f"/sharing/nfs/{endpoint}", body)

	@spinner("Checking if API is accessible")
	def check_api_availability(self) -> bool:
		try:
			api_key_response = self.perform_request(get, "/api_key")
			return len(api_key_response.json()) > 0
		except:
			return False

	@spinner("Retrieving currently active NFS shares")
	def get_shares_query_response(self):
		return self.perform_nfs_request(get)
	
	def create_share(self, share: NFSShare) -> bool:
		return self.perform_nfs_request(post, body=share.as_create_dict())

	def delete_share(self, share: NFSShare) -> bool:
		return self.perform_nfs_request(delete, f"id/{share.id}")

	def update_share(self, share: NFSShare) -> bool:
		return self.perform_nfs_request(put, f"id/{share.id}", share.as_create_dict())