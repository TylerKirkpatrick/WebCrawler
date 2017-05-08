import threading
try:
	from queue import Queue
except:
	from multiprocessing import Queue
from spider import Spider
from domain import *
from general import *
import os
import shutil

PROJECT_NAME = 'IR_project'
#HOMEPAGE = 'https://thenewboston.com/'
HOMEPAGE = 'http://lyle.smu.edu/~fmoore/'
DOMAIN_NAME = get_domain_name(HOMEPAGE)
QUEUE_FILE = PROJECT_NAME + '/queue.txt'
CRAWLED_FILE = PROJECT_NAME + '/crawled.txt'
NUMBER_OF_THREADS = 4

#thread queue
queue = Queue()
try:
    os.remove('output_html.txt')
except:
    pass
try:
    os.remove('output_txt.txt')
except:
    pass
try:
    shutil.rmtree(PROJECT_NAME)
except:
    pass

print("How many pages would you like to crawl? (leave blank to crawl all)")
num_pages_to_crawl = input()
if(num_pages_to_crawl == '' or num_pages_to_crawl == ' '):
    num_pages_to_crawl = 100
else:
    num_pages_to_crawl = int(num_pages_to_crawl)

Spider(PROJECT_NAME, HOMEPAGE, DOMAIN_NAME, num_pages_to_crawl)

# Create worker threads (will die when main exits)
def create_workers():
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work)
        t.daemon = True #ensuring it dies when main exits
        t.start()


# Do the next job in the queue
def work():
    while True:
        url = queue.get()
        Spider.crawl_page(threading.current_thread().name, url)
        queue.task_done() #tells OS its ready for next job


# Each queued link is a new job
def create_jobs():
    for link in file_to_set(QUEUE_FILE):
        queue.put(link)
    queue.join() #make sure threads don't collide
    crawl()


# Check if there are items in the queue, if so crawl them
def crawl():
    queued_links = file_to_set(QUEUE_FILE)
    if len(queued_links) > 0:
        print(str(len(queued_links)) + ' links in the queue')
        create_jobs()


create_workers()
crawl()