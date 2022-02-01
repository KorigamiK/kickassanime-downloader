import enum
from aiohttp.client import ClientSession

async def Mavereckki(server_name: str, server_link: str, client: ClientSession):
    async with client.get(server_link.replace('/embed/', '/api/source/')) as resp:
        data: dict = await resp.json() 
    subtitle_url = []
    if data.get('subtitles') and len(data.get('subtitles')):
        for idx, sub in enumerate(data.get('subtitles')):
            if 'eng' in sub.get('name').lower():
                subtitle_url.append(server_link.split('/embed/')[0] + sub.get('src'))
                del data.get('subtitles')[idx]
        subtitle_url += [server_link.split('/embed/')[0] + i.get('src') for i in data.get('subtitles')]
    return [server_name, server_link.split('/embed/')[0] + data.get('hls'), {'Referer': server_link, 'Subtitle': subtitle_url}]