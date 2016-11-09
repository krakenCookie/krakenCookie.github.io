'''
Created on Oct 31, 2016

@author: zburchill
'''

from bs4 import BeautifulSoup
import urllib.request
from datetime import datetime
from PIL import Image
import io
import pickle


'''
TO-DO: try this instead of all that shiznit :
    games = soup.find_all('tr', {'class': 'stage-finished'})

'''



################# Chainsaw suit ##########################################
def chs_is_prev_comic(x):
    is_prev_link = x.name=="a" and x.has_attr('class') and x['class']==["hvr-shrink"]
    if is_prev_link:
        contains_prev_arrow = x.img['src']=="/images/css2015-prev.png"
        return(contains_prev_arrow)
    else:
        return(False)
def chs_is_date(x):
    return(x.name=="span" and x.has_attr("class") and x["class"]==["post-date"])
##################################################################################

###################### Broodhollow #######################################################
def brood_is_prev_comic(x):
    try: 
        answer = x.name == "a" and "navi-prev" in x["class"]
        return(answer)
    except: return(False)
def brood_is_title(x):
    try: 
        answer = x["class"]==["post-title"]
        return(answer)
    except: return(False)
def brood_is_date(x):
    try: 
        answer = x.name == "span" and x["class"]==["post-date"]
        return(answer)
    except: return(False)

######################### SMBC ###################################################################



def get_smbc():
    r = urllib.request.urlopen('http://www.smbc-comics.com/').read()
    soup = BeautifulSoup(r)
    
    counter=0
    
    date_format="%B %d, %Y"
    date_csv_s="post_date,width,height"
    prev_url=""
    
    while (True):
        if (counter % 100 == 0):
            print("Finished "+str(counter) + " pages")
            print(len(date_csv_s.splitlines()))
        date = datetime.strptime(list(soup.find('div', {'class': 'cc-publishtime'}).strings)[0], date_format)
        image_url = soup.find('img',{'id': 'cc-comic'})['src']
        try:
            image_file = io.BytesIO(urllib.request.urlopen(urllib.parse.quote(image_url,safe=":/")).read())
            image_file.seek(0)
            im = Image.open(image_file)
            width, height = im.size
        except Exception as errorm:
            print(str(errorm))
            #e=io.BytesIO(urllib.request.urlopen(image_url).read())
            #ee=Image.open(e)
            #print(ee.size)
            width="NA"
            height="NA"
            print("cant get dimensions for: "+image_url+" on page: "+prev_url)
        
        date_csv_s+="\n"+date.strftime("%x")+","+str(width)+","+str(height)
        
        try:
            prev_comic_soup = soup.find('a',{'rel': 'prev'})
            if prev_comic_soup["href"]==prev_url:
                break
            r = urllib.request.urlopen(prev_comic_soup["href"]).read()
            soup = BeautifulSoup(r)
            prev_url=prev_comic_soup["href"]
            counter+=1
        except:
            print(prev_url)
            break
        pass
        
    save_obj(date_csv_s, "delete")
    print(len(date_csv_s.splitlines()))    
    with open("/Users/zburchill/Desktop/smbc_dates.csv","w") as f:
        f.write(date_csv_s)    
    print(len(date_csv_s.splitlines()))
    

get_smbc()

'''
def get_broodhollow():
    r = urllib.request.urlopen('http://broodhollow.chainsawsuit.com/').read()
    soup = BeautifulSoup(r)
    
    date_format="%B %d, %Y"
    date_csv_s="post_date,cadavre"
    prev_url=""
    
    while (True):
        date = datetime.strptime(soup.find(brood_is_date).contents[0],date_format)
        title_text = list(soup.find(brood_is_title).strings)[0]
        is_cadavre="cadavre" in title_text or "Cadavre" in title_text
        date_csv_s+="\n"+date.strftime("%x")+","+str(is_cadavre)
        
        try:
            prev_comic_soup = soup.find_all(brood_is_prev_comic)[0]
            if prev_comic_soup["href"]==prev_url:
                break
            r = urllib.request.urlopen(prev_comic_soup["href"]).read()
            soup = BeautifulSoup(r)
            prev_url=prev_comic_soup["href"]
        except:
            print(prev_url)
            print(prev_comic_soup["href"])
            break
        
    with open("/Users/zburchill/Desktop/broodhollow_dates.csv","w") as f:
        f.write(date_csv_s)    
    print(len(date_csv_s.splitlines()))
    
def get_chainsaw_suit():
    r = urllib.request.urlopen('http://www.chainsawsuit.com').read()
    soup = BeautifulSoup(r)
    print(type(soup))
    
    date_format="%B %d, %Y"
    date_list=[]
    prev_url=""
    
    while (True):
        prev_comic_soup=soup.find_all(chs_is_prev_comic)[0]
        date=datetime.strptime(soup.find(chs_is_date).contents[0],date_format)
        if prev_comic_soup["href"]==prev_url:
            break
        date_list+=[date]
        try:
            r = urllib.request.urlopen(prev_comic_soup["href"]).read()
        except:
            print(prev_url)
            print(prev_comic_soup["href"])
            break
        soup = BeautifulSoup(r)
        prev_url=prev_comic_soup["href"]
    print(len(date_list))
    
    s="post_date\n"
    for date_obj in date_list:
        date_s=date_obj.strftime("%x")
        s+=date_s+"\n"
    
    with open("/Users/zburchill/Desktop/chainsawsuit_dates.csv","w") as f:
        f.write(s)

'''