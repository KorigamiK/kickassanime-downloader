from aiohttp.client import ClientSession
from bs4 import BeautifulSoup


async def Mavereckki(server_name: str, server_link: str, client: ClientSession):
    async with client.get(server_link.replace('/embed/', '/api/source/')) as resp:
        data: dict = await resp.json() 
    return [server_name, server_link.split('/embed/')[0] + data.get('hls'), {'Referer': server_link}]