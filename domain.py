try:
    from urllib.parse import urlparse
except ImportError:
     from urlparse import urlparse

#get domain name(example.com)
def get_domain_name(url):
	
	try:
		results = get_sub_domain_name(url).split('.')
		#now results is broken up into chunks sep by .
		return results[-2] + '.' + results[-1] #return 2nd to last + . + last
	except:
		return ''
	
	return 'lyle.smu.edu/~fmoore'


#get sub domain name (name.example.com)
def get_sub_domain_name(url):
	try:
		if('lyle.smu.edu/~fmoore' in url):
			return urlparse(url).netloc + '/~fmoore'
		else:
			return ''
	except:
		return ''

