try:
	from HTMLParser import HTMLParser
except:
	from html.parser import HTMLParser

try:
	from urllib import parse
except:
	import urllib2


class LinkFinder(HTMLParser):

	def __init__(self, base_url, page_url):
		super().__init__()
		self.base_url = base_url
		self.page_url = page_url
		self.links = set()

	def handle_starttag(self, tag, attrs):
		if tag == 'a':
			for (attribute, value) in attrs:
				if attribute == 'href':
					url = parse.urljoin(self.base_url, value) #video 6
					self.links.add(url)

	def page_links(self):
		return self.links

	def error(self, message):
		pass

