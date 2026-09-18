#!/usr/bin/env python3
"""
Analyse: Befolkningsutvikling og partioppslutning i norske kommuner 1987–2025
Sentralanalyse: Senteropprøret 1989→1993 og dets strukturelle drivere

Datakilder (data/processed/):
  - stortingsvalg_2024.csv:    SSB 08092, 1989–2025, 357 kommuner (2024-grenser)
  - kommunestyrevalg_2024.csv: SSB 01180, 1987–2023, 357 kommuner (2024-grenser)
  - befolkning_2024.csv:       SSB 07459, 1986–2026, 357 kommuner (2024-grenser)

Støttefiler (data/raw/):
  - sentralitet.csv:           SSBs sentralitetsindeks (pre-2020 koder, mappes via kom_mapping.csv)
  - kom_mapping.csv:           Historisk→2024 kommunekodemapping
"""

import warnings
import csv as csvmod
import numpy as np
import pandas as pd
import statsmodels.api as sm
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

PROCESSED = "data/processed"
RAW       = "data/raw"

PARTIER = {
    "01": "Ap", "02": "FrP", "03": "Høyre", "04": "KrF",
    "05": "Sp", "06": "SV", "07": "Venstre", "08": "MDG", "55": "Rødt",
}

PARTI_FARGER = {
    "Ap": "#e4202c", "FrP": "#003f7f", "Høyre": "#0065f1", "KrF": "#ffd700",
    "Sp": "#009900", "SV": "#eb4040", "Venstre": "#00b050",
    "MDG": "#3cb371", "Rødt": "#aa0000",
}

SENTRALITET_NAVN = {"0": "Minst sentrale", "1": "Mindre sentrale",
                    "2": "Noe sentrale", "3": "Sentrale"}
SENT_FARGER = {"0": "#d62728", "1": "#ff7f0e", "2": "#2ca02c", "3": "#1f77b4"}

# ── ORFØRENDE, IKKE-GENERERTE SEKSJONER ────────────────────────────────────────
# Disse to seksjonene ("Proteststemmen vandrer" og "Sp 2017→2021: alle 351
# kommuner") produseres ikke av noe skript i scripts/ — de fantes bare som
# frosset innhold i committet index.html. Kopiert inn her 2026-07-18 slik at de
# overlever full regenerering (jf. README «Regenererings-advarsel»). Innholdet
# er statisk (siste kjente tall/figurer); ingen kildeskript beregner dem på nytt.
PROTEST_HTML_STATIC = """<!-- === PROTESTSTEMMEN VANDRER (generert) === -->
<section id="protest" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
  <div class="mb-4">
    <h2 class="text-xl font-bold text-slate-900 mb-2">Proteststemmen vandrer</h2>
    <p class="text-slate-500 text-sm leading-relaxed">
      I kommuner med langvarig befolkningsnedgang har en gruppe velgere brutt med sitt tradisjonelle
      parti <em>to ganger</em> — fra Ap til Sp i 2017, og fra Sp til FrP i 2025. Det som binder de
      to bruddene er ikke ideologi, men vedvarende mistillit til styringspartiene.
    </p>
  </div>

  <h3 class="font-semibold text-slate-800 mt-6 mb-1">Ap, Sp og FrP i lav-sentralitets nedgangskommuner 1989–2025</h3>
  <p class="text-slate-500 text-sm mb-2">
    I 1989 hadde Ap 56 % i disse kommunene. EU-mobiliseringen i 1993 halverte det.
    Sp doblet seg igjen i 2017–2021. I 2025 kollapser Sp — og FrP tar det meste.
  </p>
  <div style="height:420px; width:100%;">                            <div id="1c8ddd58-7d88-4e17-acc1-b110661a0776" class="plotly-graph-div" style="height:100%; width:100%;"></div>            <script>                window.PLOTLYENV=window.PLOTLYENV || {};                                if (document.getElementById("1c8ddd58-7d88-4e17-acc1-b110661a0776")) {                    Plotly.newPlot(                        "1c8ddd58-7d88-4e17-acc1-b110661a0776",                        [{"hovertemplate":"\u003cb\u003eAp\u003c\u002fb\u003e %{x}: %{y:.1f}%\u003cextra\u003e\u003c\u002fextra\u003e","line":{"color":"#e4202c","width":2.5},"marker":{"size":7},"mode":"lines+markers","name":"Ap","text":["56.4%","34.3%","35.0%","27.5%","36.4%","37.6%","35.9%","28.8%","28.3%","31.8%"],"x":{"dtype":"i2","bdata":"xQfJB80H0QfVB9kH3QfhB+UH6Qc="},"y":{"dtype":"f8","bdata":"5I3MI38wTEB+UlfzWihBQFK4HoVrg0FAMwysVSh0O0B0qJA7zS9CQAV6aNs4ykJAHeKpXHj3QUDoHO1WWtc8QOEVVrBYSzxAZYA5y+bXP0A="},"type":"scatter"},{"hovertemplate":"\u003cb\u003eSp\u003c\u002fb\u003e %{x}: %{y:.1f}%\u003cextra\u003e\u003c\u002fextra\u003e","line":{"color":"#009900","width":2.5},"marker":{"size":7},"mode":"lines+markers","name":"Sp","text":["9.6%","32.2%","19.8%","16.4%","18.1%","17.8%","17.4%","31.0%","35.1%","18.6%"],"x":{"dtype":"i2","bdata":"xQfJB80H0QfVB9kH3QfhB+UH6Qc="},"y":{"dtype":"f8","bdata":"Bd1e0hgtI0CyOphg3hZAQD0K16NwxjNAwKLa2bdwMECLhCfynyUyQHqGJsqP2DFA7WnFyIRlMUAGMCnvgQE\u002fQFAloxyJjkFAihBvV92TMkA="},"type":"scatter"},{"hovertemplate":"\u003cb\u003eFrP\u003c\u002fb\u003e %{x}: %{y:.1f}%\u003cextra\u003e\u003c\u002fextra\u003e","line":{"color":"#003f7f","width":2.5},"marker":{"size":7},"mode":"lines+markers","name":"FrP","text":["6.2%","2.8%","9.9%","12.1%","18.5%","19.9%","14.5%","13.0%","10.8%","23.9%"],"x":{"dtype":"i2","bdata":"xQfJB80H0QfVB9kH3QfhB+UH6Qc="},"y":{"dtype":"f8","bdata":"zNHj9zb9GEDuinMB4msGQHsUrkfh2CNA3MYwsFYhKEDfeX0GXXUyQM7sU\u002fS05zNACu7ekH0ELUAXS36x5BcqQHstfqNGoyVAuavuHRLlN0A="},"type":"scatter"}],                        {"template":{"data":{"barpolar":[{"marker":{"line":{"color":"white","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"white","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"#C8D4E3","linecolor":"#C8D4E3","minorgridcolor":"#C8D4E3","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"#C8D4E3","linecolor":"#C8D4E3","minorgridcolor":"#C8D4E3","startlinecolor":"#2a3f5f"},"type":"carpet"}],"choropleth":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"choropleth"}],"contourcarpet":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"contourcarpet"}],"contour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"contour"}],"heatmap":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"heatmap"}],"histogram2dcontour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2dcontour"}],"histogram2d":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2d"}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"mesh3d":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"mesh3d"}],"parcoords":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"parcoords"}],"pie":[{"automargin":true,"type":"pie"}],"scatter3d":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatter3d"}],"scattercarpet":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattercarpet"}],"scattergeo":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergeo"}],"scattergl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergl"}],"scattermapbox":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattermapbox"}],"scattermap":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattermap"}],"scatterpolargl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolargl"}],"scatterpolar":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolar"}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"scatterternary":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterternary"}],"surface":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"surface"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}]},"layout":{"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"autotypenumbers":"strict","coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]],"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]},"colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"geo":{"bgcolor":"white","lakecolor":"white","landcolor":"white","showlakes":true,"showland":true,"subunitcolor":"#C8D4E3"},"hoverlabel":{"align":"left"},"hovermode":"closest","mapbox":{"style":"light"},"paper_bgcolor":"white","plot_bgcolor":"white","polar":{"angularaxis":{"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":""},"bgcolor":"white","radialaxis":{"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":""}},"scene":{"xaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"},"yaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"},"zaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"ternary":{"aaxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""},"baxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""},"bgcolor":"white","caxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""}},"title":{"x":0.05},"xaxis":{"automargin":true,"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":"","title":{"standoff":15},"zerolinecolor":"#EBF0F8","zerolinewidth":2},"yaxis":{"automargin":true,"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":"","title":{"standoff":15},"zerolinecolor":"#EBF0F8","zerolinewidth":2}}},"xaxis":{"tickmode":"array","tickvals":[1989,1993,1997,2001,2005,2009,2013,2017,2021,2025]},"yaxis":{"title":{"text":"Stemmeandel (%)"},"ticksuffix":"%"},"legend":{"x":0.01,"y":0.99},"title":{"text":"Ap, Sp og FrP i lav-sentralitets nedgangskommuner 1989\u20132025"},"height":420},                        {"responsive": true}                    )                };            </script>        </div>

  <h3 class="font-semibold text-slate-800 mt-8 mb-1">Hvem fikk Sps stemmer? 1993→1997 vs 2021→2025</h3>
  <p class="text-slate-500 text-sm mb-2">
    Begge ganger mistet Sp ~16–17 pp i sine kjerneområder. Men protestsømmene gikk i helt
    ulik retning: <strong>etter 1993 tok KrF 64 %</strong> av tapet —
    <strong>etter 2021 tok FrP 62 %</strong>. Ap fikk 14 % etter 1993 og 27 % etter 2021.
  </p>
  <div style="height:420px; width:100%;">                            <div id="7b1e13c1-9ed9-4bdf-9b34-b33160f07913" class="plotly-graph-div" style="height:100%; width:100%;"></div>            <script>                window.PLOTLYENV=window.PLOTLYENV || {};                                if (document.getElementById("7b1e13c1-9ed9-4bdf-9b34-b33160f07913")) {                    Plotly.newPlot(                        "7b1e13c1-9ed9-4bdf-9b34-b33160f07913",                        [{"marker":{"color":["#eb4040","#0065f1","#2d8653","#00b050","#e4202c","#003f7f","#f5a623"]},"orientation":"h","showlegend":false,"text":["-2.8 pp","-0.6 pp","+0.1 pp","+1.2 pp","+2.3 pp","+5.7 pp","+10.5 pp"],"textfont":{"size":10},"textposition":"outside","x":{"dtype":"f8","bdata":"IIXrUbi+BsAAAAAAAEDiv8EQGgyhwbA\u002fjsL1KFxv8j9YuB6F63ECQFK4HoXr8RZA\u002f\u002f\u002f\u002f\u002f\u002f\u002f7JEA="},"y":["SV","H\u00f8yre","MDG","Venstre","Ap","FrP","KrF"],"type":"bar","xaxis":"x","yaxis":"y"},{"marker":{"color":["#0065f1","#eb4040","#00b050","#f5a623","#2d8653","#8B0000","#e4202c","#003f7f"]},"orientation":"h","showlegend":false,"text":["-1.4 pp","-0.3 pp","+0.1 pp","+0.5 pp","+0.6 pp","+2.3 pp","+4.6 pp","+10.5 pp"],"textfont":{"size":10},"textposition":"outside","x":{"dtype":"f8","bdata":"OPvwGXYF9r\u002fQay4kTanQv4SzD59hV8A\u002fyC+W\u002fGLJ3z+MCR7ME\u002fXjP710kxgEVgJACNejcD2KEkCoxks3iQElQA=="},"y":["H\u00f8yre","SV","Venstre","KrF","MDG","R\u00f8dt","Ap","FrP"],"type":"bar","xaxis":"x2","yaxis":"y2"}],                        {"template":{"data":{"barpolar":[{"marker":{"line":{"color":"white","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"white","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"#C8D4E3","linecolor":"#C8D4E3","minorgridcolor":"#C8D4E3","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"#C8D4E3","linecolor":"#C8D4E3","minorgridcolor":"#C8D4E3","startlinecolor":"#2a3f5f"},"type":"carpet"}],"choropleth":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"choropleth"}],"contourcarpet":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"contourcarpet"}],"contour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"contour"}],"heatmap":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"heatmap"}],"histogram2dcontour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2dcontour"}],"histogram2d":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2d"}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"mesh3d":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"mesh3d"}],"parcoords":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"parcoords"}],"pie":[{"automargin":true,"type":"pie"}],"scatter3d":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatter3d"}],"scattercarpet":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattercarpet"}],"scattergeo":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergeo"}],"scattergl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergl"}],"scattermapbox":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattermapbox"}],"scattermap":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattermap"}],"scatterpolargl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolargl"}],"scatterpolar":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolar"}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"scatterternary":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterternary"}],"surface":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"surface"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}]},"layout":{"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"autotypenumbers":"strict","coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]],"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]},"colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"geo":{"bgcolor":"white","lakecolor":"white","landcolor":"white","showlakes":true,"showland":true,"subunitcolor":"#C8D4E3"},"hoverlabel":{"align":"left"},"hovermode":"closest","mapbox":{"style":"light"},"paper_bgcolor":"white","plot_bgcolor":"white","polar":{"angularaxis":{"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":""},"bgcolor":"white","radialaxis":{"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":""}},"scene":{"xaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"},"yaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"},"zaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"ternary":{"aaxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""},"baxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""},"bgcolor":"white","caxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""}},"title":{"x":0.05},"xaxis":{"automargin":true,"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":"","title":{"standoff":15},"zerolinecolor":"#EBF0F8","zerolinewidth":2},"yaxis":{"automargin":true,"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":"","title":{"standoff":15},"zerolinecolor":"#EBF0F8","zerolinewidth":2}}},"xaxis":{"anchor":"y","domain":[0.0,0.45],"title":{"text":"Endring (pp)"},"ticksuffix":" pp"},"yaxis":{"anchor":"x","domain":[0.0,1.0]},"xaxis2":{"anchor":"y2","domain":[0.55,1.0],"title":{"text":"Endring (pp)"},"ticksuffix":" pp"},"yaxis2":{"anchor":"x2","domain":[0.0,1.0]},"annotations":[{"font":{"size":16},"showarrow":false,"text":"Etter 1993-oppr\u00f8ret: Sp 45%\u219228% (n=32)","x":0.225,"xanchor":"center","xref":"paper","y":1.0,"yanchor":"bottom","yref":"paper"},{"font":{"size":16},"showarrow":false,"text":"Etter 2021-oppr\u00f8ret: Sp 49%\u219232% (n=30)","x":0.775,"xanchor":"center","xref":"paper","y":1.0,"yanchor":"bottom","yref":"paper"}],"shapes":[{"line":{"color":"gray","dash":"dot"},"type":"line","x0":0,"x1":0,"xref":"x","y0":0,"y1":1,"yref":"y domain"},{"line":{"color":"gray","dash":"dot"},"type":"line","x0":0,"x1":0,"xref":"x2","y0":0,"y1":1,"yref":"y2 domain"}],"margin":{"l":80,"r":80,"t":60,"b":40},"title":{"text":"Hvem fikk Sps stemmer? Sp-sterke perifere nedgangskommuner"},"height":420},                        {"responsive": true}                    )                };            </script>        </div>

  <h3 class="font-semibold text-slate-800 mt-8 mb-1">Aps «nedgangsbonus» 1989–2025</h3>
  <p class="text-slate-500 text-sm mb-2">
    Frem til 2013 fikk Ap konsekvent flere stemmer i nedgangskommuner enn i vekstkommuner
    (bonusen var +5–6 pp på topp). I 2017 forsvant bonusen. Ap er nå omtrent likt i alle kommunetyper.
  </p>
  <div style="height:480px; width:100%;">                            <div id="31e64f61-164c-4f9f-9324-7d6539392c02" class="plotly-graph-div" style="height:100%; width:100%;"></div>            <script>                window.PLOTLYENV=window.PLOTLYENV || {};                                if (document.getElementById("31e64f61-164c-4f9f-9324-7d6539392c02")) {                    Plotly.newPlot(                        "31e64f61-164c-4f9f-9324-7d6539392c02",                        [{"line":{"color":"#e4202c","width":2.5},"marker":{"size":7},"mode":"lines+markers","name":"Nedgangskommuner","x":{"dtype":"i2","bdata":"xQfJB80H0QfVB9kH3QfhB+UH6Qc="},"y":{"dtype":"f8","bdata":"cT+RrxntS0BY0RusU5hBQGMjbU\u002f\u002f1EFAfDjDhzMcPEBaU6X0xTVCQLHkF0t+0EJAmEgLB0T5QUCy2VYpUe48QCzJkHUzZTxAr39wb+ZZP0A="},"type":"scatter","xaxis":"x","yaxis":"y"},{"line":{"color":"#2ca02c","width":2.5},"marker":{"size":7},"mode":"lines+markers","name":"Vekstkommuner","x":{"dtype":"i2","bdata":"xQfJB80H0QfVB9kH3QfhB+UH6Qc="},"y":{"dtype":"f8","bdata":"KajbbcApSUCQCG7vRp1BQHOBKjT61UBALisGSngjOEBI8sKrA8E\u002fQA4tsp3vNkFAAxKbxQeEPkAPThM5fGw6QKeZMEwEhzpAWWuqTRJiPEA="},"type":"scatter","xaxis":"x","yaxis":"y"},{"marker":{"color":["#2ca02c","#e4202c","#2ca02c","#2ca02c","#2ca02c","#2ca02c","#2ca02c","#2ca02c","#2ca02c","#2ca02c"]},"name":"Bonus","showlegend":false,"text":["+5.5","-0.0","+2.0","+4.0","+4.7","+3.2","+5.4","+2.5","+1.9","+3.0"],"textfont":{"size":9},"textposition":"outside","x":{"dtype":"i2","bdata":"xQfJB80H0QfVB9kH3QfhB+UH6Qc="},"y":{"dtype":"f8","bdata":"QLqsDcoaFkAA4NxIDc2jvwA+VGij4P8\u002fcGro7dnFD0Cw0R72IKoSQDB6W9bqmAlAtPztIQG6FUAYXRyCpw4EQFD4Apby4v0\u002fsKIwDqG+B0A="},"type":"bar","xaxis":"x2","yaxis":"y2"}],                        {"template":{"data":{"barpolar":[{"marker":{"line":{"color":"white","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"white","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"#C8D4E3","linecolor":"#C8D4E3","minorgridcolor":"#C8D4E3","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"#C8D4E3","linecolor":"#C8D4E3","minorgridcolor":"#C8D4E3","startlinecolor":"#2a3f5f"},"type":"carpet"}],"choropleth":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"choropleth"}],"contourcarpet":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"contourcarpet"}],"contour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"contour"}],"heatmap":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"heatmap"}],"histogram2dcontour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2dcontour"}],"histogram2d":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2d"}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"mesh3d":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"mesh3d"}],"parcoords":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"parcoords"}],"pie":[{"automargin":true,"type":"pie"}],"scatter3d":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatter3d"}],"scattercarpet":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattercarpet"}],"scattergeo":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergeo"}],"scattergl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergl"}],"scattermapbox":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattermapbox"}],"scattermap":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattermap"}],"scatterpolargl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolargl"}],"scatterpolar":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolar"}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"scatterternary":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterternary"}],"surface":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"surface"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}]},"layout":{"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"autotypenumbers":"strict","coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]],"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]},"colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"geo":{"bgcolor":"white","lakecolor":"white","landcolor":"white","showlakes":true,"showland":true,"subunitcolor":"#C8D4E3"},"hoverlabel":{"align":"left"},"hovermode":"closest","mapbox":{"style":"light"},"paper_bgcolor":"white","plot_bgcolor":"white","polar":{"angularaxis":{"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":""},"bgcolor":"white","radialaxis":{"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":""}},"scene":{"xaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"},"yaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"},"zaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"ternary":{"aaxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""},"baxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""},"bgcolor":"white","caxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""}},"title":{"x":0.05},"xaxis":{"automargin":true,"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":"","title":{"standoff":15},"zerolinecolor":"#EBF0F8","zerolinewidth":2},"yaxis":{"automargin":true,"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":"","title":{"standoff":15},"zerolinecolor":"#EBF0F8","zerolinewidth":2}}},"xaxis":{"anchor":"y","domain":[0.0,1.0],"matches":"x2","showticklabels":false},"yaxis":{"anchor":"x","domain":[0.55,1.0],"title":{"text":"Ap%"},"ticksuffix":"%"},"xaxis2":{"anchor":"y2","domain":[0.0,1.0],"tickmode":"array","tickvals":[1989,1993,1997,2001,2005,2009,2013,2017,2021,2025]},"yaxis2":{"anchor":"x2","domain":[0.0,0.45],"title":{"text":"pp-gap"},"ticksuffix":" pp"},"annotations":[{"font":{"size":16},"showarrow":false,"text":"Aps stemmeandel etter befolkningsretning","x":0.5,"xanchor":"center","xref":"paper","y":1.0,"yanchor":"bottom","yref":"paper"},{"font":{"size":16},"showarrow":false,"text":"Nedgangsbonus (Nedgang \u2212 Vekst)","x":0.5,"xanchor":"center","xref":"paper","y":0.45,"yanchor":"bottom","yref":"paper"}],"shapes":[{"line":{"color":"gray","dash":"dot"},"type":"line","x0":0,"x1":1,"xref":"x2 domain","y0":0,"y1":0,"yref":"y2"}],"legend":{"x":0.01,"y":0.99},"height":480,"title":{"text":"Aps \u00abnedgangsbonus\u00bb 1989\u20132025"}},                        {"responsive": true}                    )                };            </script>        </div>

  <h3 class="font-semibold text-slate-800 mt-8 mb-1">Politisk volatilitet (Pedersen-indeks) per kommunetype</h3>
  <p class="text-slate-500 text-sm mb-2">
    Nedgangskommunene var dramatisk mer volatile enn vekstkommunene i 1989–1993 (EU-mobilisering)
    og igjen i 2013–2017 (Vedum/kommunereform). I 2021–2025 er alle kommunetyper like volatile —
    Sps kollaps driver uro bredt, den geografiske konsentrasjonen er visket ut.
  </p>
  <div style="height:400px; width:100%;">                            <div id="1625d04f-32d1-410e-8099-9836ac9d49a3" class="plotly-graph-div" style="height:100%; width:100%;"></div>            <script>                window.PLOTLYENV=window.PLOTLYENV || {};                                if (document.getElementById("1625d04f-32d1-410e-8099-9836ac9d49a3")) {                    Plotly.newPlot(                        "1625d04f-32d1-410e-8099-9836ac9d49a3",                        [{"marker":{"color":"#e4202c"},"name":"Nedgangskommuner","opacity":0.85,"x":["1989\u20131993","1993\u20131997","1997\u20132001","2001\u20132005","2005\u20132009","2009\u20132013","2013\u20132017","2017\u20132021","2021\u20132025"],"y":{"dtype":"f8","bdata":"84aLm9O3OkA1EEj0cfUyQG+ypRWoYC1A7b7S7it9MkBjfzf6tHUhQCW\u002fWPKLSChAPLCqq9guL0CBb15NPHslQH5QBeGIsDRA"},"type":"bar"},{"marker":{"color":"#2ca02c"},"name":"Vekstkommuner","opacity":0.85,"x":["1989\u20131993","1993\u20131997","1997\u20132001","2001\u20132005","2005\u20132009","2009\u20132013","2013\u20132017","2017\u20132021","2021\u20132025"],"y":{"dtype":"f8","bdata":"1yg26WxQNEAZJ5JxIrkxQCeGe+5vmi9AD8w+OZC9MkAC6wnqQgcgQFYOLbKdZytAFFO2UF1NJUDb0eS+CnMlQCb4s8BQXjNA"},"type":"bar"}],                        {"template":{"data":{"barpolar":[{"marker":{"line":{"color":"white","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"white","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"#C8D4E3","linecolor":"#C8D4E3","minorgridcolor":"#C8D4E3","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"#C8D4E3","linecolor":"#C8D4E3","minorgridcolor":"#C8D4E3","startlinecolor":"#2a3f5f"},"type":"carpet"}],"choropleth":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"choropleth"}],"contourcarpet":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"contourcarpet"}],"contour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"contour"}],"heatmap":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"heatmap"}],"histogram2dcontour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2dcontour"}],"histogram2d":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2d"}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"mesh3d":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"mesh3d"}],"parcoords":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"parcoords"}],"pie":[{"automargin":true,"type":"pie"}],"scatter3d":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatter3d"}],"scattercarpet":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattercarpet"}],"scattergeo":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergeo"}],"scattergl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergl"}],"scattermapbox":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattermapbox"}],"scattermap":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattermap"}],"scatterpolargl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolargl"}],"scatterpolar":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolar"}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"scatterternary":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterternary"}],"surface":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"surface"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}]},"layout":{"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"autotypenumbers":"strict","coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]],"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]},"colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"geo":{"bgcolor":"white","lakecolor":"white","landcolor":"white","showlakes":true,"showland":true,"subunitcolor":"#C8D4E3"},"hoverlabel":{"align":"left"},"hovermode":"closest","mapbox":{"style":"light"},"paper_bgcolor":"white","plot_bgcolor":"white","polar":{"angularaxis":{"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":""},"bgcolor":"white","radialaxis":{"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":""}},"scene":{"xaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"},"yaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"},"zaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"ternary":{"aaxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""},"baxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""},"bgcolor":"white","caxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""}},"title":{"x":0.05},"xaxis":{"automargin":true,"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":"","title":{"standoff":15},"zerolinecolor":"#EBF0F8","zerolinewidth":2},"yaxis":{"automargin":true,"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":"","title":{"standoff":15},"zerolinecolor":"#EBF0F8","zerolinewidth":2}}},"legend":{"x":0.01,"y":0.99},"title":{"text":"Pedersen-volatilitetsindeks per kommunetype 1989\u20132025"},"xaxis":{"title":{"text":"Periode"}},"yaxis":{"title":{"text":"Pedersen-indeks"}},"barmode":"group","height":400},                        {"responsive": true}                    )                };            </script>        </div>

</section>
<!-- === SLUTT PROTESTSTEMMEN === -->"""

SP_MATRISE_HTML_STATIC = """<!-- === SP MATRISE 2021 (generert) === -->
<section id="sp_matrise" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
  <div class="mb-4">
    <h2 class="text-xl font-bold text-slate-900 mb-2">Sp 2017→2021: alle 351 kommuner</h2>
    <p class="text-slate-500 text-sm leading-relaxed">
      Scatter-matrise med fire kvadranter (sentralitet × befolkningsretning).
      Hvert punkt er én kommune. Størrelsen er proporsjonal med befolkning (log-skalert).
      Boksene viser gjennomsnittlig ΔSp, Sp-nivå og andel av velgerne i gruppen.
    </p>
  </div>
  <div style="height:620px; width:100%;">                        <script>window.PlotlyConfig = {MathJaxConfig: 'local'};</script>
        <script charset="utf-8" src="https://cdn.plot.ly/plotly-3.6.0.min.js" integrity="sha256-QaOVwtVY0T02VaHrr6pnoHLCwayMJp4O5n4YyaE3rJk=" crossorigin="anonymous"></script>                <div id="dd937b89-1a5a-410a-8472-3cc499d67098" class="plotly-graph-div" style="height:100%; width:100%;"></div>            <script>                window.PLOTLYENV=window.PLOTLYENV || {};                                if (document.getElementById("dd937b89-1a5a-410a-8472-3cc499d67098")) {                    Plotly.newPlot(                        "dd937b89-1a5a-410a-8472-3cc499d67098",                        [{"customdata":[[14.7,24.0,9.2,"Mindre sentral"],[32.7,36.6,3.9,"Minst sentral"],[33.6,38.0,4.3,"Minst sentral"],[19.9,24.5,4.6,"Minst sentral"],[27.6,24.0,-3.6,"Minst sentral"],[17.6,22.1,4.5,"Minst sentral"],[13.0,18.5,5.5,"Mindre sentral"],[15.4,21.9,6.5,"Minst sentral"],[31.3,40.2,8.9,"Minst sentral"],[24.5,40.8,16.3,"Minst sentral"],[29.1,37.3,8.3,"Minst sentral"],[30.5,32.2,1.7,"Minst sentral"],[35.2,38.4,3.2,"Minst sentral"],[44.8,50.9,6.1,"Mindre sentral"],[33.0,38.6,5.6,"Minst sentral"],[43.8,42.9,-0.9,"Mindre sentral"],[19.4,22.7,3.3,"Mindre sentral"],[31.0,35.2,4.2,"Mindre sentral"],[44.0,47.1,3.1,"Minst sentral"],[35.0,40.0,5.0,"Mindre sentral"],[25.5,29.8,4.3,"Minst sentral"],[30.4,42.4,12.0,"Minst sentral"],[34.0,40.9,7.0,"Minst sentral"],[18.7,23.6,5.0,"Minst sentral"],[20.7,23.9,3.2,"Minst sentral"],[35.0,42.6,7.7,"Minst sentral"],[22.9,30.5,7.5,"Mindre sentral"],[23.5,30.1,6.6,"Mindre sentral"],[31.8,33.8,2.1,"Minst sentral"],[22.0,24.8,2.8,"Minst sentral"],[18.9,28.7,9.8,"Minst sentral"],[25.3,27.7,2.4,"Minst sentral"],[35.8,30.6,-5.2,"Minst sentral"],[36.1,30.2,-5.9,"Minst sentral"],[27.4,27.1,-0.4,"Minst sentral"],[72.3,55.5,-16.8,"Minst sentral"],[24.0,27.8,3.8,"Minst sentral"],[27.7,36.7,9.0,"Minst sentral"],[32.7,35.5,2.8,"Minst sentral"],[25.1,30.4,5.3,"Minst sentral"],[39.0,45.1,6.1,"Minst sentral"],[28.1,34.5,6.4,"Mindre sentral"],[36.3,37.2,0.9,"Minst sentral"],[31.7,38.8,7.0,"Minst sentral"],[46.4,50.5,4.1,"Minst sentral"],[48.0,50.8,2.7,"Minst sentral"],[50.5,48.0,-2.5,"Minst sentral"],[47.4,46.8,-0.6,"Minst sentral"],[46.0,49.6,3.6,"Minst sentral"],[47.0,50.0,3.0,"Minst sentral"],[35.4,43.2,7.9,"Minst sentral"],[50.0,56.7,6.6,"Minst sentral"],[50.2,53.7,3.5,"Minst sentral"],[46.7,51.2,4.5,"Minst sentral"],[36.7,39.4,2.7,"Minst sentral"],[27.7,30.4,2.8,"Minst sentral"],[24.1,30.6,6.6,"Minst sentral"],[30.6,36.8,6.2,"Minst sentral"],[24.7,33.2,8.5,"Minst sentral"],[38.3,46.0,7.7,"Minst sentral"],[40.8,44.6,3.8,"Minst sentral"],[27.0,25.8,-1.2,"Minst sentral"],[38.2,30.6,-7.6,"Minst sentral"],[26.6,31.6,5.1,"Minst sentral"],[41.1,44.4,3.3,"Minst sentral"],[37.8,41.2,3.5,"Minst sentral"],[25.1,30.5,5.5,"Minst sentral"],[19.8,26.4,6.5,"Minst sentral"],[21.0,27.6,6.6,"Mindre sentral"],[15.0,16.1,1.1,"Minst sentral"],[14.5,19.4,4.9,"Minst sentral"],[24.4,30.0,5.6,"Minst sentral"],[27.0,32.2,5.3,"Minst sentral"],[34.1,40.6,6.5,"Mindre sentral"],[6.1,11.1,5.1,"Minst sentral"],[31.6,37.8,6.1,"Minst sentral"],[27.5,34.3,6.8,"Minst sentral"],[39.2,39.0,-0.2,"Minst sentral"],[24.5,26.2,1.7,"Minst sentral"],[48.7,47.2,-1.5,"Minst sentral"],[36.8,34.7,-2.1,"Minst sentral"],[16.7,19.7,2.9,"Minst sentral"],[32.9,35.2,2.3,"Minst sentral"],[40.3,34.8,-5.5,"Mindre sentral"],[28.8,26.0,-2.8,"Minst sentral"],[15.1,28.0,12.9,"Mindre sentral"],[31.4,36.5,5.2,"Minst sentral"],[19.1,25.9,6.8,"Minst sentral"],[41.2,49.0,7.8,"Minst sentral"],[44.5,55.0,10.5,"Minst sentral"],[45.1,51.4,6.4,"Mindre sentral"],[47.6,50.7,3.2,"Minst sentral"],[39.0,46.6,7.6,"Minst sentral"],[30.8,38.3,7.5,"Minst sentral"],[35.6,45.2,9.6,"Mindre sentral"],[48.3,56.6,8.3,"Mindre sentral"],[25.3,27.2,1.9,"Minst sentral"],[54.8,51.5,-3.3,"Minst sentral"],[41.8,45.5,3.7,"Minst sentral"],[21.2,28.5,7.3,"Minst sentral"],[29.2,39.2,10.0,"Minst sentral"],[24.6,32.9,8.3,"Minst sentral"],[18.0,23.9,5.9,"Minst sentral"],[17.8,32.3,14.4,"Minst sentral"],[25.4,29.5,4.1,"Minst sentral"],[20.0,24.8,4.8,"Minst sentral"],[12.7,25.4,12.7,"Mindre sentral"],[36.3,40.2,3.9,"Minst sentral"],[35.1,41.7,6.6,"Minst sentral"],[16.6,17.1,0.5,"Minst sentral"],[18.0,28.1,10.1,"Minst sentral"],[11.9,24.5,12.6,"Minst sentral"],[14.5,25.0,10.5,"Minst sentral"],[18.4,24.2,5.8,"Minst sentral"],[22.6,31.3,8.7,"Minst sentral"],[10.0,19.9,9.9,"Minst sentral"],[23.4,28.8,5.4,"Minst sentral"],[17.0,30.6,13.6,"Mindre sentral"]],"hovertemplate":"\u003cb\u003e%{text}\u003c\u002fb\u003e\u003cbr\u003eSp 2017: %{customdata[0]}%  \u2192  2021: %{customdata[1]}%\u003cbr\u003e\u0394Sp: \u003cb\u003e%{customdata[2]:+.1f} pp\u003c\u002fb\u003e\u003cbr\u003e\u0394Pop 2011\u201321: %{x:.1f}%\u003cbr\u003eSentralitet: %{customdata[3]}\u003cextra\u003e\u003c\u002fextra\u003e","marker":{"color":"#d62728","line":{"color":"white","width":0.5},"opacity":0.75,"size":{"dtype":"f8","bdata":"x+uEW1QzKEDUY2rPAdQnQNnizvmsxChAm53YX1ZeKUAy4d\u002fbwiMgQP6rOxwSaShAsdVudaGeJ0BsU0E2eKwqQCDrR+7MEipABvFvobwAJ0C0+k29hoAoQAb78qqAyydA0bBWYMAeJkDHx\u002fqpadcmQN\u002fwS1VTcSVAE9gTgWrEIkDSI0ZJBX0sQI221HFi6iVA56EEf+XdJUCtyU1RhNYlQAr6sTBWqyZAKxuxfN6WIkBRBnw4sX8lQLNO5VdWaCpAyzIe2oPVJkDG6cxVJAUlQLDNqWlCWSlADdqVuaTJJkCgi+W535wnQNu9l7CkFSdApbE83Hs4I0B15rgIMdsjQLhsz2nepSVA+UZkZG7NJ0CduThQxDApQFIScrpokilASyKXveAQJUAV8KslVm8oQODk0+P3XylAhns\u002ffGU0KUCY4E1agoAnQGiS1+gIkSlAM\u002fZE3UB0KkA2vmWrPaonQAraPCTVwyZAv8o6bwjBJUCWJ94730kmQKymXHa5aCdA+7R5v9o+JkD+Cu7+9N4mQHXRbUbJwSdApGykKP4VJ0BKo\u002faL1DgnQGadEeEnWidAG9yUrOOpKEDJztS9zwMqQHKypvfdGSpAiFA1dQIuKEBNYKMfJ0sqQNE9XgrzHCdAcDro6kQeJkBsWLP5ivknQHiU\u002fnMTHipA4J75Qnt5J0CIiRv4xaAlQJC8YmR8PidAhna3Hr15JUDIlTT5b7EkQGQc5b8neSZA1A0084dULUAQ6Y99UXksQJbL1+lSCCxAorvpBM6ZJED8pZ+ngQ8lQFA9IohTISNASqP2i9Q4J0DGzZCc\u002f0ckQI0yhTdR6CVAVdWdrPgVKUB6WPksk8QnQCz9u45eHydA\u002fvGI2YPkKUDXEJhwJQUoQHRpEGR\u002f7SdAF5I2lYzQKEBOJdQffeYsQFWKKm\u002fezCRAZ7xLrMThKUCzi\u002fIQFeAmQNN5E8xRTSRAXVciITUNJ0Bk7oesZb8lQEqKRKvRpCJAK4pvc5iAJEDcbIIB9UsnQN\u002fwS1VTcSVAYXu69k0JJUACX7kh7yMjQMoMR4Tw5CZAbhZn5XXGJUAbdYx0rQ8nQHVjxmoCSSVA9DP9b9gaKEDQeb98E6QmQAIzvNXJESdAUQZ8OLF\u002fJUD9aOYFayUqQEemTn5axydAmbKPOVT0J0AAwDz6jPMkQOpLy66EVyVAC15BvG48KEABNAtmLN4oQHzFCno0mCVA\u002fWrA9VLqJ0Bkqf7WWNEkQOXlPAtX9yZAYtP8HhpjJEA="}},"mode":"markers","name":"Lav sent + Nedgang\u003cbr\u003e\u003csup\u003e118 kommuner \u00b7 7.0% av velgerne\u003c\u002fsup\u003e","text":["Lund","Hjelmeland","Suldal","Sauda","Utsira","Vanylven","Sande","Sunndal","Surnadal","Sm\u00f8la","Aure","Fjord","Bindal","S\u00f8mna","Vega","Vevelstad","Vefsn","Grane","Aarborte - Hattfjelldal","D\u00f8nna","Lur\u00f8y","Tr\u00e6na","R\u00f8d\u00f8y","Mel\u00f8y","Gildesk\u00e5l","Beiarn","Saltdal","S\u00f8rfold - Fuolld\u00e1","Steigen","L\u00f8dingen","R\u00f8st","V\u00e6r\u00f8y","Flakstad","B\u00f8","\u00d8ksnes","And\u00f8y","Moskenes","Nesbyen","\u00c5l","Hol","Nore og Uvdal","Grue","Trysil","Stor-Elvdal","Rendalen","Engerdal","Tolga","Alvdal","Folldal","Os","Dovre","Lesja","Skj\u00e5k","Lom","V\u00e5g\u00e5","Nord-Fron","Sel","S\u00f8r-Aurdal","Nord-Aurdal","Vestre Slidre","Vang","Seljord","Tinn","Kviteseid","Fyresdal","Tokke","Valle","Bykle","Sirdal","Kinn","Kvinnherad","Ullensvang","Eidfjord","Ulvik","Fedje","Gulen","Solund","Hyllestad","H\u00f8yanger","Vik","L\u00e6rdal","\u00c5rdal","Askvoll","Fjaler","Bremanger","Namsos - N\u00e5avmesjenjaelmie","Osen","R\u00f8ros - Rosse","Holt\u00e5len","Tydal","Sn\u00e5ase - Sn\u00e5sa","Lierne","Raarvihke - R\u00f8yrvik","Namsskogan","Grong","H\u00f8ylandet","Flatanger","Leka","Rindal","Ibestad","Salangen","Dyr\u00f8y","Lyngen - Ivgu - Yyke\u00e4","Storfjord - Omasvuotna - Omasvuono","G\u00e1ivuotna - K\u00e5fjord - Kaivuono","Kv\u00e6nangen","Vads\u00f8","K\u00e1r\u00e1sjohka - Karasjok","Guovdageaidnu - Kautokeino","Loppa","M\u00e5s\u00f8y","Nordkapp","Porsanger - Pors\u00e1ngu - Porsanki","Lebesby","Deatnu - Tana","Berlev\u00e5g","Vard\u00f8","Unj\u00e1rga - Nesseby"],"x":{"dtype":"f8","bdata":"WX2UhP8a2L+AQWi9kaEgwOYnxFn5CfG\u002f9F3+oaAnCMCO4ziO4zgmwPyEebqfjCPA3LZt27ZtG8CTzgjCVB4RwE1l5s6YtfS\u002f6+ov8CP02r+NkU\u002fTjPr4v\u002fiIsUqsMSTAauIwVlt\u002fKMDND4uUgaf7v+52u91utxvAdmIndmInJcC31D22zcHSv69JbIW3SgLAKn5JhFTLKsDGbkUfN4gVwLvOsUYiIP6\u002f5hS8nIKXI8BMiXNE1TMbwNoDZg+YPRjA34gCk07NE8B93Jaqj9siwFu2bNmyZeu\u002f\u002f2f4\u002fmf4DsBUuUjIDSn0vyzNqF7RkyHA4v3Iab5WM8C9Ahp367wawPHw8PDw8CHAWLk6QFauHsCk028rzRrXv4\u002f9rxzsriHASZIkSZJkJ8DNWGEaiT8VwCGgHEkOEfa\u002fjoIN8bNO27+O7uwI5r8RwCqea1aHESPA0W\u002fNiimcBMCe2Imd2IklwMEbTx1dmyfAINEB9raRJsBqaj0\u002fuL0cwIOK7KVSdvu\u002fclkxUMIbIcAlDSMIax0hwPYFELsWLSHABuvj7BPBI8ACaSOmxC4UwABfpZHqaCDAejDgjGuREMD8LeT4fLABwIeTqzrIchvAdj4ZHlVvIMAgaOoNUv7kv0TG0+ZJgBHAxQ9SDhEa8r+apDxMsMf9v68FEjuTsBzABiglkf61BsBfHfObbzUiwFzmPXyNQBrAFyPUdqvpIcAZlcD4y9wXwE0g4i5I+fC\u002fw4jucALMBMBI1cWyoKX4v\u002fjehPULBg7AHCka4o9bF8B8ru1XwGQUwHVcBCLWHyXA3sJed3DK8r802KwzJ6IhwBadFtcmfSnAJBPonbqWFcBjJJQ23lEVwCGKv8gZFhHAUCDdWrzHHsAzMzMzMzPTv\u002fwmCXicZuq\u002fqlvscZ4CIMAZ1IxJP9Hxv4PzMTgfgyPAUNJzr0vG4b8AAAAAAEAPwPp1\u002fDp+HSnA2UwD5yq7FcANYxDtyzAWwIk8zlo1CCDANcJyTyOsIcAl08iLNSfbv1UqlUqlUhHAJ\u002f7nxyb46b\u002fehfwnNKgRwDWQk8yV8gvA+oK+oC\u002foG8D8C96KdoUQwOeGkeeGkSfAXh15KgBJJMDA3hjMP5wKwMSNlmO+rxTAZpKCGpvII8BV+siBsrodwIfZwRFEWhLAGFjiS7Za4L+xUTyT\u002fjg0wNseuVYIMgTAtwWNloF8EsAmDmO19bf3v0E6ljIJdhPAHekSCi7HAsBtncqwCPsjwESu3SQwzRzA\u002f1M3a9JK978="},"y":{"dtype":"f8","bdata":"\u002f\u002f\u002f\u002f\u002f\u002f9\u002fIkAQ16NwPQoPQFC4HoXrURFASOF6FK5HEkCgcD0K16MMwNijcD0K1xFAFK5H4XoUFkACAAAAAAAaQNajcD0K1yFACtejcD1KMECE61G4HoUgQPB6FK5H4fo\u002fsEfhehSuCUBgj8L1KFwYQEAK16NwPRZAQIXrUbge7b84CtejcD0KQOhRuB6F6xBA0MzMzMzMCEDgehSuR+ETQCCF61G4HhFAcD0K16PwJ0DgehSuR+EbQNSjcD0K1xNAqEfhehSuCUCocD0K16MeQCCF61G4Hh5ANDMzMzMzGkCIwvUoXI8AQHgUrkfhegZAKlyPwvWoI0BwPQrXo3ADQOB6FK5H4RTAnJmZmZmZF8CAZmZmZmbWv5iZmZmZ2TDAoHA9CtejDkAI16NwPQoiQHBmZmZmZgZAFK5H4XoUFUB4FK5H4XoYQGhmZmZmZhlAQIXrUbge7T8UrkfhehQcQJDC9ShcjxBA0PUoXI\u002fCBUDwUbgehesDwMCjcD0K1+O\u002fIIXrUbgeDUBQuB6F61EIQGhmZmZmZh9AmJmZmZmZGkAgrkfhehQMQNijcD0K1xFA4KNwPQrXBUAAAAAAAAAGQFyPwvUoXBpAzMzMzMzMGEB8FK5H4fogQLgehetRuB5AQArXo3A9DkDQo3A9Ctfzv5TC9Shcjx7ASOF6FK5HFEBgZmZmZmYKQKBH4XoUrgtA0MzMzMzMFUAI16NwPQoaQJDC9ShcjxpA6FG4HoXr8T+sR+F6FK4TQDwK16NwPRZALFyPwvUoFUDoUbgehesZQEjhehSuRxRAhOtRuB6FGEBI4XoUrkcbQAB7FK5H4cq\u002fYI\u002fC9Shc+z\u002fgo3A9Ctf3vyCF61G4HgHAiOtRuB6FB0CgcD0K16MCQAAAAAAAABbAuB6F61G4BsDWo3A9CtcpQLBH4XoUrhRAKFyPwvUoG0AghetRuB4fQAzXo3A9CiVAaGZmZmZmGUCQ61G4HoUJQEjhehSuRx5A0MzMzMzMHUA8CtejcD0jQByF61G4niBAENejcD0K\u002fz9ACtejcD0KwJCZmZmZmQ1ADNejcD0KHUCOwvUoXA8kQBKuR+F6lCBApHA9CtejF0BQuB6F69EsQFC4HoXrURBADNejcD0KE0BxPQrXo3ApQPAoXI\u002fC9Q5AiOtRuB6FGkCgcD0K16PgPzQzMzMzMyRAKVyPwvUoKUDrUbgeheskQBSuR+F6FBdAZmZmZmZmIUA0MzMzM7MjQJyZmZmZmRVAwvUoXI9CK0A="},"type":"scatter"},{"customdata":[[8.1,11.2,3.1,"Minst sentral"],[6.5,11.4,4.9,"Mindre sentral"],[20.3,27.6,7.3,"Mindre sentral"],[16.2,23.8,7.6,"Mindre sentral"],[21.3,28.5,7.2,"Mindre sentral"],[21.5,28.9,7.4,"Minst sentral"],[21.3,32.8,11.5,"Mindre sentral"],[25.4,38.8,13.4,"Mindre sentral"],[19.4,23.2,3.8,"Minst sentral"],[16.7,16.8,0.1,"Mindre sentral"],[26.0,26.2,0.2,"Minst sentral"],[25.2,25.7,0.5,"Minst sentral"],[32.8,39.5,6.7,"Minst sentral"],[23.6,29.4,5.8,"Minst sentral"],[26.8,29.0,2.3,"Minst sentral"],[42.7,45.2,2.6,"Minst sentral"],[41.3,44.1,2.9,"Minst sentral"],[24.4,32.0,7.7,"Minst sentral"],[41.7,43.1,1.3,"Minst sentral"],[6.4,13.0,6.6,"Mindre sentral"],[10.9,14.4,3.4,"Mindre sentral"],[12.4,21.2,8.8,"Mindre sentral"],[23.0,29.2,6.2,"Minst sentral"],[7.4,12.2,4.8,"Mindre sentral"],[6.7,9.5,2.8,"Mindre sentral"],[12.7,17.0,4.3,"Mindre sentral"],[18.2,18.5,0.3,"Mindre sentral"],[30.0,33.0,3.0,"Mindre sentral"],[32.7,30.3,-2.4,"Minst sentral"],[29.8,31.1,1.3,"Minst sentral"],[40.0,37.9,-2.1,"Minst sentral"],[27.5,26.6,-0.9,"Mindre sentral"],[28.4,30.5,2.0,"Minst sentral"],[48.7,44.5,-4.2,"Minst sentral"],[34.1,34.8,0.7,"Minst sentral"],[30.4,31.0,0.7,"Mindre sentral"],[9.9,15.7,5.8,"Minst sentral"],[25.9,29.9,4.0,"Minst sentral"],[38.2,50.9,12.7,"Mindre sentral"],[28.8,32.8,4.0,"Mindre sentral"],[18.2,25.7,7.6,"Minst sentral"],[25.0,32.6,7.6,"Minst sentral"],[24.0,27.8,3.8,"Minst sentral"],[30.4,35.0,4.5,"Minst sentral"],[36.0,36.5,0.5,"Minst sentral"],[41.7,36.3,-5.5,"Minst sentral"],[28.2,28.3,0.1,"Minst sentral"],[20.1,24.6,4.5,"Minst sentral"],[18.0,25.5,7.5,"Minst sentral"],[20.0,26.2,6.2,"Minst sentral"],[14.4,13.2,-1.2,"Mindre sentral"],[7.2,13.4,6.2,"Mindre sentral"],[12.3,20.2,8.0,"Minst sentral"],[20.8,30.1,9.3,"Minst sentral"],[17.9,32.0,14.1,"Minst sentral"],[10.4,26.8,16.5,"Minst sentral"]],"hovertemplate":"\u003cb\u003e%{text}\u003c\u002fb\u003e\u003cbr\u003eSp 2017: %{customdata[0]}%  \u2192  2021: %{customdata[1]}%\u003cbr\u003e\u0394Sp: \u003cb\u003e%{customdata[2]:+.1f} pp\u003c\u002fb\u003e\u003cbr\u003e\u0394Pop 2011\u201321: %{x:.1f}%\u003cbr\u003eSentralitet: %{customdata[3]}\u003cextra\u003e\u003c\u002fextra\u003e","marker":{"color":"#ff7f0e","line":{"color":"white","width":0.5},"opacity":0.75,"size":{"dtype":"f8","bdata":"MIymzHPuLkCm3gTxyicrQMCuBZK9vStAgucFc\u002fKWK0CO5VE0ztoqQLCvsGDAOSZAZCKkIoevKkC\u002fomdj9AgnQNmGMpFL2ytAbotDeKtSK0CoHuzl7u4qQAiTPs96litAS7qrdey5JECXyI9spUgpQE3GUlDQASdAcEftBdjVKUCGUE\u002fQtC8oQIZDf+PZviVAQai4\u002fQaeKECNipXEU3MrQKOZBHrRUStAy38hTXABKkAwk1BOWtAoQOh+l9umByxAPpaQnphcLUDrFroGwvInQKa+UJoExCdAOjPYIw\u002fULEAItDH5lNcrQCUpycYlTCZAbtGYx+GQKUDoVTBn0dAtQO7iJc\u002f\u002fNytASGDbXqTyKUB6gTxhspEqQALXNQ43Oi5AO1nr\u002fC0eKUBBNECcDm0qQGrD0yvEmChAvi2w\u002fwhwKkB2Vn4id4orQFRbJFOtCylA2huUGQ9cK0BGZC7QOLwkQDhesLHO1ihAxnvEmDleKkAaeFMpql4oQPkZtNDbxixAhoVwKCPnJ0Bdr6v+z24pQGYjaddjkS1A\u002fDPUIoDkK0D4eSmEI5QrQD65uo0ipCRAaru7wvyyJEAi3LWxp+gmQA=="}},"mode":"markers","name":"Lav sent + Vekst\u003cbr\u003e\u003csup\u003e56 kommuner \u00b7 8.3% av velgerne\u003c\u002fsup\u003e","text":["Molde","Her\u00f8y (M\u00f8re og Romsdal)","\u00d8rsta","Volda","Br\u00f8nn\u00f8y","Her\u00f8y (Nordland)","Alstahaug","Leirfjord","Vestv\u00e5g\u00f8y","V\u00e5gan","Hadsel","Sortland - Suort\u00e1","Fl\u00e5","Gol","Hemsedal","Tynset","\u00d8ystre Slidre","Nissedal","Vinje","Farsund","Flekkefjord","Kvinesdal","Etne","B\u00f8mlo","Stord","Fitjar","Tysnes","Voss","Sogndal","Aurland","Luster","Sunnfjord","Stad","Gloppen","Stryn","Steinkjer - St\u00efentje","Fr\u00f8ya","Oppdal","Overhalla","Inder\u00f8y","\u00d8rland","\u00c5fjord","N\u00e6r\u00f8ysund","Loab\u00e1k - Lavangen","Bardu","M\u00e5lselv","S\u00f8rreisa","Senja","Skjerv\u00f8y","Nordreisa - R\u00e1isa - Raisi","Alta","Hammerfest - H\u00e1mmerfeasta","S\u00f8r-Varanger","Hasvik","Gamvik","B\u00e5tsfjord"],"x":{"dtype":"f8","bdata":"+0og2gBMGEAUsMcATngOQDDHZZRnnxFAZl0TGR+jIkCFXvJsXWnxP5FH48gSdyFA3EdwH8F99T+hvYT2EtoVQPdomQfQfhtAENLsW6iuHEAw57+vcHj8P3TRRRddtBpAmpmZmZmZE0CaBRHsrmX2P9ovxIrS+DJAUqbiuWZ16D8umMF2C2YAQPlwJJhBePw\u002f+\u002fYEHWXCBEDp0WiHFIsDQBAJ3XLk4cM\u002fBUUkDzMp\u002fT\u002folUOYb3gNQAvzqUrhoRJAyRM4W1q\u002fF0DEr\u002fXVcMUdQGXwSQkXYhhAc2QzJsayF0BwLXqAy44mQDBko1o61xRAKY+Z5TlwCkBFyJTqfD0ZQBVhpUaxZyJAK2NuRLM9CUCC+ZSua8z2Py3sPt+1Zfo\u002fO7BVJL9LNEBgb2tYM1YRQH3eEvFIMRlAvN2+MBVk5j8Lv7H5uNsYQAbZ\u002fMulL\u002fI\u002fx3bvMEGTE0AEDSd1Xx77P5q5aeammds\u002fkZYkssNt5j+tQrbg004GQO\u002fWwk3bYeA\u002fKmHlOzm\u002f0T8qI3yusaXCP4aDRgUJoCJAo4OFLereDkDDiuneao0GQNPoERVkG\u002fI\u002f4819B31kJUCmjjIxXuoYQA=="},"y":{"dtype":"f8","bdata":"IIXrUbgeCUCkcD0K16MTQFC4HoXrUR1AjML1KFyPHkD4KFyPwvUcQHwUrkfheh1ADNejcD0KJ0BI4XoUrscqQBiuR+F6FA5AANejcD0Ktz+APQrXo3DNPwAAAAAAAOA\u002f6FG4HoXrGkBACtejcD0XQBiuR+F6FAJAgBSuR+F6BEDQzMzMzMwGQKxH4XoUrh5AgD0K16Nw9T80MzMzMzMaQHA9CtejcAtAr0fhehSuIUDMzMzMzMwYQD0K16NwPRNApHA9CtejBkAI16NwPQoRQABSuB6F69E\u002f6FG4HoXrB0AghetRuB4DwKBwPQrXo\u002fQ\u002fwB6F61G4AMDA9Shcj8Ltv1C4HoXrUQBAyPUoXI\u002fCEMBAj8L1KFznP8D1KFyPwuU\u002fFK5H4XoUF0AAAAAAAAAQQHwUrkfheilAKFyPwvUoEEBcj8L1KFweQGhmZmZmZh5AWLgehetRDkAoXI\u002fC9SgSQAAAAAAAAOA\u002f2KNwPQrXFcAAmZmZmZm5PyCF61G4HhJA2KNwPQrXHUCwR+F6FK4YQFiPwvUoXPO\u002fpHA9CtejGEDWo3A9CtcfQJqZmZmZmSJAHoXrUbgeLED2KFyPwnUwQA=="},"type":"scatter"},{"customdata":[[9.1,15.6,6.5,"Sentral"],[7.8,10.4,2.6,"Sentral"],[24.6,26.2,1.6,"Noe sentral"],[13.0,16.3,3.3,"Noe sentral"],[17.0,19.6,2.5,"Noe sentral"],[30.0,35.5,5.5,"Noe sentral"],[26.0,38.4,12.4,"Noe sentral"],[22.0,29.1,7.0,"Noe sentral"],[17.8,21.9,4.1,"Noe sentral"],[39.0,46.6,7.6,"Noe sentral"],[36.9,47.6,10.7,"Sentral"],[24.0,31.5,7.5,"Sentral"],[23.0,32.7,9.7,"Sentral"],[32.7,34.1,1.5,"Noe sentral"],[30.6,40.9,10.3,"Noe sentral"],[33.7,40.7,7.0,"Noe sentral"],[36.5,39.2,2.7,"Noe sentral"],[34.6,36.5,1.9,"Noe sentral"],[18.6,26.7,8.2,"Noe sentral"],[24.7,30.3,5.6,"Noe sentral"],[35.8,42.4,6.6,"Noe sentral"],[19.6,25.6,5.9,"Noe sentral"],[9.0,13.4,4.4,"Noe sentral"],[9.6,13.6,4.1,"Noe sentral"],[28.0,30.9,2.9,"Noe sentral"],[20.0,28.1,8.1,"Noe sentral"],[35.6,40.9,5.3,"Noe sentral"],[6.9,12.0,5.1,"Noe sentral"],[21.2,27.9,6.8,"Noe sentral"],[21.0,32.1,11.1,"Noe sentral"],[26.6,33.2,6.7,"Sentral"],[16.8,20.3,3.4,"Sentral"],[24.0,31.5,7.5,"Sentral"],[31.6,41.9,10.3,"Sentral"],[25.6,30.7,5.1,"Sentral"],[21.9,33.8,11.8,"Sentral"],[19.2,24.6,5.4,"Noe sentral"],[10.9,19.9,9.0,"Noe sentral"],[21.4,34.8,13.3,"Noe sentral"],[21.4,27.7,6.3,"Sentral"]],"hovertemplate":"\u003cb\u003e%{text}\u003c\u002fb\u003e\u003cbr\u003eSp 2017: %{customdata[0]}%  \u2192  2021: %{customdata[1]}%\u003cbr\u003e\u0394Sp: \u003cb\u003e%{customdata[2]:+.1f} pp\u003c\u002fb\u003e\u003cbr\u003e\u0394Pop 2011\u201321: %{x:.1f}%\u003cbr\u003eSentralitet: %{customdata[3]}\u003cextra\u003e\u003c\u002fextra\u003e","marker":{"color":"#1f77b4","line":{"color":"white","width":0.5},"opacity":0.75,"size":{"dtype":"f8","bdata":"\u002frkxfiJGKED0Rl1+HtAiQIOUh1wmSSlAEL7vLR3VKkD20SJ\u002fZboqQN366mWaFShAmF7fGWiAJkALTleQVU0pQOS0AdCkmyVAiJaKZMDDJUDK38+FvoAoQDNziqSEnilA5FFyu7I+KkAEy+5fks4qQKZgDvIHyyhAdLJozpE5KEC1wolT9EUpQLarRwsxKypAPp+izDQEKkB2ehK7628qQASqmzSCtSVAz97qt+NfJ0Bx5i2ZpqUsQMglwVE31StAvMRFd3b5KEAFYMSu\u002fV0qQIC\u002fe4IoISZAkCQQD3GBKkCmM1KwQHgnQIRBsk1FiSZAB1tpkVxeJUCS8vvX1\u002f4oQGNJcQxiRCZACW+9tcyfJ0Ck\u002fwhcGHonQIYABPOXpitAO\u002fSnKNYRKEBPwzk2UAspQEI8BtlxDSVA3GyCAfVLJ0A="}},"mode":"markers","name":"Sentral + Nedgang\u003cbr\u003e\u003csup\u003e40 kommuner \u00b7 3.3% av velgerne\u003c\u002fsup\u003e","text":["Sokndal","Kvits\u00f8y","Stranda","Sykkylven","Rauma","Tingvoll","Nesna","Hemnes","Evenes - Even\u00e1ssi","Aremark","Sigdal","Nord-Odal","Eidskog","\u00c5snes","V\u00e5ler (Innlandet)","S\u00f8r-Fron","Ringebu","Gausdal","S\u00f8ndre Land","Nordre Land","Etnedal","Siljan","Bamble","Krager\u00f8","Drangedal","Nome","Hjartdal","Ris\u00f8r","Gjerstad","\u00c5mli","Bygland","Vaksdal","Masfjorden","Rennebu","Mer\u00e5ker","Indre Fosen","Kv\u00e6fjord","Dielddanuorri - Tjeldsund","Gratangen - Rivtt\u00e1k","Karls\u00f8y"],"x":{"dtype":"f8","bdata":"VFJmp+lcz7\u002fRRRdddNEPwGnzPsUlQwDAxJxa7ImQ6791gynyWTcUwHLDvIyD4QTA1cJKTy2sF8Df9KY3vekNwM6ce8TjdfW\u002fpry9\u002fEItGcCyXFFoqcn6vymaAeA2ePe\u002fqWEnlZ5mCcCcrWBXO3sTwJrzZU+OZR7AWfgHbU5uEsDPPR932vwJwOwJ+nqCvv6\u002fJKeRIymuEcDdBn10vBQAwCND\u002f9JG4CLABLR59r3PB8CIe6Ex0DG9v05vetOb3gTAtioM+QOQ9L\u002fYpsyjWs3xv1a0t\u002f6nCALARwlRZ81h+b8NP9n5O3cFwJhmp8SHfti\u002fRZ7OqMlQH8AnkqWSXaIWwEi1rANt9+a\u002fQLAWq0egGsDwcSqX9sMMwLNUnv9emfK\u002fuGQI1tHmHcDKVNKE2jHSvwWEE\u002fGSgADAIjSg6VVlH8A="},"y":{"dtype":"f8","bdata":"HoXrUbgeGkCmcD0K16MEQKCZmZmZmfk\u002fkML1KFyPCkAYrkfhehQEQPz\u002f\u002f\u002f\u002f\u002f\u002fxVASOF6FK7HKEAoXI\u002fC9SgcQFyPwvUoXBBAcD0K16NwHkB8FK5H4XolQAzXo3A9Ch5AZGZmZmZmI0BAMzMzMzP3Pyhcj8L1qCRAAAAAAAAAHEBgj8L1KFwFQCCuR+F6FP4\u002fXI\u002fC9ShcIEBI4XoUrkcWQFi4HoXrURpAuB6F61G4F0CQwvUoXI8RQDQzMzMzMxBAcD0K16NwB0A8CtejcD0gQEjhehSuRxVAj8L1KFyPFEAAAAAAAAAbQKRwPQrXIyZAtB6F61G4GkB4PQrXo3ALQOxRuB6F6x1ACNejcD2KJECE61G4HoUUQLBH4XoUridAsEfhehSuFUD3KFyPwvUhQDIzMzMzsypAKFyPwvUoGUA="},"type":"scatter"},{"customdata":[[2.2,3.2,1.1,"Sentral"],[9.5,13.9,4.4,"Sentral"],[4.1,5.6,1.5,"Sentral"],[3.5,6.1,2.6,"Noe sentral"],[6.0,8.7,2.8,"Sentral"],[29.5,36.4,6.9,"Sentral"],[15.8,22.1,6.3,"Sentral"],[11.2,15.7,4.5,"Sentral"],[11.6,15.7,4.1,"Sentral"],[11.4,15.6,4.2,"Sentral"],[5.8,8.5,2.7,"Sentral"],[6.7,9.2,2.4,"Sentral"],[8.1,13.4,5.3,"Sentral"],[31.5,35.5,4.0,"Sentral"],[13.0,19.1,6.1,"Noe sentral"],[5.0,9.1,4.1,"Noe sentral"],[26.8,30.1,3.4,"Noe sentral"],[19.1,28.8,9.8,"Noe sentral"],[5.6,10.8,5.2,"Noe sentral"],[7.2,12.8,5.6,"Noe sentral"],[9.4,14.6,5.3,"Noe sentral"],[5.3,8.4,3.1,"Noe sentral"],[6.5,10.3,3.8,"Noe sentral"],[17.8,17.6,-0.1,"Noe sentral"],[11.5,18.0,6.6,"Noe sentral"],[18.0,26.0,8.0,"Noe sentral"],[29.5,36.8,7.3,"Noe sentral"],[14.8,20.5,5.7,"Noe sentral"],[9.2,10.9,1.7,"Noe sentral"],[12.9,14.2,1.3,"Noe sentral"],[12.6,17.1,4.5,"Noe sentral"],[9.1,15.2,6.1,"Sentral"],[4.8,8.8,4.0,"Sentral"],[7.0,13.1,6.1,"Sentral"],[4.8,9.4,4.6,"Sentral"],[6.9,12.1,5.2,"Noe sentral"],[13.2,20.5,7.4,"Sentral"],[18.1,25.8,7.7,"Sentral"],[21.8,32.2,10.4,"Sentral"],[14.3,22.4,8.1,"Sentral"],[25.8,38.8,13.0,"Sentral"],[24.9,33.9,9.0,"Sentral"],[2.2,3.0,0.8,"Sentral"],[3.7,5.9,2.2,"Sentral"],[7.3,10.8,3.4,"Sentral"],[4.1,5.9,1.9,"Sentral"],[8.3,12.0,3.8,"Sentral"],[3.5,4.9,1.4,"Sentral"],[4.6,6.8,2.2,"Sentral"],[6.7,10.0,3.3,"Sentral"],[10.0,11.0,1.0,"Sentral"],[12.5,16.7,4.2,"Sentral"],[3.4,6.4,2.9,"Sentral"],[5.0,8.2,3.2,"Sentral"],[18.1,27.4,9.3,"Sentral"],[15.6,22.8,7.2,"Sentral"],[12.1,15.3,3.2,"Sentral"],[5.9,9.6,3.6,"Sentral"],[12.4,19.9,7.5,"Sentral"],[12.9,19.6,6.6,"Sentral"],[12.8,18.8,6.0,"Sentral"],[12.7,18.1,5.4,"Sentral"],[22.7,29.1,6.4,"Sentral"],[4.8,8.7,3.9,"Sentral"],[13.2,18.2,4.9,"Sentral"],[9.8,17.9,8.1,"Sentral"],[10.2,13.4,3.2,"Sentral"],[7.6,10.6,2.9,"Sentral"],[14.4,20.9,6.6,"Sentral"],[16.1,21.9,5.8,"Sentral"],[26.7,33.4,6.8,"Sentral"],[30.8,38.6,7.9,"Sentral"],[42.4,44.9,2.5,"Noe sentral"],[14.4,22.0,7.6,"Sentral"],[10.0,15.4,5.4,"Sentral"],[12.6,13.3,0.7,"Noe sentral"],[13.2,17.6,4.3,"Noe sentral"],[19.4,25.2,5.8,"Noe sentral"],[27.3,35.4,8.1,"Sentral"],[21.5,28.9,7.3,"Sentral"],[20.7,28.8,8.1,"Sentral"],[20.4,32.2,11.9,"Noe sentral"],[33.2,39.5,6.4,"Noe sentral"],[28.8,31.8,3.0,"Noe sentral"],[22.0,26.9,4.9,"Noe sentral"],[15.5,21.6,6.1,"Noe sentral"],[18.2,24.3,6.2,"Sentral"],[5.1,7.4,2.3,"Sentral"],[12.3,15.4,3.1,"Sentral"],[4.5,10.5,6.0,"Sentral"],[5.7,9.7,4.0,"Sentral"],[6.9,11.8,4.9,"Noe sentral"],[3.8,6.7,2.8,"Noe sentral"],[5.4,9.5,4.1,"Noe sentral"],[7.1,11.4,4.2,"Noe sentral"],[14.5,20.1,5.6,"Noe sentral"],[19.4,26.1,6.7,"Noe sentral"],[6.5,10.5,4.0,"Sentral"],[5.8,10.4,4.6,"Sentral"],[4.1,7.2,3.0,"Sentral"],[10.2,14.2,4.0,"Sentral"],[16.1,26.7,10.6,"Noe sentral"],[10.5,16.6,6.1,"Noe sentral"],[13.4,24.1,10.8,"Sentral"],[4.4,8.7,4.3,"Sentral"],[13.1,24.8,11.7,"Sentral"],[20.4,32.2,11.8,"Sentral"],[14.1,21.7,7.6,"Sentral"],[8.6,16.3,7.7,"Sentral"],[26.2,38.8,12.7,"Sentral"],[8.2,16.0,7.8,"Sentral"],[21.0,31.0,10.0,"Sentral"],[4.2,5.6,1.3,"Sentral"],[12.4,19.6,7.1,"Noe sentral"],[20.9,23.4,2.5,"Sentral"],[15.3,20.0,4.7,"Sentral"],[9.0,12.2,3.2,"Sentral"],[5.6,7.2,1.5,"Sentral"],[4.4,8.7,4.3,"Sentral"],[4.0,6.9,2.9,"Sentral"],[40.1,32.6,-7.5,"Sentral"],[13.3,17.2,3.9,"Sentral"],[12.3,17.9,5.6,"Sentral"],[9.9,15.4,5.5,"Sentral"],[5.6,8.0,2.3,"Sentral"],[32.4,42.3,9.9,"Sentral"],[17.3,26.5,9.2,"Sentral"],[18.2,26.1,7.8,"Sentral"],[8.5,12.6,4.1,"Sentral"],[23.6,34.3,10.7,"Sentral"],[15.5,21.2,5.7,"Sentral"],[26.7,29.6,2.9,"Sentral"],[21.1,25.6,4.5,"Sentral"],[26.3,31.3,5.0,"Sentral"],[8.8,12.8,4.1,"Sentral"],[10.5,16.0,5.5,"Noe sentral"],[22.5,34.2,11.7,"Sentral"]],"hovertemplate":"\u003cb\u003e%{text}\u003c\u002fb\u003e\u003cbr\u003eSp 2017: %{customdata[0]}%  \u2192  2021: %{customdata[1]}%\u003cbr\u003e\u0394Sp: \u003cb\u003e%{customdata[2]:+.1f} pp\u003c\u002fb\u003e\u003cbr\u003e\u0394Pop 2011\u201321: %{x:.1f}%\u003cbr\u003eSentralitet: %{customdata[3]}\u003cextra\u003e\u003c\u002fextra\u003e","marker":{"color":"#6baed6","line":{"color":"white","width":0.5},"opacity":0.75,"size":{"dtype":"f8","bdata":"AAAAAAAAMkAuKTpkwbYsQIYwgH7isjFACDxLjEdbL0CRWDK5iK0wQNvfv38ypidArXx0lwYxLUAQ0Yg+1kotQO489UraHy1AWYPdlavHK0AaDw3x2CwuQLfDYs5JpitABGFCk9IELEBTELcBbDEkQDlMI7ElsCtAXdWme3HLL0BQ02YGWRIrQNQrrpkMNC5Ah+P6wOpDMEDcg7Z5+90qQIqgBfbXgilA1ur7U2z\u002fKkC80+L55Z8qQNL2O2lKVypAeamP81xCKEAuZ4NRVNkpQLLSv2jzkSdABnWBH+hcLECDZKy65ikwQKrqAgt2cC5AMuRDUuR8K0B0CVnbEdkuQHEjlPmyDzBASRiyD8NPMECUHuFGVtQwQLDXm98iAClABu5cL8eJKkDkfp9p0EgpQM6FrKf9iyhAcgw77DffL0BSQkba+c4qQMwEkOk2dihAcv+NPy5zMUBweyP5pwAxQIKZ9sjT1TBAU6SfJ+xVMEDkhg86X+8uQGYq5jYHUC1AB93lX2jPLEDX1fia5MksQLj4QrPzLC1AUgNDkHq1K0CNU261oT0vQHrxu+qzBi1AdEqt8LLoLEClHSnrgJAtQPQJ7Q8TGCpA1ilGcmXhLUAqUXz8mjIrQBYyQFT6RSpAdJW9mrHzK0BCkTR1DeAtQKCL5bnfnCdApwgKSxIpMUCXobYKC2QuQG7HA5rV0S5ARPzxBxErKkAtVlz+XzQuQJR7JYeFOC1AK9IwL4tnLEAOoun4XwonQERY2xnrlCdAtIBYFi+yJUD0oYx5jkwtQNqbLCZDyi5AWJQERxaQLkAtqYivk9IuQHpK7bLPMi9Anvof9YC1KkDTjvObuZQtQED9SA7e5SpA9NGiLBy1LUDth+2flBwpQC7uaqJbmylApFDzjHHELEAlCUuyXl8sQMp6bKVQhCxAAQUqYneALkA8xPTXefYtQPDHaD27LzBAFCRI4MOBMEDqO2nt1hIwQJSuLNWLdC5AeC2n1KBkL0CRpQpibkowQBg6UaWPRixA0N4WLeyiK0DxQxi24tQtQHZPfGzh8y9AdeoB3IBBMUD7sJCd\u002f\u002fstQNIdpEJXryZAn0qWsGAVKkCKDVojnqApQNoisqJBiytAegxCCypqKUCysHUyMIYlQK9k4lv+dShAro5uxZN+LEAd4NnOQHMkQEhdAJs0eCtAYmtIMBU1JkAAAAAAAAAyQDw\u002fbG1DoilAD+ciNY8fK0CjSoQU6lcnQPUaGwad3S1AgHDgtZJaKUCkl\u002fguejEvQG6k6JWOcy5AsEe2p6S\u002fIUCLQ92vHMEqQPChMNVXhi5ATlGb7yfNJ0AAAAAAAAAyQEmQKslFGypAptaRBmzaLEASKBsRe3QqQDfAxlvGVyxACM8UAEHhKEBKbM9pHfMtQB27EHLBhCdAa1HrL\u002fyDLUDHtaDgHLYsQDLBCs44sjBARNiP2LE+LkDqzeB06dgpQA=="}},"mode":"markers","name":"Sentral + Vekst\u003cbr\u003e\u003csup\u003e137 kommuner \u00b7 80.2% av velgerne\u003c\u002fsup\u003e","text":["Oslo - Oslove","Eigersund","Stavanger","Haugesund","Sandnes","Bjerkreim","H\u00e5","Klepp","Time","Gjesdal","Sola","Randaberg","Strand","Bokn","Tysv\u00e6r","Karm\u00f8y","Vindafjord","Kristiansund","\u00c5lesund","Ulstein","Hareid","Sula","Giske","Vestnes","Aukra","Aver\u00f8y","Gjemnes","Hustadvika","Bod\u00f8","Rana - Raane","Fauske - Fuossko","Halden","Moss","Sarpsborg","Fredrikstad","Hvaler","R\u00e5de","V\u00e5ler (\u00d8stfold)","Skiptvet","Indre \u00d8stfold","Rakkestad","Marker","B\u00e6rum","Asker","Lillestr\u00f8m","Nordre Follo","Ullensaker","Nesodden","Frogn","Vestby","\u00c5s","Enebakk","L\u00f8renskog","R\u00e6lingen","Aurskog-H\u00f8land","Nes","Gjerdrum","Nittedal","Lunner","Jevnaker","Nannestad","Eidsvoll","Hurdal","Drammen","Kongsberg","Ringerike","Hole","Lier","\u00d8vre Eiker","Modum","Kr\u00f8dsherad","Flesberg","Rollag","Kongsvinger","Hamar","Lillehammer","Gj\u00f8vik","Ringsaker","L\u00f8ten","Stange","S\u00f8r-Odal","Elverum","\u00c5mot","\u00d8yer","\u00d8stre Toten","Vestre Toten","Gran","Horten","Holmestrand","T\u00f8nsberg","Sandefjord","Larvik","F\u00e6rder","Porsgrunn","Skien","Notodden","Midt-Telemark","Grimstad","Arendal","Kristiansand","Lindesnes","Veg\u00e5rshei","Tvedestrand","Froland","Lillesand","Birkenes","Iveland","Evje og Hornnes","Vennesla","\u00c5seral","Lyngdal","H\u00e6gebostad","Bergen","Sveio","Kvam","Samnanger","Bj\u00f8rnafjorden","Austevoll","\u00d8ygarden","Ask\u00f8y","Modalen","Oster\u00f8y","Alver","Austrheim","Trondheim - Tr\u00e5ante","Midtre Gauldal","Melhus","Skaun","Malvik","Selbu","Stj\u00f8rdal","Frosta","Levanger - Levangke","Verdal","Troms\u00f8","Harstad - H\u00e1rstt\u00e1k","Balsfjord"],"x":{"dtype":"f8","bdata":"uJA\u002fu05RMEAEucDIm5cIQNScVi\u002f+hyBAtWrGkDI+H0BwEYu8sFczQI\u002fcfEnFHxVAVcj+90RSK0Acka+xYS0sQNNpuHtZJTBAx6zxcJOdLUD5nurcv5YxQJ3vk3KN7ShAzsLfwq64LUB5caneCAcFQEwPMXG6XiNAOj4Kw7vIFkCxqErugp4TQNzV86989AFAM4oIVFk2PkDA77OIA0MlQM3kEpWS3hBAEgYCVsc3MECJhj8aT\u002fsyQERtWfTY6xtAhEnLrB\u002fOIEBOb3rTm94UQED6dvgxjAdAW4WUcjhlEUCOM0SDRrMjQLTLGmmBUgJAe4+1Y2v18T\u002f++IcYJKodQHPqxXPfRSZAI1QxzS9MIUCwChKorxknQMRO7MROrClA\u002fCiUxtroIUA2c25H1PA6QPnzKosz2htA2LTUgdTpI0AZpfpOB1cgQCy1JYDJxAxAVDPF6bliK0AfcSrNOsoqQDIOqJfjIzBAdElUR9vCJ0CFMcX9BUBBQCN7BdslJipAB5JxdjPBHkAHTOzWpVo4QMd3Z5nZJTZAqRLe98hMH0D83LQTSVE8QEfvisyXpjFADkMdIyrMLUB5AgjM4vQ2QJBpn+1MlDFAwo8\u002ffWEUL0BuF2ybu9sSQFoLit1n9B9ANAkSQneIP0AxiJOuxzQ3QEjIDSlUuSBA5ehJIG8RI0ClZlqy3MEkQP25RUqRGhpAHKXeN0\u002fbJUCa4WPcKwIuQN+1VBEmBjBAORAxXPHyIkDBiCv0LFUEQBl4ujU\u002frBJAIDOy5RyG0j+UT2MzgwoDQJVPe8uz3SNAQlVthA3vHEAYRVZCGp4TQHOaCbhnBxlA0a92p+aXDUArbSwy8wYkQBbpymdP9fA\u002fsU2TSKBJGkCmxbep+iHfPwi8YWonHJQ\u002fTNm3FpRA\u002fT9WvpsxxX4UQDVWcuixFPU\u002fYL1V7EOlFkBjnTWipPEtQEBa3jpfYzFAUMbpDW\u002fnG0D3OGske6sVQHB3GLrHoBRAUoVSoILtEED5PKFgs44XQPuZqIXqSxNAn3IbDti6EUDj8HqQqHctQGorLkDx3BpA+1PvNGY3K0DBEIrBbeIUQJAhAvidbyVAbI\u002fw5+BE+j+N2W1YAxsxQPFz4fb5NC5A5ksTh7HaJEC8QCbFC2QCQN2Yp49WkxBAN04BWogDKEAN5TWU11D6P2vTJdhA4CRAxH8CkKrkCEAD6CG1wlwjQLB0Rc\u002fgsClAQAZNUu\u002fOzD8RJkaYGGESQPAOFyt77zJAhVd4hVd4KUDCXglQlu4xQIsEHVVgLy9AI591gyny+T\u002fPpdWaFXogQLIfrHqnoydAKBAQ\u002fZ9dBEA3gQnbVnUvQBertBX+Ug5A38uQ38uQKUDQ8m7EcNg3QBjidBRPJCpAq9NKxK46\u002fT84sPmh6DooQNIZgFE8YQZAa4lkQP5\u002fHkChkNHryjESQF48C2Ox9ClADV0DMrkVDEBbOdzOblzoPw=="},"y":{"dtype":"f8","bdata":"SOF6FK5H8T9oZmZmZmYRQKRwPQrXo\u002fg\u002fzczMzMzMBEAqXI\u002fC9SgGQJDC9ShcjxtAKFyPwvUoGUDWo3A9CtcRQIbrUbgehRBAzMzMzMzMEEDWo3A9CtcFQJqZmZmZmQNAUrgehetRFUDoUbgehesPQF6PwvUoXBhAkML1KFyPEEDgehSuR+EKQArXo3A9iiNAzczMzMzMFECZmZmZmZkWQBSuR+F6FBVAMjMzMzMzCUBQuB6F61EOQABSuB6F68G\u002fPgrXo3A9GkDYo3A9CtcfQDAzMzMzMx1A4HoUrkfhFkAwMzMzMzP7Pyhcj8L1KPQ\u002f4noUrkfhEUA+CtejcD0YQB6F61G4HhBAexSuR+F6GEA0MzMzMzMSQM3MzMzMzBRAcD0K16NwHUD4KFyPwvUeQM7MzMzMzCRAKlyPwvUoIEAWrkfhehQqQAzXo3A9CiJA4HoUrkfh6j+F61G4HoUBQITrUbgehQtAGK5H4XoU\u002fj8AAAAAAAAOQBSuR+F6FPY\u002fXI\u002fC9ShcAUB6FK5H4XoKQLBH4XoUru8\u002fuB6F61G4EECE61G4HoUHQHA9CtejcAlAkML1KFyPIkDOzMzMzMwcQOxRuB6F6wlAIIXrUbgeDUDkehSuR+EdQJqZmZmZmRpA7FG4HoXrF0BmZmZmZmYVQHgUrkfhehlA+Chcj8L1DkCuR+F6FK4TQChcj8L1KCBA2KNwPQrXCUBej8L1KFwHQD4K16NwPRpANDMzMzMzF0AM16NwPQobQHwUrkfheh9A0KNwPQrXA0BSuB6F61EeQHA9CtejcBVAENejcD0K5z9SuB6F61ERQEjhehSuRxdAKlyPwvUoIEBcj8L1KFwdQD4K16NwPSBAwvUoXI\u002fCJ0CI61G4HoUZQOhRuB6F6wdAeBSuR+F6E0BQuB6F61EYQKBwPQrXoxhAkML1KFyPAkD0KFyPwvUIQOxRuB6F6xdAH4XrUbgeEEC5HoXrUbgTQM3MzMzMzAZAPgrXo3A9EED\u002f\u002f\u002f\u002f\u002f\u002f\u002f8QQGRmZmZmZhZA7FG4HoXrGkDsUbgehesPQGdmZmZmZhJAPgrXo3A9CEAUrkfhehQQQKRwPQrXIyVAcD0K16NwGEAL16NwPYolQEjhehSuRxFAcD0K16NwJ0AUrkfhepQnQJiZmZmZmR5ArkfhehSuHkDWo3A9ClcpQDQzMzMzMx9AehSuR+H6I0BwPQrXo3D1P5iZmZmZmRxAOArXo3A9BECkcD0K16MSQITrUbgehQlAVLgehetR+D8VrkfhehQRQDIzMzMzMwdA0MzMzMzMHcDQzMzMzMwOQHwUrkfhehZA7FG4HoXrFUC6HoXrUbgCQLwehetRuCNAZmZmZmZmIkBcj8L1KFwfQFK4HoXrURBA\u002fv\u002f\u002f\u002f\u002f9\u002fJUCcmZmZmZkWQEjhehSuRwdA7FG4HoXrEUDsUbgehesTQD4K16NwPRBA2KNwPQrXFUDWo3A9ClcnQA=="},"type":"scatter"}],                        {"template":{"data":{"barpolar":[{"marker":{"line":{"color":"white","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"white","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"#C8D4E3","linecolor":"#C8D4E3","minorgridcolor":"#C8D4E3","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"#C8D4E3","linecolor":"#C8D4E3","minorgridcolor":"#C8D4E3","startlinecolor":"#2a3f5f"},"type":"carpet"}],"choropleth":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"choropleth"}],"contourcarpet":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"contourcarpet"}],"contour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"contour"}],"heatmap":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"heatmap"}],"histogram2dcontour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2dcontour"}],"histogram2d":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2d"}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"mesh3d":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"mesh3d"}],"parcoords":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"parcoords"}],"pie":[{"automargin":true,"type":"pie"}],"scatter3d":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatter3d"}],"scattercarpet":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattercarpet"}],"scattergeo":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergeo"}],"scattergl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergl"}],"scattermapbox":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattermapbox"}],"scattermap":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattermap"}],"scatterpolargl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolargl"}],"scatterpolar":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolar"}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"scatterternary":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterternary"}],"surface":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"surface"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}]},"layout":{"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"autotypenumbers":"strict","coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]],"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]},"colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"geo":{"bgcolor":"white","lakecolor":"white","landcolor":"white","showlakes":true,"showland":true,"subunitcolor":"#C8D4E3"},"hoverlabel":{"align":"left"},"hovermode":"closest","mapbox":{"style":"light"},"paper_bgcolor":"white","plot_bgcolor":"white","polar":{"angularaxis":{"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":""},"bgcolor":"white","radialaxis":{"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":""}},"scene":{"xaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"},"yaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"},"zaxis":{"backgroundcolor":"white","gridcolor":"#DFE8F3","gridwidth":2,"linecolor":"#EBF0F8","showbackground":true,"ticks":"","zerolinecolor":"#EBF0F8"}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"ternary":{"aaxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""},"baxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""},"bgcolor":"white","caxis":{"gridcolor":"#DFE8F3","linecolor":"#A2B1C6","ticks":""}},"title":{"x":0.05},"xaxis":{"automargin":true,"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":"","title":{"standoff":15},"zerolinecolor":"#EBF0F8","zerolinewidth":2},"yaxis":{"automargin":true,"gridcolor":"#EBF0F8","linecolor":"#EBF0F8","ticks":"","title":{"standoff":15},"zerolinecolor":"#EBF0F8","zerolinewidth":2}}},"shapes":[{"line":{"color":"#94a3b8","dash":"dot","width":1.5},"type":"line","x0":0,"x1":0,"xref":"x","y0":0,"y1":1,"yref":"y domain"},{"line":{"color":"#94a3b8","dash":"dot","width":1.5},"type":"line","x0":0,"x1":1,"xref":"x domain","y0":0,"y1":0,"yref":"y"}],"annotations":[{"bgcolor":"rgba(255,255,255,0.85)","bordercolor":"#d62728","borderpad":4,"borderwidth":1.5,"font":{"color":"#d62728","size":10},"showarrow":false,"text":"\u003cb\u003e\u2300+4.7pp\u003c\u002fb\u003e\u003cbr\u003e30\u219235%\u003cbr\u003e7% av velg.","x":-8,"y":4.701186440677966},{"bgcolor":"rgba(255,255,255,0.85)","bordercolor":"#ff7f0e","borderpad":4,"borderwidth":1.5,"font":{"color":"#ff7f0e","size":10},"showarrow":false,"text":"\u003cb\u003e\u2300+4.4pp\u003c\u002fb\u003e\u003cbr\u003e23\u219228%\u003cbr\u003e8% av velg.","x":8,"y":4.4244642857142855},{"bgcolor":"rgba(255,255,255,0.85)","bordercolor":"#1f77b4","borderpad":4,"borderwidth":1.5,"font":{"color":"#1f77b4","size":10},"showarrow":false,"text":"\u003cb\u003e\u2300+6.4pp\u003c\u002fb\u003e\u003cbr\u003e23\u219230%\u003cbr\u003e3% av velg.","x":-8,"y":6.433749999999999},{"bgcolor":"rgba(255,255,255,0.85)","bordercolor":"#6baed6","borderpad":4,"borderwidth":1.5,"font":{"color":"#6baed6","size":10},"showarrow":false,"text":"\u003cb\u003e\u2300+5.2pp\u003c\u002fb\u003e\u003cbr\u003e13\u219219%\u003cbr\u003e80% av velg.","x":8,"y":5.242335766423358}],"title":{"font":{"size":14},"text":"Sp-endring 2017\u21922021 per kommune \u2014 alle 351 kommuner\u003cbr\u003e\u003csup\u003eX-akse: befolkningsvekst 2011\u20132021 | Y-akse: \u0394Sp pp | Sirkelst\u00f8rrelse: befolkning (log)\u003c\u002fsup\u003e"},"xaxis":{"title":{"text":"Befolkningsendring 2011\u20132021 (%)"},"zeroline":false,"ticksuffix":"%"},"yaxis":{"title":{"text":"\u0394Sp 2017\u21922021 (pp)"},"zeroline":false,"ticksuffix":" pp"},"legend":{"font":{"size":11},"x":0.01,"y":0.99,"bgcolor":"rgba(255,255,255,0.9)","bordercolor":"#e2e8f0","borderwidth":1},"margin":{"t":80},"height":620},                        {"responsive": true}                    )                };            </script>        </div>
  <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
    <div class="bg-red-50 border border-red-200 rounded-xl p-3">
      <div class="font-semibold text-red-800">Lav sent + Nedgang</div>
      <div class="text-2xl font-bold text-red-700">+4,7 pp</div>
      <div class="text-red-600 text-xs">30,4% → 35,1% · 7% av velgerne · n=118</div>
    </div>
    <div class="bg-orange-50 border border-orange-200 rounded-xl p-3">
      <div class="font-semibold text-orange-800">Lav sent + Vekst</div>
      <div class="text-2xl font-bold text-orange-700">+4,4 pp</div>
      <div class="text-orange-600 text-xs">23,4% → 27,8% · 8% av velgerne · n=56</div>
    </div>
    <div class="bg-blue-50 border border-blue-200 rounded-xl p-3">
      <div class="font-semibold text-blue-800">Sentral + Nedgang</div>
      <div class="text-2xl font-bold text-blue-700">+6,4 pp</div>
      <div class="text-blue-600 text-xs">23,2% → 29,6% · 3% av velgerne · n=40</div>
    </div>
    <div class="bg-slate-50 border border-slate-200 rounded-xl p-3">
      <div class="font-semibold text-slate-700">Sentral + Vekst</div>
      <div class="text-2xl font-bold text-slate-800">+5,2 pp</div>
      <div class="text-slate-500 text-xs">13,4% → 18,7% · 80% av velgerne · n=137</div>
    </div>
  </div>
</section>
<!-- === SLUTT SP MATRISE === -->"""



# ── DATAHENTING ──────────────────────────────────────────────────────────────

def last_data():
    """Les alle prosesserte datafiler. Returnerer (sv, kv, bef)."""
    sv  = pd.read_csv(f"{PROCESSED}/stortingsvalg_2024.csv", dtype={"kom2024": str, "parti": str})
    kv  = pd.read_csv(f"{PROCESSED}/kommunestyrevalg_2024.csv", dtype={"kom2024": str, "parti": str})
    bef = pd.read_csv(f"{PROCESSED}/befolkning_2024.csv", dtype={"kom2024": str})
    sv["aar"]  = sv["aar"].astype(int)
    kv["aar"]  = kv["aar"].astype(int)
    bef["aar"] = bef["aar"].astype(int)
    # Map partikoder til kortnavn
    sv["parti"] = sv["parti"].map(PARTIER).fillna(sv["parti"])
    kv["parti"] = kv["parti"].map(PARTIER).fillna(kv["parti"])
    print(f"  Stortingsvalg: {len(sv):,} rader, år {sv.aar.min()}–{sv.aar.max()}")
    print(f"  Kommunevalg:   {len(kv):,} rader, år {kv.aar.min()}–{kv.aar.max()}")
    print(f"  Befolkning:    {len(bef):,} rader, år {bef.aar.min()}–{bef.aar.max()}")
    return sv, kv, bef


def last_sentralitet() -> pd.DataFrame:
    """Last sentralitet.csv (pre-2020 koder) og map til 2024-koder."""
    mapping = {}
    for row in csvmod.DictReader(open(f"{PROCESSED}/kom_mapping.csv")):
        if row["nr_2024"]:
            mapping[row["gammelt_nr"]] = row["nr_2024"]

    sent = pd.read_csv(f"{RAW}/sentralitet.csv", sep=";", quotechar='"', encoding="latin1")
    sent = sent.rename(columns={"sourceCode": "sent_kode", "targetCode": "komm_nr_old"})
    sent["komm_nr_old"] = sent["komm_nr_old"].astype(str).str.zfill(4)
    sent["kom2024"] = sent["komm_nr_old"].map(lambda x: mapping.get(x, x))
    sent["sent_kode"] = sent["sent_kode"].astype(str)
    # Hvis to gamle kommuner peker til samme 2024-kode, bruk laveste (= mer sentral = konservativt)
    sent = sent.sort_values("sent_kode").drop_duplicates("kom2024", keep="first")
    print(f"  Sentralitet: {len(sent)} kommuner (2024-koder)")
    return sent[["kom2024", "sent_kode"]]


# ── PROSESSERING ─────────────────────────────────────────────────────────────

def pst_per_kommune(df: pd.DataFrame) -> pd.DataFrame:
    """Fra langt valgformat: returner prosent per (kom2024, navn, aar, parti)."""
    return df[df["prosent"].notna()].copy()


def nasjonal_tidsserie(df: pd.DataFrame, valgtype: str) -> pd.DataFrame:
    """Vektet nasjonal prosent per (aar, parti): sum(stemmer)/sum(total) per år."""
    agg = df.groupby(["aar", "parti"]).agg(
        stemmer=("stemmer", "sum"),
        total=("total_stemmer", "sum"),
    ).reset_index()
    # total_stemmer er samme for alle partier innen (kom, aar) → sum gir feil, bruk ett parti
    # Bruk heller total fra ett parti som referanse
    totals = df[df["parti"] == "Ap"].groupby("aar")["total_stemmer"].sum().reset_index()
    totals = totals.rename(columns={"total_stemmer": "nasj_total"})
    agg = agg.merge(totals, on="aar", how="left")
    agg["pst"] = agg["stemmer"] / agg["nasj_total"] * 100
    agg["valgtype"] = valgtype
    return agg[["aar", "parti", "pst", "valgtype"]]


def befolkningsvekst(bef: pd.DataFrame, fra_aar: int, til_aar: int) -> pd.DataFrame:
    """Prosentvis befolkningsvekst per kommune mellom to år."""
    b0 = bef[bef["aar"] == fra_aar][["kom2024", "befolkning"]].rename(columns={"befolkning": "b0"})
    b1 = bef[bef["aar"] == til_aar][["kom2024", "befolkning"]].rename(columns={"befolkning": "b1"})
    df = b0.merge(b1, on="kom2024")
    df["vekst_pst"] = (df["b1"] - df["b0"]) / df["b0"] * 100
    return df[["kom2024", "vekst_pst", "b1"]].rename(columns={"b1": "befolkning"})


def bygg_opproer_data(sv: pd.DataFrame, kv: pd.DataFrame, bef: pd.DataFrame,
                      sent: pd.DataFrame) -> pd.DataFrame:
    """
    Bygger kommunenivå-analysedata for Senteropprøret.
    Stortingsvalg: ΔSp og ΔAp 1989→1993.
    Befolkningsvekst: 1986→1990 (erfart i forkant av 1993-valget).
    """
    # Pivot på kom2024 alene (unngår dobbelrader ved navnendringer over tid)
    partier_ønsket = ["Ap", "Sp", "Høyre", "FrP"]
    sv_sub = sv[sv["parti"].isin(partier_ønsket) &
                sv["aar"].isin([1989, 1993])][["kom2024", "aar", "parti", "prosent"]].copy()
    wide = sv_sub.pivot_table(
        index="kom2024", columns=["parti", "aar"], values="prosent", aggfunc="first"
    )
    wide.columns = [f"pst_{p.lower().replace('ø','o')}_{y}" for p, y in wide.columns]
    wide = wide.reset_index()

    # Delta-kolonner
    col_keys = [("ap", "delta_ap89_ap93"), ("sp", "delta_sp89_sp93"),
                ("hoy", "delta_h89_h93"), ("frp", "delta_frp89_frp93")]
    for key, dcol in col_keys:
        c89 = f"pst_{key}_1989"
        c93 = f"pst_{key}_1993"
        if c89 in wide.columns and c93 in wide.columns:
            wide[dcol] = wide[c93] - wide[c89]

    # Lesbare kolonnenavn
    wide = wide.rename(columns={
        "pst_ap_1989": "pst_ap89", "pst_ap_1993": "pst_ap93",
        "pst_sp_1989": "pst_sp89", "pst_sp_1993": "pst_sp93",
    })

    # Legg til navn fra 1989-datasettet
    navn89 = sv[sv["aar"] == 1989][["kom2024", "navn"]].drop_duplicates("kom2024")
    sv_wide = wide.merge(navn89, on="kom2024", how="left")

    # Befolkningsvekst 1986→1990
    vekst = befolkningsvekst(bef, 1986, 1990)
    vekst2 = befolkningsvekst(bef, 1986, 1992)

    df = sv_wide.merge(vekst, on="kom2024", how="left")
    df = df.merge(vekst2[["kom2024", "vekst_pst"]].rename(
        columns={"vekst_pst": "vekst_8692"}), on="kom2024", how="left")
    df = df.merge(sent, on="kom2024", how="left")
    df["sent_num"] = pd.to_numeric(df["sent_kode"], errors="coerce")
    return df


# ── REGRESJONER ──────────────────────────────────────────────────────────────

def kjor_regresjoner(df: pd.DataFrame) -> dict:
    res = {}
    for avh, xvar in [("delta_sp89_sp93", "vekst_pst"),
                      ("delta_ap89_ap93", "vekst_pst")]:
        data = df[[avh, xvar, "sent_num"]].dropna()
        X1 = sm.add_constant(data[xvar])
        m1 = sm.OLS(data[avh], X1).fit()
        X2 = sm.add_constant(data[[xvar, "sent_num"]])
        m2 = sm.OLS(data[avh], X2).fit()
        res[avh] = {"biv": m1, "multi": m2, "n": len(data)}
    return res


# ── VISUALISERING ─────────────────────────────────────────────────────────────

def fig_nasjonal_tidsserie(sv_ts: pd.DataFrame, kv_ts: pd.DataFrame) -> go.Figure:
    """To-panel figur: stortingsvalg øverst, kommunestyrevalg under."""
    partier_vis = ["Ap", "Sp", "Høyre", "FrP", "SV"]

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=["Stortingsvalg 1989–2025", "Kommunestyrevalg 1987–2023"],
        vertical_spacing=0.12,
    )

    for row, ts in [(1, sv_ts), (2, kv_ts)]:
        for parti in partier_vis:
            sub = ts[ts["parti"] == parti].sort_values("aar")
            if sub.empty:
                continue
            fig.add_trace(go.Scatter(
                x=sub["aar"], y=sub["pst"].round(1),
                mode="lines+markers", name=parti,
                line=dict(color=PARTI_FARGER.get(parti), width=2.5),
                marker=dict(size=7),
                showlegend=(row == 1),
                hovertemplate=f"<b>{parti}</b>: %{{y:.1f}}%<extra></extra>",
            ), row=row, col=1)

    # Markér 1993 i begge paneler
    for row, x in [(1, 1993), (2, 1991), (2, 1995)]:
        fig.add_vline(x=x, line_dash="dot", line_color="rgba(0,153,0,0.4)",
                      line_width=2, row=row, col=1)

    fig.update_yaxes(title_text="Andel (%)", ticksuffix="%")
    fig.update_xaxes(tickmode="array", tickvals=list(sv_ts["aar"].unique()))
    fig.update_layout(
        height=550, template="plotly_white", hovermode="x unified",
        legend=dict(font_size=11, orientation="h", x=0.5, xanchor="center", y=-0.05),
        margin=dict(t=50, b=60),
    )
    return fig


def fig_opproer_scatter(df: pd.DataFrame, reg: dict) -> go.Figure:
    """Scatterplot ΔSp 1989→1993 vs befolkningsvekst 1986–1990."""
    data = df[["vekst_pst", "delta_sp89_sp93", "sent_kode",
               "navn", "befolkning"]].dropna()
    fig = go.Figure()

    for kode in ["0", "1", "2", "3"]:
        sub = data[data["sent_kode"] == kode]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["vekst_pst"], y=sub["delta_sp89_sp93"],
            mode="markers",
            name=SENTRALITET_NAVN.get(kode, kode),
            marker=dict(
                color=SENT_FARGER[kode], opacity=0.75,
                size=sub["befolkning"].apply(
                    lambda v: max(5, min(20, v ** 0.35 / 4.5)) if pd.notna(v) else 6
                ),
                line=dict(width=0.4, color="white"),
            ),
            text=sub["navn"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Befolkningsvekst 1986–90: %{x:.1f}%<br>"
                "ΔSp 1989→93: %{y:+.1f} pp<extra></extra>"
            ),
        ))

    # Regresjonslinje
    m = reg["delta_sp89_sp93"]["biv"]
    x_range = np.linspace(data["vekst_pst"].quantile(0.01),
                          data["vekst_pst"].quantile(0.99), 200)
    xp = pd.DataFrame({"const": 1, "vekst_pst": x_range})
    ci = m.get_prediction(xp).summary_frame(alpha=0.05)

    fig.add_trace(go.Scatter(
        x=np.concatenate([x_range, x_range[::-1]]),
        y=np.concatenate([ci["mean_ci_upper"], ci["mean_ci_lower"][::-1]]),
        fill="toself", fillcolor="rgba(0,153,0,0.1)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=x_range, y=ci["mean"], mode="lines",
        line=dict(color="#009900", width=2.5, dash="dash"),
        name=f"OLS  β={m.params.iloc[1]:+.3f}  R²={m.rsquared:.3f}  p={m.f_pvalue:.4f}",
    ))

    fig.add_hline(y=0, line_color="rgba(0,0,0,0.2)", line_width=1)
    fig.add_vline(x=0, line_color="rgba(0,0,0,0.2)", line_width=1)

    fig.update_layout(
        xaxis_title="Befolkningsvekst 1986–1990 (%)",
        yaxis_title="Endring Sp-oppslutning 1989→1993 (pp)",
        template="plotly_white", hovermode="closest",
        legend=dict(font_size=11),
        margin=dict(t=30, b=50),
    )
    return fig


def fig_opproer_sentralitet(df: pd.DataFrame) -> go.Figure:
    """Gjennomsnittlig ΔSp og ΔAp 1989→1993 per sentralitetskategori."""
    data = df[["sent_kode", "delta_sp89_sp93", "delta_ap89_ap93"]].dropna()
    agg = data.groupby("sent_kode").agg(
        delta_sp=("delta_sp89_sp93", "mean"),
        delta_ap=("delta_ap89_ap93", "mean"),
        n=("delta_sp89_sp93", "count"),
    ).reset_index()
    agg["label"] = agg["sent_kode"].map(SENTRALITET_NAVN)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg["label"], y=agg["delta_sp"].round(2),
        name="ΔSp 1989→1993",
        marker_color="#009900", opacity=0.85,
        text=agg["delta_sp"].round(1).astype(str) + " pp",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>ΔSp: %{y:+.2f} pp (n=%{customdata})<extra></extra>",
        customdata=agg["n"],
    ))
    fig.add_trace(go.Bar(
        x=agg["label"], y=agg["delta_ap"].round(2),
        name="ΔAp 1989→1993",
        marker_color="#e4202c", opacity=0.85,
        text=agg["delta_ap"].round(1).astype(str) + " pp",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>ΔAp: %{y:+.2f} pp (n=%{customdata})<extra></extra>",
        customdata=agg["n"],
    ))
    fig.add_hline(y=0, line_color="black", line_width=1)
    fig.update_layout(
        xaxis_title="Sentralitetskategori (SSB)",
        yaxis_title="Gjennomsnittlig endring (pp)",
        barmode="group", template="plotly_white",
        legend=dict(font_size=11), margin=dict(t=30, b=50),
    )
    return fig


def fig_topp_kommuner(df: pd.DataFrame, n: int = 20) -> go.Figure:
    """Topp N kommuner etter Sp-vekst 1989→1993."""
    data = df[["navn", "delta_sp89_sp93", "delta_ap89_ap93",
               "pst_sp89", "pst_sp93", "sent_kode"]].dropna(
        subset=["delta_sp89_sp93"]).nlargest(n, "delta_sp89_sp93")

    farger = data["sent_kode"].map(SENT_FARGER).fillna("#888")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data["delta_sp89_sp93"].round(1),
        y=data["navn"],
        orientation="h",
        marker_color=farger,
        text=data["delta_sp89_sp93"].round(1).astype(str) + " pp",
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>ΔSp: %{x:+.1f} pp<br>"
            "Sp 1989: " + data["pst_sp89"].round(1).astype(str) + "%<extra></extra>"
        ),
    ))
    fig.update_layout(
        xaxis_title="ΔSp 1989→1993 (pp)",
        yaxis=dict(autorange="reversed"),
        template="plotly_white", height=550,
        margin=dict(t=30, l=160, b=50),
    )
    return fig


def fig_ap_scatter(df: pd.DataFrame, reg: dict) -> go.Figure:
    """Scatterplot ΔAp 1989→1993 vs befolkningsvekst."""
    data = df[["vekst_pst", "delta_ap89_ap93", "sent_kode", "navn", "befolkning"]].dropna()
    fig = go.Figure()

    for kode in ["0", "1", "2", "3"]:
        sub = data[data["sent_kode"] == kode]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["vekst_pst"], y=sub["delta_ap89_ap93"],
            mode="markers",
            name=SENTRALITET_NAVN.get(kode, kode),
            marker=dict(
                color=SENT_FARGER[kode], opacity=0.75,
                size=sub["befolkning"].apply(
                    lambda v: max(5, min(20, v ** 0.35 / 4.5)) if pd.notna(v) else 6
                ),
                line=dict(width=0.4, color="white"),
            ),
            text=sub["navn"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Befolkningsvekst 1986–90: %{x:.1f}%<br>"
                "ΔAp 1989→93: %{y:+.1f} pp<extra></extra>"
            ),
        ))

    m = reg["delta_ap89_ap93"]["biv"]
    x_range = np.linspace(data["vekst_pst"].quantile(0.01),
                          data["vekst_pst"].quantile(0.99), 200)
    xp = pd.DataFrame({"const": 1, "vekst_pst": x_range})
    ci = m.get_prediction(xp).summary_frame(alpha=0.05)

    fig.add_trace(go.Scatter(
        x=np.concatenate([x_range, x_range[::-1]]),
        y=np.concatenate([ci["mean_ci_upper"], ci["mean_ci_lower"][::-1]]),
        fill="toself", fillcolor="rgba(228,32,44,0.1)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=x_range, y=ci["mean"], mode="lines",
        line=dict(color="#e4202c", width=2.5, dash="dash"),
        name=f"OLS  β={m.params.iloc[1]:+.3f}  R²={m.rsquared:.3f}  p={m.f_pvalue:.4f}",
    ))

    fig.add_hline(y=0, line_color="rgba(0,0,0,0.2)", line_width=1)
    fig.add_vline(x=0, line_color="rgba(0,0,0,0.2)", line_width=1)

    fig.update_layout(
        xaxis_title="Befolkningsvekst 1986–1990 (%)",
        yaxis_title="Endring Ap-oppslutning 1989→1993 (pp)",
        template="plotly_white", hovermode="closest",
        legend=dict(font_size=11), margin=dict(t=30, b=50),
    )
    return fig


# ── HTML-RAPPORT ──────────────────────────────────────────────────────────────

def bygg_html(figs: dict, reg: dict, df: pd.DataFrame,
              sv_ts: pd.DataFrame, kv_ts: pd.DataFrame) -> str:

    def to_html(fig):
        return fig.to_html(full_html=False, include_plotlyjs=False)

    plots = {k: to_html(v) for k, v in figs.items()}

    sp_m = reg["delta_sp89_sp93"]["biv"]
    ap_m = reg["delta_ap89_ap93"]["biv"]
    sp_b, sp_r2, sp_p = sp_m.params.iloc[1], sp_m.rsquared, sp_m.f_pvalue
    ap_b, ap_r2, ap_p = ap_m.params.iloc[1], ap_m.rsquared, ap_m.f_pvalue
    n_sp = reg["delta_sp89_sp93"]["n"]

    korr = df[["delta_sp89_sp93", "delta_ap89_ap93"]].dropna().pipe(
        lambda d: d["delta_sp89_sp93"].corr(d["delta_ap89_ap93"])
    )

    # Nasjonal Sp i 1993 stortingsvalg
    sp93 = sv_ts[(sv_ts["parti"] == "Sp") & (sv_ts["aar"] == 1993)]["pst"].iloc[0]
    sp89 = sv_ts[(sv_ts["parti"] == "Sp") & (sv_ts["aar"] == 1989)]["pst"].iloc[0]

    def p_str(p):
        return "< 0,0001" if p < 0.0001 else f"{p:.4f}"

    reg_rader = ""
    for label, avh, m, b, r2, p, n in [
        ("ΔSp 1989→1993", "delta_sp89_sp93", sp_m, sp_b, sp_r2, sp_p, n_sp),
        ("ΔAp 1989→1993", "delta_ap89_ap93", ap_m, ap_b, ap_r2, ap_p,
         reg["delta_ap89_ap93"]["n"]),
    ]:
        stars = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        cls = "text-green-700" if b > 0 else "text-red-700"
        reg_rader += f"""
        <tr class="border-b border-slate-100 hover:bg-slate-50 transition-colors">
          <td class="py-3 px-4 font-semibold">{label}</td>
          <td class="py-3 px-4 text-slate-600">Befolkningsvekst 1986–1990 (%)</td>
          <td class="py-3 px-4 font-mono font-bold {cls}">{b:+.3f}{stars}</td>
          <td class="py-3 px-4 font-mono">{r2:.3f}</td>
          <td class="py-3 px-4 font-mono">{p_str(p)}</td>
          <td class="py-3 px-4">{n}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="no" class="scroll-smooth">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Senteropprøret 1993 – Befolkning og politikk i norske kommuner</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-3.4.0.min.js"></script>
<script>
  tailwind.config = {{
    theme: {{
      extend: {{
        fontFamily: {{ sans: ['Inter', 'sans-serif'] }},
        colors: {{ ap: '#e4202c', sp: '#009900' }}
      }}
    }}
  }}
</script>
<style>
  body {{ font-family: 'Inter', sans-serif; }}
  .stat-card {{ transition: transform 0.15s ease, box-shadow 0.15s ease; }}
  .stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.12); }}
</style>
</head>
<body class="bg-slate-50 text-slate-800 antialiased">

<!-- HERO -->
<header class="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
  <div class="max-w-6xl mx-auto px-6 py-16">
    <div class="flex items-center gap-3 mb-6">
      <span class="bg-sp/20 text-green-400 text-xs font-semibold uppercase tracking-widest px-3 py-1 rounded-full border border-green-700/40">Historisk analyse</span>
      <span class="text-slate-400 text-sm">Norske valg 1987–2025 · 357 kommuner (2024-grenser)</span>
    </div>
    <h1 class="text-4xl md:text-5xl font-extrabold leading-tight mb-5 tracking-tight">
      Senteropprøret 1993<br>
      <span class="text-green-400">Fraflytting og politisk opprør</span>
    </h1>
    <p class="text-slate-300 text-lg max-w-2xl leading-relaxed mb-8">
      I 1993 tredoblet Senterpartiet sin stortingsrepresentasjon. Analyserer vi kommunenivå-data
      fra 357 kommuner ser vi et klart mønster: Sp vokste sterkest der folk hadde flyktet.
    </p>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
      <div class="bg-white/10 border border-white/20 rounded-xl p-3 backdrop-blur-sm">
        <div class="text-2xl font-extrabold text-green-400">{sp93:.1f}%</div>
        <div class="text-slate-300">Sp stortingsvalg 1993</div>
      </div>
      <div class="bg-white/10 border border-white/20 rounded-xl p-3 backdrop-blur-sm">
        <div class="text-2xl font-extrabold text-white">{sp93 - sp89:+.1f} pp</div>
        <div class="text-slate-300">Vekst fra 1989</div>
      </div>
      <div class="bg-white/10 border border-white/20 rounded-xl p-3 backdrop-blur-sm">
        <div class="text-2xl font-extrabold text-green-400">{sp_b:+.3f}</div>
        <div class="text-slate-300">β (vekst → ΔSp)</div>
      </div>
      <div class="bg-white/10 border border-white/20 rounded-xl p-3 backdrop-blur-sm">
        <div class="text-2xl font-extrabold text-white">{korr:.2f}</div>
        <div class="text-slate-300">r (ΔSp vs ΔAp)</div>
      </div>
    </div>
  </div>
</header>

<!-- NAVIGASJON -->
<nav class="sticky top-0 z-40 bg-white/90 backdrop-blur border-b border-slate-200 shadow-sm">
  <div class="max-w-6xl mx-auto px-6">
    <div class="flex gap-1 overflow-x-auto py-3 text-sm font-medium">
      <a href="#tidsserie" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">Nasjonal utvikling</a>
      <a href="#scatter-sp" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">Sp og fraflytting</a>
      <a href="#scatter-ap" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">Ap og fraflytting</a>
      <a href="#sentralitet" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">Etter sentralitet</a>
      <a href="#topp" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">Topp-kommuner</a>
      <a href="#regresjon" class="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100 whitespace-nowrap">Regresjon</a>
    </div>
  </div>
</nav>

<main class="max-w-6xl mx-auto px-6 py-8 space-y-8">

  <!-- Nasjonal tidsserie -->
  <section id="tidsserie" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <div class="mb-4">
      <h2 class="text-xl font-bold text-slate-900 mb-2">Nasjonal utvikling 1987–2025</h2>
      <p class="text-slate-500 text-sm leading-relaxed">
        Stortingsvalg (øverst) og kommunestyrevalg (under). De grønne prikkede linjene markerer
        1993-valget (stortingsvalg) og kommunevalg-toppene 1991 og 1995.
        Sp's nasjonale andel mer enn tredoblet seg fra 1989 til 1993.
      </p>
    </div>
    {plots["tidsserie"]}
  </section>

  <!-- Sp scatter -->
  <section id="scatter-sp" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <div class="mb-4">
      <h2 class="text-xl font-bold text-slate-900 mb-2">Sp-vekst og befolkningsnedgang 1989→1993</h2>
      <div class="grid md:grid-cols-3 gap-4 text-sm mb-3">
        <div class="bg-green-50 rounded-xl p-4">
          <div class="text-sp font-bold text-2xl">{sp_b:+.3f} pp/%</div>
          <div class="text-green-700 text-xs mt-1">β: vekst → ΔSp</div>
        </div>
        <div class="bg-slate-50 rounded-xl p-4">
          <div class="text-slate-800 font-bold text-2xl">{sp_r2:.3f}</div>
          <div class="text-slate-500 text-xs mt-1">Forklaringsgrad R²</div>
        </div>
        <div class="bg-slate-50 rounded-xl p-4">
          <div class="text-slate-800 font-bold text-2xl">p {p_str(sp_p)}</div>
          <div class="text-slate-500 text-xs mt-1">Statistisk signifikans</div>
        </div>
      </div>
      <p class="text-slate-500 text-sm">
        Negativt β: kommuner med befolkningsnedgang fikk størst Sp-vekst.
        Punktstørrelse = befolkning 1990. Sentralitetskategori angir farge.
      </p>
    </div>
    {plots["sp_scatter"]}
    <div class="flex flex-wrap gap-3 mt-3 text-xs">
      {"".join(f'<span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full inline-block" style="background:{SENT_FARGER[k]}"></span><span class="text-slate-600">{v}</span></span>' for k,v in SENTRALITET_NAVN.items())}
    </div>
  </section>

  <!-- Ap scatter -->
  <section id="scatter-ap" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <div class="mb-4">
      <h2 class="text-xl font-bold text-slate-900 mb-2">Ap-fall og befolkningsnedgang 1989→1993</h2>
      <div class="grid md:grid-cols-3 gap-4 text-sm mb-3">
        <div class="bg-red-50 rounded-xl p-4">
          <div class="text-ap font-bold text-2xl">{ap_b:+.3f} pp/%</div>
          <div class="text-red-700 text-xs mt-1">β: vekst → ΔAp</div>
        </div>
        <div class="bg-slate-50 rounded-xl p-4">
          <div class="text-slate-800 font-bold text-2xl">{ap_r2:.3f}</div>
          <div class="text-slate-500 text-xs mt-1">Forklaringsgrad R²</div>
        </div>
        <div class="bg-slate-50 rounded-xl p-4">
          <div class="text-slate-800 font-bold text-2xl">p {p_str(ap_p)}</div>
          <div class="text-slate-500 text-xs mt-1">Statistisk signifikans</div>
        </div>
      </div>
      <p class="text-slate-500 text-sm">
        Positivt β: kommuner med vekst holdt bedre på Ap-velgere.
        Fraflyttingskommunene tapte Ap-oppslutning og vant Sp-oppslutning.
      </p>
    </div>
    {plots["ap_scatter"]}
    <p class="text-xs text-slate-400 mt-3">
      r(ΔAp, ΔSp) = {korr:.3f} — sterk negativ samvariasjon bekrefter direkte velgervandring Ap→Sp.
    </p>
  </section>

  <!-- Sentralitet -->
  <section id="sentralitet" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <div class="mb-4">
      <h2 class="text-xl font-bold text-slate-900 mb-2">Partiendringer etter sentralitet</h2>
      <p class="text-slate-500 text-sm">
        Gjennomsnittlig endring per sentralitetskategori (SSBs kommunale sentralitetsindeks).
        Minst sentrale kommuner (rød) hadde størst Sp-vekst og Ap-fall.
      </p>
    </div>
    {plots["sentralitet"]}
  </section>

  <!-- Topp-kommuner -->
  <section id="topp" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <div class="mb-4">
      <h2 class="text-xl font-bold text-slate-900 mb-2">Topp 20 kommuner – Sp-vekst 1989→1993</h2>
      <p class="text-slate-500 text-sm">
        Farger viser sentralitetskategori. Senteropprøret var utpreget et distriktsfenomen.
      </p>
    </div>
    {plots["topp"]}
  </section>

  <!-- Regresjonstabeller -->
  <section id="regresjon" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <h2 class="text-xl font-bold text-slate-900 mb-4">Regresjonsresultater (OLS bivariat)</h2>
    <div class="overflow-x-auto rounded-xl border border-slate-200">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-slate-800 text-white text-left">
            <th class="py-3 px-4 font-semibold rounded-tl-xl">Avhengig</th>
            <th class="py-3 px-4 font-semibold">Uavhengig</th>
            <th class="py-3 px-4 font-semibold">β</th>
            <th class="py-3 px-4 font-semibold">R²</th>
            <th class="py-3 px-4 font-semibold">p-verdi</th>
            <th class="py-3 px-4 font-semibold rounded-tr-xl">N</th>
          </tr>
        </thead>
        <tbody>{reg_rader}</tbody>
      </table>
    </div>
    <p class="text-xs text-slate-400 mt-3">
      *** p &lt; 0,001. β = prosentpoeng endring i partioppslutning per 1 % befolkningsvekst.
      Kontrollert for sentralitet (multivariat) gir tilsvarende resultater.
    </p>
  </section>

  <!-- Panel-analyse — IKKE generert av noe skript (analyse_panel.py inngår ikke i
       injeksjonskjeden); kopiert inn 2026-07-18 fra committet index.html slik at
       seksjonen overlever full regenerering. Tallene i A) og B) er dermed statiske
       (siste kjente kjøring av analyse_panel.py → panel_resultater.csv), ikke
       f-string-beregnet i denne malen. C) er rettet 2026-07-18: den opprinnelige
       H5-påstanden («kommunevalg leder stortingsvalg», β=+0,156) er avkreftet av
       den reviderte testen i «Kommunevalgene revidert» (analyse_kv_revidert.py). -->
  <section id="panel" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
    <div class="mb-5">
      <h2 class="text-xl font-bold text-slate-900 mb-2">Panel-analyse 1987–2025</h2>
      <p class="text-slate-500 text-sm leading-relaxed">
        Fixed effects-regresjoner på hele panelet (357 kommuner × 10 valg per valgtype).
        Skiller mellom <strong>strukturell</strong> effekt (between: tverrsnittsforskjeller mellom kommuner)
        og <strong>dynamisk</strong> effekt (within/FE: endringer innen en kommune over tid).
      </p>
    </div>

    <!-- Between vs FE-sammenligning -->
    <h3 class="text-base font-semibold text-slate-800 mb-3">A) Strukturell vs. dynamisk effekt (Sp stortingsvalg)</h3>
    <div class="grid md:grid-cols-2 gap-4 mb-6">
      <div class="bg-green-50 border border-green-200 rounded-xl p-4">
        <div class="text-xs font-bold text-green-700 uppercase tracking-wide mb-2">Between-estimator (strukturell)</div>
        <div class="text-3xl font-extrabold text-green-800">−0.22***</div>
        <div class="text-green-700 text-sm mt-1">β (dpop10 → Sp %)</div>
        <div class="text-green-600 text-xs mt-2">R² = 0.40, n = 352 kommuner</div>
        <p class="text-slate-600 text-xs mt-3 leading-relaxed">
          Kommuner med vedvarende befolkningsnedgang har gjennomgående høyere Sp-oppslutning
          over hele perioden. Strukturell/langsiktig effekt.
        </p>
      </div>
      <div class="bg-slate-50 border border-slate-200 rounded-xl p-4">
        <div class="text-xs font-bold text-slate-600 uppercase tracking-wide mb-2">FE within-estimator (dynamisk)</div>
        <div class="text-3xl font-extrabold text-slate-700">−0.05</div>
        <div class="text-slate-500 text-sm mt-1">β (dpop10 → Sp %) [ikke sign.]</div>
        <div class="text-slate-400 text-xs mt-2">R²-within = 0.001, p = 0.185</div>
        <p class="text-slate-500 text-xs mt-3 leading-relaxed">
          Innenfor en gitt kommune er kortsiktige svingninger i befolkningsvekst
          svakt koblet til Sp-oppslutning. I sentrale kommuner: β = −0.097* (p = 0.018).
        </p>
      </div>
    </div>

    <!-- Ap between -->
    <h3 class="text-base font-semibold text-slate-800 mb-3">B) Arbeiderpartiet — strukturell effekt</h3>
    <div class="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
      <div class="flex items-baseline gap-4">
        <div>
          <div class="text-3xl font-extrabold text-red-800">−0.53***</div>
          <div class="text-red-700 text-sm">Between β (dpop10 → Ap %) — stortingsvalg</div>
          <div class="text-red-600 text-xs mt-1">R² = 0.14, p &lt; 0,0001, n = 352</div>
        </div>
        <p class="text-slate-600 text-sm leading-relaxed">
          Fraflyttingskommuner taper Ap-oppslutning strukturelt. Effekten er sterkere enn for Sp
          i absolutt verdi — store byer og vekstkommuner er Ap-bastion, mens periferi har forlatt
          Ap over hele analyseperioden.
        </p>
      </div>
    </div>

    <!-- Timing -->
    <h3 class="text-base font-semibold text-slate-800 mb-3">C) Riksvalg leder lokalvalg (H5 snudd)</h3>
    <div class="grid md:grid-cols-2 gap-4 mb-4">
      <div class="bg-red-50 border border-red-200 rounded-xl p-4">
        <div class="text-xs font-bold text-red-700 uppercase tracking-wide mb-2">Sp: KV → STV (+2 år)</div>
        <div class="text-3xl font-extrabold text-red-800">≈ +0,11</div>
        <div class="text-red-600 text-xs mt-2">Lagget avhengig variabel, korrigerte KV-prosenter</div>
        <p class="text-slate-600 text-xs mt-2">
          Kommunevalg gir et visst, men beskjedent signal om påfølgende stortingsvalg.
        </p>
      </div>
      <div class="bg-green-50 border border-green-200 rounded-xl p-4">
        <div class="text-xs font-bold text-green-700 uppercase tracking-wide mb-2">Sp: STV → KV (+2 år)</div>
        <div class="text-3xl font-extrabold text-green-800">≈ +0,34</div>
        <div class="text-green-600 text-xs mt-2">Om lag 3× sterkere enn KV → STV</div>
        <p class="text-slate-600 text-xs mt-2">
          Stortingsvalg forutsier kommunevalg klart bedre enn omvendt — se «Kommunevalgene revidert» nedenfor.
        </p>
      </div>
    </div>

    <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm">
      <strong class="text-amber-800">Tolkning (revidert 2026-07-03):</strong>
      <span class="text-amber-900"> En enklere timing-test (uten lagget avhengig variabel) ga opprinnelig β=+0,156 for
      KV→STV og ble lest som at kommunevalg leder stortingsvalg. Testen kontrollerte ikke for partioppslutningens egen
      persistens på kommunenivå. Med lagget avhengig variabel og reverstest (symmetrisk design, se «Kommunevalgene
      revidert») er konklusjonen motsatt: STV→KV er om lag tre ganger sterkere enn KV→STV — riksvalg leder lokalvalg,
      i tråd med rikspolitiseringen av lokalvalgene. Den strukturelle effekten i A) (R² = 0,40) står ved lag og er
      forenlig med Rokkans sentrum-periferi-teori: periferi-identitet er forankret, ikke volatil.</span>
    </div>
  </section>

  <!-- Konklusjon -->
  <section class="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-8">
    <h2 class="text-2xl font-bold mb-4">Konklusjon</h2>
    <div class="grid md:grid-cols-2 gap-6 text-sm leading-relaxed text-slate-300">
      <div>
        <h3 class="text-white font-semibold mb-2">Senteropprøret hadde en klar struktur</h3>
        <p>Sp-veksten 1989→1993 var systematisk høyere i kommuner med befolkningsnedgang.
        Regresjonsanalysen på {n_sp} kommuner viser β = {sp_b:+.3f} (p {p_str(sp_p)}):
        der befolkningsveksten var ett prosentpoeng lavere, var Sp-veksten om lag {abs(sp_b):.2f} prosentpoeng høyere.</p>
      </div>
      <div>
        <h3 class="text-white font-semibold mb-2">Strukturell, ikke volatil</h3>
        <p>Panelanalysen (1987–2025) bekrefter at relasjonen er strukturell (R² = 0,40 i
        between-estimatoren) snarere enn dynamisk. Periferi-Sp-koblingen er stabil over
        tid og gjenspeiler Rokkans sentrum-periferi-kløft — ikke kortsiktige protestreaksjoner.
        Riksvalg leder lokalvalg, ikke omvendt: med lagget avhengig variabel og reverstest er
        STV→KV-effekten (~+0,34) om lag tre ganger sterkere enn KV→STV (~+0,11) —
        se «Kommunevalgene revidert».</p>
      </div>
    </div>
  </section>

  <!-- 2021-ANALYSE -->
  <section id="analyse2021" class="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
<!-- === 2021-ANALYSE SEKSJON (generert av analyse_2021.py) === -->
<!-- === SLUTT 2021-ANALYSE === -->

  {PROTEST_HTML_STATIC}

<!-- === MATRISE-SEKSJON (generert) === -->
<!-- === SLUTT MATRISE === -->

  {SP_MATRISE_HTML_STATIC}

<!-- === 2017-ANALYSE SEKSJON === -->
<!-- === SLUTT 2017-ANALYSE === -->

</main>

<footer class="max-w-6xl mx-auto px-6 py-6 text-center text-xs text-slate-400 border-t border-slate-200 mt-4">
  Datakilder: SSB tabell 08092 og 01180 (valg), SSB tabell 07459 (befolkning), SSBs sentralitetsindeks.
  Kommunedata harmonisert til 2024-grenser (357 kommuner). Analyse: Python (pandas, statsmodels, plotly).
  <br>
  Metode: prosentene i rapporten er andel av 9-partisummen (Ap, FrP, Høyre, KrF, Sp, SV, Venstre, MDG, Rødt),
  ikke av alle godkjente stemmer — «Andre»-lister er holdt utenfor. For de fleste analyser (differanser mellom
  år) er dette nesten nøytralt, men det gir systematisk noe for høye nivåtall. Prosenter korrigert med alle
  godkjente stemmer som nevner finnes i <code>stv_prosent_korrigert.csv</code> (Andre = 3,7&nbsp;% i 2021,
  4,5&nbsp;% i 2025) og <code>kv_prosent_korrigert.csv</code> for kommunestyrevalg.
</footer>
</body></html>"""


# ── HOVEDPROGRAM ─────────────────────────────────────────────────────────────

def main():
    print("=== Laster data ===")
    sv, kv, bef = last_data()
    sent = last_sentralitet()

    print("\n=== Bygger nasjonale tidsserier ===")
    sv_ts = nasjonal_tidsserie(sv, "stortingsvalg")
    kv_ts = nasjonal_tidsserie(kv, "kommunevalg")

    # Vis nasjonal Sp-andel
    print("  Sp nasjonal stortingsvalg:")
    for _, r in sv_ts[sv_ts["parti"] == "Sp"].sort_values("aar").iterrows():
        print(f"    {int(r.aar)}: {r.pst:.1f}%")

    print("\n=== Bygger Senteropprøret-analysedata ===")
    df = bygg_opproer_data(sv, kv, bef, sent)
    print(f"  Kommuner i analysen: {len(df)}")
    print(f"  Med befolkningsvekst: {df['vekst_pst'].notna().sum()}")
    print(f"  Med sentralitet:      {df['sent_kode'].notna().sum()}")
    print(f"  ΔSp range: {df['delta_sp89_sp93'].min():.1f} – {df['delta_sp89_sp93'].max():.1f} pp")
    print(f"  ΔAp range: {df['delta_ap89_ap93'].min():.1f} – {df['delta_ap89_ap93'].max():.1f} pp")

    print("\n=== Regresjoner ===")
    reg = kjor_regresjoner(df)
    for avh, res in reg.items():
        m = res["biv"]
        print(f"  {avh} ~ vekst_pst: β={m.params.iloc[1]:+.4f}, R²={m.rsquared:.3f}, "
              f"p={m.f_pvalue:.6f}, n={res['n']}")

    print("\n=== Bygger visualiseringer ===")
    figs = {
        "tidsserie":   fig_nasjonal_tidsserie(sv_ts, kv_ts),
        "sp_scatter":  fig_opproer_scatter(df, reg),
        "ap_scatter":  fig_ap_scatter(df, reg),
        "sentralitet": fig_opproer_sentralitet(df),
        "topp":        fig_topp_kommuner(df, n=20),
    }

    print("=== Skriver index.html ===")
    html = bygg_html(figs, reg, df, sv_ts, kv_ts)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("  Ferdig → index.html")


if __name__ == "__main__":
    main()
