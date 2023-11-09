from io import BytesIO
from typing import Dict, Optional, Any

import aiohttp
from PIL import Image


class APIProvider:
    @staticmethod
    async def get(
        url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, headers=headers) as response:
                if response.status != 200:
                    raise IOError(
                        f"Request returned an error: {response.status} {await response.text()}"
                    )

                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await response.json()
                elif "image" in content_type:
                    return Image.open(BytesIO(await response.read()))
                else:
                    # Here you can add more elif clauses for different content types.
                    raise NotImplementedError(f"Unhandled content type: {content_type}")

    @staticmethod
    async def post(
        url: str, data: Optional[str] = None, headers: Optional[Dict] = None
    ) -> Dict:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, data=data, headers=headers) as response:
                if response.status != 200:
                    raise IOError(
                        f"Request returned an error: {response.status}, {await response.text()}"
                    )
                return await response.json()
