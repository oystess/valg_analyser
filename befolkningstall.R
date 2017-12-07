


befolkning_k <- read_csv2("http://data.ssb.no/api/v0/dataset/104857.csv?lang=no")


options(encoding="UTF-8")
library(httr)
# henter rjstat bibliotek for behandling av JSON-stat
library(rjstat)
# Adresse til et ferdig json-stat datasett for Detaljomsetningsindeksen
url <- "http://data.ssb.no/api/v0/dataset/104857.json?lang=no"
d.tmp<-GET(url)
# Henter ut innholdet fra d.tmp som tekst deretter bearbeides av fromJSONstat
sbtabell <- fromJSONstat(content(d.tmp, "text"))
# Henter ut kun datasettet fra sbtabell
kommunedata <- sbtabell[[1]]
# Viser datasettet

#sysselsettingsandel
http://data.ssb.no/api/v0/dataset/100145.json?lang=no