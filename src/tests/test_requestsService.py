import unittest
from unittest import mock

from services.requestsService import RequestsService
from constants import SCRAPE_URL

def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, text_data, status_code):
            self.text_data = text_data
            self.status_code = status_code

        @property
        def text(self):
            return self.text_data

    if args[0] == 'https://www.citizensinformation.ie/health':
        return MockResponse("<html><body>Health Information</body></html>", 200)

    return MockResponse(None, 404)

class TestRequestsService(unittest.TestCase):
    def test_construct_url_https(self):
        """
        Test the construct url method returns same url for https
        """

        requests_service = RequestsService(SCRAPE_URL)

        url = "https://www.citizensinformation.ie/en/"

        result = requests_service.construct_url(url)

        self.assertEqual(result, url)

    def test_construct_url_http(self):
        """
        Test the construct url method returns same url for http
        """

        requests_service = RequestsService(SCRAPE_URL)

        url = "http://www.citizensinformation.ie/en/"

        result = requests_service.construct_url(url)

        self.assertEqual(result, url)

    def test_construct_url_centre(self):
        """
        Test the construct url method returns same url if url starts with centres
        """

        requests_service = RequestsService(SCRAPE_URL)

        url = "centres.citizensinformation.ie/en/"

        result = requests_service.construct_url(url)

        self.assertEqual(result, url)

    def test_construct_url_partial(self):
        """
        Test the construct url method adds prefix if internal url like /health
        """

        requests_service = RequestsService(SCRAPE_URL)

        url = "/health"

        result = requests_service.construct_url(url)

        self.assertEqual(result, "https://www.citizensinformation.ie/health")

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_make_request_valid_url(self, mock_get):
        """
        Test that request successfully returns response
        """

        requests_service = RequestsService(SCRAPE_URL)

        url = "/health"

        result = requests_service.make_request(url)

        self.assertEqual(result.text, "<html><body>Health Information</body></html>")



if __name__ == '__main__':
    unittest.main()