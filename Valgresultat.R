library(tidyverse)
library(readxl)
library(stringr)

###Valgersultat

valg2017 <- read_csv2("valg2017_parti.csv")

kommune2017 <- valg2017 %>%
  group_by(Fylkenavn, Kommunenavn, Kommunenummer, Partikode, Partinavn) %>% 
  summarise( "stemmer17" = sum(`Antall stemmer totalt`)) %>%
  group_by(Fylkenavn, Kommunenavn, Kommunenummer) %>% 
  mutate( "prosent17" = stemmer17/sum (stemmer17))

valg2013 <- read_csv2("valg2013_parti.csv")

kommune2013 <- valg2013 %>%
  group_by(Kommunenummer, Partikode, Partinavn) %>% 
  summarise( "stemmer13" = sum(`Antall stemmer totalt`))


tonsberg <- valg2013 %>% 
  #Kommuner som ble Tønsberg https://www.ssb.no/offentlig-sektor/kommunekatalog/endringer-i-de-regionale-inndelingene/kommunesammenslainger-og-endringer-i-fylkesinndelingene#Kommunesammenslinger
  filter(Kommunenummer== "0706"| Kommunenummer=="0719"| Kommunenummer=="0720") %>% 
  group_by(Partikode, Partinavn) %>% 
  summarise(stemmer13=sum(`Antall stemmer totalt`)) %>% 
  mutate(Kommunenummer = "0710") %>% 
  rekkefølge <- names(kommune2013) %>% 
  select(rekkefølge[-5])

kommune2013 <- kommune2013 %>% 
  filter(Kommunenummer!= "0706"| Kommunenummer!="0719"| Kommunenummer!="0720") %>% 
  rbind(tonsberg) %>% 
  group_by(Kommunenummer) %>% 
  mutate( "prosent13" = stemmer13/sum (stemmer13))



indeks <- read_xlsx("distriktstall.xlsx") %>% 
  separate(Kommunenavn, c("Kommunenummer", "Kommunenavn"), sep = " ", extra = "merge")


samlet <- left_join(kommune2017, kommune2013)
samlet <- left_join(samlet, indeks, by= "Kommunenummer")

samlet <- samlet %>% 
  mutate( endring_s = (stemmer17/stemmer13 -1)) %>% 
  mutate( endring_p = prosent17-prosent13)

samlet %>% 
  filter( Partikode=="SP"| Partikode=="A") %>%
  filter( Kommunenummer!= "1871") %>%
  filter( `B16-O`<=25000) %>% 
ggplot(aes(befvekst10, prosent13))+
  geom_point(aes(color=Partinavn))

samlet %>% 
  filter(Partikode=="H"| Partikode=="FRP") %>%
  filter( Kommunenummer!= "1871") %>% 
  ggplot(aes(befvekst10, endring_p))+
  geom_point(aes(color=Partinavn))


samlet %>% 
  filter( Partikode=="SP"| Partikode=="A") %>%
  filter( Kommunenummer!= "1871") %>% 
  ggplot(aes(befvekst10, endring_p))+
  geom_point(aes(color=Partinavn))

samlet %>% 
  filter( Partikode=="KRF"| Partikode=="V") %>%
  filter( Kommunenummer!= "1871") %>% 
  ggplot(aes(befvekst10, endring_s))+
  geom_point(aes(color=Partinavn))

samlet %>% 
  filter( Partikode=="SP"| Partikode=="H") %>%
  filter( Kommunenummer!= "1871") %>% 
  ggplot(aes(NIBR11, endring_p))+
  geom_point(aes(color=Partinavn))


samlet %>% 
  filter( Partikode=="SP"| Partikode=="H") %>%
  filter( `B16-O`<= 80000) %>% 
  ggplot(aes(`B16-O`, befvekst10))+
  geom_point(aes(color=Partinavn))



tonsberg <- valg2013 %>% 
  #Kommuner som ble Tønsberg https://www.ssb.no/offentlig-sektor/kommunekatalog/endringer-i-de-regionale-inndelingene/kommunesammenslainger-og-endringer-i-fylkesinndelingene#Kommunesammenslinger
  filter(Kommunenummer== "0706"| Kommunenummer=="0719"| Kommunenummer=="0720") %>% 
  group_by(Partikode, Partinavn) %>% 
  summarise(stemmer13=sum(`Antall stemmer totalt`)) %>% 
  mutate(Kommunenummer = "0710") %>% 
  rekkefølge <- names(kommune2013) %>% 
  select(rekkefølge[-5])







