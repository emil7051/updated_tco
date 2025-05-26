# TCO Application Module

This directory contains the core Total Cost of Ownership (TCO) calculator application for comparing electric and diesel trucks.

## Quick Start

```bash
# From the project root
streamlit run tco_app/main.py
```

For detailed documentation, installation instructions, and usage guide, please see the [main README](../README.md).

## Module Structure

```text
tco_app/
├── main.py                 # Streamlit entry point
├── ui/                     # User interface layer
│   ├── pages/              # Application pages
│   ├── components/         # Reusable UI components
│   ├── builders/           # Input builders
│   ├── context/            # Context management
│   ├── orchestration/      # Calculation coordination
│   └── renderers/          # UI rendering
├── domain/                 # Business logic
│   ├── energy.py           # Energy calculations
│   ├── finance.py          # Financial calculations
│   ├── externalities.py    # Environmental costs
│   └── sensitivity/        # Sensitivity analysis
├── services/               # Service layer
│   ├── tco_calculation_service.py
│   ├── scenario_service.py
│   └── dtos.py
├── plotters/               # Visualisation modules
├── repositories.py         # Data access layer
├── src/                    # Core utilities
│   ├── constants.py        # Application constants
│   ├── config.py           # Configuration
│   └── utils/              # Utility functions
├── data/                   # Data files
│   ├── tables/             # CSV data tables
│   └── dictionary/         # Data definitions
└── tests/                  # Test suite
```

## Key Components

### UI Layer (`ui/`)
- **Pages**: Home dashboard, cost breakdown analysis, sensitivity analysis
- **Context Management**: Handles caching and state management
- **Builders**: Modular input collection using builder pattern

### Domain Layer (`domain/`)
- **Energy**: Energy cost and emissions calculations
- **Finance**: TCO, NPV, and financial metric calculations
- **Externalities**: Social and environmental cost calculations
- **Sensitivity**: Parameter sensitivity and scenario analysis

### Service Layer (`services/`)
- **TCO Calculation Service**: Orchestrates all TCO calculations
- **Scenario Service**: Manages scenario parameters and overrides
- **DTOs**: Data transfer objects for clean interfaces

### Data Layer
- **Repositories**: Abstracts data access with clean APIs
- **CSV Tables**: All parameter data in standardised format

## Testing

```bash
# Run unit tests
pytest tco_app/tests/unit/

# Run integration tests
pytest tco_app/tests/integration/

# Run all tests with coverage
pytest --cov=tco_app
```

## Development Notes

- Follow the existing module patterns when adding new features
- Maintain separation between UI, domain, and data layers
- Use type hints and comprehensive docstrings
- Write tests for new functionality

See the [architecture documentation](../documentation/architecture_diagram.md) for detailed data flow and design patterns.

