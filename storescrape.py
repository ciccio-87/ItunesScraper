#!/usr/bin/python
"""
Detail desc: 
1) In addition to the games name i also want each games image, description and whether they are free or payed app.
2) the output format can be csv, xml. 
3) I want to see the accuracy of the data and if i am impressed i will provide long term work. 
4) Candidate who can prove they have work experience in scrapping will be given higher priority. 
"""
from bs4 import BeautifulSoup
import urllib2
import unicodedata
import os
import re
import random
import time
import sqlite3

def downloadfile(url, path, file_name, proxy, agent):
	while (True):
		#file_name = url.split('/')[-1]
		#u = urllib2.urlopen(url)
		#proxy = str(proxies[random.randrange(0,len(proxies))])
		#agent = str(agents[random.randrange(0,len(agents))])
		proxy_handler = urllib2.ProxyHandler({'http': proxy})
	        #proxy_auth_handler = urllib2.ProxyBasicAuthHandler()
	        #request = urllib2.build_opener(proxy_handler, proxy_auth_handler)
		request = urllib2.build_opener(proxy_handler)
		request.addheaders= [('User-agent', agent)]
		try:	
			u = request.open(url)
		except:
			for i in range(0,random.randrange(longsleep[0],longsleep[1])):
				time.sleep(1)
			proxy = str(proxies[random.randrange(0,len(proxies))])
			agent = str(agents[random.randrange(0,len(agents))])
			continue
		
		f = open(os.path.join(path,'images',file_name), 'wb')
		meta = u.info()
		file_size = int(meta.getheaders("Content-Length")[0])
		#print "Downloading: %s Bytes: %s" % (file_name, file_size)

		file_size_dl = 0
		block_sz = 8192
		while True:
	    		buffer = u.read(block_sz)
	    		if not buffer:
	        		break
	
	    		file_size_dl += len(buffer)
	    		f.write(buffer)
	    		#status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
	    		#status = status + chr(8)*(len(status)+1)
	    		#print status
	
		f.close()
		break		

def make_soup(url):
	tries = 0
	while(True):
		proxy = str(proxies[random.randrange(0,len(proxies))])
		agent = str(agents[random.randrange(0,len(agents))])
		proxy_handler = urllib2.ProxyHandler({'http': proxy})
        	#proxy_auth_handler = urllib2.ProxyBasicAuthHandler()
        	#request = urllib2.build_opener(proxy_handler, proxy_auth_handler)
		request = urllib2.build_opener(proxy_handler)
        	request.addheaders= [('User-agent', agent)]
		try:        
			if tries >= 2:
				#go with google cache
				print "# miss, going with Gcache"
				url = cacheurl + url			
			html = request.open(url).read()
		except:
			for i in range(0,random.randrange(longsleep[0],longsleep[1])):
				time.sleep(1)
			tries += 1
			# better luck next time		
			continue
		# all good, man
		break
	return BeautifulSoup(html, "lxml"),proxy, agent

def getcatlinks(start_url):
	soup = make_soup(start_url)[0]
	cat_list = soup.find('ul','list top-level-subgenres')
	cat_dict = {}
	for li in cat_list.findAll('li'):
		cat_dict[li.a['title'].split(' - ')[0]] = li.a['href']
		#print 'Category: ' + li.a['title'].split(' ')[0]
		#print 'URL: ' + li.a['href']
		#print '\n'
	return cat_dict

def findpagenum(url):
	soup = make_soup(url)[0]
	num_page = soup.find('ul','list paginate')
	if num_page is not None:
		for li in num_page.findAll('li'):
			if len(str(li.string)) <= 2:
				pagenum = int(li.string)
		return pagenum
	else:
		return 1

def get_gamelinks(url):
	soup = make_soup(url)[0]
	#first column
	link_list = []
	for col in ['column first','column','column last']:
		column = soup.find('div',col)
		for li in column.ul.findAll('li'):
			link_list.append(li.a['href'])
	return link_list
	
def scrape_game(url):
	gamedict = {}
	soup,proxy,agent = make_soup(url)
	block = soup.find('div',{'class':'platform-content-block display-block'})
	snip = block.find('div',{'class':'left'})
	gamedict['permalink'] = url
	gamedict['storeid'] = url.split('?')[0].split('/')[-1]
	urlname = url.split('?')[0].split('/')[-2]
	gamedict['title'] = snip.h1.string
	gamedict['developer'] = snip.h2.string
	snip = soup.find('div',{'metrics-loc':'Titledbox_Description'})
	gamedict['description'] = snip.p.getText()
	snip = soup.find('div','extra-list customer-ratings')
	ratings = []
	for div in snip.findAll('div',{'class':'rating'}):
		ratings.append(div['aria-label'])
	if len(ratings) >= 1:	
		gamedict['rating_current'] = ratings[0]
	else:
		gamedict['rating_current'] = None
	if len(ratings) >= 2:
		gamedict['rating_all'] = ratings[1]
	else:
		gamedict['rating_all'] = None
	
	snip = soup.find('div',{'id':'left-stack'})
	list = snip.find('ul','list')
	arr = []
	for li in list.findAll('li'):
		splittext = li.getText().split(' ')
		if len(splittext) >= 2:
			arr.append(' '.join(splittext[1::]))
		else:
			arr.append(li.getText())
	gamedict['price'] = arr[0]
	gamedict['category'] = arr[1]
	gamedict['release'] = arr[2]
	gamedict['version'] = arr[3]	
	gamedict['filesize'] = arr[4]
	gamedict['languages'] = arr[5]
 		
	get_images(soup,str(urlname) + '-' + str(gamedict['storeid'][2:]),gamedict,proxy,agent)
	return gamedict

def get_images(soup,gameid,dic,proxy,agent):
	cantfind = False
	try:
		os.mkdir(gameid)
	except OSError, e:
		#print 'Directory already exists, prepare for cascading exceptions'
		pass	
	#find game(app) icon
	snip = soup.find('img',{'alt':dic['title']})
	linkre = re.compile('src=".+" ')
	try:
		artwork = str(re.findall(linkre,str(snip))[0][5:-2])
	except:
		cantfind = True
		print gameid
	if not cantfind:
		downloadfile(artwork,gameid,'artwork.jpg',proxy,agent)
	
	#find screenshots
	snip = soup.find('div',{'class':'swoosh lockup-container application large screenshots'})
	i = 1
	for div in snip.findAll('div',{'class':'lockup'}):
		shot = str(div.img['src'])
		downloadfile(shot,gameid,'screenshot'+str(i)+'.jpg',proxy,agent)
		i += 1
		
	"""
	#soup.find('div','artwork')
	#snip.img['src']
	#soup.find(
	"""
def buildurls(url):
	urls = []
	random.shuffle(startchar)
	for char in startchar:
		temp = url + url_params[0] + char.upper()
		for i in range(0,random.randrange(shortsleep[0],shortsleep[1])):
			time.sleep(1)
		print 'searching letter ' + char.upper()
		n = int(findpagenum(temp))
		for num in range(1,n):
			urls.append(temp + url_params[1] + str(num))
	return urls		
	


if __name__ == '__main__':

	proxies = open('proxylist.txt','r').readlines()
	agents = []
	for UA in open('user-agents.txt','r').readlines():
		if UA.startswith('#'):
			continue
		else:
			agents.append(UA)
	first_url = 'https://itunes.apple.com/us/genre/ios-games/id6014?mt=8'
	url_params =['&letter=','&page=']
	startchar = []
	for i in range(ord('a'),ord('z')+1):
	#for i in range(ord('a'),ord('b')+1):
		startchar.append(unichr(i))
	startchar.append('*')

	shortsleep = [5,10]
	mediumsleep = [20,30]
	longsleep = [40,60]
	linksfile = 'links.txt'
	cacheurl = 'http://webcache.googleusercontent.com/search?q=cache:'
	
	try:
		os.mkdir('images')
	except OSError, e:
		#probably it already exists		
		pass
	catlinks = getcatlinks(first_url)
	toscrape = 0
	pages = []
	stop = 0
	for key in catlinks:
		stop += 1
		#if stop >=3:
		#	break
		for i in range(0,random.randrange(mediumsleep[0],mediumsleep[1])):
			time.sleep(1)
		print 'searching category: ' + key
		links = buildurls(catlinks[key])
		for link in links:
			pages.append(link)
		random.shuffle(pages)
		for page in pages:
			links = get_gamelinks(page)
			outfile = open(linksfile,'a')
			for link in links:
				#toscrape.append(link)
				outfile.write(link + '\n')
				toscrape += 1

	newlinksfile = 'unique.txt'
	shell_command = "cat " + linksfile + " | sort | uniq > " + newlinksfile
	ret = os.system(shell_command)
	linksfile = newlinksfile
	if ret != 0:
		print "TROUBLES EXECUTING SHELL COMMAND"
	final_links = open(linksfile,'r').readlines()
	con = sqlite3.connect('gamedb.db')
	c = con.cursor()
	c.execute("CREATE TABLE IF NOT EXISTS appstore (id integer primary key autoincrement,storeid text,title text,permalink text,developer text,description text,rating_cur text,rating_all text,price text,category text,release text,version text,filesize text,languages text)")
	for link in final_links:
		for i in range(0,random.randrange(mediumsleep[0],mediumsleep[1])):
			time.sleep(1)
		dic = scrape_game(link)
		arr = [dic['storeid'],dic['title'],dic['permalink'],dic['developer'],dic['description'],dic['rating_current'],dic['rating_all'],dic['price'],dic['category'],dic['release'],dic['version'],dic['filesize'],dic['languages']]
		c.execute("INSERT INTO appstore(storeid,title,permalink,developer,description,rating_cur,rating_all,price,category,release,version,filesize,languages) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",arr)
		con.commit()
	con.close()
	# str(len(toscrape)) + ' links to scrape'
	#for link in toscrape:
	#	dic = scrape_game(url)
		
	



