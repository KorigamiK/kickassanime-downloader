import asyncio
from bs4 import BeautifulSoup as bs
from ssl import SSLCertVerificationError
import os
from contextlib import redirect_stderr


async def fetch(url, client) -> bs:
    try:
        f = open(os.devnull, "w")
        with redirect_stderr(f):  # ignore any error output inside context
            async with client.get(url) as resp:
                # print(resp.status)
                html = await resp.read()
                return bs(html, "html.parser")

    except SSLCertVerificationError as e:
        print("Error handled", e)


if __name__ == "__main__":
    from aiohttp import ClientSession

    async def main():
        url = "https://kickassanime.rs/anime/appare-ranman-446954/episode-01-814553"
        async with ClientSession() as session:
            html_body = await fetch(url, session)
        return html_body.select_one("strong")

    print(asyncio.run(main()))
