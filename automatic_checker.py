import asyncio
import json
from utilities.pace_scraper import COLOUR
from kickassanime_scraper import CONFIGS, automate_scraping, update_config
import re
import traceback
from os.path import isdir, join as join_path
from os import makedirs
from pathlib import Path 

with open("./Config/to_update.json") as f:
    data = json.loads(f.read())
    needed = data['anime']
    download_location: str = data['download_location']

    if not isdir(download_location):
        print(COLOUR.warn('Download directory not currectly set in `Config/to_update.json`!'))
        data['download_location'] = download_location = join_path(Path.home(), 'Videos', 'Anime')
        print(COLOUR.info(f'Changing the directory to {download_location}'))
        makedirs(download_location, exist_ok=True)
        update_config(CONFIGS.to_update, data)

    pause = data['pause_on_complete']

async def main():
    tasks = []
    for link, start in needed.items():
        tasks.append(
            automate_scraping(
                link,
                start_episode=start,
                end_episode=None,
                automatic_downloads=True,
                download_location=download_location,
                check_version=False,
            )
        )
    try:
        new_starts = await asyncio.gather(*tasks)
    except Exception:
        new_starts = [(None, None)]
        print(traceback.format_exc())
    index = -1
    for j, i in new_starts:
        index += 1
        if i != None:
            new = int(re.search(r"ep_(\d+)", i).group(1)) + 1
            needed[list(needed.keys())[index]] = new
        else:
            print()
            print(COLOUR.grey(f"Latest for {j}"))
            continue

    data['anime']=needed
    update_config(CONFIGS.to_update, data)

if __name__ == "__main__":
    asyncio.run(main())
    if pause:
        _ = input('\nPress ENTER to exit...')
    else:
        pass