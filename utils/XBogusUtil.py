import execjs
import urllib.parse


def generate_url_with_xbs(url, user_agent):
    query = urllib.parse.urlparse(url).query
    xbogus = execjs.compile(open('utils/X-Bogus.js').read()).call('sign', query, user_agent)
    return xbogus
