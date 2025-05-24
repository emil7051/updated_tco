# Watershed TCO - Electric vs. Diesel Truck Comparison Tool

A comprehensive Total Cost of Ownership (TCO) modeling application to compare Battery Electric Vehicles (BEV) with traditional diesel trucks in the Australian context.

## Overview

This Streamlit application provides a detailed economic analysis of electric trucks versus diesel equivalents, helping fleet operators and decision-makers understand the financial implications of transitioning to electric vehicles.

## Key Features

- **Comprehensive TCO Analysis**: Compare upfront costs, operational expenses, and long-term economics
- **Customizable Parameters**: Adjust vehicle types, usage patterns, discount rates, and more
- **Infrastructure Modeling**: Analyze charging infrastructure requirements and costs
- **Emission Calculations**: Quantify CO₂ emission reductions and abatement costs
- **Scenario Analysis**: Pre-defined scenarios for different economic assumptions
- **Visual Comparisons**: Interactive charts and visualizations for easy interpretation

## Getting Started

### Prerequisites

- Python 3.7+
- Streamlit
- Pandas
- Plotly
- NumPy

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/watershed-tco.git
cd watershed-tco
```

2. Install the required dependencies:
```bash
pip install -r tco_app/requirements.txt
```

3. Run the application:
```bash
streamlit run tco_app/app.py
```

## Usage

1. Select a scenario from the dropdown menu
2. Choose the vehicle type and BEV model
3. Adjust operating parameters (annual distance, vehicle lifetime)
4. Customize financial parameters (discount rate, fuel costs)
5. Configure charging and infrastructure options
6. Review the TCO comparison results and visualizations

## Application Structure

- `tco_app/app.py`: Main Streamlit application
- `tco_app/src/`: Component modules for calculations and visualizations
- `tco_app/data/tables/`: CSV data files with vehicle and cost information
- `tco_app/assets/`: CSS and visual assets

## Naming Map
A mapping of legacy identifiers to updated names is maintained in `documentation/naming_map.csv`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Data Engineering Team - Development and modeling
- Australian Clean Energy Finance Corporation - Reference data 
