'''
Created on Oct 31, 2016

@author: zburchill
'''

from bs4 import BeautifulSoup
import urllib.request
from datetime import datetime
# Need to use Pillow!!!!!!!!!!!!!!!!!!!!!!
from PIL import Image
import io
import pickle

# for threading
import threading
from queue import Queue
import time

# In case you need to save stuff
def save_obj(obj, name ):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)
    
    
# lock to serialize output
#csv_string="Date,IsCadavre" # this is the header for the Broodhollow .csv file
#csv_string="Date,Width,Height" # this is the header for the SMBC .csv file
csv_string="Date,SorryCount" # this is the one I used for the prague race .csv file
csv_string_lock = threading.Lock()


# --------------------------- Helper functions and utility functions ---------------------#

# makes sure there are the same number of commas in two csv lines
# e.g., that you have the same number of columns in the header and the lines
def check_csv(csv_string1,csv_string2):
    try:
        assert(csv_string1.count(",")==csv_string2.count(","))
    except:
        raise AssertionError("Number of columns differs")

# So, you can also pass a FUNCTION as an argument to `soup.find()` to search the tree
# This function just makes it so that it puts the arguments in `soup.find()` in the right way
# Don't fret about this too much if you aren't familiar with bs4
def clean_find(soup_t,args):
    # for Python 3.x but before 3.2, use: `if hasattr(args, '__call__'):`
    if callable(args):
        return(soup_t.find(args))
    else:
        return(soup_t.find(*args))
        

# This is the default function that gets the time. If getting the timestamp is more complicated, write your own
def default_get_time(soup_t,time_args,date_format):
    return(datetime.strptime(list(clean_find(soup_t,time_args).strings)[0], date_format))

# ----------------------- Threading functions ---------------------------- #


# The worker thread pulls an item from the queue and processes it
def worker(time_args, other_function=None, date_format="%B %d, %Y", **kwargs):
    while True:
        item = q.get()
        get_soup_stuff(item,
                       time_args=time_args,
                       date_format=date_format,
                       other_function=other_function, **kwargs)
        q.task_done()

# Takes a page from the queue, get its date of publication, and whatever else you want from it
# i.e. you can pass in a function that gets other data from the page 
def get_soup_stuff(soup_t, 
                   time_args, #a list of whatever you want in soup.find()
                   date_format="%B %d, %Y",
                   date_output_format="%x",
                   other_function=None, # a function that takes in a soup object and returns  string or list
                   custom_time_function=None # if you're a real go-getter and need your own time function
                   ):
    # Maybe the timestamp will be more complicated to extract. If so, edit this
    if not custom_time_function:
        date = default_get_time(soup_t,time_args,date_format)
    else:
        date = custom_time_function(soup_t)
    date_s = date.strftime(date_output_format)
    if other_function:
        other_results = other_function(soup_t)
        write_csv_data(date_s,other_results)
    else:
        write_csv_data(date_s)

# writes the data gathered from a page to the .csv file
def write_csv_data(date_string,other_thing=None):
    global csv_string
    if not other_thing is None:
        if isinstance(other_thing, list):
            csv_line="\n{0!s},{1}".format(date_string,
                                       ",".join([str(e) for e in other_thing]))
        else:
            try:
                csv_line="\n{0!s},{1!s}".format(date_string,
                                            other_thing)
            except Exception:
                #Just guessing it was a casting error here, too lazy to do more
                raise TypeError("can't turn both variables into strings, probably")
    else:
        csv_line="\n"+date_string
    # Checks to see if the new line has the same # of columns as the header
    # I don't do anything to CATCH this error though... so, be careful
    try:
        check_csv(csv_line,csv_string.splitlines()[0])
    except AssertionError:
        raise AssertionError("Different number of columns from header: '{0}' and '{1}'".format(csv_line,
                                                                                               csv_string.splitlines()[0]))
    with csv_string_lock:
        csv_string+=csv_line


# ----------------------------  Image analyzing functions ---------------------------------- #

# Remember you can pass in other functions that will analyze the soup besides just getting time in `get_soup_stuff()`
# Gets the image url from the page and tries to load it
def get_image_from_soup(soup_t,image_args):
    image_url = clean_find(soup_t,image_args)['src']
    try: 
        width, height = get_image_dim(image_url)
    except Exception as errorm:
        print(str(errorm))
        width="NA"
        height="NA"
        print("cant get dimensions for: "+image_url)
    return([width,height])


# Uses Pillow to load the image and get its dimensions
def get_image_dim(image_url_t):
    image_file = io.BytesIO(urllib.request.urlopen(urllib.parse.quote(image_url_t,safe=":/")).read())
    image_file.seek(0)
    im = Image.open(image_file)
    width, height = im.size
    return(width, height)
    

# ----------------------------  SMBC example instantiations or whatever ---------------------------------- #

# Takes in a page, gets the image as SMBC uses, and passes it on. A wrapper for `get_image_from_soup()` basically
def get_smbc_image(soup_t):
    image_args=['img',{'id': 'cc-comic'}]
    return(get_image_from_soup(soup_t, image_args))

# This is a wrapper function for `worker()` that is specific to smbc
def smbc_worker():
    date_format="%B %d, %Y" # the format of smbc's time_stamp
    time_args=['div', {'class': 'cc-publishtime'}] # the html element with the time_stamp
    worker(time_args, get_smbc_image, date_format)

# The arguments to `soup.find()` that will return the element with SMBC's previous button
smbc_prev_comic_args=['a',{'rel': 'prev'}]
# The filename we want to save to
smbc_filename="/Users/zburchill/Desktop/smbc_dates_threaded.csv"


# ------------------------- An example for the webcomic 'Prague Race' ---------------------------------------------#

# This is a wrapper function for `worker()` that is specific to Prague Race
def prague_race_worker():
    date_format="posted %b.%d.%y at %I:%M %p" # the format of PR's time_stamp
    time_args=['div', {'class': 'cc-publishtime'}] # also the html element for prague race
    worker(time_args, get_prague_race_comments_and_sorry_count, date_format)
    
# I feel like the author of prague race apologizes a lot--might that correlate with delays? let's find out
# Also maybe number of comments could be interesting?
# Ah, dang, the number of comments is posted using javascript, which BS4 can't handle without a bit more seriousness than what I want to get into
# To use BS4 with javascript-generated content, checkout PhantomJS and Selenium
def get_prague_race_comments_and_sorry_count(soup_t):
    #comments_string=list(soup_t.find('div',{'class': 'cc-commentlink'}).strings)[0]
    #comment_num=int(comments_string.split()[0])
    news_text="\n".join(list(clean_find(soup_t,['div',{'class': 'cc-newsbody'}]).strings))
    sorry_count=news_text.lower().count("sorry")
    return(sorry_count)
    
# The arguments to `soup.find()` that will return the element with SMBC's previous button
prague_race_prev_comic_args=['a',{'rel': 'prev'}]
# The filename we want to save to
prague_race_filename="/Users/zburchill/Desktop/praguerace_dates_threaded.csv"



# ---------------------------- Broodhollow example code --------------------------------------#

# The argument to `soup.find()` that will return the element with Broodhollow's previous button
# Yes, the argument can be a function
def brood_is_prev_comic(x):
    try: 
        answer = x.name == "a" and "navi-prev" in x["class"]
        return(answer)
    except: return(False)


# Gets whether element is a title or not
def brood_is_title(x):
    try: 
        answer = x["class"]==["post-title"]
        return(answer)
    except: return(False)

# If 'cadavre' is in the title, it's a cadavre comic
def get_cadavre_bool(soup_t):
    title_text = list(soup_t.find(brood_is_title).strings)[0]
    is_cadavre="cadavre" in title_text or "Cadavre" in title_text
    return(str(is_cadavre))
    
# This is a wrapper function for `worker()` that is specific to Broodhollow
def broodhollow_worker():
    date_format="%B %d, %Y" # the format of smbc's time_stamp
    time_args=['span', {'class': 'post-date'}] # the html element with the time_stamp
    worker(time_args, get_cadavre_bool, date_format)

# The prev comic argument for broodhollow
broodhollow_prev_comic_args=brood_is_prev_comic
# The filename we want to save to
broodhollow_filename="/Users/zburchill/Desktop/broodhollow_dates_threaded.csv"




# ----------------------- The thread queue and web scraping code ------------------------------------------- #

# Remember to the `target` to whatever `worker()` wrapper you come up with!
# Create the queue and thread pool.
q = Queue()
for i in range(100): #IDK, i just picked that many threads. YOU should do it more principled?
    #t = threading.Thread(target=smbc_worker) # change this to what you make
    t = threading.Thread(target=prague_race_worker) # change this to what you make
    t.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
    t.start()

# My crappy web-scraping code. The main loop just loads pages and puts them on the queue.
# The queue's job is to basically do stuff with that. In my case, I *think* it makes sense
# to use threading--while the loop is loading the pages, the threads are loading the images, 
# instead of doing those sequentially.
def web_scrape(url,prev_comic_args):
    # reads the url
    r = urllib.request.urlopen(url).read()
    # turns the page into a soup object
    soup = BeautifulSoup(r)
    
    counter=0
    prev_url=""
    
    while True:
        if (counter % 100 == 0):
            print("Finished "+str(counter) + " pages")
        # adds the page to the queue
        q_item=soup
        q.put(q_item)
        try:
            prev_comic_soup = clean_find(soup,prev_comic_args)
            # if it starts a loop, kill it
            if prev_comic_soup["href"]==prev_url:
                break
            # get the previous page and soupify it
            r = urllib.request.urlopen(prev_comic_soup["href"]).read()
            soup = BeautifulSoup(r)
            prev_url=prev_comic_soup["href"]
            counter+=1
        except Exception as errorm:
            print(str(errorm))
            print(prev_url)
            break
    
start = time.perf_counter() 
#web_scrape('http://www.smbc-comics.com/', smbc_prev_comic_args)
#web_scrape('http://www.broodhollow.chainsawsuit.com/', broodhollow_prev_comic_args)
web_scrape('http://www.praguerace.com', prague_race_prev_comic_args)

q.join()       # block until all tasks are done

with open(prague_race_filename,"w") as f:
    f.write(csv_string)    
print(len(csv_string.splitlines()))
