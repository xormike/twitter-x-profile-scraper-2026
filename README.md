# tweet-url-scraper

Scrapes tweet URLs from any X/Twitter profile for a given date range — using Chrome DevTools Protocol (CDP) and xdotool for browser automation. No API key required.

## How it works

The script opens Chrome, navigates day-by-day through X's search (`from:user since:… until:…`), intercepts the internal `SearchTimeline` API responses via CDP, and extracts tweet IDs. Results are saved as URLs to a text file.

> **FYI:** xdotool simulates manual mouse scrolling — it is till now the best working option which I found to function properly. With that in mind, **it is not possible to do any other action while executing the script, while being on the same desktop session!**
>
> For profile scraping, scraping for daily posted tweets via the search query was the best working option for me. With direct scraping from the main profile you will run into limits to loaded tweets.
>
> **It is not guaranteed that this script can scrape all tweets reliably, because the Twitter search function is buggy as hell.**

## Requirements

- **Linux** with a running X11 desktop session
- **Google Chrome** or **Chromium**
- **xdotool**
- **Python 3.10+**
- Python package: `websockets`

### Install dependencies

```bash
# xdotool
sudo apt install xdotool

# Chrome (if not installed)
# Option A — Chromium
sudo apt install chromium-browser

# Option B — Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb

# Python package
pip install websockets
```

## Installation

```bash
git clone https://github.com/yourname/tweet-url-scraper.git
cd tweet-url-scraper
pip install websockets
```

## Usage

```bash
python tweet_url_scraper.py --user elonmusk --since 2024-03-01 --until 2024-01-01
```

> **Note:** `--since` is the **newer** date, `--until` is the **older** date.  
> The script scrapes from newest to oldest.

### All options

| Argument | Short | Default | Description |
|---|---|---|---|
| `--user` | `-u` | *(required)* | X/Twitter screen name without `@` |
| `--since` | `-s` | *(required)* | Start date `YYYY-MM-DD` (newer end) |
| `--until` | `-e` | *(required)* | End date `YYYY-MM-DD` (older end) |
| `--output` | `-o` | `tweet_urls.txt` | Output file path |
| `--port` | `-p` | `9222` | Chrome remote debugging port |
| `--no-launch` | | off | Don't auto-launch Chrome, use existing instance |
| `--replies` | | off | Include replies in results (default: replies excluded) |
| `--scroll-clicks` | | `8` | Mouse wheel clicks per scroll step |
| `--scroll-wait` | | `2.5` | Seconds to wait after each scroll |
| `--idle-rounds` | | `4` | Stop after N scrolls with no new tweets |

### Examples

```bash
# Scrape January 2024, save to custom file
python tweet_url_scraper.py -u naval -s 2024-01-31 -e 2024-01-01 -o naval_jan.txt

# Include replies
python tweet_url_scraper.py -u naval -s 2024-01-31 -e 2024-01-01 --replies

# Use already running Chrome instance on custom port
python tweet_url_scraper.py -u paulg -s 2024-06-01 -e 2024-05-01 --no-launch --port 9223

# Slower scrolling for slower connections
python tweet_url_scraper.py -u ID_AA_Carmack -s 2024-12-31 -e 2024-01-01 --scroll-wait 4 --idle-rounds 6
```

## Output format

One URL per line:

```
https://x.com/i/web/status/1748291234567890123
https://x.com/i/web/status/1748100987654321000
...
```

Already known URLs are never duplicated — re-running the script on the same output file safely resumes or extends.

## Notes

- You must be **logged in to X** in the Chrome session for search results to load properly.
- The script does **not** use the X/Twitter API and requires no API key.
- Tested on Ubuntu 22.04 / 24.04 with Chrome 124+ and Chromium.
- Only works on **Linux** (xdotool is Linux-only).

## License

MIT
