---
layout: page
title: Categories
permalink: /categories/
---

<!-- thanks to Houssain Mohd Faysel, https://stackoverflow.com/questions/20945944/jekyll-liquid-output-category-list-with-post-count/21080786#21080786 .  Adapted slightly.-->
<!-- also thanks to Christian Specht, https://stackoverflow.com/questions/24700749/how-do-you-sort-site-tags-by-post-count-in-jekyll/24744306#24744306. Adapted slightly -->

<h2>Category list </h2>

{% capture cats %}
  {% for cat in site.categories %}
    {{ cat[1].size | plus: 1000 }}OOOO{{ cat[0] }}OOOO{{ cat[1].size }}XXXX
  {% endfor %}
{% endcapture %}
{% assign sortedcats = cats | split:'XXXX' | sort %}
<ul class="cat-box inline">
{% for cat in sortedcats reversed %}
  {% assign catitems = cat | split: 'OOOO' %}
  {% assign post_number = catitems[2] | plus: 0 %}
    <li><a href="#{{ catitems[1] }}">{{ catitems[1] | capitalize }}</a> - <span>{{ post_number }} </span><span>
  {% if post_number > 1 %}
    {{ 'posts' }}
  {% else %}
    {{ 'post' }}
  {% endif %}
  </span></li>
{% endfor %}
</ul>

<br>
<hr>
<br>

{% for cat in site.categories %} 
  <h2 id="{{ cat[0] }}">{{ cat[0] | capitalize }}</h2>
  <ul class="post-list">
    {% assign pages_list = cat[1] %}  
    {% for post in pages_list %}
      {% if post.title != null %}
      {% if group == null or group == post.group %}
      <li><a href="{{ site.baseurl }}{{ post.url }}" class = "post-title">
            {{ post.title }}<span class="entry-date"><time datetime="{{ post.date | date_to_xmlschema }}" itemprop="datePublished"> - {{ post.date | date: "%B %d, %Y" }}</time></span></a></li>
      {% endif %}
      {% endif %}
    {% endfor %}
    {% assign pages_list = nil %}
    {% assign group = nil %}
  </ul>
{% endfor %}
