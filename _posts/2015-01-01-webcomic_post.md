---
layout:  post
title: "Web scraping and webcomics"
comments:  true
published:  true
author: "Zach Burchill"
date: 2015-12-12 20:00:00
categories: ['web scraping',webcomics,python,threading,R]
output:
  html_document:
    mathjax:  default
    fig_caption:  true
---



I like learning statistical modeling. I like webcomics.  I 

It started with the thought: "Can I use statistical modelling to tell me when I should stop hoping a webcomic will keep updating?"  There are few feelings worse than returning to a comic week after week in the vain hope its creator will start releasing new strips again.

And while that model is still in the works, I've gotten my hands on a bunch of cool data in the meantime.

## Web scraping

In order to make a model, you generally need data to train it on.  Most webcomics don't have a downloadable R database of all their updates, so you'll have to get the data yourself.  You can click through potentially thousands of pages, recording the dates manually, or you can use **web scraping** to do it automatically.

If you use Python and want an incredibly easy-to-get-into web scraping tool, check out the Python module, [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/) (I used `bs4`). In a nutshell, it loads HTML pages and parses the elements into a tree automatically. Extracting, say, all the `img` tags on a page can be as simple as: `soup.find_all('img')`. Beautiful Soup is pretty simple to learn and the [documentation](http://www.crummy.com/software/BeautifulSoup/bs4/doc/) makes it a breeze. 

## Data

## Broodhollow updates: a story of an author's life

"Broodhollow."  The name sounds like a title that a moody fifteen-year-old would come up with, but it is **absolutely** my favorite webcomic. _**Ever.**_ _Broodhollow's_ art is beautiful and the story writing is some of the best I've ever read. One part comedy and two parts creeping horror, if the phrase "Tintin meets H.P. Lovecraft" appeals to you at all, [go read it right now](http://broodhollow.chainsawsuit.com/). If author Kris Straub can finish the comic with a _tenth_ of the talent he's exhibited so far, I'm confident this will go down as one of the great graphic novels of our generation.

![plot of chunk broodhollow_snippet](/figure/source/2015-01-01-webcomic_post/broodhollow_snippet-1.png)

<p class = "figcaption">A sample of Kris Staub's genius.</p>
 
That is, _if_ he can finish it. Kris is a [pretty prolific artist](http://studios.chainsawsuit.com/) and just had a child a couple of years ago.  While he's continued regular updates to his non-serial comedic strip, [Chainsawsuit](http://chainsawsuit.com/) (another one of my favorites, actually), Broodhollow has gone through a few hiatuses.

### The data

So let's actually look at how often _Broodhollow_ has been updating.

![plot of chunk broodhollow_graph](/figure/source/2015-01-01-webcomic_post/broodhollow_graph-1.png)

<p class = "figcaption">'Cadavre' comics are non-serial humorous strips about the daily life of a French-accented skeleton, generally consider filler material.</p>

I like this graph because it visually tells the story of the evolving involvement of the author with the comic. **Book I** of Broodhollow, "Curious Little Thing", has _very_ consistent updates, as evidenced by the tight line of updates.  **Book II**, "Angleworm", continues after a short rest, and updates are still _fairly_ regular, although you see there's definitely more variability. But then, BAM!  As they say, [a baby changes everything](https://www.youtube.com/watch?v=-y0_wNPSOaw&t=1m20s). After a long hiatus, *Book III* teeters to a start, with sporadic updates and lots of filler material.

To me, webcomics that fall into this pattern are the reason why I want a model to tell me if I should give up on them.  They keep toying with my hope that they will start updating like they were before.  But on the other hand, we can see that even though Book III updates less frequently, Kris hasn't forgotten about it. We'll need more data.

## SMBC: longer and more uncut

Unlike _Broodhollow_, _Saturday Morning Breakfast Cereal_ has no problems with regular updates. In a downright _freakish_ display of perseverance, _Saturday Morning Breakfast Cereal_ (or SMBC as its often known by) updates every. _Damn_. _**DAY**_.  [Zach Weinersmith](https://twitter.com/ZachWeiner) is a gangly, red-headed _beast_, and just by virtue of his update schedule, SMBC would remain one of my favorites.  

Early SMBC comics usually consisted of a single panel, and relied on a specific brand of humor to get laughs. To long-time readers of the comic, [my brother](https://twitter.com/andrewburchill) and I, it felt that a while ago Zach started doing longer and longer strips, which we joked got less and less funny.  So when I started collected data, my brother suggested that I collect data on how long his strips were at the same time. Were his strips _really_ getting longer, or was it just our imagination?

### The data

Combining the `Pillow` module for Python 3 with my web scraping code, I recorded the width and height of each of his comics.  Unlike many webcomics, I should add, SMBC generally is in "portrait" orientation, meaning that **the longer the comic, the taller the image**.

![plot of chunk smbc_graph](/figure/source/2015-01-01-webcomic_post/smbc_graph-1.png)

<p class = "figcaption">It would seem that around late 2008, (<a href="http://www.smbc-comics.com/comic/2008-08-10">August 10th by my reckoning</a>, marked on the graph) Zach started getting bored with one-panel comic strips.</p>

I was surprised by how quickly SMBC started coming out with longer comics after late 2008. Clearly, once Zach tasted the sweet, sweet taste of multi-panel comics, he couldn't let it go.

Now, for a little bit of humor only Zach Weinersmith could find funny:

![plot of chunk smbc_votey_graph](/figure/source/2015-01-01-webcomic_post/smbc_votey_graph-1.png)

<p class = "figcaption">Just kidding Zach, I know how much you appreciate graph jokes. Typical height of 1 panel $$ \approx $$ 500 px. If you want to make graphs that look like this in `ggplot`, you can with the... `xkcd` package in R.</p>

## Prague Race:

1 panel $$ \approx $$ 500 px.

## Source Code:

> `web_scraper_threaded_general.py`

 My multi-thread web-scraper, written for Python 3.4+, requires Beautiful Soup and Pillow. If you have `pip` you can try: `python3 pip install beautifulsoup4` and `python3 pip install pillow`.  This is my first time ever working with threads in Python. Probably overkill, but it was fun to learn about. If you have any comments about what I could do better--any rookie mistakes I made--feel free to leave a comment... Once I get around to adding a comment section.

> `web_scraper.py`

My crappier, non-threaded, web-scraper with poor documentation. Also written for Python 3.4+, requires Beautiful Soup and Pillow. This is the earlier, crappier version of my code for a few of the examples, more or less.

> `2015-01-01-webcomic_post.Rmd`

The R Markdown file this blog post is generated from.


