# Total Cost of Ownership (TCO) Calculator for Electric vs Diesel Trucks

A comprehensive Streamlit web application for comparing the Total Cost of Ownership between Battery Electric Vehicles (BEV) and diesel trucks in the Australian market. This tool helps fleet operators, policymakers, and researchers make informed decisions about vehicle electrification.

## 🚀 Features

### Core Functionality
- **Vehicle Comparison**: Compare BEV and diesel trucks across multiple vehicle classes (Light Rigid, Medium Rigid, Articulated)
- **Scenario Analysis**: Pre-configured scenarios for different use cases and policy environments
- **Financial Modelling**: Comprehensive TCO calculations including NPV, payback periods, and cost per kilometre
- **Emissions Analysis**: Calculate lifetime emissions and environmental impact
- **Sensitivity Analysis**: Explore how changes in key parameters affect outcomes
- **Incentive Modelling**: Apply various government incentives and subsidies

### Key Metrics Calculated
- Total Cost of Ownership (lifetime and per km)
- Payback period / Price parity year
- Emissions reduction (CO₂-e)
- Abatement cost ($/tonne CO₂-e)
- Social TCO (including externalities)
- Annual operating cost savings

## 📊 Architecture Overview

The application follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                   UI Layer (Streamlit)                   │
├─────────────────────────────────────────────────────────┤
│                  Context Management                      │
├─────────────────────────────────────────────────────────┤
│                 Service/Orchestration                    │
├─────────────────────────────────────────────────────────┤
│                    Domain Logic                          │
├─────────────────────────────────────────────────────────┤
│                   Data Access Layer                      │
├─────────────────────────────────────────────────────────┤
│                   CSV Data Storage                       │
└─────────────────────────────────────────────────────────┘
```

For a detailed architecture diagram, see [documentation/architecture_diagram.md](documentation/architecture_diagram.md).

## 🛠️ Installation

### Prerequisites
- Python 3.13 or higher
- pip package manager
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/updated_tco.git
   cd updated_tco
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run tco_app/main.py
   ```

5. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

## 📁 Project Structure

```
updated_tco/
├── tco_app/                    # Main application directory
│   ├── main.py                 # Streamlit entry point and router
│   ├── ui/                     # User interface components
│   │   ├── pages/              # Application pages (Home, Cost Breakdown, Sensitivity)
│   │   ├── components/         # Reusable UI components
│   │   ├── builders/           # Input builders (vehicle, charging, parameters)
│   │   ├── context/            # Context management and caching
│   │   ├── orchestration/      # Calculation coordination
│   │   └── renderers/          # UI rendering logic
│   ├── domain/                 # Business logic modules
│   │   ├── energy.py           # Energy calculations
│   │   ├── finance.py          # Financial calculations
│   │   ├── externalities.py    # Environmental cost calculations
│   │   └── sensitivity/        # Sensitivity analysis logic
│   ├── services/               # Service layer
│   │   ├── tco_calculation_service.py  # Core TCO calculations
│   │   ├── scenario_service.py         # Scenario management
│   │   └── dtos.py                     # Data transfer objects
│   ├── plotters/               # Visualisation modules
│   ├── data/                   # Data files
│   │   ├── tables/             # CSV data tables
│   │   └── dictionary/         # Data dictionary files
│   ├── src/                    # Core utilities and constants
│   │   ├── constants.py        # Application constants
│   │   ├── config.py           # Configuration settings
│   │   └── utils/              # Utility functions
│   ├── repositories.py         # Data access layer
│   └── tests/                  # Test suite
├── documentation/              # Project documentation
├── reports/                    # Generated reports (gitignored)
├── utility_scripts/            # Development and maintenance scripts
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Test configuration
├── .coveragerc                 # Coverage configuration
└── .pre-commit-config.yaml     # Code quality hooks
```

## 📖 Usage Guide

### Basic Workflow

1. **Select a Scenario**: Choose from pre-configured scenarios or customise parameters
2. **Choose Vehicles**: Select the BEV model and its diesel comparison
3. **Configure Parameters**:
   - Annual distance travelled
   - Vehicle lifetime
   - Financial parameters (discount rate, fuel prices)
   - Charging infrastructure options
   - Fleet size
4. **View Results**:
   - **Home Page**: Summary metrics and key comparisons
   - **Cost Breakdown**: Detailed cost analysis with visualisations
   - **Sensitivity Analysis**: Parameter sensitivity and tornado diagrams

### Key Input Parameters

- **Vehicle Type**: Light Rigid, Medium Rigid, or Articulated
- **Annual Distance**: 10,000 - 200,000 km
- **Vehicle Lifetime**: 1 - 20 years
- **Discount Rate**: 0% - 20%
- **Charging Mix**: Single or mixed time-of-use charging
- **Fleet Size**: Number of vehicles sharing infrastructure

## 🔧 Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tco_app --cov-report=html

# Run specific test categories
pytest tco_app/tests/unit/
pytest tco_app/tests/integration/
pytest tco_app/tests/e2e/
```

### Code Quality
```bash
# Run linting
ruff check .

# Format code
black .

# Run pre-commit hooks
pre-commit run --all-files
```

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Coding Standards
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write comprehensive docstrings
- Maintain test coverage above 80%
- Use British/Australian spelling in documentation

## 📊 Data Sources

The application uses CSV data files located in `tco_app/data/tables/`:

- **Vehicle Data**: Models, specifications, costs
- **Financial Parameters**: Fuel prices, discount rates
- **Charging Infrastructure**: Options and costs
- **Incentives**: Government subsidies and policies
- **Emissions Factors**: CO₂ and pollutant emissions
- **Externalities**: Social and environmental costs

Data dictionary files in `tco_app/data/dictionary/` provide detailed descriptions of all parameters.

## 🐛 Troubleshooting

### Common Issues

1. **ImportError on startup**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility (3.13+)

2. **Data not loading**
   - Verify CSV files are present in `tco_app/data/tables/`
   - Check file permissions

3. **Streamlit connection errors**
   - Ensure port 8501 is not in use
   - Try: `streamlit run tco_app/main.py --server.port 8502`

### Debug Mode
Enable debug logging by setting the environment variable:
```bash
export STREAMLIT_LOG_LEVEL=debug
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](documentation/LICENSE) file for details.

## 🤝 Acknowledgements

- Developed for the Australian trucking industry
- Data sources from various government and industry reports
- Built with Streamlit, Pandas, and Plotly

## 📧 Contact

For questions, bug reports, or feature requests, please open an issue on GitHub or contact the maintainers.

---

**Note**: This application is under active development. Features and calculations may be updated based on user feedback and industry requirements. 