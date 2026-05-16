# Data Storm 7.0 - Storming Round: Latent Potential Estimator

This repository contains the end-to-end data pipeline and modeling solution for estimating the Maximum Monthly Purchase Potential of traditional FMCG retail outlets. The project adheres to a Lakehouse architecture (Bronze, Silver, Gold) and incorporates external geospatial data via the OpenStreetMap Overpass API.

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
