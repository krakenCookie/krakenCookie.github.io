
# install.packages("openNLPmodels.en", repos = "http://datacube.wu.ac.at/", type = "source")

# This was run on the UofR compute cluster
# The code is a combination of Andrew Burchill and Zachary Burchill's work
options(java.parameters = "- Xmx1024m")
library(tidyverse)
library(future)
library(furrr)
# Make a multisession so I don't get weird java errors?
plan(tweak(multisession, workers=4))

library(NLP)
library(tm)  # make sure to load this prior to openNLP
library(openNLP)
library(openNLPmodels.en)
annotate <- NLP::annotate

#======Constants===========

wh_word_regexp <- "^(when|what|why|who|how|where)($|\')"
aux_word_regexp <- "^(is|are|was|were|isn't|aren't|wasn't|weren't|do|does|did|don't|doesn't|didn't|have|has|had|haven't|hasn't|hadn't|can|could|would|should|can't|couldn't|wouldn't|shouldn't|could've|would've|should've|shall|will|must|shan't|won't|mustn't|may|might|mightn't)($|\')"

# I've changed my username to 'XXXXXXXX' for safety/privacy reasons
dir_path <- "/u/XXXXXXXX/imdb/"
# We downloaded this file from https://www.imdb.com/interfaces/
filename <- "title.basics.tsv"
file_path <- paste0(dir_path, filename)

#======Functions===========
get_question_titles <- function(df, title_col, media_type = "movie") {
  tq <- enquo(title_col)

  df %>%
    filter(titleType %in% media_type) %>%
    mutate(words = stringr::str_split(tolower(originalTitle), " "),
           num_words = map_dbl(words, length)) %>%
    filter(num_words > 1) %>%
    mutate(first_word  = map_chr(words, ~.[[1]]),
           question_word = str_detect(first_word, wh_word_regexp),
           aux_word = str_detect(first_word, aux_word_regexp)) %>%
    filter(question_word | aux_word) %>%
    mutate(has_mark = grepl("\\?", !!tq),
           contraction = str_detect(first_word,"\'"))
}

POS <- function(title, gc=FALSE) {
  lower_title <- tolower(title) # weird but you cant do in pipeline
  lower_title2 <- as.String(lower_title)
  p <- annotate(lower_title2,
                list(Maxent_Sent_Token_Annotator(),
                     Maxent_Word_Token_Annotator()))
  annotate(lower_title2, Maxent_POS_Tag_Annotator(), p) %>%
  { if(sample(1:2, 1)==2) gc(verbose = FALSE); .} %>% #
    subset( type=='word') %>%
    {sapply(.$features , '[[', "POS")}
}
chunk2 <- function(x,n) split(x, cut(seq_along(x), n, labels = FALSE))


#======Code===========

data <- readr::read_delim(file_path, "\t",
                          escape_double = FALSE, trim_ws = TRUE,
                          na = "\\N", quote = '')

possible_questions <- get_question_titles(data, originalTitle)
rm(data)

wh_only <- possible_questions %>% filter(question_word==TRUE)
aux_only <- possible_questions %>% filter(question_word==FALSE)

#======Delicately getting the POS tags for WH===========
og_titles <- wh_only$originalTitle
chunked_titles <- chunk2(og_titles, 100)

tictoc::tic()
chunked_title_pos_lists <- chunked_titles %>%
  future_map(function(x) {
    options(java.parameters = "- Xmx1024m")
    res <- map(x, POS)
    gc()
    res
  })
tictoc::toc()

pos_title_list <- unlist(chunked_title_pos_lists, FALSE, FALSE)
wh_only$pos <- pos_title_list


#======Delicately getting the POS tags for auxiliaries ===========
og_titles <- aux_only$originalTitle
chunked_titles <- chunk2(og_titles, 100)

tictoc::tic()
chunked_title_pos_lists <- chunked_titles %>%
  future_map(function(x) {
    options(java.parameters = "- Xmx1024m")
    res <- map(x, POS)
    gc()
    res
  })
tictoc::toc()

pos_title_list <- unlist(chunked_title_pos_lists, FALSE, FALSE)
aux_only$pos <- pos_title_list


#======Saving it ===========
possible_questions_with_pos <- bind_rows(wh_only, aux_only)
saveRDS(possible_questions_with_pos, paste0(dir_path, "questions.RDS"))
