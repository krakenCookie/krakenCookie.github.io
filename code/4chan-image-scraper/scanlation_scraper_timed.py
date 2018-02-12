'''
Created on Feb 1, 2018

@author: zburchill
'''

import urllib.parse
import os, re, sys
import io
import datetime, time
from collections import Iterable
# I touch on these a little more in the blog post:
import warnings, logging, argparse, json
from functools import partial

# for threading
import threading
from queue import Queue

#--------- These are the non-standard libraries ---------#
from bs4 import BeautifulSoup # https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-beautiful-soup
from PIL import Image  # Use "Pillow"! http://pillow.readthedocs.io/en/latest/installation.html
import requests # http://docs.python-requests.org/en/latest/user/install/#install


# Sets the version number of this software, useful for debugging
global version_number 
version_number = "0.9"

MAIN_DATA_FILE = "archive_information" # sans the extension
SECONDARY_DATA_FILE = "data.txt"
DEFAULT_ARCHIVE_URL = "http://boards.4chan.org/a/archive"
READABLE_THREAD_FILE = "human_readable_data.html"

# A custom exception so that I know when a page failed to load or image failed to `Image.save()`
class PageScrapeException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self,*args,**kwargs)

# --------------------------- Helper functions and utility functions -----------------------------#
# If you want to save or load anything
def save_json(obj, name):
    with open(name + '.json', 'w') as outfile:
        json.dump(obj, outfile)
def load_json(name):
    with open(name + '.json') as infile:
        return(json.load(infile))
def save_dict(d, name):
    save_json(d, name)    

# Flattens lists (a hybrid monster of a function)
def flatten_list(seq):
    if isinstance(seq, Iterable) and not isinstance(seq, (str, bytes)):
        l = []
        for elt in seq:
            t = type(elt)
            if t is tuple or t is list:
                for elt2 in flatten_list(elt):
                    l.append(elt2)
            else:
                l.append(elt)
        return l
    else:
        return(seq)
    
# Just to try to reduce any filenaming issues
def filename_cleaner(s):
    """ Turns whitespaces into underscores and only keeps them and alphanumeric chars. """
    return(re.sub('[^0-9a-zA-Z_]+','',
                      re.sub("\s","_",s)))
    
# Could be written with much less code, but I wanted to keep it readable for newbies
# This gives each image a unique file name so they don't overwrite each other
def unique_filenames(file_names, urls):
    # If each name is unique, don't worry
    if len(set(file_names)) == len(file_names):
        return(file_names)
    else:
        # Otherwise, just add part of the images' urls (which by definition are unique) to the old name
        url_ids = [os.path.splitext(os.path.basename(e))[0] for e in urls]
        name_and_extensions = [os.path.splitext(e) for e in file_names]
        saved_names = [n[0]+"_"+u+n[1] for n, u in zip(name_and_extensions,url_ids)]
        return(saved_names)
    
# Instead of using custom classes/objects to bundle information about pages and images,
# I just use dictionaries as key-value info holders.
# These two functions below take information about archived threads and images, respectively, and make dicts out of them
def make_archive_thread_data_dict(soup_element, re_obj, url, thread_id):
    title = "".join(list(soup_element.strings))
    match_object = re_obj.search(title)
    d = {'title': title, 'match_object': match_object, 'url': url, 'thread_id':thread_id}
    return(d)
def make_image_meta_data_dict(url, image_name, post, post_number, saved_name):
    d = {'url': url, 'image_name': image_name, 'post': post, 'post_number': post_number, 'saved_name': saved_name}
    return(d)   

# This is a function that tries to get a response from a url, trying to do so `n_attempts` number of times
def try_to_urlopen(url_t, timeout_sec=30, n_attempts=2, new_header=False, safer=False, **kwargs):
    """ This function tries to retrieve a url with `requests.get` a specified number of times for specified lengths of time,
    and uses a customized header if it gets a 403 error. """
    attempts = 0
    # I have an option for when you think the URL might be really wonky. Doesn't really happen with 4chan
    if safer:
        url_t=urllib.parse.quote(url_t,safe=":/")
    while attempts <= n_attempts:
        try:
            if new_header:
                custom_header={'User-Agent': 'Mozilla/5.0'}
                r = requests.get(url_t, timeout=timeout_sec, headers=custom_header, **kwargs)
                # check to see what the status was
                r.raise_for_status()
                break
            else:
                r = requests.get(url_t, timeout=timeout_sec, **kwargs)
                # check to see if the status sucked
                r.raise_for_status()
                break
        except requests.exceptions.HTTPError as err:
            # If you get a 'forbidden' (403) error, sometimes its because they can tell you're using a Python "browser"
            if err.response.status_code == 403:
                # If you get that error, you can generally avoid it by changing your headers
                if new_header:
                    raise requests.exceptions.HTTPError("Modifying the header for '{url!s}' couldn't fix 403 problem: {error!s}".format(url=url_t, error=err))
                else: new_header = True
            else:
                raise
        except requests.exceptions.Timeout:
            attempts += 1
            warning_string = "Url '{url!s}' timed out. {n!s} tries until skipping".format(url=url_t, n=n_attempts-attempts)
            logging.warning(warning_string)
    if attempts == n_attempts:
        raise requests.exceptions.Timeout("URL '{url!s}' timed out {n!s} times, at {sec!s} sec. each try.".format(url=url_t, n=n_attempts, sec=timeout_sec))
    return(r)
     
# Because when closing my laptop stops the the `time.sleep()` counter,
#   if I were to set it to sleep for a day, then immediately close my laptop for a day,
#   when I open it, it would keep sleeping for an entire extra day. This balances that problem
#   with CPU intensiveness by breaking down the sleep time into ten chunks and checking to see 
#   if it has gone past the time it was aiming for at each chunk
def wait_for(minutes_to_sleep, subdivide_time_by=10):
    """ A way of doing something similar to `time.sleep()` but one that plays better with closing your laptop occasionally """
    logging.info("Entering sleep mode for {!s} minutes".format(minutes_to_sleep))
    current_time = datetime.datetime.now()
    working_time = current_time
    time_delta = datetime.timedelta(minutes=minutes_to_sleep)
    check_time = current_time + time_delta
    # So you don't oversleep too much, check to see if you've gone past 
    #   the right time every 10th of what you're waiting for
    fraction_of_total_sleep_time = time_delta.seconds / subdivide_time_by
    while datetime.datetime.now() < check_time:
        time.sleep(fraction_of_total_sleep_time)
        logging.debug("Turning in sleep. Expected time - real time = {!s} seconds".format(
            (working_time + datetime.timedelta(seconds=fraction_of_total_sleep_time) -
            datetime.datetime.now()).seconds))
        working_time = datetime.datetime.now()
    logging.info("Exiting sleep mode. Expected to sleep for {!s} minutes, but slept for {!s} minutes".format(minutes_to_sleep, (datetime.datetime.now() - check_time).minutes))
    

# --------------------------------- Beautiful soup-based functions ----------------------------------------- #
# Request url and turn it into a bs4 object
def soupify(url_t, safer=False, **kwargs):
    """ Returns a bs4 soup object from a url """
    response_for_url = try_to_urlopen(url_t, safer=safer, **kwargs)
    soup = BeautifulSoup(response_for_url.text)
    # turns the page into a soup object
    return(soup)

# So, you can also pass a FUNCTION as an argument to `soup.find()` to search the tree
# This function just makes it so that it puts the arguments in `soup.find()` in the right way
# Don't fret about this too much if you aren't familiar with bs4
def clean_find(soup_t, args):
    """ Does `bs4.BeautifulSoup.find()`, but if the argument is a non-function variable, it unpacks the arguments """
    # for Python 3.x but before 3.2, use: `if hasattr(args, '__call__'):`
    if callable(args):
        return(soup_t.find(args))
    else:
        return(soup_t.find(*args))
    
# the 'soup.find_all' version of 'clean_find'
def clean_find_all(soup_t,args):
    """ Does the same thing as `clean_find()`, but for `bs4.BeautifulSoup.find_all()` """
    # for Python 3.x but before 3.2, use: `if hasattr(args, '__call__'):`
    if callable(args):
        return(soup_t.find_all(args))
    else:
        return(soup_t.find_all(*args))

# --------------------------- Functions that are more "4chan-specific" -----------------------------#

# To be used with 'partial()'
# This searches the main archive page's HTML elements for a title that matches the re object
def archived_threads_with_regex_match(re_obj, tag):
    """ Checks if a BeautifulSoup element is "<td class='teaser-col' ...>" 
    (i.e., the element on 4chan's archive page that holds the thread's title) 
    and then checks if it matches a regular expression.
      To be used with `clean_find()`, it needs to be used in a partial function with 
    the regular expression already supplied. """
    try:
        # Gets 'td' elements with `class='teaser-col'` that have text that matches the search string
        if tag.name == "td" and tag["class"] == ["teaser-col"] and re_obj.search("".join(list(tag.strings))):
            return(True)
        else: return(False)
    except: return(False)
    
# The 4chan-specific way of getting certain elements elements
def get_archived_thread_url_fragment(soup_element):
    """ Returns the url from the HTML element of an archived thread on the archive page """ 
    return(soup_element.next_sibling.a['href'])
def get_archived_thread_id(soup_element):
    """ Returns the thread ID from the HTML element of an archived thread on the archive page """ 
    return(soup_element.previous_sibling.string)
# Given a soup element (specifically, the image's HTML element), this gets the image name
def get_image_names(soup_element):
    """ Returns the image name from the HTML element used in downloading images on a thread """ 
    if soup_element.previous_sibling.a.has_attr('title'):
        return(soup_element.previous_sibling.a['title'])
    # Spoiler images are treated differently on 4chan
    elif soup_element.parent.a.string == "Spoiler Image":
        return(soup_element.previous_sibling['title'])
    else: 
        return("".join(list(soup_element.previous_sibling.a.strings))) 
    
# This function searches the archive page for the titles
def regex_archive(re_obj, archive_url):
    """ Returns a list of dictionaries that contain information about the threads whose titles match `re_obj` """
    archive_soup = soupify(archive_url)
    # makes a function that can be used with soup.find()
    search_func = partial(archived_threads_with_regex_match, re_obj)
    matched_threads = clean_find_all(archive_soup, search_func)
    matched_urls = [urllib.parse.urljoin(archive_url, get_archived_thread_url_fragment(e)) for e in matched_threads]
    thread_ids = [get_archived_thread_id(e) for e in matched_threads]
    # Bundles all the information for each thread together into a list of dictionaries
    meta_data = [make_archive_thread_data_dict(soup_e, re_obj, url_e, id_e) for soup_e, url_e, id_e in zip(matched_threads, matched_urls, thread_ids)]
    return(meta_data)
    
# Scrapes an archived thread on 4chan for images
def scrape_page_fourchan(page_url):
    page_soup = soupify(page_url)
    image_link_elements = page_soup.find_all('a',{'class': 'fileThumb'})
    urls=[urllib.parse.urljoin(page_url, e['href']) for e in image_link_elements]
    # Relatively complex due to the way 4chan puts distributes its information about spoiler images
    image_names=[get_image_names(e) for e in image_link_elements]
    post_number=[e.parent.parent.blockquote['id'][1:] for e in image_link_elements]
    posts  =    [e.parent.parent.blockquote.prettify() for e in image_link_elements]
    saved_names = unique_filenames(image_names, urls) 
    return([make_image_meta_data_dict(*e) for e in zip(urls, image_names, posts, post_number, saved_names)])

# The worker thread pulls an item from the queue and processes it
def worker():
    while True:
        directory, image_data = q.get()
        # Changes the name of the thread to the image url being downloaded (for debugging/logging purposes)
        curr_thread = threading.current_thread()
        curr_thread.name = str(directory)+" "+str(image_data['url'])
        try:
            load_and_save_image(directory, image_data)
        # If it encounters this custom exception, we know I've already handled the error
        except PageScrapeException:
            q.task_done()
            pass
        except Exception:
            q.task_done()
            # Log any errors
            warning_vals={'name': image_data['image_name'], 'dir': directory}
            logging.exception("Exception for the image '{name!s}' in '{dir!s} happened before `PIL.Image.save()`".format(**warning_vals))
            warnings.warn("Image failed to save. '{name!s}' in {dir!s}. (Probably failed to load)".format(**warning_vals), category=Warning)
        else:
            q.task_done()

# The thread that loads and saves an image
def load_and_save_image(output_dir, image_data):
    """ Tries to open and save an image """
    image_file_response = try_to_urlopen(urllib.parse.quote(image_data['url'], safe=":/"))
    image_file = io.BytesIO(image_file_response.content)
    image_file.seek(0)
    im = Image.open(image_file)
    try:
        im.save(os.path.join(output_dir, image_data['saved_name']))
    except Exception:
        error_string = "{!s} ({!s} failed to save as {!s}".format(image_data['image_name'], image_data['url'], os.path.join(output_dir, image_data['saved_name']))
        logging.exception(error_string)
        warnings.warn("-----------------\n" + error_string, category=Warning)
        raise PageScrapeException(error_string)
    pass
    
# Changes how the folders are named. 
# "Title" means that each folder is named based of the thread's title
# "Match" means that each folder is named starting with the regex search string that found it
# The user should feel free to add their own naming schemes if they want
def dir_namer(thread_meta_data, naming_scheme):
    if naming_scheme == "title":
        return(filename_cleaner(thread_meta_data["title"]) + "_" + thread_meta_data["thread_id"])
    elif naming_scheme == "match":
        return(filename_cleaner("".join(thread_meta_data["match_object"].groups)) + "_" + thread_meta_data["thread_id"])
    else:
        raise AssertionError("Naming scheme: `"+str(naming_scheme)+"`not known!")
    
# This downloads all the files and makes the directory given a particular 4chan thread
def make_new_thread_dir(top_level_dir, thread_meta_data, naming_scheme):
    """ Makes and populates the directory for a particular thread """
    # Makes the thread's new name
    new_dir_name = dir_namer(thread_meta_data, naming_scheme)
    # For making the human readable html file
    big_formatter="<html><head><title>{0}</title></head><body><p>{1}</p><hr />{2}</body></html>"
    # High-level information
    top_info = [str(datetime.date.today()),
                "version: "+version_number,
                thread_meta_data['title'], 
                thread_meta_data['url'], 
                "Matched via: `" + str(thread_meta_data['match_object'].re) +"`",
                "Thread No.: " + thread_meta_data['thread_id']]
    html_top_info="<br />".join(top_info)
    txt_top_info="\n".join(top_info)
    # No error handling HERE, baby! 
    os.mkdir(os.path.join(top_level_dir, new_dir_name))
    # Make the Images folder
    os.mkdir(os.path.join(top_level_dir, new_dir_name, "Images"))
    # Try to get the html for the image posts
    try: post_html_list = save_images(os.path.join(top_level_dir, new_dir_name, "Images"), thread_meta_data['url'])
    except Exception as errorm:
        raise PageScrapeException("'{!s}' encountered an issue loading the images and is being skipped.".format(new_dir_name)) from errorm
        
    html_s = big_formatter.format(thread_meta_data['title'], html_top_info, "\n".join(post_html_list))
    # Write the readable thread file
    with open(os.path.join(top_level_dir, new_dir_name, READABLE_THREAD_FILE), "w", encoding="utf-8") as f:
        f.write(html_s)
    # Write the metadata file
    with open(os.path.join(top_level_dir, new_dir_name, SECONDARY_DATA_FILE), "w", encoding="utf-8") as f:
        f.write(txt_top_info)
    return(0)
    
# Saves the images in the thread and returns the HTML of the text of each image post
def save_images(out_dir, page_url):
    """ From a page url, it attempts to get all the image information from that url and archive/save them """
    image_data = scrape_page_fourchan(page_url)
    string_list = []
    post_formatter="<p><b>{0}</b>  {1}<br /><img src='{2}' /><br />{3}</p>"
    
    for image_datum in image_data:
        # Add the image loader to the queue
        # Currently does not load webm's
        if ".webm" in os.path.splitext(image_datum["saved_name"])[1]:
            warning_string="The file format for `{saved_name!s}` in {dir!s} is not supported for download. Skipping.".format(dir=out_dir,**image_datum)
            warnings.warn(warning_string, category=Warning)
            logging.warning(warning_string)
        elif ".gif" in os.path.splitext(image_datum["saved_name"])[1]:
            warning_string="Currently, only the first frame of .gif files are ever loaded. `{saved_name}` in {dir!s} is thus static".format(dir=out_dir,**image_datum)
            warnings.warn(warning_string, category=Warning)
            logging.warning(warning_string)
        else:
            q.put((out_dir, image_datum))
        string_list += [post_formatter.format(os.path.splitext(image_datum["image_name"])[0],
                                             image_datum["post_number"],
                                             os.path.join(out_dir, image_datum["saved_name"]),
                                             image_datum["post"])]
    return(string_list)
                
def check_fourchan(archive_url, re_obj, top_level_dir):
    """ For a re.compiled search pattern, it gets all the titles that match and tries to save the new ones """
    saved_thread_ids = get_saved_thread_data(top_level_dir)['thread_ids']
    archived_thread_data = regex_archive(re_obj, archive_url)
    threads_to_archive = [e for e in archived_thread_data if e['thread_id'] not in saved_thread_ids]
    return(threads_to_archive)

# Basically, it just saves the json material for each new thread and tries to make it
def scrape_new_threads(top_level_dir, threads_to_archive, naming_scheme):
    """ Goes through each thread to scrape/archive and does that """
    logging.debug("Found these threads to scrape:")
    for t in threads_to_archive:
        logging.debug("Title: {title!s} ID: {thread_id!s}".format(**t))
    # Get the old thread ids
    saved_thread_data = get_saved_thread_data(top_level_dir)
    # Save them just in case    
    save_dict(saved_thread_data, os.path.join(top_level_dir, MAIN_DATA_FILE))
    saved_thread_ids = saved_thread_data["thread_ids"]
    for thread_to_archive in threads_to_archive:
        print("Making new thread: "+thread_to_archive["title"])
        try:
            make_new_thread_dir(top_level_dir, thread_to_archive, naming_scheme)
        except PageScrapeException:
            warning_string="Thread '%s' (%s):" % (thread_to_archive['title'],thread_to_archive['thread_id']) 
            logging.exception(warning_string) 
            warnings.warn(warning_string, category=Warning)
        except FileExistsError:
            raise
        except Exception as err:
            warning_string="Thread '%s' (%s) encountered an unexpected issue and did not properly load: %s" % (thread_to_archive['title'], thread_to_archive['thread_id'], err) 
            logging.exception(warning_string.encode('utf-8')) 
            warnings.warn(warning_string, category=Warning)
        else:
            saved_thread_ids += [thread_to_archive["thread_id"]]
            saved_thread_data["thread_ids"] = saved_thread_ids
            save_json(saved_thread_data, os.path.join(top_level_dir, MAIN_DATA_FILE))     
    return(0)  

# -------------------------- Functions that deal with managing information that was already saved ----------------------- #
# If you accidentally delete the main data file, this will try to rebuild it
def rebuild_saved_information(top_level_dir):
    """ Tries to collect what thread IDs have already been saved in case the .json file with that info was accidentally deleted """
    subdirectories = [os.path.join(top_level_dir, e) for e in os.listdir(top_level_dir) if os.path.isdir(os.path.join(top_level_dir, e))]
    data_files = [os.path.join(e, SECONDARY_DATA_FILE) for e in subdirectories if os.path.exists(os.path.join(e, SECONDARY_DATA_FILE))]
    thread_IDs=[]
    for data_file in data_files:
        with open(data_file, "r", encoding="utf-8") as f:
            data_text=f.read()
            thread_num_match = re.search("(?<=Thread\ No\.\:\ )[0-9]{9}", data_text)
            thread_IDs+=[thread_num_match.group(0)]
    if not thread_IDs:
        logging.warning("No main data file detected, and cannot be recovered from current directory.")
        warnings.warn("No main data file detected, and cannot be recovered from current directory.", category=Warning)
    return({"thread_ids": thread_IDs})

# Currently, the only data that's being saved are the thread ids, but I made the object being saved a dictionary so it 
#  can be expanded in the future to include more metadata if need-be
def get_saved_thread_data(top_level_dir):
    """ Gets the data about which threads have already been saved. If there isn't a .json file, it tries to build a new one """
    # Make sure the top-level directory exists
    if not os.path.isdir(top_level_dir):
        raise FileNotFoundError("The top-level directory, `{0}`, doesn't appear to exist.".format(top_level_dir))
    try:
        saved_data = load_json(os.path.join(top_level_dir, MAIN_DATA_FILE))
    except FileNotFoundError:
        logging.debug("{!s} not found".format(os.path.join(top_level_dir, MAIN_DATA_FILE)))
        saved_data = rebuild_saved_information(top_level_dir)
    return(saved_data)
   
# --------------------------- Argument-parsing functions  -----------------------------#
# Gets all the possible patterns from a list of their names
def get_cl_pattern_args(arg_obj, pattern_arg_names):
    """ Returns a flat list of patterns from all the possible args that could have patterns in them """
    l=[]
    # I HATED writing this code, do the the `flatten_list()` function never quite doing the right thing
    for arg_name in pattern_arg_names:
        if hasattr(arg_obj, arg_name) and getattr(arg_obj, arg_name):
            pattern_obj = getattr(arg_obj, arg_name)
            flattened_obj = flatten_list(pattern_obj)
            if isinstance(flattened_obj, Iterable) and not isinstance(flattened_obj, (str, bytes)):
                l += list(flattened_obj)
            else: l += [flattened_obj]
    l=[e for e in l if e]
    if not l: raise AttributeError("No patterns found in arguments!")
    return(l)
# Read the patterns from a files
def get_patterns_from_file(file_name):
    with(file_name, "r") as f:
        lines=f.read().splitlines()
    return([e for e in lines if e])
# Turn the pattern into a re obj
def re_compile_pattern(pattern, ignore_case, regexp):
    if not regexp:
        pattern=re.escape(pattern)
    if ignore_case: return(re.compile(pattern, flags=re.IGNORECASE))
    else: return(re.compile(pattern))

# Examples:
# python3 scanlation_scraper_timed.py ~/Pictures/Archived/ "tsure[zd]+ure|woop woop" -i --wait 360 --log-level INFO
# python3 scanlation_scraper_timed.py ~/Pictures/Archived/ -e "tsure[zd]+ure|woop woop" -i -w --log-level INFO -e "pop team"
# python3 scanlation_scraper_timed.py ~/Pictures/Archived/ -a "Tsure[zd]+ure|Woop woop" "Pop Team" -c -w --naming-scheme match

def main():  
    # --------------------------- Argument-parsing  --------------------------------------------#
    arg_parser = argparse.ArgumentParser(add_help=False, )
    
    arg_parser.add_argument("top_level_dir", metavar="path",
                            help="Directory storing image threads. Must already exist.")
    arg_parser.add_argument("pattern", metavar="pattern", 
                            help = "(By default, a regexp pattern.)\n\nUsed to match the titles of archived threads you want to scrape.")
    
    re_choices = arg_parser.add_argument_group(title="Search options")
    re_choices.add_argument("-e", dest="extra_patterns", metavar="<pattern>", action='append',
                            help = "Specify multiple additional pattern(s) (i.e., `grep -e`).")
    re_choices.add_argument("-f", "--pattern-file", dest="pattern_file",  metavar="<file>", type=argparse.FileType('r'), 
                            help="Path to file of line-separated patterns, no quotes.")
    re_choices.add_argument("-a", dest="multi_patterns", metavar="<patterns>", action='append', nargs="+",
                            help = "Like -e, but takes any number of other additional patterns. (Each pattern should be in quotes.)")
    
    cap_cases = re_choices.add_mutually_exclusive_group()
    cap_cases.add_argument("-i", "--ignore-case", dest="ignore_case", action='store_true', 
                           help="Title search ignores case (default).")
    cap_cases.add_argument("-c", "--case-sensitive", dest="ignore_case", action='store_false', 
                           help="Make title search case sensitive.")
    
    regexp_cases = re_choices.add_mutually_exclusive_group()
    regexp_cases.add_argument("--regexp", dest="regexp", action='store_true', default=True,
                            help="Make patterns regexps (default).")
    regexp_cases.add_argument("--no-regexp", dest="regexp", action='store_false',
                            help="Make patterns non-regexp strings.")
                     
    optional_args = arg_parser.add_argument_group(title="Optional arguments")
    optional_args.add_argument("-h", "--help", action="help", 
                               help="show this help message and exit")
    optional_args.add_argument("-w", "--wait", metavar="<minutes>", type=int, nargs="?", const=720,
                               help="Minutes to wait before re-checking for new archived threads. By default, waits 12 hours.\nWithout this argument, the scraping will only run once (e.g., because you're using `cron` to schedule it).")
    optional_args.add_argument("--naming-scheme", dest="naming_scheme", choices=["title","match"], default="title",                                
                               help="How to name the subdirectories. By default, names by thread title. 'match' will name by search pattern used to match title (i.e., a pattern relating to the series' name)")
    optional_args.add_argument("--log-level", dest="log_level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="WARN",
                               help="Sets threshold of logging output via `logging.setLevel()`")
    optional_args.add_argument("--url", metavar="<url>", default=DEFAULT_ARCHIVE_URL,
                               help="The url of the archive page you want to scrape. By default, 'http://boards.4chan.org/a/archive'. Don't change unless you've edited the code or are scraping a 4chan clone.")
    
    args = arg_parser.parse_args()
    
    # ------------------------------------------- Start assigning variables ----------------------------- #
    top_level_dir = args.top_level_dir
    archive_url = args.url
    naming_scheme = args.naming_scheme
    if args.wait: minutes_to_sleep = args.wait  # should be adjusted to whatever the half-life of archived threads is on 4chan
    else: minutes_to_sleep = None
    # I don't want people checking too frequently. It's intended use.
    if minutes_to_sleep and minutes_to_sleep < 10:
        raise ValueError("Minimum sleep time between checks for new threads must be > 10 minutes. (Set at {!s})".format(minutes_to_sleep))
    # Get the title patterns from the command line arguments and from files and re.compile them
    patterns = get_cl_pattern_args(args, ["pattern", "extra_patterns", "multi_patterns"])
    if args.pattern_file:
        patterns += get_patterns_from_file(args.pattern_file)
    re_patterns = [re_compile_pattern(e, args.ignore_case, args.regexp) for e in patterns]

    # ----------------------- Start logging ------------------------ #
    # Logging stuff. Right now there's only a single main log
    logging.basicConfig(filename = urllib.parse.urljoin(top_level_dir, "main.log"), 
                    level=getattr(logging, args.log_level), format='%(asctime)s -- %(threadName)s %(levelname)s %(message)s')
    log_header = "# {:-^80s} #"
    logging.info(log_header.format("Starting up"))
    logging.info("Arguments: ({!s})".format(args))
    
    # ----------------------- Start thread stuff ------------------------ #
    # Remember to the `target` to whatever `worker()` wrapper you come up with!
    # Create the queue and thread pool.
    global q
    q = Queue()
    for i in range(100): #IDK, i just picked that many threads. YOU should do it more principled?
        t = threading.Thread(target=worker) # change this to what you make
        t.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
        t.start()
        
    # ----------------------- Start running for real ------------------------ #
    for re_obj in re_patterns:
        new_threads = check_fourchan(archive_url, re_obj, top_level_dir)
        scrape_new_threads(top_level_dir, new_threads, naming_scheme)
    print("Scraping session complete")
    while not q.empty():
        print("Please wait while the {!s} remaining images are downloading.".format(threading.active_count()))
        time.sleep(30)
    q.join()
    logging.info("Scraping session complete")
    logging.info("Scraped for matches of: ({!s})".format(patterns))
    
    if minutes_to_sleep:
        wait_for(minutes_to_sleep)
        for re_obj in re_patterns:
            new_threads = check_fourchan(archive_url, re_obj, top_level_dir)
            scrape_new_threads(top_level_dir, new_threads, naming_scheme)
        print("Scraping session complete")
        logging.info(log_header.format("Scraping session complete"))
        logging.info("Scraped for matches of: ({!s})".format(patterns))
        while not q.empty():
            print("Please wait while the {!s} remaining images are downloading.".format(threading.active_count()))
            time.sleep(30)
            
    q.join()       # block until all tasks are done
    print("Shutting down")
    logging.info(log_header.format("Shutting down"))
    
  
if __name__ == "__main__":
    req_version = (3, 3)
    cur_version = sys.version_info
    if cur_version >= req_version:
        main()
    else:
        raise SystemError("Your Python interpreter is too old. You have {!s}.{!s} but you need 3.3+ or higher. Please consider upgrading.".format(cur_version[0], cur_version[1]))
    

