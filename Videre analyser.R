library(tidyverse)
library(dplyr)
library(RCurl)
library(lubridate)

source("Alle meningsmålinger.R")
rm(list = ls())
data<- read_csv("polls.csv")
                 
data$Parti <- parse_factor(data$Parti, levels = NULL)

data <- data %>% 
  mutate( posisjon = fct_collapse(Parti,
    Nydal = c("Høyre", "Frp", "Venstre", "KrF" ),
    Opposisjon= c("Ap","MDG","Sp", "SV", "Rødt", "Andre")
  ))

#flertall mandater
snitt_m_pos <- data %>%
  group_by(år, måned, Parti, posisjon) %>% 
  summarise(snitt_parti =mean(Mandater)) %>%
  group_by(år, måned, posisjon) %>% 
  summarise(snitt_m = sum(snitt_parti)) %>% 
mutate(
  måned2 = make_date(år, måned)
) %>% 
  group_by(år, måned) %>% 
  mutate( andel_m= snitt_m/sum(snitt_m))
  
snitt_m_pos %>% 
  filter(år>=2013) %>% 
  ggplot(aes(måned2, snitt_m))+
  geom_line(aes(color=posisjon))

#flertall prosent
snitt_p_pos <- data %>%
  group_by(år, måned, Parti, posisjon) %>% 
  summarise(snitt_parti =mean(Prosent)) %>%
  group_by(år, måned, posisjon) %>% 
  summarise(snitt_p = sum(snitt_parti)) %>% 
  mutate(
    måned2 = make_date(år, måned)
  ) %>% 
  group_by(år, måned) %>% 
  mutate( andel_p= snitt_p/sum(snitt_p))

snitt_p_pos %>% 
  filter(år>=2013) %>% 
  ggplot(aes(måned2, snitt_p))+
  geom_line(aes(color=posisjon))

#sammenligne prosentvis flertall mot mandater
snitt_p_m_pos <- select(snitt_m_pos, c("måned2", "posisjon", "andel_m")) %>% 
  left_join(snitt_p_pos) %>% 
  select(måned2, posisjon, andel_m, andel_p) %>% 
  
  snitt_p_m_pos %>% 
  ggplot(aes(x = måned2, y= andel_p))+
  geom_line(aes(color=posisjon))+
  geom_line(aes(x = måned2, y=andel_m, color=posisjon))


#månedlig gjennomsnitt i prosent
snitt_p <- data %>%
  group_by(år, måned, Parti) %>% 
  summarise(snitt_måned = mean(Prosent)) %>% 
  ungroup() %>% 
  mutate(
    måned2 = make_date(år, måned)
  ) 

snitt_p %>% 
  filter(Parti=="Frp" | Parti == "Høyre" | Parti == "Ap" | Parti == "KrF") %>% 
ggplot(aes(måned2, snitt_måned))+
  geom_smooth(aes(color=Parti), se = FALSE)

snitt_p %>% 
  filter(år==2017, Parti=="Frp" | Parti == "Høyre" | Parti == "Ap" | Parti == "KrF" | Parti == "Sp" | Parti == "Venstre") %>% 
  ggplot(aes(måned2, snitt_måned))+
  geom_smooth(aes(color=Parti), se = FALSE)


snitt_p %>% 
  filter(år==2017, Parti=="KrF" | Parti =="Sp") %>% 
  ggplot(aes(måned2, snitt_måned))+
  geom_line(aes(color=Parti))



