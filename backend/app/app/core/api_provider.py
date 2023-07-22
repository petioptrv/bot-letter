from typing import Dict, Optional

import aiohttp


class APIProvider:
    @staticmethod
    async def get(
        url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> Dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, headers=headers) as response:
                if response.status != 200:
                    raise IOError(
                        f"Request returned an error: {response.status}, {await response.text()}"
                    )
                return await response.json()
