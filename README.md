# webScraperCitizensInformation

#### Running Tests

```
python -m unittest discover -s tests
```

##### TODO

- Handle request failures (slowing down scrape - have timeout of 3 seconds but it adds up over hundreds of pages - about 150 links per page)
- Handle preprocessing of link - ../ is being resolved to https://www.citizensinformation.ie/../ which is wrong
- After html files are parsed, further process these files using html2text package
- Irish language files are being scraped - will probably exclude for first implementation
