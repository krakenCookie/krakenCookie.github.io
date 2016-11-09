---
layout:  post
title: "Sample Post"
comments:  true
published:  true
author: "Homer White"
date: 2015-12-12 20:00:00
categories: [R]
output:
  html_document:
    mathjax:  default
    fig_caption:  true
---





This is an R Markdown document. Markdown is a simple formatting syntax for authoring HTML, PDF, and MS Word documents. For more details on using R Markdown see <http://rmarkdown.rstudio.com>.

When you click the **Knit** button a document will be generated that includes both content as well as the output of any embedded R code chunks within the document. You can embed an R code chunk like this:



{% highlight r %}
summary(cars) %>% names()
{% endhighlight %}



{% highlight text %}
## NULL
{% endhighlight %}

You can also embed plots, for example: 


![plot of chunk unnamed-chunk-3](/figure/source/2015-12-12-sample-post/unnamed-chunk-3-1.png)

<p class = "figcaption">Here is a plot for you.</p>

The border around the graph above is due to custom CSS for this site (see `public/css/custom.css`).  The caption was produced with some HTML:

> `<p class = "figcaption">Here is a plot for you.</p>`

You can write mathematics, of course, but the syntax will be a bit different from R Mardown.  Here's some inline math:  $$ \pi/2 \approx 1.57 $$.  There is displayed math as well:

$$ \sum_{i=1}^{n} i = \frac{n(n+1)}{2}.$$

Here's the source so you can see how the above worked:


{% highlight r %}
You can write mathematics, of course, but the syntax will be a bit different from R Markdown.  Here's some inline math:  $$ \pi/2 \approx 1.57 $$.  There is displayed math as well:

$$ \sum_{i=1}^{n} i = \frac{n(n+1)}{2}.$$

Here's the source ...
{% endhighlight %}

Happy blogging.

I like learning statistical modeling. I like webcomics.  I 

It started with the thought: "Can I use statistical modelling to tell me when I should stop hoping a webcomic will keep updating?"  There are few feelings worse than returning to a comic week after week in the vain hope its creator will start releasing new strips again.

And while that model is still in the works, I've gotten my hands on a bunch of cool data in the meantime.

## Web scraping

In order to make a model, you generally need data to train it on.  Most webcomics don't have a downloadable R database of all their updates, so you'll have to get the data yourself.  You can click through potentially thousands of pages, recording the dates manually, or you can use **web scraping** to do it automatically.

If you use Python and want an incredibly easy-to-get-into web scraping tool, check out the Python module, [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/) (I used `bs4`). In a nutshell, it loads HTML pages and parses the elements into a tree automatically. Extracting, say, all the `img` tags on a page can be as simple as: `soup.find_all('img')`. Beautiful Soup is pretty simple to learn and the [documentation](http://www.crummy.com/software/BeautifulSoup/bs4/doc/) makes it a breeze. 

## Data

## Broodhollow updates: a story of an author's life

"Broodhollow."  The name sounds like a title that a moody fifteen-year-old would come up with, but it is **absolutely** my favorite webcomic. _**Ever.**_ The art is beautiful and the story writing is some of the best I've ever read. One part comedy and two parts creeping horror, if author [Kris Straub](http://studios.chainsawsuit.com/) can finish the comic with a _tenth_ of the talent he's exhibited so far, I'm confident this will go down as one of the great graphic novels of our generation.

![test text](/Users/zburchill/Desktop/broodhollow_snippet.png "markdown alt test")


{% highlight text %}
## Error in rasterGrob(image, x = x, y = y, width = width, height = height, : object 'img' not found
{% endhighlight %}

<p class = "figcaption">A sample of Kris Staub's genius.</p>
 
That is, _if_ he can finish it.  Kris is 

## Notes on my code:
