import json

try:
    from slacker import Slacker
except ImportError:
    raise ImportError


class SlackLogger(object):
    def __init__(self, slacktoken):
        self.slack = Slacker(slacktoken)

    def logError(self, ex, site, channel):
        text = "Error while crawling external site indexes!"

        attdata = self.generateAttdata(ex, site)
        channel = self.checkChannel(channel)

        self.send(text, attdata, channel)

    def checkChannel(self, channel):
        if not channel.startswith('#'):
            channel = '#' + channel
        return channel

    def generateAttdata(self, ex, site):
        return json.dumps(
            [
                {
                    "color": 'danger',
                    "fields": [
                        {
                            "title": "Site",
                            "value": site.url
                        },
                        {
                            "title": "Exception Type",
                            "value": type(ex).__name__
                        },
                        {
                            "title": "Error Message",
                            "value": str(ex.message)
                        }
                    ]
                }
            ]
        )

    def send(self, text, attdata, channel):
        username = self.slack.auth.test().body['user']
        self.slack.chat.post_message(channel,
                                     text,
                                     as_user=username,
                                     link_names=1,
                                     attachments=attdata)
