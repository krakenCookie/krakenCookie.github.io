local({
  # fall back on '/' if baseurl is not specified
  baseurl = servr:::jekyll_config('.', 'baseurlknitr', '/')
  knitr::opts_knit$set(base.url = baseurl)
  # fall back on 'kramdown' if markdown engine is not specified
  markdown = servr:::jekyll_config('.', 'markdown', 'kramdown')
  # see if we need to use the Jekyll render in knitr
  if (markdown == 'kramdown') {
    knitr::render_jekyll()
  } else knitr::render_markdown()

  # input/output filenames are passed as two additional arguments to Rscript
  a = commandArgs(TRUE)
  d = gsub('^_|[.][a-zA-Z]+$', '', a[1])
  d = gsub("source/","source/x",d)
  knitr::opts_chunk$set(
    fig.path   = sprintf('_posts/figures/generated/%s/', d),
    cache.path = sprintf('cache/%s/', d)
  )
  
  knitr::knit_hooks$set(autocaption = function(before, options, envir) {
  if (!before) {
  	if (length(options$fig.cap)>0) {
  	  paste0("\n\n<p class='figcaption'>", options$fig.cap, "</p>")
  	}
  	#paste0(" WAAAA  ", str(options[c("fig.cap")]), "  sss  ", length(str(options[c("fig.cap")])), "mmmmm", options$fig.cap)
    #z = capture.output(str(options[c('eval', 'dev', 'results', 'bar1', 'bar2', 'bar3')]))
    #z = paste('    ', z, sep = '', collapse = '\n')
    #paste('Some chunk options in the above chunk are:\n\n', z, sep = '')
  }
  })
  knitr::opts_knit$set(width = 70)
  knitr::knit(a[1], a[2], quiet = TRUE, encoding = 'UTF-8', envir = .GlobalEnv)
})
