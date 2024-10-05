# webScraperCitizensInformation

#### Running Tests

```
python -m unittest discover -s tests
```

##### Scraping

Sitemap is at https://www.citizensinformation.ie/sitemap.xml

##### TODO

- Handle request failures (slowing down scrape - have timeout of 3 seconds but it adds up over hundreds of pages - about 150 links per page)
- Handle preprocessing of link - ../ is being resolved to https://www.citizensinformation.ie/../ which is wrong
- Irish language files are being scraped - will probably exclude for first implementation

#### Commands

##### Processing flag converts stored html files to markdow

`python3  main.py --process`

#### Scrape flag checks existing html files, extracts links within and scrapes for those that are not present in the directory

`python3  main.py --scrape`
