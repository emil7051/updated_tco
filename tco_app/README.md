# Total Cost of Ownership Model for Electric vs. Diesel Trucks

This Streamlit application provides a comprehensive Total Cost of Ownership (TCO) comparison between battery electric and diesel trucks in the Australian context.

## Features

- Compare battery electric (BEV) and diesel trucks across multiple dimensions
- Customize scenarios, vehicle types, and operating parameters
- Visualize cost breakdowns, emissions comparisons, and payback periods
- Calculate key metrics including TCO per kilometer, emissions savings, and abatement costs
- Apply various incentives and policy mechanisms
- Export detailed results for further analysis

## Directory Structure

```text
 tco_app/
 │
 ├── main.py                 # Entry-point; thin Streamlit router
 ├── app.py                  # Legacy wrapper (deprecated; removed in v2)
 ├── ui/                     # Pure presentation layer (widgets & pages)
 │   ├── pages/              # Individual Streamlit pages
 │   └── components.py       # Shared UI widgets / controls
 │
 ├── domain/                 # Business-logic packages (NEW)
 │   ├── energy.py           # Energy & charging helpers
 │   ├── finance.py          # Monetary / NPV helpers
 │   ├── battery.py          # Degradation & replacement economics
 │   ├── externalities.py    # Emissions & societal cost helpers
 │   └── sensitivity.py      # Scenario & tornado analysis
 │
 ├── src/                    # Legacy monoliths – progressively strangled
 │   ├── calculations.py     # To be retired once fully modularised
 │   ├── utils/              # Reusable low-level maths (authoritative)
 │   └── data_loading.py     # IO & ETL helpers
 │
 ├── plotters/              # Figure builders extracted from monolith
 │   ├── cost_breakdown.py
 │   ├── emissions.py
 │   ├── key_metrics.py
 │   ├── charging_mix.py
 │   ├── sensitivity.py
 │   ├── tornado.py
 │   └── payload.py
 │
 ├── tests/                  # pytest suite with golden regression fixtures
 ├── data/                   # CSV parameter tables & dictionaries
 ├── requirements.txt        # Python dependencies
 └── README.md               # You are here
```

## Setup

```bash
pip install -r requirements.txt

# Preferred: new multi-page interface
streamlit run tco_app/main.py

# Fallback (deprecated)
# streamlit run tco_app/app.py
```

## Data Sources

The application now uses CSV files stored in the `data/tables` directory. These were generated from the original Excel file `tco_tidytables.xlsx` and include:

- Vehicle models and specifications
- Vehicle fees and maintenance costs
- Charging and infrastructure options
- Financial and operational parameters
- Incentives and policies
- Emissions factors and externality costs

The data dictionary with detailed calculation formulas is stored in `data/dictionary`.

## Using the Application

1. Select a scenario from the dropdown in the sidebar
2. Choose a vehicle type and specific BEV model
3. Adjust operating parameters (annual distance, vehicle lifetime)
4. Configure financial parameters as needed
5. Explore the results across the different tabs
6. Export the detailed results for further analysis

## Development

To contribute to this project:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

