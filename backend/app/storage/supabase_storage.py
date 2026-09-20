import httpx

from app.config import Settings


class SupabaseStorage:
    """Thin httpx wrapper around Supabase Storage's REST API -- avoids pulling
    in the full supabase-py client (and its own auth/session handling) for
    what is otherwise a handful of simple upload/sign/delete calls."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.SUPABASE_URL.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        }

    async def upload_file(self, *, bucket: str, path: str, content: bytes, content_type: str) -> str:
        url = f"{self._base_url}/storage/v1/object/{bucket}/{path}"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                content=content,
                headers={**self._headers, "Content-Type": content_type, "x-upsert": "true"},
            )
            response.raise_for_status()
        return path

    async def get_signed_url(self, *, bucket: str, path: str, expires_in_seconds: int = 3600) -> str:
        url = f"{self._base_url}/storage/v1/object/sign/{bucket}/{path}"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json={"expiresIn": expires_in_seconds}, headers=self._headers
            )
            response.raise_for_status()
            signed_path = response.json()["signedURL"]
        return f"{self._base_url}/storage/v1{signed_path}"

    async def download(self, *, bucket: str, path: str) -> bytes:
        url = f"{self._base_url}/storage/v1/object/{bucket}/{path}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers)
            response.raise_for_status()
        return response.content

    async def delete(self, *, bucket: str, path: str) -> None:
        url = f"{self._base_url}/storage/v1/object/{bucket}/{path}"
        async with httpx.AsyncClient() as client:
            response = await client.request("DELETE", url, headers=self._headers)
            response.raise_for_status()
