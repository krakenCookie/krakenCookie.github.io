library(tidyverse)
library(zplyr) # A package for some personal functions that I keep. Not necessary for the data cleaning, and not ACTUALLY related to `plyr` or `dplyr`. You can install it with `devtools::install_github("burchill/zplyr)`

# Change all these paths to whatever you're using/downloaded
main_path <- "~/Downloads/PDF_STuff/"

# These are the _edited_ files from `PFD Tables` under `Personal Finance Data` from `https://www.opensecrets.org/bulk-data/downloads`
#   See the regex on the blogpost for what I used to correct _most_ of the problems.
#   There might still be some lingering issues with line breaks that you'll have to correct yourself
income_file <- paste0(main_path, "PFD/PFDincome.txt")
assets_file <- paste0(main_path, "PFD/PFDasset.txt")

# These are the names of the candidates and the details of who ran / won each race
#   Called `Campaign Finance Data` on `https://www.opensecrets.org/bulk-data/downloads`
cand_2012_file <- paste0(main_path, "CandidateData/cands12.txt")
cand_2014_file <- paste0(main_path, "CandidateData/cands14.txt")
cand_2016_file <- paste0(main_path, "CandidateData/cands16.txt")
cand_2018_file <- paste0(main_path, "CandidateData/cands18.txt")

# Constants #########################################################
income_col_names <- c("ID","Chamber","CID","CalendarYear",
                      "ReportType","IncomeSource","Orgname",
                      "Ultorg","Realcode","Source","IncomeLocation",
                      "IncomeSpouseDep","IncomeType","IncomeAmt",
                      "IncomeAmtText","Dupe")

asset_col_names <- c("ID", "Chamber", "CID", "CalendarYear", "ReportType", "SenAB", "AssetSpouseJointDep", "AssetSource", "Orgname", "Ultorg", "RealCode", "Source", "AssetDescrip", "Orgname2", "Ultorg2", "RealCode2", "Source2", "AssetSourceLocation", "AssetValue", "AssetExactValue", "AssetDividends", "AssetRent", "AssetInterest", "AssetCapitalGains", "AssetExemptedFund", "AssetExemptedTrust", "AssetQualifiedBlindTrust", "AssetTypeCRP", "OtherTypeIncome", "AssetIncomeAmtRange", "AssetIncomeAmountText", "AssetIncomeAmt", "AssetPurchased", "AssetSold", "AssetExchanged", "AssetDate", "AssetDateText", "AssetNotes", "Dupe")

candidate_col_names <- c("Cycle", "FECCandID", "CID", "FirstLastP", "Party", "DistIDRunFor", "DistIDCurr", "CurrCand", "CycleCand", "CRPICO", "RecipCode", "NoPacs")

# Utility functions #################################################

# Calculates empirical logit. `p_is_success` is a boolean on whether `p` is the number of successes (vs. the proportion of successes of `n`)
emp_logis <- function(p, n, p_is_success) {
  if (is.null(p_is_success)) stop("You need to say whether p is a probability or number of successes!")
  if (p_is_success==TRUE) return(log10((p + 0.5)/(n - p + 0.5)))
  else return(log10((p*n + 0.5)/(n - p*n + 0.5)))
}

read_data_file <- function(path, col.names, ...) {
  data.table::fread(path, sep=",", quote="|", header=FALSE, col.names = col.names,
                    stringsAsFactors = FALSE, ...) %>%
    as.tibble()
}
# if it has no non-alpha-numeric-characters other than commas, dots, digits, and dollor signs
is_money_amount <- function(char) {
  char %>% trimws() %>%
    # TRUE for a string:
    #   * either starts with '$' once or not
    #   * and then only consists of digits, dots, or commas
  { grepl("^\\${0,1}[0-9,.]+$", .) }
}
white_space_to_NA <- function(df) {
  df %>%
    mutate_if(is.character,
              ~ifelse(trimws(.) == "", NA, .))
}
# A 'prettier' way of giving warnings from the checks
pretty_warning <- function(df, message, display_row, secondary_row=NULL, group_by_secondary=FALSE) {
  if (nrow(df) == 0) return(FALSE)
  if (is.null(secondary_row))
    warning(message, paste0(df[[display_row]], collapse=", "), call.=FALSE)
  else {
    if (group_by_secondary==TRUE) {
      list_string <- purrr::map_chr(
        unique(df[[secondary_row]]),
        function(secondary_val) {
          new_df <- df %>% filter(!! rlang::sym(secondary_row) == secondary_val)
          list_string <- paste(new_df[[display_row]], collapse=", ")
          # print()
          paste0("  ", secondary_val, ": ", list_string)
        }) %>%
        paste(collapse="\n")
      warning(message, "\n", list_string, call. = FALSE)
    } else {
      list_string <- paste0(df[[display_row]], " (", df[[secondary_row]], ")",  collapse=", ")
      warning(message, list_string, call. = FALSE)
    }
  }
}

# Cleaning newly-read files ########################################
clean_candidate_df <- function(df) {
  df %>%
    mutate(didTheyWin = substr(RecipCode,2,2) == "W",
           inPrimary = CurrCand == "Y",
           didTheyRun = CycleCand == "Y") %>%
    filter(didTheyRun == TRUE) %>%
    mutate(isIncumbent = CRPICO == "I",
           NoPacs = NoPacs == "Y") %>%
    select(-CurrCand, -CycleCand) %>%
    white_space_to_NA()
}
clean_income_df <- function(df) {
  df %>%
    # Supposing capitalization doesn't matter here
    mutate_at(vars(Chamber, IncomeSpouseDep, Dupe),
              tolower) %>%
    filter(Dupe != "d") %>%
    filter(Chamber %in% c("s","h")) %>%
    mutate(CalendarYear = 2000 + as.numeric(CalendarYear),
           isMoneyfiable = is_money_amount(IncomeAmtText) &
             is.na(IncomeAmt),

           # If the income amount can be turned into a number, do it
           ExtendedIncomeAmt = ifelse(
             isMoneyfiable==T,
             readr::parse_number(
               IncomeAmtText,
               locale = readr::locale(decimal_mark=".",
                                      grouping_mark=",")),
             IncomeAmt),
           isOver1KOption = IncomeAmtText == "Over $1,000") %>%
    select(-Dupe) %>%
    # Fix handwritten NAs
    mutate(IncomeAmtText = ifelse(IncomeAmtText == "N/A" |
                                    IncomeAmtText == "NA",
                                  NA, IncomeAmtText)) %>%
    white_space_to_NA()
}

# Checking processed files for weird things ########################
check_candidate_df <- function(df) {
  no_winners <- df %>%
    group_by(DistIDRunFor, Cycle) %>%
    summarise(NoWins = all(didTheyWin == FALSE)) %>%
    filter(NoWins==TRUE) %>% arrange(Cycle)
  ran_more_than_once <- df %>%
    group_by(CID, Cycle) %>%
    summarise(n=n()) %>%
    filter(n>1) %>% arrange(Cycle)
  won_but_not_in_primary <- df %>%
    group_by(CID, DistIDRunFor, Cycle) %>%
    summarise(weird = any(didTheyWin == TRUE & (inPrimary == F | didTheyRun == F))) %>%
    filter(weird==TRUE) %>% arrange(Cycle)
  pretty_warning(no_winners, "These races did not have 'winners': ",
                 "DistIDRunFor", "Cycle", TRUE)
  pretty_warning(ran_more_than_once, "These candidates ran more than once per cycle: ",
                 "CID", "Cycle", TRUE)
  pretty_warning(won_but_not_in_primary, "These candidates won without running/being in the primary? ",
                 "CID", "Cycle")

  invisible(df)
}
check_income_df <- function(df) {
  negative_vals <- df %>% filter(ExtendedIncomeAmt < 0)
  incomprehensible <- df %>%
    filter(isMoneyfiable == F &
             isOver1KOption == F &
             !is.na(IncomeAmtText) &
             is.na(IncomeAmt))
  pretty_warning(negative_vals, "These IDs have negative income amounts: ", "ID")
  pretty_warning(incomprehensible, "These IDs have income amounts that can't be parsed: ", "ID")
  invisible(df)
}
# Other ##############################################
add_pfd_data <- function(canidate_df, pfd_df, newColName) {
  small_pfd <- pfd_df %>%
    filter(CID %in% canidate_df$CID) %>%
    tidyr::nest(-CID,
                .key = !! newColName)
  left_join(canidate_df, small_pfd, by="CID")
}

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

canidata <- bind_rows(
  read_data_file(cand_2012_file, candidate_col_names),
  read_data_file(cand_2014_file, candidate_col_names),
  read_data_file(cand_2016_file, candidate_col_names)
  # read_data_file(cand_2018_file, candidate_col_names) # Election results not released yet? Still?
) %>%
  clean_candidate_df() %>%
  check_candidate_df() %>%
  # Case-by-case cleaning
  # Michele Bachmann was listed in her race twice
  filter(!(Cycle==2012 & CID=="N00027493" & inPrimary == "FALSE")) %>%
  # Since the 2018 PFD data isn't released yet?
  filter(Cycle != 2018)

# Get the income data cleaned
pfd_income <- read_data_file(income_file, income_col_names) %>%
  clean_income_df() %>%
  check_income_df()

# Read the assets data (not really cleaned that much yet)
pfd_assets <- read_data_file(assets_file, asset_col_names)

# See which people have ANY asset data
any_data <- pfd_assets %>%
  mutate(CalendarYear = as.numeric(CalendarYear)) %>%
  filter(CalendarYear > 9) %>%
  distinct(CID, CalendarYear, ReportType)

# for the new senate candidates
new_sen_cands <- read_data_file(cand_2018_file, candidate_col_names) %>%
  clean_candidate_df() %>%
  check_candidate_df() %>%
  filter(grepl("..S[12]", DistIDRunFor)) %>%
  mutate(TempName = stringr::str_replace(FirstLastP, " \\([A-Z3]\\)", ""),
         State = stringr::str_sub(DistIDRunFor,end=2)) %>%
  distinct(Cycle, CID, FirstLastP, Party, DistIDRunFor, .keep_all = T)

new_sen_cands %>%
  rowwise() %>%
  mutate(x = length(strsplit(TempName, " ")[[1]])) %>%
  ungroup() %>%
  arrange(-x) %>%
  select(FirstLastP, x, TempName, DistIDRunFor)


# This is the point past which zplyr is required -----------------------------------

# Below was my attempt to see whether Republicans or Democrats were more likely to "hide" how much their spouses make---if their spouse makes more than $1k, they aren't required to specify how MUCH more, but can choose to do so anyway.
# The data suggested that Republicans were _less_ likely to hide their spouses' finances (a mild suprise lol), but then I realized that the new electronic filing system the Senate uses seems to _prevent_ applicants from revealing how much more than $1k their spouses make. At least, IIRC, there are no electronically-filed examples that give dollar amounts for spouses, so I'm assuming what I said was true.
# This kind of ruins the reliability of the comparison below, but I've included it for posterity

add_pfd_data(canidata, pfd_income, "income") %>%
  distinct(CID, .keep_all=TRUE) %>%
  zplyr::drop_empty_subs(income) %>% # These are zplyr functions
  zplyr::filter_in_sub(income, drop_empty = TRUE,
                       !(!is.na(ExtendedIncomeAmt) && ExtendedIncomeAmt < 1000),
                       IncomeSpouseDep == "s") %>%
  zplyr::summarise_sub(
    income,
    has_spouse_income = some(IncomeSpouseDep, ~ !is.na(.) && . == "s"),
    percent_exact = mean(ifelse(isOver1KOption == T, 0, 1)),
    majority_exact = ifelse(percent_exact >= 0.5, 1, 0),
    # Most of the time, you should never add proportions in proportion space.
    # I tried using empirical logit space, but I don't think it matters here.
    percent_emplog = zplyr::emp_logis(mean(ifelse(isOver1KOption==T, 0, 1)), n(), FALSE),
    spouse_sum = sum(ifelse(isOver1KOption == T, 1000,
                            ExtendedIncomeAmt))
  ) %>%
  filter(Party!="I") %>%
  ggplot(aes(x = Party, y=percent_emplog, color=Party)) +
  geom_violin() +
  zplyr::stat_errorbar()
