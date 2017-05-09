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

import operator
from stemmer import PorterStemmer
import string

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
    os.remove('out_going_links.txt')
except:
    pass
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
        #print(str(len(queued_links)) + ' links in the queue')
        create_jobs()
    else:
        #print("DONE")
        docIDDict = Spider.getDocIDDict()

        keys_to_delete = []

        for key in docIDDict:
            if(docIDDict[key] != [] and key not in keys_to_delete):
                for key_to_compare in docIDDict:
                    if(key != key_to_compare and docIDDict[key] == docIDDict[key_to_compare] and key_to_compare not in keys_to_delete):
                        #print("DUPLICATE CONTENT FOUND:")
                        #print(key)
                        #print(key_to_compare)
                        keys_to_delete.append(key_to_compare)
                        #docIDDict.pop(key_to_compare, None)

        #delete duplicate keys
        for todelete in keys_to_delete:
            #print("DELETING: " + todelete)
            docIDDict.pop(todelete, None)

        #make dict of individual words: frequency
        word_dict = {}
        for key in docIDDict:
            for word in docIDDict[key]:
                if word in word_dict:
                    word_dict[word] += 1
                else:
                    word_dict[word] = 1
        
        
        #sort by term frequency in descending order
        sorted_term_frequency = sorted(word_dict.items(), key=operator.itemgetter(1), reverse=True)
        #print(sorted_term_frequency)

        #keep track of term: document freq.

        #Make a dict of term: document frequency
        tdf = {}

        #loop thru every word in the sorted_term_freq array
        for k in range(len(sorted_term_frequency)):
            #loop thru each document to see if the term_key is present
            for document_key in docIDDict:
                #print("NEW DOC!", docIDDict[document_key])
                #loop thru each word in the doc
                for word in docIDDict[document_key]:
                    if(word == sorted_term_frequency[k][0]):
                        if word in tdf:
                            tdf[word] += 1
                        else:
                            #tdf[word] = [document_key]
                            tdf[word] = 1
                    
                       
                        
                        #break because we are just counting the number of DOCUMENTS that the term is found in...
                        

        #sorted_tdf = sorted(tdf.values(), key=len, reverse=True)
        sorted_tdf = sorted(tdf.items(), key=operator.itemgetter(1), reverse= True)

        #print(sorted_tdf)
        
        '''
        counter = 0
        for i in sorted_tdf:
            if counter < 20:
                print(i)
                counter += 1
            else:
                break
        '''

        #array of ALL words!
        dict_all_words = []
        for word in word_dict:
            if word not in dict_all_words:
                dict_all_words.append(word)

        #print("ALLWORDS: ", len(dict_all_words ))

        #term-document frequency matrix
        tdfm = Spider.tdfm
        
        '''
        for doc in tdfm:
            print(doc, ": ", tdfm[doc])
            print("\n")
        '''
        
        
        #NOW FOR QUERY
        to_stop = 0

        while to_stop == 0:
            hitList = []
            hitListTitle = []
            print("Enter a query!")
            query = input("-->" )
            query = query.lower()
            if query == "stop":
                to_stop = 1
                continue
            
            query_array = trimQuery(query)
            
            #see if any of the words are in the dictionary
            for word in word_dict:
                for q_word in query_array:
                    if word == q_word:
                        getResults(query_array, tdfm)

            


def trimQuery(query):
    stopwordsfile = open("stopwords.txt", "r")
    stopwords = stopwordsfile.read().split('\n')

    print("before stemming: ", query)
    stem = PorterStemmer()
    
    wordsArray = []

    for word in query.split():
        word = word.lower().rstrip()
        if(word in stopwords):
            continue
        else:
            word = remove_punctuation(word)
            #print("AFTER STEMMING: " + Spider.p.stem_word(toCheck))
            word = Spider.p.stem_word(word)
            wordsArray.append(word)
    
    query = wordsArray
    print("after stemming: ", query)
    return query


def remove_punctuation(text) :
    """
    Author: Nicole
    This method uses regex to remove the punctuation in text.
    http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
    """
    exclude = set(string.punctuation)
    return ''.join(ch for ch in text if ch not in exclude)

def getResults(query_array, tdfm):
    found_at_least_one = False
    for word in query_array:
        for docURL in tdfm:
            for term in tdfm[docURL]:
                if term == word:
                    found_at_least_one = True
                    print("FOUND MATCH AT: ", docURL, " for a total of ", tdfm[docURL][term], " times")
    
    if(!found_at_least_one):
        print("No results found")


create_workers()
crawl()
