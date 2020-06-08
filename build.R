local({
  # This build.R file needs to be in the main directory for the plotly stuff to work!!!!!!!!!!!!

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
    dpi = 200, # Want the default dpi to be high
    fig.path   = sprintf('_posts/figures/generated/%s/', d),
    proj.basedir = getwd(),
    plotly.savepath  = sprintf('%s/_posts/figures/generated/html_dependencies/', getwd()),
    cache.path = sprintf('cache/%s/', d)
  )

  knitr::knit_hooks$set(autocaption = function(before, options, envir) {
    if (!before && isTRUE(options$autocaption)) {
      if (length(options$fig.cap)>0) {
        paste0("\n\n<p class='figcaption'>", options$fig.cap, "</p>")
      }
    }
  })
  knitr::opts_knit$set(width = 70)
  knitr::knit(a[1], a[2], quiet = TRUE, encoding = 'UTF-8', envir = .GlobalEnv)
})
