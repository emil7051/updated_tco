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

```
tco_app/
│
├── app.py                  # Main Streamlit application entry point
├── requirements.txt        # Project dependencies
├── README.md               # Project documentation
│
├── data/                   # Data directory
│   ├── tables/             # CSV data tables for the model
│   │   ├── vehicle_models.csv
│   │   ├── vehicle_fees.csv
│   │   └── ...
│   │
│   ├── dictionary/         # Data dictionary and documentation
│   │   ├── calculations.csv
│   │   ├── parameter_library.csv
│   │   └── ...
│
├── src/                    # Source code modules
│   ├── __init__.py
│   ├── calculations.py     # Calculation functions
│   ├── data_loading.py     # Data loading functions
│   ├── visualization.py    # Visualization functions
│   └── ui_components.py    # UI component functions
│
└── assets/                 # Static assets
    └── styles.css          # CSS styles for the application
```

## Setup Instructions

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Run the Streamlit application:

```bash
streamlit run app.py
```

4. Access the application in your web browser at http://localhost:8501

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

