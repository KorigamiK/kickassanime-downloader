import asyncio
import json
from kickassanime_scraper import automate_scraping
import re
import traceback

with open("to_update.json") as f:
    needed = json.loads(f.read())


async def main():
    tasks = []
    for link, start in needed.items():
        tasks.append(
            automate_scraping(
                link,
                start_episode=start,
                end_episode=None,
                automatic_downloads=True,
                download_location="/home/origami/Videos/Anime/",
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
            print(f"\nlatest for {j}")
            continue

    with open("to_update.json", "w") as f:
        json.dump(needed, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
