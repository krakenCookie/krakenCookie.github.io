
# This is the code we used to determine which movie titles were questions
#   The actual code was written almost exclusively by Zachary Burchill, although
#     it was based conceptually on a lot of work Andrew Burchill had done

library(tidyverse)
library(magrittr)
# Constants + functions ==================================

cutoff_votes <- 5

stative_verbs <- c("is",    "are",    "was",    "were",
                   "isn't", "aren't", "wasn't", "weren't")

neg_aux_words <- c("isn't", "aren't", "wasn't", "weren't",
                   "don't", "doesn't", "didn't",
                   "haven't", "hasn't", "hadn't",
                   "can't", "couldn't", "wouldn't", "shouldn't",
                   "shan't", "won't", "mustn't", "mightn't")

aux_words <- c("is",    "are",    "was",    "were",
               "isn't", "aren't", "wasn't", "weren't",
               "do",    "does",    "did",
               "don't", "doesn't", "didn't",
               "have",    "has",    "had",
               "haven't", "hasn't", "hadn't",
               "can",   "could",    "would",    "should",
               "can't", "couldn't", "wouldn't", "shouldn't",
               "shall",  "will",  "must",
               "shan't", "won't", "mustn't",
               "may", "might", "mightn't")

verb_regexp <- "\\b(VB|VBD|VBP|VBZ|MD)\\b"

# Gets binomial confidence intervals for % question mark
binom_confs <- function(df, grouping_col) {
  q <- enquo(grouping_col)
  df %>%
    group_by(!!q) %>%
    summarise(w_mark = sum(ifelse(has_mark,1,0)), n=n()) %>%
    {cbind(., as_tibble(Hmisc::binconf(.$w_mark, .$n)))}
}

add_ratings <- function(df) {
  left_join(df, ratings_df) %>%
    filter(numVotes > cutoff_votes) %>%
    mutate(comedy = genres %>% str_detect("Comedy"),
           drama = genres %>% str_detect("Drama"),
           genre = case_when(
             comedy & !drama  ~ "comedy",
             drama  & !comedy ~ "drama",
             drama  &  comedy ~ "both",
             TRUE ~ "neither"),
           prop_ratings = (averageRating - 1)/9,
           transformed_ratings = car::logit(prop_ratings, adjust=0)
    )
}

# This is something I whipped up to help me test the filtering criteria
# Check if filter statements help
check_changes <- function(df, ...,
                          print=TRUE,
                          width = 20) {
  qs <- enquos(...)
  q2s <- function(q) {
    s <- rlang::quo_text(q)
    if (nchar(s) > width-3)
      paste0(substr(s, 1, width), "...")
    else s
  }

  f1 <- df %>% ungroup() %>%
    summarise(no_q = sum(!has_mark), has_q = sum(has_mark),
              n = n(), prop_q = has_q/n)
  df <- df %>%
    filter(!!!qs)
  f2 <- df %>% ungroup() %>%
    summarise(no_q = sum(!has_mark), has_q = sum(has_mark),
              n = n(), prop_q = has_q/n)

  excl_df <- data.frame(
    type = c("no mark", "mark"),
    excluded = c(f1$no_q-f2$no_q, f1$has_q-f2$has_q),
    now = c(f2$no_q, f2$has_q)) %>%
    mutate(` ` = (excluded/c(f1$no_q, f1$has_q)*100) %>%
             format(digits=2) %>% paste0("(",.,"%)")) %>%
    select(type, excluded, ` `, now) %>%
    tibble::column_to_rownames("type") %>%
    {capture.output(print(.))} %>%
    paste0(collapse="\n")

  bar <- paste(rep("-", width+14), collapse="")

  thing <- reduce(qs, ~paste(.x, q2s(.y)), .init=NULL) %>%
    paste0(bar, "\nCommand: `", ., "`")

  top <- paste0(
    "% Marks: ",
    format(f1$prop_q*100, digits=3), "% -> ",
    format(f2$prop_q*100, digits=3), "%"
  )
  cat(paste(thing, top, excl_df, "", sep="\n",""))
  df
}


# regexping at depth 1 of index i
is_pos <- function(l,i,s) {
  map_lgl(l, ~str_detect(.[[i]], s))
}
# A back-up, manual way of finding aux verbs
is_aux <- function(v) {
  tolower(v) %in% aux_words
}
is_neg_aux <- function(v) {
  tolower(v) %in% neg_aux_words
}
is_stative <- function(v) {
  tolower(v) %in% stative_verbs
}
is_verb <- function(v) {
  str_detect(v, verb_regexp)
}

# Uses the Carnegie Mellon University Pronouncing Dictionary for word forms
# Would be better served with corpora like SUBTLEX-US, with freq counts
# But I'm lazy
add_fw <- function(df) {
  # Ugly hack to let this function work with dfs without POS
  if ("pos" %in% names(df)) {
    pos <- df$pos
    qqs <- quos(everything(), -words2, -words,
                -pos, -num_words, -isEnglish)
  } else {
    qqs <- quos(everything(), -words2, -words,
                -num_words, -isEnglish)
  }
  w <- df$words
  df %>%
    ungroup() %>%
    mutate(words2 = tolower(originalTitle)) %>%
    mutate(words2 = words2 %>%
             str_replace("'s", "") %>%
             str_replace("\\s\\s", " ") %>%
             str_replace("[^[:lower:] ']", "")
    ) %>%
    tidyr::separate_rows(words2, sep=" ") %>%
    mutate(isEnglish = ifelse(words2 %in% word_forms, 1, 0)) %>%
    group_by_at(vars(!!!qqs)) %>%
    summarise(
      n_nonEng = sum(!isEnglish),
      num_words = n(),
      p_nonEng = n_nonEng/num_words,
      diffTitle = first(originalTitle != primaryTitle),
      nonEngString = paste(words2[!isEnglish], collapse=" ")
    )  %>%
    ungroup() %>%
    mutate(words=w) %>%
    # This is an ugly hack so we can use it with
    #   the dataframe without POS tags
    {
      if ("pos" %in% names(df)) {
        mutate(., pos=pos)
      } else {
        .
      }
    }
}
non_English_words <- function(v, as_string = FALSE) {
  data.frame(x=v) %>%
    mutate(id = seq_along(x),
           words = tolower(x)) %>%
    mutate(words = gsub("'s","", words) %>%
             gsub("[^a-z ']","", .)) %>%
    tidyr::separate_rows(words, sep=" ") %>%
    mutate(isEnglish = ifelse(words %in% word_forms, 1, 0)) %>%
    group_by(id, x) %>%
    summarise(bads = paste(words[!isEnglish], collapse=" "),
              m = mean(isEnglish)) %>%
    arrange(id) %>%
    pluck("m")
}

# This is the hackiest piece of my code in the whole project.
#   Basically, foreign and English titles are not linearly separable on a single continuum.
#   I use a point-based system here, with the hackiest part of it saying that films that
#     start with 'was' are likely to be foreign (There are a LOT of German films that
#     sneak through our filtering that begin with that).
#   If you wanted to do this right, an XGBoost classifier would do very well, I think
remove_foreign_films <- function(df, uncap_word_list,
                                 filter=TRUE, threshold=1) {
  df <- df %>%
    add_fw() %>%
    mutate(words = str_split(originalTitle, " ")) %>%
    mutate(uncapped = words %>%
             map_int(~sum(str_detect(.x, "^[:lower:]") &
                            !(.x %in% uncap_word_list)))) %>%
    mutate(
      # If there are lots of uncapitalized words (more common in foreign titles)
      points = ifelse(uncapped > 2 & uncapped/num_words > 0.3, 1, 0),
      # If there are at least two non-English words
      points = points + ifelse(n_nonEng > 2, 1, 0),
      # If there is at least 50% non-English words
      points = points + ifelse(n_nonEng/num_words > 0.5, 1, 0),
      # If the primary title is different than the original
      points = points + ifelse(diffTitle, 1, 0),
      # A hack, but targetting German.
      points = points + ifelse(first_word=="was", 2, 0),
      # If all words are English, it's good
      points = ifelse(n_nonEng==0, 0, points)
    )
  if (filter==TRUE) {
    df %>%
      filter(points <= threshold) %>%
      select(-points, -uncapped)
  } else {
    df
  }
}


# Load data ==============================================


dir_path <- "/Users/zburchill/burchill.github.io/non_git_building_material/movie_questions/"
# This should refer to the output of the pos_tagging.R script
raw_df <- readRDS(paste0(dir_path, "pos_tagged_possible_questions.RDS")) %>%
  mutate(second_word = map_chr(words, ~.[[2]]))

# This should refer to the title.ratings.tsv file downloaded from https://www.imdb.com/interfaces/
ratings_df <- read_delim(paste0(dir_path, "title.ratings.tsv"),
                      "\t", escape_double = FALSE, trim_ws = TRUE,
                      na = "\\N",  quote = '')

# This should refer to a version of the CMUPD, but I altered this particular
#   file to make it better suited for R about 4 years ago, and don't remember what exactly
#   I changed. It shouldn't matter much though, as I just use the word forms themselves.
word_forms <- read_delim(paste0(dir_path, "cmu-dict-for-R.txt"),
                         delim="|", col_names = FALSE) %>%
  mutate(wordform = tolower(X1)) %>%
  distinct(wordform) %>%
  pluck(1)

# The top 15 words that are uncapitalized
top_15_uncapped_words <- raw_df %>%
  tidyr::separate_rows(originalTitle, sep=" ") %>%
  filter(grepl("^[a-z]", originalTitle)) %>%
  group_by(originalTitle) %>%
  summarise(n=n()) %>%
  arrange(-n) %>%
  head(n=15) %>%
  pluck("originalTitle")

# Sanity checks ================================

# how good is the POS tagger for auxs?
# False positives (essentially nothing)
raw_df %>%
  filter(is_pos(pos, 1, "^MD$")) %>%
  filter(!is_aux(first_word)) %>%
  group_by(first_word) %>%
  summarise(n=n()) %>% arrange(-n) %>%
  mutate(total=sum(n))
# False negatives ?  (not perfect)
raw_df %>%
  check_changes(is_aux(first_word)) %>%
  mutate(first_pos = map_chr(pos, ~.[[1]])) %>%
  filter(first_pos != "MD") %>%
  group_by(first_word, first_pos) %>%
  summarise(n=n()) %>% ungroup() %>% arrange(-n) %>%
  mutate(total=sum(n))

raw_df %>%
  filter(is_aux(first_word)) %>%
  group_by(first_word) %>%
  summarise(n=n(), m = sum(has_mark), prop = m/n) %>%
  arrange(m) %>% as.data.frame()

# what about for WH words?
raw_df %>%
  filter(is_pos(pos, 1, "^(WDT|WP|WP\\$|WRB)$")) %>%
  mutate(first_pos = map_chr(pos, ~.[[1]])) %>%
  distinct(first_word, first_pos) %>%
  filter(!grepl("where|who|how|when|why|what", first_word))
# And the reverse
raw_df %>%
  filter(grepl("where|who|how|when|why|what", first_word)) %>%
  filter(!is_pos(pos, 1, "^(WDT|WP|WP\\$|WRB)$")) %>%
  mutate(first_pos = map_chr(pos, ~.[[1]])) %>%
  distinct(first_word, first_pos)


# Filter the bad stuff out out ====================================

# Strictest filtering --------------------------------------

# This filtering picks out all titles that have versions that end in
#   both question marks and blank spaces.
# E.g. 'What About Me' and 'What About Me?'
# This is the strictest filtering but basically gaurunteed to have
#   no false positives

# get all question mark titles
real_qs <- raw_df %>%
  filter(has_mark) %>%
  pluck("originalTitle") %>%
  tolower() %>%
  gsub("\\?","",.)

# Get all the titles that have titles identical to the question mark titles
#   (including those without question marks)
paired_df <- raw_df %>%
  mutate(title = tolower(gsub("\\?","", originalTitle))) %>%
  filter(title %in% real_qs) %>%
  # Add ratings now so you can filter out tiles without enough votes
  add_ratings() %>%
  group_by(title) %>%
  # each title needs to have a version with a question mark and without it
  filter(n_distinct(has_mark) > 1)

# All you can really do is plot it:
paired_df %>%
  group_by(title, has_mark) %>%
  # Combine identical titles, with averageRating becoming the weighted avg
  summarise(total_votes = sum(numVotes),
            averageRating = sum(averageRating*numVotes)/total_votes) %>%
  rename(numVotes = total_votes) %>%
  ungroup() %>%
  mutate(prop_ratings = (averageRating - 1)/9,
         transformed_ratings = car::logit(prop_ratings)) %>%
  # Get the difference
  group_by(title) %>%
  summarise(diff = transformed_ratings[has_mark] - transformed_ratings[!has_mark]) %>%
  ggplot(aes(x=title, y=diff)) +
  geom_point() +
  geom_hline(aes(yintercept=0),linetype="dashed")

# Second strictest filtering --------------------------------------

strict_wh_df <- raw_df %>%
  filter(question_word) %>%
  # Filter by number of ratings early so we don't optimize for everything
  add_ratings() %>%

  # The next word needs to be a non-participle verb. Overly strict? Sure.
  # The POS tagger is really bad about contractions being labelled
  #   as possesive markers, e.g., "What's the matter?" has " 's " as posessive,
  #   so I let possesive markers qualify as verbs
  check_changes(
    is_pos(pos, 2, verb_regexp) | is_pos(pos, 2, "^POS$")
  ) %>%

  # If the wh-word is 'when', it needs to be followed by an aux verb
  check_changes(
    first_word != "when" |
      (second_word %in% aux_words | is_pos(pos, 2, "^MD$"))
  )

strict_aux_df <- raw_df %>%
  filter(is_aux(first_word)) %>%
  # Filter by number of ratings early so we don't optimize for everything
  add_ratings() %>%

  # A question needs to either be an inverted 'to be' question
  #     e.g., <is/are/etc.> <noun> <predicate>
  #   or be an aux verb + 'real verb' + noun.
  #   In either case, at least three words
  check_changes(map_lgl(words, ~length(.) >= 3)) %>%
  mutate(pos_string = pos %>%
           map_chr(~paste(.[2:length(.)], collapse=" "))) %>%
  mutate(is_neg = is_neg_aux(first_word) | second_word == "not") %>%

  # If it isn't a 'to be' verb, it needs to have a real verb elsewhere
  check_changes(
      is_stative(first_word) |
        (!is_stative(first_word) & grepl("\\b(VB|VBD|VBP|VBZ)\\b", pos_string))
  ) %>%

  # If it isn't a 'to be' verb, the real verb can't be the second word
  filter(
    is_stative(first_word) | !is_pos(pos, 2, verb_regexp)
  ) %>%

  # If it's negative it can't be followed by a verb
  check_changes(
    !is_neg | !grepl("\\bRB (VB|VBD|VBP|VBZ)\\b", pos_string)
  )

# Put them together and remove foreign films
#   This is what we ended up using
zach_df <- bind_rows(strict_wh_df, strict_aux_df) %>%
  distinct(tconst, .keep_all = T) %>%
  remove_foreign_films(top_15_uncapped_words)


# Andrew's crazy least strict filtering --------------------------------------
# This was the first iteration of our filtering strategy, before I decided to do it
#   in a more principled way. We did not end up using this code.
andrew_df <- raw_df %>%
  # select(originalTitle, question_word, aux_word,
  #        has_mark, contraction, pos, genres,
  #        first_word, second_word, tconst) %>%
  #Remove aux words that aren't aux (or verbs)
  filter(!aux_word | map_lgl(pos, ~str_detect(.[[1]], "^(MD|V)"))) %>%
  add_ratings() %>%
  #take out "Can'ts" and "should'ves"
  filter(!(contraction & map_lgl(pos, ~str_detect(.[[2]], "^(RB|VB)$")))) %>%
  #W-questions should have verbs... or other stuff
  #the RB and the IN need to get figured out better though
  #db2 %>% filter(question_word & (map(pos,~pluck(.,2)) %>% str_detect("^(RB)$")) & (map(pos,~pluck(.,1)) %>% str_detect("^(WRB)$"))) %>% View()
  filter(!question_word | map_lgl(pos, ~str_detect(.[[2]], "^(RB|VB|:|,|POS|CC|IN|MD)"))) %>%
  #take out all "Do/have __", other than "do I" or "do you"
  filter(!(first_word %in% c("do", "have")) |
           second_word %in% c("you", "i")) %>%
  #figure out aux words, second word in sentence
  filter(second_word=="i" |
           !aux_word | map_lgl(pos,~str_detect(.[[2]], "^(DT|PRP|RB)$")))
