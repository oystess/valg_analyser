library(tidyverse)
library(dplyr)
library(RCurl)
library(lubridate)

#URL fra Poll og Poll sine nettsider
URL1 <- "http://www.pollofpolls.no/lastned.csv?tabell=liste_gallupserie&serieid=1&limit=0"
URL2 <- "http://www.pollofpolls.no/lastned.csv?tabell=liste_gallupserie&serieid=2&limit=0"
URL3 <- "http://www.pollofpolls.no/lastned.csv?tabell=liste_gallupserie&serieid=3&limit=0"
URL4 <- "http://www.pollofpolls.no/lastned.csv?tabell=liste_gallupserie&serieid=4&limit=0"
URL5 <- "http://www.pollofpolls.no/lastned.csv?tabell=liste_gallupserie&serieid=5&limit=0"
URL6 <- "http://www.pollofpolls.no/lastned.csv?tabell=liste_gallupserie&serieid=6&limit=0"
URL7 <- "http://www.pollofpolls.no/lastned.csv?tabell=liste_gallupserie&serieid=7&limit=0"
URL8 <- "http://www.pollofpolls.no/lastned.csv?tabell=liste_gallupserie&serieid=8&limit=0"
URL9 <- "http://www.pollofpolls.no/lastned.csv?tabell=liste_gallupserie&serieid=9&limit=0"

#Laster inn data 
test1 <- read_csv2(URL1,
                      skip = 2,
                      locale = locale(encoding = "Latin1"))
test2<- read_csv2(URL2,
                  skip = 2,
                  locale = locale(encoding = "Latin1"))
test3<- read_csv2(URL3,
                  skip = 2,
                  locale = locale(encoding = "Latin1"))
test4<- read_csv2(URL4,
                  skip = 2,
                  locale = locale(encoding = "Latin1"))
test5<- read_csv2(URL5,
                  skip = 2,
                  locale = locale(encoding = "Latin1"))
test6<- read_csv2(URL6,
                  skip = 2,
                  locale = locale(encoding = "Latin1"))
test7<- read_csv2(URL7,
                  skip = 2,
                  locale = locale(encoding = "Latin1"))
test8<- read_csv2(URL8,
                  skip = 2,
                  locale = locale(encoding = "Latin1"))
## kombinerer datasett
samlet <- test8 %>% 
  bind_rows(test1) %>% 
  bind_rows(test2) %>% 
  bind_rows(test3) %>% 
  bind_rows(test4) %>% 
  bind_rows(test5) %>% 
  bind_rows(test6) %>% 
  bind_rows(test7)

##Rydder i data
samlet <- samlet %>% 
  filter(Måling!= "Valg S-2017") %>% 
  gather(Ap:Andre, key = Parti, value=mid) %>%
  separate(Måling, c("hvem", "dato", "år"), sep = "-") %>% 
  separate(dato, c("dag", "måned"), sep = "/") %>% 
  separate(mid, c("Prosent", "Mandater"), sep = "\\(") %>% 
  mutate(
    dato = make_date( år, måned, dag)
  )
samlet$Mandater <- str_replace(samlet$Mandater,"\\)","") 
samlet$Prosent <- str_replace(samlet$Prosent,",",".") 
write_csv(samlet, "polls.csv")

guess_parser(data$Prosent)


