# Kickassanime Downloader
A nice and fast asynchronous anime downloader, streamer and more for kickassanime. 

[Here's a demo](#some-usage-examples) of this tool.

## Index: 
- [INSTALLATION](#installation)
- [UPDATE](#update)
- [COMMAND ALIAS](#to-set-up-the-command-alias)
- [CONFIGURATION](#config)
- [USAGE](#usage)
- [FAQ](#faq)
- [USAGE EXAMPLES](#some-usage-examples)


## Update :
1. If you used `git` to clone the repository then running `git pull` will do the trick.

2. If you downloaded the repository as a zip file then you need to download the repository again and replace all the files except the `Config` folder

3. You would need to check if there are any changes to the `.eg.json` files in the `Config` folder (there may be some breaking changes) and change your `.json` files in the `Config` folder accordingly.


## Installation :

The setup is a little tedious at the moment, but I might make a nice installable package using pip. But right now these are the installation steps:

1. Install [python 3](https://www.python.org/) with python and pip on path.

2. Clone this repository using `git clone https://github.com/KorigamiK/kickassanime-downloader` or download and extract this repository to a directory. For example: `~/Documents/kickassanime-downloader`.

3. Open terminal/command prompt and navigate to the directory using: `cd /home/origami/Documents/kickassanime-downloader`.

4. Run `pip install -r requirements.txt`

5. `[Optional]` if you are on Linux also run `pip install SelectMenu` to get the nice looking command line menu.

6. Navigate to your download directory and navigate to the `Config` folder (`~/Documents/kickassanime-downloader/Config` for example). 

7. Rename all the `.eg.json` and remove the `.eg` from the file name. Open each one of them and adjust the configurations as you want. Refer to [Config section.](#config)


8. Set up the command line aliases [from the wiki](#to-set-up-the-command-alias) or run the command line interface directly by running `python cli.py`.

9. You may need to download tools like [MPV](https://mpv.io/) or [VLC](https://www.videolan.org/) and add them to your path to stream the shows. [This website](https://www.vlchelp.com/add-vlc-command-prompt-windows/) shows how to add VLC to path on Windows.

10. Now profit.

## To set up the command alias:
1. [For windows](https://github.com/KorigamiK/kickassanime-downloader/wiki/Command-alias-Windows)

2. [For Linux/Mac](https://github.com/KorigamiK/kickassanime-downloader/wiki/Command-alias-Linux-Mac)


## Config :

1.  The quality of downloads from servers can be adjusted in the `config.json` or from example `~/Documents/kickassanime-downloader/Config/config.json`

2. The numbers for each of the servers refer to the qualities in the order in which they appear on the website.

3. For example, for KICKASSANIMEX the numbers would refer to the qualities like this:

    ![qualities](/example/quality_selection.jpg)

## Usage :

1. Run the alias with no commands/arguments or just `python cli.py` to get the menu of all the actions you have.

```
$ kaa
What would you like? (Use arrow keys)
 > Play Episode            
   Search And Download     
   Autoupdate Library      
   Fetch Latest            
   Check For Updates       
   See Config
```

2. `kaa update` or `python cli.py update` -> auto updates library

3. `kaa download` or `python cli.py download` -> starts menu to download a series

4. `kaa latest` or `python cli.py latest` -> Shows the latest updates on the website

5. Run the alias with commands to stream any anime that you want. `kaa --help` or `python cli.py --help` for list of all the commands.

6. Here's the output of the above command: 

```
$ kaa -h 

usage: play.py [-h] [--list] [--ep EP] [--url URL] [--opt OPT] [--ext]
               [--stop] [--encode] [--custom_server [CUSTOM_SERVER]]
               [name [name ...]]

play anime directly

positional arguments:
  name                  Name of the anime to search

optional arguments:
  -h, --help            show this help message and exit
  --list, -L            Optional switch to list available player servers (not
                        ext) with their index
  --ep EP, -e EP        Episode number. Default is the latest episode.
  --url URL, -u URL     Optional kickass anime url
  --opt OPT, -o OPT     Optional way to select search result number.
  --ext                 Optional switch to play only from ext servers (its
                        faster if it works). Needs no arguments
  --stop, -s            Optional switch to stop the script after searching
                        without playing anything. Will also display the url of
                        the anime.
  --encode              Optional switch to print ffmpeg command to encode the
                        stream
  --custom_server [CUSTOM_SERVER], -c [CUSTOM_SERVER]
                        Name of the player/server you want or the INDEX number
                        in the watch_config priority dictionary. Overrides the
                        current priority.
```

## FAQ :

If you have any questions about errors or installation you can check the [issues page](https://github.com/KorigamiK/kickassanime-downloader/issues) and read the [already closed issues](https://github.com/KorigamiK/kickassanime-downloader/issues?q=is%3Aissue+is%3Aclosed). I have answered most of the problems that you might be facing.

```
You are welcome to make an issue for any bug or error or feature that you might need.
```

#### ```If you encounter any problems due to repeated requests and cloudflare protection, wait for some time and then run the script again.```


## Some usage examples:

1. Auto update your ongoing series for new episodes
![autoupdate](/example/autoupdate.gif)

2. Play any episode of any show
![play episode](/example/play_ep.gif)

3. Download a range of episodes of any show
![search and download](/example/search_and_download.gif)

Make sure to correctly create the config files or remove the `.eg` from the file names in the `config` folder.
