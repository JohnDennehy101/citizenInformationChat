import unittest

from services.htmlParser import HTMLParser

class TestHTMLParser(unittest.TestCase):
    def test_extract_valid_links_no_links(self):
        """
        Test the extract valid links method returns empty list if no links found
        """

        html_contents = "<html></html>"

        html_parser = HTMLParser(html_contents)

        result = html_parser.extract_valid_links()

        self.assertEqual(result, [])

    def test_extract_valid_links_links(self):
        """
        Test the extract valid links method returns link tags in html
        """

        html_contents = "<html><a href='health'>Health</a></html>"

        html_parser = HTMLParser(html_contents)

        result = html_parser.extract_valid_links()

        self.assertEqual(result, ["health"])
    
    def test_valid_link_returns_true(self):
        """
        Test the valid link method - valid url returns True
        """

        html_contents = "<html><a href='health'>Health</a></html>"

        html_parser = HTMLParser(html_contents)

        link = "/health"

        result = html_parser.valid_link(link)

        self.assertEqual(result, True)
    
    def test_invalid_link_hash_returns_false_(self):
        """
        Test the valid link method - invalid url starting with (hash) returns False
        """

        html_contents = "<html><a href='health'>Health</a></html>"

        html_parser = HTMLParser(html_contents)

        link = "#health"

        result = html_parser.valid_link(link)

        self.assertEqual(result, False)
    
    def test_invalid_link_county_returns_false_(self):
        """
        Test the valid link method - invalid url starting with (county) returns False
        """

        html_contents = "<html><a href='health'>Health</a></html>"

        html_parser = HTMLParser(html_contents)

        link = "county"

        result = html_parser.valid_link(link)

        self.assertEqual(result, False)
    
    def test_invalid_link_centre_returns_false_(self):
        """
        Test the valid link method - invalid url starting with (centre) returns False
        """

        html_contents = "<html><a href='health'>Health</a></html>"

        html_parser = HTMLParser(html_contents)

        link = "centre"

        result = html_parser.valid_link(link)

        self.assertEqual(result, False)
    
    def test_invalid_link_javascript_returns_false_(self):
        """
        Test the valid link method - invalid url starting with (javascript) returns False
        """

        html_contents = "<html><a href='health'>Health</a></html>"

        html_parser = HTMLParser(html_contents)

        link = "javascript:void()"

        result = html_parser.valid_link(link)

        self.assertEqual(result, False)
    
    def test_invalid_link_whatsapp_returns_false_(self):
        """
        Test the valid link method - invalid url starting with (whatsapp) returns False
        """

        html_contents = "<html><a href='health'>Health</a></html>"

        html_parser = HTMLParser(html_contents)

        link = "whatsapp"

        result = html_parser.valid_link(link)

        self.assertEqual(result, False)
    
    def test_invalid_link_telephone_returns_false_(self):
        """
        Test the valid link method - invalid url starting with (tel:) returns False
        """

        html_contents = "<html><a href='health'>Health</a></html>"

        html_parser = HTMLParser(html_contents)

        link = "tel:"

        result = html_parser.valid_link(link)

        self.assertEqual(result, False)
    
    def test_invalid_link_facebook_returns_false_(self):
        """
        Test the valid link method - invalid url with facebook returns False
        """

        html_contents = "<html><a href='health'>Health</a></html>"

        html_parser = HTMLParser(html_contents)

        link = "https://citizeninformation.ie?facebook"

        result = html_parser.valid_link(link)

        self.assertEqual(result, False)
    
    def test_invalid_link_twitter_returns_false_(self):
        """
        Test the valid link method - invalid url with twitter returns False
        """

        html_contents = "<html><a href='health'>Health</a></html>"

        html_parser = HTMLParser(html_contents)

        link = "https://citizeninformation.ie?twitter"

        result = html_parser.valid_link(link)

        self.assertEqual(result, False)
    
    def test_valid_link_external_url_returns_false_(self):
        """
        Test the valid link method - return False if not on citizens info - don't want external pages
        """

        html_contents = "<html><a href='health'>Health</a></html>"

        html_parser = HTMLParser(html_contents)

        link = "https://google.ie"

        result = html_parser.valid_link(link)

        self.assertEqual(result, False)



if __name__ == '__main__':
    unittest.main()