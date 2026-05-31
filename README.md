# Data Storm 7.0 - Team Nybble: Enterprise Latent Potential Estimator

This repository contains the end-to-end data pipeline, predictive modeling solution, and enterprise web application for estimating the Maximum Monthly Purchase Potential of traditional FMCG retail outlets. 

This project was developed across two phases: the **Storming Round** (establishing a Lakehouse architecture and unconstrained baseline) and the **Final Prototype Phase** (implementing spatial distance-decay math, Linear Programming budget optimization, and a full-stack XAI dashboard).

**Team Nybble:** M.M.H.M.Valantina, K.H.G.Akinda Udaneth

## Repository Structure

```text
data_storm_7/
├── backend/                      # FastAPI Server & GenAI Integration
│   └── main.py                   # REST endpoints and Gemini zero-shot prompt logic
├── frontend/                     # React Enterprise Dashboard (Dark Mode / Neon Theme)
│   ├── src/
│   │   ├── App.js                # Core UI, XAI interactions, and Dataset Directory
│       └── App.css               # Styling, animations, and glassmorphic UI
│   └── package.json
├── data/
│   ├── bronze/                   # Raw, unmodified data from source (Git-Ignored)
│   │   ├── external/             # Scraped POI data (Haversine distance arrays)
│   │   └── ...raw_csv_files
│   ├── silver/                   # Cleaned data with implemented DE checks
│   │   ├── rejected/             # Quarantined records with failure reasons
│   │   ├── cleaned_outlet_master.csv
│   │   └── cleaned_spatial_data.csv
│   └── gold/                     # Model-ready data and final output deliverables
│       ├── nybble_predictions.csv
│       ├── nybble_budget_allocations.csv
│       └── dashboard_data.csv    # Fat-table export for the React UI features
├── scripts/
│   ├── poi_scraper.py            # Overpass API extraction with exact geometric distances
│   ├── data_quality_checks.py    # Reusable DE forensics and array-parsing safeguards
│   ├── latent_potential_model.py # Calculates historical max peaks
│   └── run_final_round_pipeline.py # Applies Gaussian decay, saturation, and PuLP LP optimization
└── README.md
```

Prerequisites
-------------

Ensure you have Python 3.9+ and Node.js installed.

Python Dependencies:
Bash

    pip install pandas requests fastapi uvicorn google-genai pulp

Node Dependencies (Frontend):
```Bash
cd frontend
npm install recharts
``` 

End-to-End Execution Pipeline
-----------------------------

To reproduce the final predictions, budget allocations, and launch the UI, execute the following steps from the root directory.

### 1. Advanced Spatial Extraction (Bronze Layer Supplement)

Extracts competing outlets and external POIs using the Overpass API. Calculates exact Haversine distances in meters and formats them as mathematical arrays. Features exponential backoff and localized backup caching.

Bash

    python3 scripts/poi_scraper.py

*Output: `data/bronze/external/scraped_spatial_arrays_final.csv` and `data/bronze/external/scraped_spatial_arrays_backup.csv`*

### 2. Data Forensics & Quality Checks (Silver Layer)

Runs the automated Data Engineering pipeline. Cleans raw datasets, validates ID prefixes, and safely parses stringified JSON arrays into native Python lists (ast.literal_eval). Malformed API responses are strictly quarantined.

Bash

    python3 scripts/data_quality_checks.py

*Output: `data/silver/cleaned_outlet_master.csv`, `data/silver/cleaned_spatial_data.csv` and `data/silver/rejected/`*

### 3. Causal Math & Budget Optimization (Gold Layer)

Executes the Phase 2 mathematics. Applies Gaussian distance-decay to spatial proximity arrays, calculates competitive market saturation, and runs a Linear Programming (Simplex) model via PuLP to optimally distribute a 5M LKR budget across the Western Province.

Bash

    python3 scripts/run_final_round_pipeline.py

*Output: `data/gold/nybble_predictions.csv` and `data/gold/nybble_budget_allocations.csv`*

### 4. Launching the Enterprise XAI Dashboard

The web application features a full dataset directory with Distributor/Province filtering, comparative visualization charts, and a dynamic LLM Strategic Advisor. It requires both the Python backend and React frontend to run concurrently.

Terminal 1(Backend):
```Bash
cd backend
python3 main.py
```

Terminal 2(Frontend):
```Bash
cd frontend
npm start
```

Access the dashboard at http://localhost:3000 to view interactive predictions, localized catchment data, and dynamic AI strategic insights

GenAI Transparency Log
----------------------

Generative AI tools (Gemini) were utilized strictly as developmental accelerators and natively integrated into the final application architecture.

- Phase 1 (Data Engineering): AI assisted in generating boilerplate Pandas operations and debugging API timeout schemas (implementing the User-Agent and exponential backoff algorithms).

- Phase 2 (Spatial Architecture): Prompted the LLM to write a Haversine geometric calculation to map exact distances in meters between coordinates. Validated that the Overpass QL query successfully parsed returned arrays into the dataframe without triggering format corruption.

- Phase 2 (Silver Layer Safegaurds): Engineered an ingestion function utilizing ast.literal_eval with custom exception handling. If the API returns malformed JSON arrays, the function safely routes the corrupted row to the rejected store rather than fatally crashing the pipeline.

- Phase 2 (UI/UX Architecture): Utilized AI to rapidly scaffold the React JSX and CSS grid layouts for the Outlet Intelligence dashboard. Manually wired state management hooks to handle asynchronous UI loading states. Migrated the backend from Spring Boot to FastAPI to ensure seamless native integration with the Python data science pipelines.

- Phase 2 (Explainable AI - XAI): Engineered a zero-shot prompt template within the FastAPI backend that dynamically injects calculated feature weights (Market Saturation, Historical Max). Applied strict constraints (3-sentence limit, non-technical business language) to prevent hallucinations and translate complex mathematical proximity logic into direct FMCG sales strategy.
