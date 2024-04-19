from requests import Response, delete, get, post

import helpers.global_fields as g

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

	def perform_request(self, request_method: callable, endpoint: str, data: dict | None = None) -> Response:
		data_kwarg = { "data": data } if data else {}
		return request_method(
			self.get_uri(endpoint),
			headers=self.request_headers,
			**data_kwarg,
		)

	def get_nfs_shares_query_response(self):
		return self.perform_request(get, "/sharing/nfs")