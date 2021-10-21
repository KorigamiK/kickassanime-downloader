import asyncio
import json
from utilities.pace_scraper import COLOUR
from kickassanime_scraper import automate_scraping
import re
import traceback

with open("./Config/to_update.json") as f:
    data = json.loads(f.read())
    needed = data['anime']
    download_location = data['download_location']
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

    with open("./Config/to_update.json", "w") as f:
        data['anime']=needed
        json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(main())
    if pause:
        _ = input('\nPress ENTER to exit...')
    else:
        pass