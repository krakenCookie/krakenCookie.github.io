library(tidyr)
library(dplyr)
library(stringr)

# What versions I'm using, etc.:

# R version 3.3.1 (2016-06-21)
# Platform: x86_64-apple-darwin13.4.0 (64-bit)
# Running under: OS X 10.9.5 (Mavericks)
# 
# locale:
#   [1] en_US.UTF-8/en_US.UTF-8/en_US.UTF-8/C/en_US.UTF-8/en_US.UTF-8
# 
# attached base packages:
#   [1] stats     graphics  grDevices utils     datasets  methods   base     
# 
# other attached packages:
#   [1] purrr_0.2.2    lazyeval_0.2.0 stringr_1.1.0  dplyr_0.5.0    tidyr_0.6.2   
# 
# loaded via a namespace (and not attached):
#   [1] R6_2.2.0       assertthat_0.1 magrittr_1.5   DBI_0.5-1      tools_3.3.1    tibble_1.2    
#   [7] Rcpp_0.12.8    stringi_1.1.2 



selfspy_db <- src_sqlite("~/.selfspy/selfspy.sqlite", create = T)
# selfspy_db <- src_sqlite("~/.selfspy/selfspy_old.sqlite", create = T)
selfspy_db

key_db <- tbl(selfspy_db, "keys")
process_db <- tbl(selfspy_db, "process")

# Cleans up the weird escaped characters
cleanUpStrings <- function(string_vec) {
  ifelse(string_vec=="\"\\\"\"", "\"", # Cleaning up escaped chars
  ifelse(string_vec=="\"\\\\\"", "\\", # Clean up escaped backslash
         stringr::str_sub(string_vec,2,-2)))
}

# Add extra clean-up criteria in this function
extraCleanUpStrings <- function(string_vec) {
  # For me, Shift + Tab produces the string \uu0019, 
  # so I change it to what it should be below
  ifelse(!grepl("\\\\u0019",string_vec),string_vec,
  ifelse(string_vec=="\\u0019","<[Shift: Tab]>",
         str_replace(string_vec,"\\\\u0019","Tab")))
}

# Decompresses, cleans, and organizes the keystrokes into a tbl_df()
getPresses <- function(.data, # the db
                       process_id_df=NA, # generally, `tbl(selfspy_db, "process") %>% collect()` or the like
                       group_by_process=FALSE, # Whether or not you want to analyze keystrokes for processes individually
                       extra_clean_f=extraCleanUpStrings # A function that operates on a vector that cleans up extra weird stuff. Set to NA to skip
                       ) {
  .data %>% 
    collect() %>% # Forces dplyr to actually get all the data from the Sqlite database
    mutate(Strings=purrr::map(keys,
                              ~memDecompress(.,type=c("gzip"), # decompresses the key-press data
                                             asChar=TRUE)) %>% #  as a single string
             purrr::simplify() %>% 
             stringr::str_sub(2,-2)) %>% # gets rid of the initial and final brackets in the string
    tidyr::separate_rows(Strings,sep=", ") %>% # breaks the string apart into presses
    mutate(cleanStrings = cleanUpStrings(Strings)) %>% # cleans up the individual key-press strings
    # If you give it a data frame of names for the process ids:
   {if (is.data.frame(process_id_df)) {
    left_join(.,rename(process_id_df,"process_id"=id),by="process_id") %>%
       mutate(process_id=name) %>%
       select(-name)
   } else {.}}  %>%
    # If there are extra clean-up functions you've passed in
   {if (is.function(extra_clean_f)) {
     (.) %>%
       mutate(cleanStrings = extra_clean_f(cleanStrings))
   } else {.}} %>%
   # If you want to group it by process id
   {if (group_by_process == TRUE) {
     (.) %>%
       group_by(process_id) %>%
       tidyr::nest()
   } else {.}}
}

# Gets the number of presses for each key combination
getStats <- function(.data, 
                     s_col, # string, the name of the column with the keypresses
                     break_multitaps=FALSE # Breaks up something like <[Cmd: Tab]x3> into 3 separate <[Cmd: Tab]>'s
                                           #    If you're using n>1-grams, make sure it's "FALSE"
                     ) {
  .data %>%
    mutate_(TempCol = lazyeval::interp(quote(vvv), vvv=as.name(s_col))) %>%
    group_by(TempCol) %>%
    summarise(n=n()) %>%
    mutate(areModsPressed = ifelse(grepl("<\\[.*\\].*>",TempCol),1,0),
           Multiplier = ifelse(areModsPressed & grepl("x[0-9]+", TempCol),
                               stringr::str_extract(TempCol, "x[0-9]+") %>%
                                 stringr::str_sub(2) %>%
                                 as.numeric(),
                               1)) %>%
    {if (break_multitaps == TRUE) {
      (.) %>%
        mutate(TempCol = ifelse(areModsPressed==1,
                                stringr::str_replace(TempCol, "x[0-9]+>",">"),
                                TempCol)) %>%
        group_by(TempCol,areModsPressed) %>%
        summarise(n=sum(Multiplier*n))
    } else { (.) %>% select(-Multiplier) } } %>%
    rename_(.dots=setNames(list(quote(TempCol)),s_col)) %>%
    arrange(-n)
}


# A more generalized way of getting the key presses: this has the option of getting n-grams of subsequent key presses
nGramPresses <- function(.data, # e.g., `key_db`
                         process_id_df=NA, # generally, `tbl(selfspy_db, "process") %>% collect()` or the like
                         group_by_process=FALSE, # Whether or not you want to analyze keystrokes for processes individually
                         extra_clean_f=extraCleanUpStrings, # A function that operates on a vector that cleans up extra weird stuff. Set to NA to skip
                         n=1, # the n in the n-gram collection
                         key_delimter="-", # If n > 1, the string that joins key press strings in the n-gram strings
                         joiner_string="XXXXXX" # A string that will not appear in any keypresses--used for joining and separating rows
) {
  .data %>% 
    collect() %>% 
    mutate(StringLists = purrr::map(keys, ~memDecompress(.,type=c("gzip"), asChar=TRUE)) %>% 
             purrr::simplify() %>% 
             stringr::str_sub(2,-2) %>%
             str_split(", ") %>%
             purrr::map(~cleanUpStrings(.))) %>%
             {if (n>1) {
               mutate(., cleanStrings = purrr::map(StringLists,
                                                   ~purrr::reduce(1:(n-1),
                                                                  function(x,i) { paste0(x, key_delimter, lead(.,i))},.init=.) %>%
                                                     head(-(n-1)) %>%
                                                     paste0(collapse=joiner_string)) %>%
                        purrr::simplify()) %>%
                 tidyr::separate_rows(cleanStrings,sep=joiner_string) 
             } else if (n==1) {
               mutate(., cleanStrings = purrr::map(StringLists,
                                                   ~paste0(.,collapse=joiner_string)) %>%
                        purrr::simplify()) %>%
                 tidyr::separate_rows(cleanStrings,sep=joiner_string)
             }
             } %>%
    # If you give it a df of names for the process ids:
             {if (is.data.frame(process_id_df)) {
               left_join(.,rename(process_id_df,"process_id"=id),by="process_id") %>%
                 mutate(process_id=name) %>%
                 select(-name)
             } else {.}}  %>%
    # If there are extra clean-up functions you've passed in
             {if (is.function(extra_clean_f)) {
               (.) %>%
                 mutate(cleanStrings = extra_clean_f(cleanStrings))
             } else {.}} %>%
    # If you want to group it by process id
             {if (group_by_process == TRUE) {
               (.) %>%
                 group_by(process_id) %>%
                 tidyr::nest()
             } else {.}}
}
#############################################################################################
#############################      Examples   ###############################################
#############################################################################################
#############################################################################################

# An example of how to analyze without respect to processes (and breaks up multi-taps)
key_db %>% 
  getPresses(.,
             process_id_df    = process_db %>% select(-created_at) %>% collect(), 
             group_by_process = FALSE) %>%
  getStats(.,
           s_col="cleanStrings", 
           break_multitaps=TRUE) %>%
  arrange(-n)

# An example of how to analyze processes individually
key_db %>% 
  getPresses(.,
             process_id_df    = process_db %>% select(-created_at) %>% collect(), 
             group_by_process = TRUE) %>%
  mutate(data = purrr::map(data, ~getStats(.,
                                           s_col="cleanStrings",
                                           break_multitaps=FALSE))) %>%
  tidyr::unnest() %>% 
  arrange(-n)

# To see what presses you might have missed/characters that aren't cleaned up
key_db %>% 
  getPresses(process_db %>% select(-created_at) %>% collect(), FALSE) %>%
  # mutate(data=purrr::map(data, ~getStats(.,"cleanStrings", TRUE))) %>% tidyr::unnest() %>%
  getStats(.,"cleanStrings", TRUE) %>%
  select(cleanStrings,n) %>%
  filter(grepl("<.+: [^A-Z].+]>",cleanStrings) | # Find all modified things that don't start with a capital letter and are more than one character
         (str_length(cleanStrings)>1 & !grepl("<.+>",cleanStrings))) %>% # find multi-character strings that aren't modifiers
  arrange(-n) %>%
  as.data.frame()

# An example showing how to use the nGramPresses:
key_db %>% 
  nGramPresses(.,
               process_id_df    = process_db %>% select(-created_at) %>% collect(), 
               group_by_process = TRUE,
               n=4) %>%
  # getStats(., s_col="cleanStrings", break_multitaps=FALSE) %>%
  mutate(data = purrr::map(data, ~getStats(., s_col="cleanStrings", break_multitaps=FALSE))) %>%
  tidyr::unnest() %>%
  arrange(-n) %>% 
  filter(areModsPressed!=0) %>% 
  head(100) %>% as.data.frame()
