from typing import Any

import httpx


class BeszelClient:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._client = httpx.Client(timeout=30.0)

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = self.token
        return headers

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self._client.get(f"{self.base_url}{path}", headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def _post(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self._client.post(f"{self.base_url}{path}", json=data or {}, headers=self._headers())
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def _patch(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        response = self._client.patch(f"{self.base_url}{path}", json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def _delete(self, path: str) -> None:
        response = self._client.delete(f"{self.base_url}{path}", headers=self._headers())
        response.raise_for_status()

    # Authentication
    def login(self, email: str, password: str) -> str:
        response = self._client.post(
            f"{self.base_url}/api/collections/users/auth-with-password",
            json={"identity": email, "password": password},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        self.token = response.json()["token"]
        return self.token  # type: ignore[return-value]

    def auth_refresh(self) -> dict[str, Any]:
        return self._post("/api/collections/users/auth-refresh")

    def get_current_user(self) -> dict[str, Any]:
        result = self.auth_refresh()
        return result.get("record", {})  # type: ignore[no-any-return]

    # Generic collection helpers
    def list_records(
        self,
        collection: str,
        page: int = 1,
        per_page: int = 200,
        sort: str = "",
        filter_expr: str = "",
        expand: str = "",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        if sort:
            params["sort"] = sort
        if filter_expr:
            params["filter"] = filter_expr
        if expand:
            params["expand"] = expand
        return self._get(f"/api/collections/{collection}/records", params)

    def get_record(self, collection: str, record_id: str, expand: str = "") -> dict[str, Any]:
        params: dict[str, Any] = {}
        if expand:
            params["expand"] = expand
        return self._get(f"/api/collections/{collection}/records/{record_id}", params)

    def create_record(self, collection: str, data: dict[str, Any]) -> dict[str, Any]:
        return self._post(f"/api/collections/{collection}/records", data)

    def update_record(self, collection: str, record_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return self._patch(f"/api/collections/{collection}/records/{record_id}", data)

    def delete_record(self, collection: str, record_id: str) -> None:
        self._delete(f"/api/collections/{collection}/records/{record_id}")

    # Systems
    def get_systems(self, filter_expr: str = "") -> list[dict[str, Any]]:
        result = self.list_records("systems", per_page=200, filter_expr=filter_expr)
        return result.get("items", [])  # type: ignore[no-any-return]

    def get_system(self, system_id: str) -> dict[str, Any]:
        return self.get_record("systems", system_id)

    def update_system(self, system_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return self.update_record("systems", system_id, data)

    def delete_system(self, system_id: str) -> None:
        self.delete_record("systems", system_id)

    # System Stats
    def get_system_stats(
        self,
        system_id: str,
        record_type: str = "1m",
        per_page: int = 30,
    ) -> list[dict[str, Any]]:
        result = self.list_records(
            "system_stats",
            per_page=per_page,
            sort="-created",
            filter_expr=f'system="{system_id}" && type="{record_type}"',
        )
        return result.get("items", [])  # type: ignore[no-any-return]

    # Container Stats
    def get_container_stats(
        self,
        system_id: str,
        per_page: int = 30,
    ) -> list[dict[str, Any]]:
        result = self.list_records(
            "container_stats",
            per_page=per_page,
            sort="-created",
            filter_expr=f'system="{system_id}"',
        )
        return result.get("items", [])  # type: ignore[no-any-return]

    # Alerts
    def get_alerts(self, system_id: str = "") -> list[dict[str, Any]]:
        filter_expr = f'system="{system_id}"' if system_id else ""
        result = self.list_records("alerts", per_page=200, filter_expr=filter_expr, expand="system")
        return result.get("items", [])  # type: ignore[no-any-return]

    def get_alert(self, alert_id: str) -> dict[str, Any]:
        return self.get_record("alerts", alert_id, expand="system")

    def create_alert(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.create_record("alerts", data)

    def update_alert(self, alert_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return self.update_record("alerts", alert_id, data)

    def delete_alert(self, alert_id: str) -> None:
        self.delete_record("alerts", alert_id)

    # Alert History
    def get_alert_history(self, per_page: int = 50) -> list[dict[str, Any]]:
        result = self.list_records("alerts_history", per_page=per_page, sort="-created")
        return result.get("items", [])  # type: ignore[no-any-return]

    # Containers
    def get_containers(self, system_id: str = "") -> list[dict[str, Any]]:
        filter_expr = f'system="{system_id}"' if system_id else ""
        result = self.list_records("containers", per_page=200, filter_expr=filter_expr)
        return result.get("items", [])  # type: ignore[no-any-return]

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BeszelClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
