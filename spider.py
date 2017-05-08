try:
	from urllib.request import urlopen
except:
	from urllib import urlopen
try:
	import urllib.robotparser
except:
	import robotparser

from bs4 import BeautifulSoup as soup

from link_finder import LinkFinder
from domain import *
from general import *

import re
import string
from stemmer import PorterStemmer

#grabs a link, grabs html, passes to linkFinder
class Spider:
	rp = urllib.robotparser.RobotFileParser()
	rp.set_url("http://lyle.smu.edu/~fmoore/robots.txt")
	rp.read()
	#print(rp.can_fetch("*", "/dontgohere/"))
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
	num_crawled = 0
	stopwords = []
	num_graphics_files = 0 #jpg, jpeg, png, PDF(?), gif
	p = 0

	page_dict = {} #keep a dictionary of page_url : [parsed words]

	def __init__(self, project_name, base_url, domain_name, num_pages_to_crawl):
		#shared information
		Spider.project_name = project_name
		Spider.base_url = base_url
		Spider.domain_name = domain_name
		Spider.queue_file = Spider.project_name + '/queue.txt'
		Spider.crawled_file = Spider.project_name + '/crawled.txt'
		Spider.broken_links_file = Spider.project_name + '/broken_links.txt'
		Spider.num_pages_to_crawl = num_pages_to_crawl
		Spider.num_crawled = 0
		Spider.num_graphics_files = 0
		#read stopwords into array
		stopwordsfile = open("stopwords.txt", "r")
		Spider.stopwords = stopwordsfile.read().split('\n')
		Spider.p = PorterStemmer()

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
			#print(thread_name + ' crawling ' + page_url)
			#print('Queue ' + str(len(Spider.queue)) + ' | crawled ' + str(len(Spider.crawled)))
			
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

			Spider.page_dict[page_url] = []

			if 'text/html' in response.getheader('Content-Type') or 'text/htm' in response.getheader('Content-Type'):
				print("URL: ", page_url)
				html_bytes = response.read() # receive byte data
				html_string = html_bytes.decode("utf-8")
				
				#html data
				web_soup = soup(html_string, "html.parser")
				main_div = web_soup.find(name="p", attrs={'class': 'main-content'})
				#print(web_soup.get_text())
				words = web_soup.get_text().split() 
				
				Spider.addToDict(page_url, words, 'output_html.txt')
						

			elif 'text/plain' in response.getheader('Content-Type'):
				html_bytes = response.read() # receive byte data
				html_string = html_bytes.decode("utf-8")
				
				#html data
				web_soup = soup(html_string, "html.parser")
				#print(web_soup.get_text())
				words = web_soup.get_text().split() 
				
				Spider.addToDict(page_url, words, 'output_txt.txt')
			else:
				#print("RESPONSE: " + response.getheader('Content-Type'))
				if 'image/' in response.getheader('Content-Type') or 'images/' in response.getheader('Content-Type') or 'application/pdf' in response.getheader('Content-Type'):
					Spider.num_graphics_files += 1
					#print("images: " + str(Spider.num_graphics_files))
				

			
			#check for prev. seen content

			
			finder = LinkFinder(Spider.base_url, page_url)
			finder.feed(html_string)

		except Exception as e:
			Spider.broken_links.add(page_url)
			Spider.update_files()
			#print("Found broken link: ", page_url)
			#print("ERROR: " + str(e))
			return set()
		return finder.page_links()

	@classmethod
	def addToDict(self, page_url, data, filename):
		with open(filename, 'a') as out:
			for word in data:
				#print(word)
				#out.write(web_soup.get_text() + '\n')
				try:
					trimmed = re.match("^[0-9a-zA-Z\-\']+$", word)
					toCheck = trimmed[0].lower().rstrip()
					#print("TRIMMED: ", trimmed[0])
					for sw in Spider.stopwords:
						sw_fixed = sw.lower().rstrip() #convert to lowercase and remove trailing whitespace
						if toCheck == sw_fixed:
							break
						elif sw == Spider.stopwords[-1]:
							#print("WRITING: " + toCheck)
							toCheck = self.remove_punctuation(toCheck)
							#print("AFTER STEMMING: " + Spider.p.stem_word(toCheck))
							toCheck = Spider.p.stem_word(toCheck)
							Spider.page_dict[page_url].append(toCheck)
							out.write(toCheck + '\n')

				except:
					#print("NOT A WORD!")
					pass
	
	#below: credit to https://github.com/jstumbaugh/web_crawler/blob/master/crawler.py
	@classmethod
	def remove_punctuation(self, text) :
		"""
		Author: Nicole
		This method uses regex to remove the punctuation in text.
		http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
		"""
		exclude = set(string.punctuation)
		return ''.join(ch for ch in text if ch not in exclude)

	@staticmethod
	def add_links_to_queue(links):
		for url in links:
			if url in Spider.queue:
				continue
			if url in Spider.crawled:
				continue
			if Spider.domain_name != get_domain_name(url):
				#make sure you stay in the domain name (lyle.smu.edu/~fmoore)	

				#add to out_going_links.txt		
				with open('out_going_links.txt', 'a') as out:
					out.write(url + '\n')
				out.close()

				continue
			#below checks to see if content is allowed to be crawled
			tempUrl = url.replace('http://lyle.smu.edu/~fmoore', '')	
			allowed_var = Spider.rp.can_fetch("*", tempUrl)
			if(allowed_var != True):
				print("In an illegal area")
				continue
			
			if Spider.num_pages_to_crawl > Spider.num_crawled + 1:
				Spider.num_crawled += 1
				Spider.queue.add(url)


	@staticmethod
	def update_files():
		set_to_file(Spider.queue, Spider.queue_file)
		set_to_file(Spider.crawled, Spider.crawled_file)
		set_to_file(Spider.broken_links, Spider.broken_links_file)

	@classmethod
	def getDocIDDict(self):
		return Spider.page_dict

	@classmethod
	def checkForMatch(self, arr1, arr2):
		if arr1 == arr2:
			return True
		else:
			#TO DO: check for >99% equivalence
			return False