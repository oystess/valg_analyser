# CLAUDE.md — valg_analyser

## Project Overview

**valg_analyser** is a Norwegian electoral analysis project that tests whether Labour Party (Ap) voters shifted to the Centre Party (Sp) in municipalities experiencing population decline. The primary output is an interactive HTML report (`index.html`) deployed to GitHub Pages.

**Research hypothesis:** Ap lost voters to Sp in 2013→2017 in municipalities with low population growth.
**Result:** Confirmed (p < 0.0001).

---

## Repository Structure

```
valg_analyser/
├── analyse.py                  # Main analysis script — single entry point
├── index.html                  # Generated output (do not edit manually)
│
├── Data files
│   ├── data_valg_1317.csv      # Election data 2013 & 2017 (primary dataset)
│   ├── data_valg_2125.csv      # Election data 2021 & 2025
│   ├── valg2013_parti.csv      # Detailed 2013 party results by municipality
│   ├── valg2017_parti.csv      # Detailed 2017 party results by municipality
│   ├── valg2009_parti.csv      # 2009 party data
│   ├── valg2013.csv / valg2017.csv  # Summary election files
│   ├── distriktstall.xlsx      # Population & centrality data (SSB)
│   ├── sentralitet.csv         # SSB centrality index (429 rows, 4 groups)
│   ├── polls.csv               # Current polling data (auto-updated weekly)
│   └── polls.rds               # R binary format polls data
│
├── R scripts (exploratory/supplementary)
│   ├── Alle meningsmålinger.R  # Fetches polling data from pollofpolls.no
│   ├── Valgresultat.R          # Election results exploration
│   ├── Videre analyser.R       # Coalition/mandate analysis
│   ├── befolkningstall.R       # Fetches population data from SSB API
│   └── valganalyser v01.R      # Early prototype
│
└── .github/workflows/
    ├── update-polls.yml        # Weekly Monday poll data sync (auto-commits)
    ├── deploy.yml              # Deploy index.html to GitHub Pages on push to master
    └── jekyll-gh-pages.yml     # Jekyll build pipeline (fallback)
```

---

## Tech Stack

### Python (primary analysis)
- **pandas** — data loading, pivoting, merging, delta calculations
- **statsmodels** — OLS regression (bivariate and multivariate)
- **plotly** — interactive scatter plots and time series charts

### Frontend (generated HTML)
- **Tailwind CSS** (CDN) — utility-first styling
- **Plotly.js 3.4.0** (CDN) — client-side chart rendering
- **Google Fonts** — Inter typeface

### R (exploratory / data fetching)
- **tidyverse / dplyr** — data manipulation
- **readxl** — Excel file reading
- **rjstat / httr** — SSB JSON-stat API access

### CI/CD
- **GitHub Actions** — automated deploys and weekly data refresh
- **GitHub Pages** — static site hosting

---

## Running the Analysis

```bash
python3 analyse.py
```

This produces `index.html` in the working directory. No arguments needed.

**No test suite exists.** Validation is done by inspecting console output (regression stats, sample sizes) and the generated HTML.

---

## analyse.py Architecture

The script is organized into clearly delineated sections (marked with `# ──` decorators):

| Section | Key Functions | Responsibility |
|---------|--------------|----------------|
| `KONSTANTER` | — | Party codes, colors, centrality names |
| `DATAHENTING` | `hent_valgdata_1317()`, `hent_valgdata_2125()`, `hent_befolkning()`, `last_sentralitet()` | Read CSV/Excel files |
| `PROSESSERING` | `prosesser_valg()`, `lag_bred_valgtabell()`, `prosesser_befolkning()` | Normalize to long format, pivot to wide |
| `ANALYSE` | `bygg_analysedata()`, `kjor_regresjoner()` | Merge datasets, compute deltas, run OLS |
| `PLOTLY VISUALISERING` | `scatter_med_reg()`, `lag_tidsserie_nasjonal()`, `lag_korrscatter()` | Build Plotly figures |
| `HTML-RAPPORT` | `bygg_html()` | Assemble full HTML with embedded charts |
| `HOVEDPROGRAM` | `main()` | Orchestrate all steps |

### Data flow

```
CSV/Excel files
    → hent_* functions (load raw data)
    → prosesser_valg() (long format: komm_nr, komm_navn, ar, parti, pst)
    → lag_bred_valgtabell() (wide: one column per party per year)
    → bygg_analysedata() (merge with population & centrality; compute Δ columns)
    → kjor_regresjoner() (OLS: ΔAp ~ vekst_10yr, ΔSp ~ vekst_10yr, with controls)
    → Plotly figures
    → index.html
```

---

## Code Conventions

### Naming
- **Norwegian names** throughout: variables, function names, comments, and commit messages are in Norwegian
- Functions: `snake_case` with Norwegian words (`hent_valgdata`, `prosesser_befolkning`, `lag_tidsserie_nasjonal`)
- Constants: `UPPER_SNAKE_CASE` dicts (`PARTIER`, `PARTI_FARGER`, `SENTRALITET_NAVN`)
- Delta columns: `delta_Ap`, `delta_Sp` (change in percentage points)

### Python style
- Type hints on function signatures (`→ pd.DataFrame`, `→ go.Figure`)
- Docstrings (triple-quoted) on all public functions
- `warnings.filterwarnings("ignore")` and `errors="coerce"` for tolerant parsing
- F-strings for all string construction including HTML templating

### Data conventions
- Municipality codes: 4-digit strings, e.g. `"0101"` = Halden
- Year stored as string: `"2013"`, `"2017"`
- Party codes: `"01"` = Ap, `"02"` = FrP, etc.
- Centrality: `"0"` = least central → `"3"` = most central (SSB scale)
- Population growth (`befvekst10`): raw fraction from SSB — multiply by 100 for percentage points

### Party colors
```python
PARTI_FARGER = {
    "Ap": "#e4202c",    # red
    "Sp": "#009900",    # green
    "Høyre": "#0065f1", # blue
    ...
}
```

### Statistical conventions
- OLS via `statsmodels.formula.api.ols`
- Significance: `***` p<0.001, `**` p<0.01, `*` p<0.05
- 95% confidence intervals (`alpha=0.05`)
- Reported as: β (coefficient), R², p-value, N

---

## Data Sources

| Source | Data | Access |
|--------|------|--------|
| SSB Table 08092 | Stortingsvalg (Parliamentary elections) 2009–2025 | CSV download |
| SSB Table 104857 | Population data | API (R script) |
| SSB Distriktsindikatorene | Population growth + centrality index | Excel download |
| pollofpolls.no | Weekly polling aggregates | API (GitHub Actions + R) |

---

## GitHub Actions Workflows

### `update-polls.yml`
- **Trigger:** Every Monday at 06:00 UTC, or manual dispatch
- **Action:** Downloads fresh `polls.csv` from pollofpolls.no; auto-commits if changed
- **Branch:** `master`

### `deploy.yml`
- **Trigger:** Push to `master`
- **Action:** Deploys the entire repo (including `index.html`) to GitHub Pages

> **Note:** `jekyll-gh-pages.yml` is a fallback Jekyll pipeline; it may conflict with `deploy.yml` if both are active.

---

## Development Workflow

1. **Branch:** Feature branches are prefixed `claude/` for AI-assisted work. Merge to `master` via pull requests.
2. **Run analysis:** `python3 analyse.py` — inspect console output and open `index.html` in a browser.
3. **Data updates:** `polls.csv` is auto-updated weekly by CI. Other data files are manually updated from SSB.
4. **Deploy:** Pushing to `master` triggers automatic GitHub Pages deployment.

### Branch conventions
```
master                          # Production branch, auto-deployed
claude/<short-description>-<id> # AI-assisted feature branches
```

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `analyse.py` | The entire Python analysis — modify this for any logic changes |
| `index.html` | Generated output — never edit manually, always regenerate via `analyse.py` |
| `data_valg_1317.csv` | Core dataset for the primary hypothesis test |
| `distriktstall.xlsx` | Population growth data — essential for regression variables |
| `sentralitet.csv` | Centrality index — used as control variable in multivariate models |
| `polls.csv` | Current polling snapshot — auto-updated, used in time series chart |
| `.github/workflows/deploy.yml` | Deployment config — edit carefully |

---

## What Not to Do

- **Do not edit `index.html` directly** — it is generated output and will be overwritten on the next `python3 analyse.py` run.
- **Do not rename data files** without updating the corresponding `hent_*` function in `analyse.py`.
- **Do not push to `master` directly** for feature work — use feature branches and PRs.
- **Do not add English** to Norwegian-language variable names, comments, or commit messages — maintain language consistency.
