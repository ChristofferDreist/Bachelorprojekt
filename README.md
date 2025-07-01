# Bachelorprojekt

## Overview

This codebase models passenger route-choice behavior in Copenhagen’s public transit network using GTFS data and Rejsekort smart-card data. It includes:
- **Feature Engineering**: build per-route features (travel time, transfers, walking, service frequency, mode flags)
- **Baseline Heuristics**: simple rules (fastest-only, fastest-then-fewest-transfers, fewest-transfers-only, fewest-transfers-then-fastest)
- **Random Forest Models**: pilot OD pairs vs. full network; 5-fold OD-grouped cross-validation; feature importance analysis
- **TabNet Neural Network**: attention-based deep model; 5-fold OD CV; calibration & reliability diagrams
- **What-If Scenarios**: simulate closing M3/M4 lines; compare predicted route shares and travel-time impacts

## Data Requirements

> **Note:** Private choice-set data is *not* included in this repository.  
You must supply:
- `choice_set_Final*.csv`: all feasible route alternatives per trip  
- `chosen_trips_Rejsekort.csv`: actual chosen route per trip  
- GTFS feed files: `stops.txt`, `trips.txt`, `stop_times.txt`, etc.  

Place these files in the same folder as the notebooks or adjust the file paths at the top of each notebook before running.

## Get Software


To get started, you must first download the folder to your computer.

## Create a Virtual Environment

1. Create a new Conda environment by running:

    ```bash
    conda create --name bachelorprojekt python=3.11  # Name and version is up to you.
    ```

2. Select your environment in VS Code. To do this, open the command palette using `ctrl+Shift+P`, type `Python: Select Interpreter`, and select your environment (`bachelorprojekt`) from the list. If it does not appear, select **Enter interpreter path** and navigate to it.

3. Navigate to the `bachelorprojekt` folder and run:

    ```bash
    conda install -c conda-forge --file requirements_conda.txt
    pip install -r requirements_pip.txt
    ```
```sh
conda deactivate
```

4. Clone or download this repository:  
   ```bash
   git clone <repository_url>
   cd Bachelorprojekt


## Running the Notebooks

Follow this sequence so that each step’s outputs are available for the next:

1. **Feature Engineering**  
   - `3_CHDR_FeatureEngineering.ipynb` → generates `features_final.parquet`  
   - `4_CHDR_FeatureEngineering2.ipynb` → generates `features_full.parquet`  

2. **Baseline Heuristics**  
   - `2_CHDR_Baseline.ipynb` → evaluates heuristics 

3. **Pilot Study**  
   - `1_CHDR_PilotStudy.ipynb` → analyzes Cityringen (M3) usage for 12 OD pairs  

4. **Random Forest Models**  
   - `5_CHDR_RandomForest_ObsID.ipynb` → trains RF on pilot/full sets; saves `rf_pilot.joblib` & `rf_full.joblib`  
   - `6_CHDR_RandomForest_Cross_OD.ipynb` → 5-fold OD-grouped CV; plots feature importances  

5. **TabNet Neural Network**  
   - `7_CHDR_TabNet_Cross_OD.ipynb` → TabNet 5-fold OD CV; calibration & performance metrics  

6. **What-If Analysis**  
   - `8_CHDR_WhatIf.ipynb` → simulates “No M3/M4” scenario (requires trained TabNet model + imputer)  

7. **Shortest-path**
    - `graph_builder.py`,`graph_to_html.py` and `shortest_path.py` can be run independently and can create shortest path between any OD and makes interactive map of GTFS