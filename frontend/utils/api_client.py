import os
from typing import Any, Dict, List, Optional

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")


class APIClient:
    def __init__(self, access_token: Optional[str] = None) -> None:
        self.access_token = access_token

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def login(self, email: str, password: str) -> Optional[str]:
        data = {"username": email, "password": password}
        resp = requests.post(f"{API_URL}/auth/login", data=data)
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            self.access_token = token
            return token
        return None

    def register(self, email: str, password: str, org_name: str | None = None) -> bool:
        payload: Dict[str, Any] = {"email": email, "password": password, "org_name": org_name}
        resp = requests.post(f"{API_URL}/auth/register", json=payload)
        return resp.status_code == 200

    def me(self) -> Dict[str, Any] | None:
        resp = requests.get(f"{API_URL}/users/me", headers=self._headers())
        if resp.status_code == 200:
            return resp.json()
        return None

    def agent_chat(
        self,
        message: str,
        mode: str = "recruiter_assistant",
        conversation_id: int | None = None,
    ) -> str:
        payload: Dict[str, Any] = {
            "message": message,
            "mode": mode,
            "conversation_id": conversation_id,
        }
        resp = requests.post(f"{API_URL}/agent/chat", json=payload, headers=self._headers())
        if resp.status_code == 200:
            return resp.json()["reply"]
        return f"[error {resp.status_code}] {resp.text}"

    def router_chat(
        self,
        message: str,
        messages: List[Dict[str, Any]] | None = None,
        user_type: str | None = None,
        qna_tree_id: str | None = None,
        qna_mode: bool = False,
        current_question_id: str | None = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"message": message}
        if messages:
            payload["messages"] = messages
        if user_type:
            payload["user_type"] = user_type
        if qna_tree_id:
            payload["qna_tree_id"] = qna_tree_id
        payload["qna_mode"] = qna_mode
        payload["current_question_id"] = current_question_id

        resp = requests.post(f"{API_URL}/chat/router", json=payload, headers=self._headers())
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"[error {resp.status_code}] {resp.text}"}

    def get_jobs(self, status_filter: Optional[str] = None, q: Optional[str] = None) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if status_filter:
            params["status_filter"] = status_filter
        if q:
            params["q"] = q

        resp = requests.get(f"{API_URL}/jobs", headers=self._headers(), params=params)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("items", [])
        return []

    def match_candidates_for_job(self, job_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"job_id": job_id, "limit": limit}
        resp = requests.post(
            f"{API_URL}/matching/candidates_for_job",
            json=payload,
            headers=self._headers(),
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("matches", [])
        return []

    def match_jobs_for_candidate(self, candidate_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"candidate_id": candidate_id, "limit": limit}
        resp = requests.post(
            f"{API_URL}/matching/jobs_for_candidate",
            json=payload,
            headers=self._headers(),
        )
        if resp.status_code == 200:
            return resp.json().get("matches", [])
        return []

    def create_candidate_from_resume(self, file, notes: str | None = None) -> Dict[str, Any] | None:
        headers: Dict[str, str] = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        files = {
            "resume": (file.name, file.getvalue(), "application/octet-stream"),
        }
        data: Dict[str, Any] = {}
        if notes:
            data["notes"] = notes

        resp = requests.post(
            f"{API_URL}/agent/candidates/from_resume",
            headers=headers,
            files=files,
            data=data,
        )
        if resp.status_code == 200:
            return resp.json()
        return None

    def create_job_from_req(self, file, notes: str | None = None) -> Dict[str, Any] | None:
        headers: Dict[str, str] = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        files = {
            "job_req": (file.name, file.getvalue(), "application/octet-stream"),
        }
        data: Dict[str, Any] = {}
        if notes:
            data["notes"] = notes

        resp = requests.post(
            f"{API_URL}/agent/jobs/from_req",
            headers=headers,
            files=files,
            data=data,
        )
        if resp.status_code == 200:
            return resp.json()
        return None
