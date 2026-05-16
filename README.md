# Data Storm 7.0 - Storming Round: Latent Potential Estimator

This repository contains the end-to-end data pipeline and modeling solution for estimating the Maximum Monthly Purchase Potential of traditional FMCG retail outlets. The project adheres to a Lakehouse architecture (Bronze, Silver, Gold) and incorporates external geospatial data via the OpenStreetMap Overpass API.

- Team Nybble: M.M.H.M.Valantina, K.H.G.Akinda Udaneth

## Repository Structure

```text
data_storm_7/
├── data/
│   ├── bronze/                   # Raw, unmodified data from source
│   │   ├── external/             # Scraped POI data (schools, hospitals, transit)
│   │   ├── transactions_history_final.csv
│   │   ├── outlet_master.csv
│   │   ├── outlet_coordinates.csv
│   │   ├── distributor_seasonality_details.csv
│   │   └── holiday_list.csv
│   ├── silver/                   # Cleaned data with implemented DE checks
│   │   ├── rejected/             # Quarantined records with failure reasons
│   │   ├── cleaned_outlet_master.csv
│   │   └── base_potential.csv
│   └── gold/                     # Model-ready data and engineered features
├── scripts/
│   ├── poi_scraper.py            # External POI extraction with exponential backoff
│   ├── data_quality_checks.py    # Reusable DE forensics (Null, Duplicates, Range, Types)
│   ├── latent_potential_model.py # Calculates historical max peaks
│   └── gold_layer_pipeline.py    # Applies POI scaling logic and uncaps potential
├── submission/
│   └── teamname_predictions.csv  # Final output
└── README.md
```

Prerequisites
-------------

Ensure you have Python 3.9+ installed along with the required libraries:

Bash

    pip install pandas requests

End-to-End Execution Pipeline
-----------------------------

To run the pipeline and reproduce the final predictions, execute the scripts in the following order from the root directory.

### 1. External Data Extraction (Bronze Layer Supplement)

Extract external Point of Interest (POI) data to calculate catchment drivers. This script features exponential backoff, rate-limiting (`time.sleep`), and automatic backups every 100 rows to prevent API timeouts.

Bash

    python3 scripts/poi_scraper.py

*Output: `data/bronze/external/scraped_pois.csv`*

### 2. Data Forensics & Quality Checks (Silver Layer)

Run the automated Data Engineering forensics pipeline. This cleans the raw datasets by filtering out nulls, duplicates, and out-of-range values (e.g., negative cooler counts). Rejected records are not deleted; they are quarantined with an audit timestamp and failure reason.

Bash

    python3 scripts/data_quality_checks.py

*Output: `data/silver/cleaned_outlet_master.csv` and `data/silver/rejected/`*

### 3. Base Latent Potential Calculation

Calculate the baseline uncapped demand. This script identifies the absolute historical maximum sales month for each outlet to solve the left-censored demand curve problem.

Bash

    python3 scripts/latent_potential_model.py

*Output: `data/silver/base_potential.csv`*

### 4. Final Aggregation & Scaling (Gold Layer)

Merge the cleaned Silver data with the external POI data. This script applies the mathematical scaling factor (based on proximity to schools, hospitals, and transit hubs) to the base potential, outputting the final uncapped volume predictions.

Bash

    python3 scripts/gold_layer_pipeline.py

*Output: `submission/teamname_predictions.csv`*

GenAI Transparency
------------------

Generative AI tools (Gemini) were utilized strictly as accelerators during this sprint. They assisted with generating boilerplate Pandas operations and debugging API timeout schemas (implementing the `User-Agent` and exponential backoff). All logic, including the Lakehouse architecture setup, causal scaling mathematics, and data quarantine validation, was human-directed and tested.
