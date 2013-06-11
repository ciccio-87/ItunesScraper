import urllib2
import lxml.html as html
import re
import socket
import sys


def replaceme(source):

    xpathsource = html.fromstring(source)
    for styleinfo in xpathsource.xpath('//style/text()'): 
        stylelines = styleinfo.split("\n")

        for styleline in stylelines:
            matchObj = re.match(r"\.(.*?){(.*?)}", styleline)
            if matchObj:
                classname = 'class="' + matchObj.group(1) + '"'
                styleattr = 'style="' + matchObj.group(2) + '"'
                source = source.replace(classname, styleattr)

    return source

def hidemyass(url):
    source = urllib2.urlopen(url).read()
    source = html.fromstring(replaceme(source))
    list = []
    for tr in source.xpath('//tr'):
        array = tr.xpath("td[2]//*[not(contains(@style,'display:none'))]/text() | td[3]/text()")
        anonimity = tr.xpath("td[8]/text() | td[7]/text()")

        String = '.'.join(array)
        bla = re.sub(r"\.+",'.', re.sub(r"\.\n",":",String))
        findip = re.findall( r'(([0-9]+(?:\.[0-9]+){3}))+(.*)', bla)

	if (len(findip)):
		ip = ''.join(findip[0][1] + findip[0][2])
		list.append([ip, anonimity])
    return list

def proxy(url,proxy):
    try:
        proxy_handler = urllib2.ProxyHandler({'http': proxy})
        proxy_auth_handler = urllib2.ProxyBasicAuthHandler()
        request = urllib2.build_opener(proxy_handler, proxy_auth_handler)
        request.addheaders= [('User-agent', "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.2; en) Opera 9.50")]
        return request.open(url).read()
    except (urllib2.URLError, urllib2.HTTPError), e:
        return
    except Exception, detail:
        return
try:
    desired_proxies = int(sys.argv[1])
except:
    desired_proxies = 100
try:
    maxpages = int(sys.argv[2])
except:
    maxpages = 30
print 'so we\'re looking for at least ' + str(desired_proxies) + ' proxies, in a max of ' + str(maxpages) + ' pages'
socket.setdefaulttimeout(3)
#proxylist = []
final_list = []
for i in xrange(maxpages):
    temp = hidemyass("http://hidemyass.com/proxy-list" + "/" + str(i))
    #for item in temp:
    #    proxylist.append(item)
#for entry in proxylist:
#    print str(entry) + '\n\n'
    for i in xrange(len(temp)):
    	website = proxy("http://www.whatismyip.com/", temp[i][0])
        if website is not None and temp[i][0][:8] in website:
        #print [i],proxylist[i][0], proxylist[i][1]
            final_list.append(temp[i][0])
    if len(final_list) > desired_proxies:
        break
        
outfile = open('proxylist.txt','w')
for entry in final_list:
    outfile.write(entry + '\n')
outfile.close()
