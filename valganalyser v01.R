
library(tidyverse)
library(readxl)
library(stringr)

norstat2 <- read_csv2("myfilename-2.csv",
          skip = 2,
          locale = locale(encoding = "Latin1"))

norstat3 <- norstat2 %>% 
  separate(Måling, c("hvem", "dato", "år"), sep = "-") %>% 
  separate(dato, c("dag", "måned"), sep = "/") %>% 
  separate(Ap, c("AP%", "APM"), sep = "\\(") %>% 
  separate(Høyre, c("Høyre%", "HøyreM"), sep = "\\(") %>%
  separate(Frp, c("Frp%", "FrpM"), sep = "\\(") %>% 
  separate(SV, c("SV%", "SVM"), sep = "\\(") %>% 
  separate(Sp, c("Sp%", "SpM"), sep = "\\(") %>% 
  separate(KrF, c("KrF%", "KrFM"), sep = "\\(") %>% 
  separate(Venstre, c("Venstre%", "VenstreM"), sep = "\\(") %>% 
  separate(MDG, c("MDG%", "MDGM"), sep = "\\(") %>% 
  separate(Rødt, c("Rødt%", "RødtM"), sep = "\\(") %>% 
  separate(Andre, c("Andre%", "AndreM"), sep = "\\(") %>% 
  gather("AP%":"AndreM", key = antall, value = verdi)

norstat3$verdi <- str_replace(norstat3$verdi,"\\)","")

norstat4 <- spread(norstat3, key = antall, value = verdi)

norstat5 <- select(norstat4,hvem, dag, måned, år, "AP%", "Høyre%", "Frp%", 
                   "SV%", "Sp%", "KrF%", "Venstre%", 
                    "MDG%","Rødt%", "Andre%",
                   "APM", "HøyreM", "FrpM", 
                   "SVM", "SpM", "KrFM", "VenstreM", 
                   "MDGM","RødtM", "AndreM"
                  )
norstat5 <-filter(norstat5, dag!=2017)

write_csv(norstat5, "norstat5.csv")




