## Article Scraper [Crawler]
Install the by executing the following command:
```commandline
pip install -r requirements.txt
```
Run the script using:
```commandline
python sel_scraper.py
```
# Features:
## 1. Can directly start rank scraping from Google using existing records of GFG articles from news portal.
   1. For this `scraped_{category}_Output.csv` file must be present inside `data` folder.
   2. This `scraped_{category}_Output.csv` file contains all records scraped from news.geeksforgeeks.org portal.
## 2. Can load and save last scraping information.
   1. Inside `data` folder, it saves `rank_{category}-config.json` file.
   2. `rank_{category}-config.json` contains the information for the row to start scraping with.
   3. `rank_{category}-config.json` file requires `rank_{category}.csv` file also to be present inside `data` folder.

`data/rank_{category}-config.json`
```json
{
    "last_scraped_row": 30
}
```

## 3. Supports stopping in midst of scraping.

-  User can stop the script, at any time by raising `KeyboardInterruptError` (Ctrl+C) from terminal.
- In this case the last scraped row index will be saved inside `rank_{category}-config.json`