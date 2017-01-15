
## Installation:

* headless on ubuntu: https://christopher.su/2015/selenium-chromedriver-ubuntu/
* sudo pip install lxml
* sudo pip install beautifulsoup4
* sudo pip install requests
* sudo pip install argparse

## Run examples:

__retain only links which text starts with 'The'__
* --browser Chrome-Headless :Chrome headless
* --follow 1 :click upon each and every scraped link (with "the") from the cnn.com and once on the selected page, scrape again.
```
--retain-regex ^The --site-url cnn.com --browser Chrome-Headless --follow 1
```

__exclude all links which text starts with 'The'__
* --browser Chrome-Headless :Chrome headless
* --follow 0 :scrape only links from cnn.com and don't follow links
```
--exclude-regex ^The --site-url cnn.com --browser Chrome-Headless --follow 0
```

__retain all links which text contains either 'trump' or 'russia' and must have the text 'obama'__
* --unite : results are united which means that first we select only links that contains trump or russia
and then all matching links are searched for the word 'obama' and the end results is created
```
--browser Chrome-OSX --retain-links-any-key trump russia --site-url cnn.com --retain-links-keys obama --unite
```
* if it was not with --unite, we would have ALL links on the page searched trump and russia and saved and
again ALL links would be searched for the 'obama'
* if we pass in the arg --retain-links-keys with trump and russia. we'll select only links which text match both words
trump and russia

__exclude links which contain either: trump or russia and the link text has the word Trudeau. Also the text link must have the word
'Jared'__
* --browser Chrome-OSX :Chrome on Mac
```
--browser Chrome-OSX --exclude-links-keys trump russia --site-url cnn.com --exclude-links-any-key Trudeau --unite --retain-links-any-key Jared
```


