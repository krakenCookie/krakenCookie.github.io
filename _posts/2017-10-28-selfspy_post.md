---
layout:  post
title: "Optimizing Your Keyboard Layout"
comments:  true
published:  true
author: "Zach Burchill"
date: 2016-11-14 10:00:00
permalink: /selfspy.html
categories: ['mechanical keyboards',selfspy,analysis,'keyboard layout',R]
output:
  html_document:
    mathjax:  default
    fig_caption:  true
---





I've recently gotten into the fabulous world of [mechanical keyboards](https://www.reddit.com/r/MechanicalKeyboards/).  Other than the Ａｅｓｔｈｅｔｉｃｓ and the fact that building working electronics is cool, the main draw for me was the ability to _completely_ customize how your board works. Just imagine all the chances for increased ｐｒｏｄｕｃｔｉｖｉｔｙ!

Of course, good cognitive scientist as I am, I know that optimal performance requires a good grip of the statistics of the environment you're working in. For us, that's going to be our typing patterns!  Here, I'll show you how I was able to capture a huge amount of data on how I type, how to play around with it, and how to do the same for your own keyboard.

<!--more-->

## My set up

This tutorial/demonstration is for those who know something about mechanical keyboards, and just a _little_ bit about [the QMK firmware that powers most custom boards](http://qmk.fm/). I'm relatively new to QMK myself, but I'm trying to make things a little bit easier for the next guy. However, I'm not a developer for this project, and my free time is limited, so this will be specific to my experience and setup, etc.

After suffering through the hell that was the Massdrop group buy for [Jack Humbert's](http://jackhumbert.com/) [Planck mechanical keyboard](https://www.youtube.com/watch?v=bEPg8kk84gw)[^1], I've finally got a fully programmable keyboard of my own.  This guide will be for that rev4 Planck. I use an old Macbook Pro with OSX 10.9.5 (I _really_ need to get around to updating!) and `R` version 3.3.1 (more shame!).

I can tell you right now, following this tutorial on a PC is going to be challenging. Making and flashing custom QMK layouts to your keyboard is way easier on Unix-based systems, and most of the cool open-source stuff is for Unix as well. Now is the perfect time to get in on that Linux action if you haven't already. Installing a virtual machine on your PC is a committment-free way of playing around with Linux, and I'd recommend that.

## Getting your typing data

Alright folks, this here's the secret I learned: download [selfspy](https://github.com/gurgeh/selfspy).  Selfspy is basically spyware you use on yourself--it collects _enormous_ amounts of information on your activity on your computer. It records every keystroke, every name of every window you open, and your mouse movements as well. Unlike spyware, it doesn't send this data to anybody else, it justs saves all of it in an Sqlite database on your computer.

### Installing selfspy

Heads up: this might not that be easy to do. I kinda blacked out from the stress of trying to get it installed right, so my memory about what I did to get it to work is a little hazy. Follow the instructions on the Github page as well as you can, but IIRC I had to install the exact versions of some of the stuff listed in the `osx_requirements.txt` file. In particular, I think I had to make sure I was using the 3.0.4 version of `pyobjc` in the end (I used the `pip` installer).

Looking back, you might be able to just update the pyobjc requirements in `osx_requirements.txt` to whatever you have currently, but I'm not positive about that.

## Analyzing your data

Open up a terminal, and run `selfspy` to have it start collecting your data.  **A word to the wise: unless you sometimes pause it, it will record _EVERYTHING_**. All your passwords, the names of all those dirty, _dirty_ site you visit (you filthy animal!)--everything.

This isn't a such a big deal, however, because you can have it encrypt the data it stores in the database on your computer. If you're fine with somewhat surface-level analyses of your data, this is fine--`selfspy` comes with a program called `selfstats` that lets you print out some basic analyses of your data, including key frequencies. If you want to see how often you've pressed each key while `selfspy` has been running, you can do it with `selfstats` easy-peasy.

But if you want to manipulate all that juicy, _succulent_ data yourself (you little pervert!), the fact that it's all encrypted _is_ a bit of problem. At least it was for me, who doesn't know how to decrypt it with the tools I had on hand.  Instead, I opted to just leave everything unecrypted and pray to God that the Russians don't get a hold of my computer[^2]. The `R` code that I've written to analyze the data at a more fine-grain level only works when it's unecrypted, so either figure out how to decrypt [Blowfish](https://en.wikipedia.org/wiki/Blowfish_(cipher)) in `R` or `Python`, or let your freak flag fly.

## Walking through the code I've written

I do a lot of `R` coding and use [Hadley Wickham's beautiful `R` babies](https://github.com/tidyverse/tidyverse) all the time. One of his packages, `dplyr`, has[^3] the capability of manipulating SQL data, so that's what I use to access the data stored in `~/.selfspy/selfspy.sqlite`.  I'll run you through some of it so you can get a sense of how it works. You can download it for yourself in the link at the end of the post--it comes with (hopefully) helpful comments and multiple examples for you to acquaint yourself with different possibilities.


{% highlight r %}
library(dplyr) # you should add `library(dbplyr)` if you're using the newest version of dplyr
library(tidyr)
library(stringr)
library(purrr)

# Loading in the data from the default location for the database
selfspy_db <- src_sqlite("~/.selfspy/selfspy.sqlite", create = T) 
selfspy_db
{% endhighlight %}



{% highlight text %}
## src:  sqlite 3.11.1 [~/.selfspy/selfspy.sqlite]
## tbls: click, geometry, keys, process, window
{% endhighlight %}

You can see that there are five tables in the database: `click` (mouse data?), `geometry` (window size data?), `keys` (key press data), `process` (the names of the programs), `window` (data on what windows have been active).  For this excursion, we'll only care about `keys` and `process`.


{% highlight r %}
# Opening connections to the key and process databases
key_db <- tbl(selfspy_db, "keys")
process_db <- tbl(selfspy_db, "process")

key_db
{% endhighlight %}



{% highlight text %}
## Source:   query [?? x 10]
## Database: sqlite 3.11.1 [~/.selfspy/selfspy.sqlite]
## 
##       id                 created_at        text
##    <int>                      <chr>      <list>
## 1      1 2017-10-18 14:24:13.692624  <raw [12]>
## 2      2 2017-10-18 14:24:28.915149  <raw [24]>
## 3      3 2017-10-18 14:24:30.259072  <raw [12]>
## 4      4 2017-10-18 14:25:05.551297  <raw [42]>
## 5      5 2017-10-18 14:27:39.875412 <raw [397]>
## 6      6 2017-10-18 14:27:50.265004  <raw [27]>
## 7      7 2017-10-18 14:27:57.575051  <raw [48]>
## 8      8 2017-10-18 14:27:59.317140  <raw [12]>
## 9      9 2017-10-18 14:28:00.678074  <raw [13]>
## 10    10 2017-10-18 14:28:02.835207  <raw [19]>
## # ... with more rows, and 7 more variables: started <chr>,
## #   process_id <int>, window_id <int>, geometry_id <int>,
## #   nrkeys <int>, keys <list>, timings <list>
{% endhighlight %}

See the `Source:   query [?? x 10]` at the top? As it currently stands, `key_db` isn't a data frame or a `tbl_df`--it's just a query to the database--it doesn't know how many rows there are yet. When dealing with SQL, `dplyr` evaluates things _lazily_, meaning it won't actually fetch all the data from the database unless you demand it.  

You can see that there's a lot of info in `key_db`: in addition to timining information for the key presses, it has the IDs of all the applications and windows that were active while you were typing. Today, I'll only be focusing on the key presses and the names of the applications.

Let's look at some of the functions I've written to help you analyze your data.

### Getting the keypresses in human-readable formats

In order analyze the key presses, we have to get them to a point where we can work with them. For this, I've written the function `getPresses()`. There are a lot of optional arguments, but they're detailed in the code. The basic functionality is like this:


{% highlight r %}
getPresses(key_db) %>%
  select(cleanStrings) # selecting only the "cleaned up" version of the key presses
{% endhighlight %}



{% highlight text %}
## # A tibble: 108,520 × 1
##    cleanStrings
##           <chr>
## 1  <[Cmd: Tab]>
## 2             a
## 3             a
## 4             a
## 5             a
## 6             s
## 7             s
## 8             s
## 9             s
## 10            a
## # ... with 108,510 more rows
{% endhighlight %}

For those of you not used to `R` and those `R` users not used to the `tidyverse`, the `%>%` operator pipes the output of everything on the left of it (`getPresses(key_db)`) into the function on the right of it as the first argument (or, wherever you put a `.`). Thus, what is above is equivalent to `select(getPresses(key_db), cleanStrings)`. My irrational commitment to never declare new variables might make some of the code seem a little weird to some of you--each function is basically a single "flow".

## Understanding the output: Part I

The output from `getPresses()` is essentially a table where every row is a single key press (kind of). The keypresses are saved as strings with the "cleaned up" version of each press in the `cleanStrings` column. A row with "a" in this column means you typed that character--unfortunately, `selfspy` includes the presence of the Shift key in this value, so "A" actually means `Shift + 'a'`. For modifier combos and certain other key presses, such as `Command + Tab` or `Backspace`, the key press is saved in brackets like `<[Cmd: Tab]>`. Technically speaking, these probably aren't "key presses"--`selfspy` doesn't record pressing the Command, Alt, or Ctrl keys unless they are pressed along with some other key.

By itself, the output of `getPresses` is pretty useless. If we want to analyze the data, maybe we'd want to start looking at which keys are pressed the most often, or what shortcuts are used the most. That way, we could decide how accessible each key should be on our keyboard, or what shortcut macros might help the most.

To get a sense of this, I've created a function called `getStats()`:


{% highlight r %}
key_db %>% 
  getPresses() %>%
  getStats(s_col="cleanStrings", # The name of the column of the key press strings being passed in
           break_multitaps=TRUE # This will ungroup repeated taps (see below)
           ) %>%
  arrange(-n) # order the keys with the highest frequencies on top
{% endhighlight %}



{% highlight text %}
## Source: local data frame [201 x 3]
## Groups: cleanStrings [201]
## 
##     cleanStrings areModsPressed     n
##            <chr>          <dbl> <dbl>
## 1       <[Down]>              1 27465
## 2  <[Backspace]>              1 13729
## 3                             0 13228
## 4              e              0  7849
## 5              t              0  6169
## 6              a              0  5197
## 7              o              0  4771
## 8              i              0  4513
## 9              s              0  4462
## 10             n              0  4287
## # ... with 191 more rows
{% endhighlight %}

You can see from the output that there are three columns: the names of the key presses, `areModsPressed` (a column indicating whether functional/modifier keys were pressed down, excluding Shift), and `n` (the number of presses).

It seems that so far, I press "Down" and "Backspace" the most, followed by "Space" (annoyingly represented as actual whitespace) and then some really common letters. (You can show _all_ the rows by piping the output into `as.data.frame()`.)  Not super surprising. But we set the `break_multitaps` to `TRUE`--what was up with that?

Well, `selfspy` automatically records repeated "bracketed" key presses with a single entry. So 15 `Command + Tab`s in a row will be recorded as `<[Command + Tab]x15>`. By default, `getStats()` treats this as a single key press. This is useful if you want to consider making macros for, say, something that presses Backspace three times in a row. Note that only "bracketed" key presses are recorded this way. By setting `break_multitaps=TRUE`, we treat these repeated presses individually.

## Understanding the output: Part II

But what if you're not satisfied with something that you could basically do with the `selfstats` command? For example, what if you wanted to look at how you typed differently in different applications (perhaps for creating a `Python` layer or an `R` layer), or if you wanted to look at multi-press patterns?

I've made `getPresses()` capable of separating key presses by application name, so that they can be analyzed independently in parallel. Here we use our old friend `process_db` from earlier. Because the `key_db` only has numbers for each process, if we want to see the names those numbers refer to, we have to pass in what is essentially a number-to-name dictionary (`process_db`, after we call `collect()` on it).


{% highlight r %}
key_db %>% 
  getPresses(process_id_df    = process_db %>% # so we can use application names rather than numbers for process IDs
               select(-created_at) %>% # I remove a column that we don't need
               collect(), # this function makes dplyr stop being lazy and fetch us the actual data
             group_by_process = TRUE)
{% endhighlight %}



{% highlight text %}
## # A tibble: 22 × 2
##             process_id                  data
##                  <chr>                <list>
## 1             Terminal  <tibble [4,561 × 8]>
## 2              RStudio <tibble [33,478 × 8]>
## 3        Google Chrome <tibble [39,359 × 8]>
## 4         TextWrangler  <tibble [3,097 × 8]>
## 5               Finder    <tibble [580 × 8]>
## 6             TextEdit  <tibble [5,213 × 8]>
## 7                Notes  <tibble [1,851 × 8]>
## 8          QMK Flasher      <tibble [3 × 8]>
## 9  CoreServicesUIAgent      <tibble [1 × 8]>
## 10     Microsoft Excel    <tibble [151 × 8]>
## # ... with 12 more rows
{% endhighlight %}

A marvel of the `tidyverse` is that it can store entire data frames as single cells in bigger data frames. Each cell in the `data` column above is a data frame of all the key presses for the application in the `process_id` column.

We can analyze each of these data frames the same as we would a single data frame with Hadley Wickham's [`purrr`](https://github.com/tidyverse/purrr) package. Having started my programming journey in [`Scheme`](https://en.wikipedia.org/wiki/Scheme_(programming_language)), I love me some functional programming. The `map` function in `purrr` lets us apply the `getStats` function to the inside of each data frame in the `data` column.


{% highlight r %}
key_db %>% 
  getPresses(process_id_df = process_db %>% select(-created_at) %>% collect(), 
             group_by_process = TRUE) %>%
  mutate(data = purrr::map(data, ~getStats(., # Don't forget the tilde in front of the function, and you have to use the '.' to indicate where the first argument of `purrr::map` should appear
                                           s_col="cleanStrings",
                                           break_multitaps=FALSE))) %>%
  tidyr::unnest() %>% # Expands the data frames in the `data` column
                      # If you want to keep them separate, keep manipulating them with `map`!
  arrange(-n)
{% endhighlight %}



{% highlight text %}
## # A tibble: 2,224 × 4
##        process_id cleanStrings     n areModsPressed
##             <chr>        <chr> <int>          <dbl>
## 1   Google Chrome               4950              0
## 2         RStudio               3992              0
## 3   Google Chrome            e  3014              0
## 4         RStudio            e  2395              0
## 5   Google Chrome            t  2358              0
## 6  Microsoft Word               2151              0
## 7   Google Chrome            o  2023              0
## 8   Google Chrome            a  1948              0
## 9         RStudio            t  1907              0
## 10  Google Chrome            i  1793              0
## # ... with 2,214 more rows
{% endhighlight %}



{% highlight r %}
test_plot_data <- key_db %>% 
  getPresses(process_id_df = process_db %>% select(-created_at) %>% collect(), 
             group_by_process = TRUE) %>%
  mutate(data = purrr::map(data, ~getStats(., # Don't forget the tilde in front of the function, and you have to use the '.' to indicate where the first argument of `purrr::map` should appear
                                           s_col="cleanStrings",
                                           break_multitaps=FALSE))) %>%
  tidyr::unnest() %>% # Expands the data frames in the `data` column
                      # If you want to keep them separate, keep manipulating them with `map`!
  arrange(-n) %>%
  group_by(process_id) %>%
  mutate(id_size=sum(n)) %>%
  ungroup() %>%
  filter(id_size > mean(id_size)/2) %>%
  group_by(cleanStrings) %>%
  mutate(string_num=sum(n)) %>%
  ungroup() %>%
  filter(string_num > 500) %>%
  arrange(-string_num) %>%
  mutate(cleanStrings=factor(cleanStrings,
                             levels=unique(cleanStrings))) %>%
  group_by(process_id) %>%
  mutate(normalized_log_n=scale(log(n))) %>%
  ungroup()



label_data <- test_plot_data %>%
  filter(areModsPressed==1)

test_plot_data %>%
  ggplot(aes(x=cleanStrings,y=normalized_log_n,color=as.factor(areModsPressed))) + geom_point() +
  facet_wrap(~process_id) + 
  theme(axis.text.x=element_blank(),
        axis.ticks.x=element_blank()) + 
  scale_color_discrete(guide=FALSE) + 
  geom_label_repel(aes(label=cleanStrings), 
                   #color="black",
                   size=5,
                   alpha=0.7,
                   data=label_data, 
                   force=10,
                 box.padding = unit(0.5, "lines"),
                 min.segment.length = unit(0.0, "lines"),
                 show.legend = FALSE)
{% endhighlight %}

![BABABA this is a test, this is a test, waaaaaaaa waaaaaaaaaaa, waaaaaaaaa](/figure/source/2017-10-28-selfspy_post/unnamed-chunk-7-1.png)








<hr />
<br />

## Source Code:

> [`web_scraper_threaded_general.py`]({{ site.url }}/code/web-scraping/web_scraper_threaded_general.py)

My multi-thread web-scraper, written for Python 3.4+, requires Beautiful Soup and Pillow. If you have `pip` you can try: `python3 pip install beautifulsoup4` and `python3 pip install pillow`.  This is my first time ever working with threads in Python--probably overkill, but it was fun to learn about. If you have any comments about what I could do better--any rookie mistakes I made--feel free to leave a comment below.

> [`web_scraper_nonthreaded.py`]({{ site.url }}/code/web-scraping/web_scraper_nonthreaded.py)

My crappier, non-threaded, web-scraper with poor documentation. Also written for Python 3.4+, requires Beautiful Soup and Pillow. This is the earlier, crappier version of my code for a few of the examples, more or less.

> [`2016-11-14-webcomic_post.Rmd`]({{ site.url }}/_source/2016-11-14-webcomic_post.Rmd)

The R Markdown file this blog post is generated from, if you want to know what R code I used for the analysis and plotting.

### Footnotes



[^1]: None of the trainwreck was Jack's fault--Massdrop is just a horrible company.

[^2]: You can leave your data unencrypted with: `selfspy -p ""`. I also learned that you can completely screw up your database by trying to change the password, so my advice is to pick if you want it encrypted or not and stay with that decision.

[^3]: Technically it "had" the ability. The latest release of `dplyr` has separated this functionality into the `dbplyr` package. I haven't yet made the leap to the newest `dplyr` though (even though it's _way_ better), and my code reflects that. The code I wrote should be basically identical to what you'd use if you use the new package though.

