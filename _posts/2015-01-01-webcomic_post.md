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

"Broodhollow."  The name sounds like a title that a moody fifteen-year-old would come up with, but it is **absolutely** my favorite webcomic. _**Ever.**_ The art is beautiful and the story writing is some of the best I've ever read. One part comedy and two parts creeping horror, if the phrase "Tintin meets H.P. Lovecraft" appeals to you at all, [go read it right now](http://broodhollow.chainsawsuit.com/). If author Kris Straub can finish the comic with a _tenth_ of the talent he's exhibited so far, I'm confident this will go down as one of the great graphic novels of our generation.

![plot of chunk broodhollow_snippet](/figure/source/2015-01-01-webcomic_post/broodhollow_snippet-1.png)

<p class = "figcaption">A sample of Kris Staub's genius.</p>
 
That is, _if_ he can finish it. Kris is a [pretty prolific artist](http://studios.chainsawsuit.com/) and just had a child a couple of years ago.  While he's continued regular updates to his non-serial comedic strip, [Chainsawsuit](http://chainsawsuit.com/) (another one of my favorites, actually), Broodhollow has gone through a few hiatuses.

![plot of chunk broodhollow_graph](/figure/source/2015-01-01-webcomic_post/broodhollow_graph-1.png)

<p class = "figcaption">'Cadavre' comics are non-serial humorous strips about the daily life of a French-accented skeleton, generally consider 'filler' material.</p>

I like this graph because it visually tells the story of the evolving involvement of the author with the comic. **Book I** of Broodhollow, "Curious Little Thing", has _very_ consistent updates, as evidenced by the tight line of updates.  **Book II**, "Angleworm", continues after a short rest, and updates are still _fairly_ regular, although you see there's definitely more variability. But then, BAM!  As they say, [a baby changes everything](https://www.youtube.com/watch?v=-y0_wNPSOaw&t=1m20s). After a long hiatus, *Book III* teeters to a start, with sporadic updates and lots of filler material.





## Notes on my code:


