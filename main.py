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
import math

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

        #
        #NORMALIZED term-document frequency matrix
        ntdfm = normalize(tdfm)

        #get Inverse Document Frequency (maps terms: IDF)
        term_IDF_dict = {}
        #print("num docs: ", len(ntdfm))  
        for word in word_dict:
            term_IDF_dict[word] = inverseDocumentFrequency(word, ntdfm)
            #print(word, ": ", term_IDF_dict[word])
                
        #
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
            
            '''
            #see if any of the words are in the dictionary
            found_at_least_one = False
            for word in word_dict:
                for q_word in query_array:
                    if word == q_word:
                        getResults(q_word, tdfm)
                        found_at_least_one = True
            
            if(found_at_least_one == False):
                print("No results found :(")
            '''

            #
            #nTF * IDF
            query_ntfIDF_dict = {}
            #first populate:
            for term in query_array:
                query_ntfIDF_dict[term] = {}
                #then compute ntf * idf for each term
                #1. find normalized tf score
                tf_score = 0
                for docID in ntdfm:
                    query_ntfIDF_dict[term][docID] = 0 #default value
                    if term in ntdfm[docID]:
                        tf_score = ntdfm[docID][term]
                        query_ntfIDF_dict[term][docID] = tf_score * term_IDF_dict[term]
                        #print("ntfidf for ,", term , " at ", docID,": ", query_ntfIDF_dict[term][docID])
                
            #
            #Cosine similarity

            
            #(4.a?) Find TF, IDF and TF * IDF of query
            
            query_t = {}
            for q in query_array:
                query_t[q] = {}
                query_t[q]['tf'] = {}
                query_t[q]['idf'] = {}
                query_t[q]['tfidf'] = {}
                query_t[q]['tf'] = 1/len(query_array)
                try:
                    query_t[q]['idf'] = term_IDF_dict[q]
                except:
                    query_t[q]['idf'] = 0

                query_t[q]['tfidf'] = query_t[q]['tf'] * query_t[q]['idf']
                #print(query_t[q]['tf'], " x ", query_t[q]['idf'], " = ", query_t[q]['tfidf'])

            #(2) Compute Cosine similarity between query and ALL docs
            
            query_results = []
            cos_sim = {}

            print("RESULTS:")
            for docID in ntdfm:
                #print("cosine similarity for ", docID, ": ",cosineSimilarity(query_t, ntdfm, docID))
                cos_sim['url'] = docID
                cos_sim['title'] = Spider.getTitle(docID)
                cos_sim['cosine_similarity_score'] = cosineSimilarity(query_t, ntdfm, docID)
                query_results.append(cos_sim)
                print(cos_sim)

            
                
                        

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

def getResults(word, tdfm):
    for docURL in tdfm:
        for term in tdfm[docURL]:
            if term == word:
                print("FOUND ",  word, " AT: ", docURL, " for a total of ", tdfm[docURL][term], " times")
    
def normalize(tdfm):
    for docID in tdfm:
        counter = 0
        #get count of all the terms in the doc
        for term in tdfm[docID]:
            counter += tdfm[docID][term]
        #done going through all docs, now go thru them again and reassign scores
        for term in tdfm[docID]:
            tdfm[docID][term] = tdfm[docID][term]/counter
            #print("new score: ", tdfm[docID][term])
    return tdfm

def numDocsWordIsIn(term, allDocuments):
    sum = 0
    for doc in allDocuments:
        if term in allDocuments[doc]:
            sum += 1

    return sum

#below function: credit to https://janav.wordpress.com/2013/10/27/tf-idf-and-cosine-similarity/
def inverseDocumentFrequency(term, allDocuments):
    numDocumentsWithThisTerm = 0
    for doc in allDocuments:
        if term in allDocuments[doc]:
            numDocumentsWithThisTerm = numDocumentsWithThisTerm + 1

    if numDocumentsWithThisTerm > 0:
        #return 1.0 + math.log(float(len(allDocuments)) / numDocumentsWithThisTerm)
        return math.log(len(allDocuments) / (1 + numDocsWordIsIn(term, allDocuments)))
    else:
        return 1.0

def cosineSimilarity(doc1, doc2, docID):
    # cosine similarity:
    #top / bottom
    # top = d1[0] * d2[0] + d1[1] * d2[1]...
    # bottom = ( sqrt(d1[0]^2 + d1[1]^2 +...) * sqrt(sqrt(d2[0]^2 + d2[1]^2 +...) )

    num_reps = len(doc1)
    doc1_to_square = 0
    doc2_to_square = 0
    top_sum = 0

    for term_index in doc1:
        #print("TERM INDEX: ", term_index)
        try:
            top_sum += ( doc1[term_index]['tfidf'] * doc2[docID][term_index])
            doc1_to_square += (doc1[term_index]['tfidf'] * doc1[term_index]['tfidf'])
            doc2_to_square += (doc2[docID][term_index] * doc2[docID][term_index])

            bottomQ = math.sqrt(doc1_to_square)
            bottomD = math.sqrt(doc2_to_square)
        except:
            bottomQ = 0
            bottomD = 0

    
    

    #print(top_sum, ", ", bottomQ, ", ", bottomD)

    #print(doc1[term_index]['tfidf'])
    

    try:
        similarity = ( top_sum / (bottomQ * bottomD) )
        if similarity == 0:
            return 0
        else:
            return similarity
    
    except:
        return 0

    


    
    '''
    for q in doc1:
        for docID_temp in doc1[q]:
            if docID_temp == docID:
                print("    ", doc1[q][docID_temp])
                print("")
    '''

create_workers()
crawl()
