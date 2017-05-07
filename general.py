import os

#each website crawled is a separate project (folder)
def create_project_dir(directory):
	if not os.path.exists(directory):
		print('creating project ', directory)
		os.makedirs(directory)

#create queue and crawled files
def create_data_files(project_name, base_url):
	queue = project_name + '/queue.txt' #variable for file path
	crawled = project_name + '/crawled.txt'
	broken_links = project_name + '/broken_links.txt'
	if not os.path.isfile(queue):
		write_file(queue, base_url)
	if not os.path.isfile(crawled):
		write_file(crawled, '')
	if not os.path.isfile(broken_links):
		write_file(broken_links, '')

#create new file
def write_file(path, data):
	f = open(path, 'w')
	f.write(data)
	f.close() #free up memory resources

#add data onto an existing file
def append_to_file(path, data):
	with open(path, 'a') as file: #a: append (add to end)
		file.write(data + '\n')

#delete contents of a file
def delete_file_contents(path):
	with open(path, 'w'):
		pass #do nothing

#store url's in a SET (not list) because there are NO duplicates

#read a file, convert each line to set items
def file_to_set(file_name):
	results = set() #create empty set
	with open(file_name, 'rt') as f:
		#loop thru each line
		for line in f:
			#iterate one line at a time
			#take each line, add to the set
			results.add(line.replace('\n', ''))	#replace newlines with nothing...
	return results

#convert a set(links) to a file
def set_to_file(links, file):
	delete_file_contents(file)
	for link in sorted(links):
		append_to_file(file, link)
