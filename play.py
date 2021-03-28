from utilities.watcher import watch, names as server_names
import asyncio
import argparse

parser = argparse.ArgumentParser(description="play anime directly")

parser.add_argument(
    "--list",
    "-L",
    action="store_true",
    help="Optional switch to list available player servers (not ext) with their index",
)

# Optional positional argument
parser.add_argument("name", type=str, nargs="*", help="Name of the anime to search")

# Optional argument
parser.add_argument("--ep", "-e", type=int, help="Episode number. Default is the latest episode.")

parser.add_argument("--url", "-u", type=str, help="Optional kickass anime url")

parser.add_argument(
    "--opt",
    "-o",
    type=int,
    help="Optional way to select search result number.",
)

parser.add_argument(
    "--ext",
    action="store_true",
    help="Optional switch to play only from ext servers (its faster if it works). Needs no arguments",
)

def parse_server_name(arg):
    if arg:
        try:
            index = int(arg)
            if index < len(server_names):
                return server_names[index]
            else:
                print('Priority Index out of range')
                return ''
        except:
            return arg.upper()
    else:
        return ''

parser.add_argument(
    "--custom_server",
    "-c",
    help="Name of the player/server you want or the INDEX number in the watch_config priority dictionary. Overrides the current priority.",
    type = parse_server_name,
    nargs='?',
    # default=''
)

args = parser.parse_args()
episode = args.ep
link = args.url
query = " ".join(args.name) if args.name else None
opt = args.opt
ext_only = args.ext
custom_server = args.custom_server
to_list = args.list

if to_list:
    print('Possible player servers are:')
    for j, i in enumerate(server_names):
        print(j, i)
    exit()

asyncio.get_event_loop().run_until_complete(
    watch(episode, link=link, query=query, option_number=opt, ext_only=ext_only, custom_server=custom_server)
)
