
## Installation:

* headless on ubuntu: https://christopher.su/2015/selenium-chromedriver-ubuntu/
* sudo pip install lxml
* sudo pip install beautifulsoup4
* sudo pip install requests
* sudo pip install argparse

## Run examples:

__retain only links which text starts with The__
* --browser Chrome-Headless :Chrome headless
* --follow 1 :click upon the each scraped link and scrape again pages
```
python run_scraper.py --retain-regex ^The --site-url cnn.com --browser Chrome-Headless --follow 1
```

__exclude all links which text starts with The__
* --browser Chrome-Headless :Chrome headless
* --follow 0 :scrape only links from cnn.com and don't follow links
```
python run_scraper.py --exclude-regex ^The --site-url cnn.com --browser Chrome-Headless --follow 0
```
