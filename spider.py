try:
	from urllib.request import urlopen
except:
	from urllib import urlopen
try:
	import urllib.robotparser
except:
	import robotparser

from link_finder import LinkFinder
from domain import *
from general import *

#grabs a link, grabs html, passes to linkFinder
class Spider:
	rp = urllib.robotparser.RobotFileParser()
	rp.set_url("http://lyle.smu.edu/~fmoore/robots.txt")
	rp.read()
	print(rp.can_fetch("*", "/dontgohere/"))
	#class var: shared among all instances
	project_name = ''
	base_url = ''
	domain_name = ''
	queue_file = ''
	crawled_file = ''
	broken_links_file = ''
	queue = set()
	crawled = set()
	broken_links = set()

	def __init__(self, project_name, base_url, domain_name):
		#shared information
		Spider.project_name = project_name
		Spider.base_url = base_url
		Spider.domain_name = domain_name
		Spider.queue_file = Spider.project_name + '/queue.txt'
		Spider.crawled_file = Spider.project_name + '/crawled.txt'
		Spider.broken_links_file = Spider.project_name + '/broken_links.txt'
		self.boot()
		self.crawl_page('First spider', Spider.base_url)

	@staticmethod
	def boot():
		#if you're the first spider, create the project directory then the two data files (queue and crawled)
		create_project_dir(Spider.project_name)
		create_data_files(Spider.project_name, Spider.base_url)

		Spider.queue = file_to_set(Spider.queue_file) #get updated list of links and save as set
		Spider.crawled = file_to_set(Spider.crawled_file)
		Spider.broken_links = file_to_set(Spider.broken_links_file)

	@staticmethod
	def crawl_page(thread_name, page_url):
		if page_url not in Spider.crawled:
			print(thread_name + ' crawling ' + page_url)
			print('Queue ' + str(len(Spider.queue)) + ' | crawled ' + str(len(Spider.crawled)))
			
			Spider.add_links_to_queue(Spider.gather_links(page_url)) #add links to waiting list	
			Spider.queue.remove(page_url) #remove page you just crawled
			Spider.crawled.add(page_url) #move to crawl list

			#update files (at top)
			Spider.update_files()

	@staticmethod
	def gather_links(page_url):
		html_string = ''
		try:
			response = urlopen(page_url)
			if 'text/html' in response.getheader('Content-Type'):
				html_bytes = response.read() # receive byte data
				html_string = html_bytes.decode("utf-8")
			
			finder = LinkFinder(Spider.base_url, page_url)
			finder.feed(html_string)

		except Exception as e:
			Spider.broken_links.add(page_url)
			Spider.update_files()
			print(str(e))
			return set()
		return finder.page_links()

	@staticmethod
	def add_links_to_queue(links):
		for url in links:
			if url in Spider.queue:
				continue
			if url in Spider.crawled:
				continue
			if Spider.domain_name != get_domain_name(url):
				#make sure you stay in the domain name (lyle.smu.edu/~fmoore)				
				continue
			#below checks to see if content is allowed to be crawled
			tempUrl = url.replace('http://lyle.smu.edu/~fmoore', '')	
			allowed_var = Spider.rp.can_fetch("*", tempUrl)
			if(allowed_var != True):
				print("In an illegal area")
				continue
			Spider.queue.add(url)

	@staticmethod
	def update_files():
		set_to_file(Spider.queue, Spider.queue_file)
		set_to_file(Spider.crawled, Spider.crawled_file)
		set_to_file(Spider.broken_links, Spider.broken_links_file)
