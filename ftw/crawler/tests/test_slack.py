from ftw.crawler.testing import CrawlerTestCase
from ftw.crawler.slack import SlackLogger
from ftw.crawler.configuration import Site
import json


class TestSlack(CrawlerTestCase):
    def setUp(self):
        CrawlerTestCase.setUp(self)
        self.token = 'this-is-a-slack-token'
        self.slacklogger = SlackLogger(self.token)

    def test_slack_token_required_for_logger_init(self):
        with self.assertRaises(TypeError):
            SlackLogger()

    def test_slack_can_handle_all_channels(self):
        # The channel-name always needs a # infornt of it
        no_hashtag = self.slacklogger.checkChannel('no-hashtag')
        hashtag = self.slacklogger.checkChannel('#hashtag')

        self.assertEquals('#no-hashtag', no_hashtag)
        self.assertEquals('#hashtag', hashtag)

    def test_slack_can_format_json_from_data(self):
        ex = Exception('error message')
        site = Site('http://some-url.com/')

        data = json.loads(self.slacklogger.generateAttdata(ex, site))[0]

        self.assertEquals("http://some-url.com/",
                          data['fields'][0]['value'])

        self.assertEquals("Exception",
                          data['fields'][1]['value'])

        self.assertEquals("error message",
                          data['fields'][2]['value'])
