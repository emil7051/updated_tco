# Product Requirements Document (PRD)
# Total Cost of Ownership (TCO) Model for Electric vs. Diesel Trucks in Australia

## Overview

This PRD outlines the requirements for developing a web-based Total Cost of Ownership (TCO) model using Streamlit. The application will enable users to compare the costs and benefits of Battery Electric Vehicles (BEV) versus Diesel trucks in the Australian context, with a focus on providing a clean, intuitive interface for exploring different scenarios and vehicle combinations.

## Business Objectives

1. Provide fleet operators, policy makers, and stakeholders with a credible, data-driven tool to evaluate the economic case for transitioning to electric trucks
2. Enable detailed comparison of life-cycle costs between electric and diesel truck alternatives
3. Allow exploration of different scenarios including policy interventions, market changes, and technological improvements
4. Visualise key metrics including upfront costs, operational costs, emissions, and TCO calculations
5. Support evidence-based decision making for commercial fleet transitions

## Target Users

- Fleet managers and operators
- Transport and logistics companies
- Policy makers and government agencies
- Environmental and sustainability analysts
- Academic and research institutions
- Electric vehicle manufacturers and suppliers

## Data Sources

The application will use the following data tables (as defined in the tco_tidytables.csv.xlsx file):

1. `vehicle_models.csv` - Detailed specifications of available trucks (both BEV and diesel)
2. `vehicle_fees.csv` - Associated fees for each vehicle model
3. `charging_options.csv` - Different charging approaches and costs
4. `infrastructure_options.csv` - Infrastructure requirements and costs
5. `operating_params.csv` - Standard operating parameters by vehicle type
6. `financial_params.csv` - Financial assumptions and parameters
7. `battery_params.csv` - Battery-specific parameters
8. `emission_factors.csv` - Emissions data for different fuel types
9. `externalities.csv` - External costs associated with different vehicle types
10. `incentives.csv` - Available incentives and policy mechanisms
11. `scenarios.csv` - Predefined scenarios for analysis
12. `scenario_params.csv` - Parameter values for each scenario

## Technical Requirements

### 1. Data Loading and Processing

- Load all tables from the tco_tidytables.csv.xlsx file
- Implement all calculations defined in the "calculations.csv" sheet of the data dictionary
- Ensure proper handling of scenario parameters and their impact on base calculations
- Process vehicle comparison pairs correctly for side-by-side analysis

### 2. User Interface Structure

The application will consist of:

#### 2.1 Sidebar (Configuration Panel)
- Vehicle selection 
- Scenario selection
- Financial parameters adjustment
- Operating parameters adjustment
- Charging and infrastructure options
- Incentives and policy levers
- Battery parameters adjustment
- Export/save functionality

#### 2.2 Main Frame (Results Display)
- Summary metrics dashboard
- Comparative visualisations
- Detailed cost breakdowns
- Emissions analysis
- Sensitivity analysis (optional)
- Data tables with key metrics

### 3. Core Functionality

#### 3.1 TCO Calculation Engine
The core calculations must implement all formulas specified in the data dictionary, including:

- Energy costs and consumption metrics
- Vehicle acquisition and depreciation costs
- Financing and operational costs
- Battery replacement and degradation modelling
- Emissions calculations
- External cost considerations
- Full TCO and social TCO metrics

#### 3.2 Scenario Management
- Load default scenarios from the scenarios.csv table
- Apply scenario-specific parameter adjustments as defined in scenario_params.csv
- Allow users to create and save custom scenarios
- Display scenario descriptions and assumptions clearly

#### 3.3 Comparison Framework
- Enable side-by-side comparisons of paired vehicles (BEV vs. Diesel) as defined in vehicle_comparison.csv
- Calculate and display key comparative metrics:
  - TCO per kilometre
  - TCO per tonne-kilometre
  - Lifetime TCO
  - Annual operating costs
  - Payback period
  - Upfront cost difference
  - Emission savings
  - Abatement cost ($/tonne CO₂)

#### 3.4 Incentives and Policy Modelling
- Incorporate all incentives listed in incentives.csv
- Allow toggling of incentives to assess impact
- Calculate modified TCO with various incentive combinations
- Show impact of carbon pricing and other policy mechanisms

## User Interface Design Requirements

### 1. Layout and Navigation

The application will follow a clean, professional layout with:

- Fixed sidebar for configuration options
- Main display area for results and visualisations
- Tab-based navigation for different analysis views
- Consistent colour scheme and formatting

### 2. Sidebar Configuration Panel

#### 2.1 Vehicle Selection
- Dropdown menus to select vehicle type (Light Rigid, Medium Rigid, Articulated)
- Selection of specific vehicle pairs for comparison
- Option to filter by payload capacity or other attributes

#### 2.2 Scenario Selection
- Radio buttons or dropdown for selecting predefined scenarios
- Brief description of the selected scenario
- Option to create a custom scenario

#### 2.3 Parameter Controls
- Organised sections for different parameter categories
- Sliders for continuous variables (e.g., discount rate, diesel price)
- Numeric inputs for specific values
- Toggles for binary options (e.g., incentive flags)
- Reset buttons to return to defaults

#### 2.4 Advanced Options
- Collapsible sections for less common parameters
- Battery degradation models
- Infrastructure combinations
- Charging mix configurations

### 3. Main Display Area

#### 3.1 Summary Dashboard
- Key metrics prominently displayed:
  - Total Cost of Ownership (lifetime)
  - TCO per kilometre
  - Payback period
  - Emission savings
  - Annual operating costs
  - Side-by-side comparison of BEV vs. Diesel

#### 3.2 Cost Breakdown View
- Visualisation of cost components:
  - Capital costs (vehicle acquisition)
  - Energy costs
  - Maintenance costs
  - Registration and insurance
  - Battery replacement (if applicable)
  - Infrastructure costs
  - Residual value
- Stacked bar or pie charts for proportion analysis
- Timeline view of costs over vehicle lifetime

#### 3.3 Emissions Analysis
- Comparison of lifetime emissions
- Annual emissions by vehicle
- Emissions savings visualisation
- Abatement cost metrics ($ per tonne CO₂ avoided)

#### 3.4 Detailed Results Table
- Comprehensive table with all calculated metrics
- Sortable and filterable
- Export functionality to CSV

#### 3.5 Sensitivity Analysis (Optional)
- Interactive tornado charts
- Key parameter sensitivity visualisation
- Break-even analysis for critical variables

## Implementation Details

### 1. Data Model

The application will implement the calculation framework as defined in the data dictionary, with particular focus on these key calculations:

#### 1.1 Energy and Operational Costs
```
energy_cost_per_km = IF(vehicle_drivetrain="BEV", 
                        kwh_per100km/100 * [electricity_price], 
                        litres_per100km/100 * [diesel_price])

annual_energy_cost = energy_cost_per_km * [annual_kms]

annual_operating_cost = annual_energy_cost + 
                        maintenance_perkm_price*[annual_kms] + 
                        registration_annual_price + 
                        insurance_annual_price
```

#### 1.2 TCO Calculations
```
npv_annual_cost = SUM(annual_operating_cost / ((1+[discount_rate])^year)) 
                  for year in 1 to [truck_life_years]

npv_total_cost = Acquisition cost + NPV of operating costs - NPV of residual value

tco_per_tonne_km = tco_per_km / payload_t

levelised_cost_of_driving = npv_total_cost / ([annual_kms] * [truck_life_years])
```

#### 1.3 Emissions and Externalities
```
co2_per_km = IF(vehicle_drivetrain="BEV", 
               kwh_per100km/100 * [electricity_emission_factor], 
               litres_per100km/100 * [diesel_emission_factor])

annual_emissions = co2_per_km * [annual_kms]

lifetime_emissions = annual_emissions * [truck_life_years]

emission_savings_lifetime = [diesel:lifetime_emissions] - lifetime_emissions

abatement_cost = (npv_total_cost - [diesel:npv_total_cost]) / 
                (emission_savings_lifetime / 1000)
```

### 2. User Interaction Flow

1. **Initial Load:**
   - Load all data tables
   - Display default scenario (Base Case)
   - Show comparison of default vehicle pair
   - Present key metrics and visualisations

2. **User Configuration:**
   - User selects different vehicles or scenario
   - Application recalculates all metrics based on selection
   - Real-time update of all visualisations and results

3. **Parameter Adjustment:**
   - User modifies individual parameters
   - Calculations update in real-time
   - Visualisations reflect changes immediately
   - Differences from baseline are highlighted

4. **Analysis and Export:**
   - User explores different views and metrics
   - Additional analysis can be performed on specific aspects
   - Results can be exported or saved for later reference

### 3. Technical Implementation

The application will be built using:

- **Streamlit** for the web interface
- **Pandas** for data processing and calculations
- **Plotly** or **Matplotlib** for interactive visualisations
- Python data model implementing all formulas from the data dictionary

### 4. Key Algorithms

The application must correctly implement:

- Present value calculations for future costs
- Correct handling of depreciation and residual values
- Battery degradation models
- Appropriate application of incentives
- Externality cost calculations

## Testing Requirements

The application must be tested for:

1. **Calculation Accuracy:**
   - Validation against standard financial calculators
   - Verification of all formula implementations
   - Edge case testing for extreme parameter values

2. **Usability Testing:**
   - Navigation and interaction flow
   - Clarity of presented information
   - Responsiveness and performance

3. **Data Validation:**
   - Proper handling of missing values
   - Appropriate error messages for invalid inputs
   - Boundary checking for user inputs

## Performance Requirements

The application should:

- Load within 5 seconds
- Respond to user interactions within 1 second
- Handle recalculations for parameter changes in real-time
- Support exporting of results quickly
- Function effectively on standard modern browsers

## Future Expansion Possibilities

The initial implementation should be designed to accommodate future additions:

1. User account system for saving custom scenarios
2. Additional vehicle types and comparison options
3. Integration with external data sources for updated prices
4. Enhanced sensitivity and Monte Carlo analysis
5. Geographic variations in costs and incentives
6. Fleet-level analysis for multiple vehicle transitions

## Delivery Timeline

1. **Phase 1: Core Functionality (2 weeks)**
   - Data loading and processing
   - Basic UI implementation
   - Core calculation engine

2. **Phase 2: Enhanced Visualisations (1 week)**
   - Comprehensive charts and graphs
   - Interactive elements
   - Detailed results tables

3. **Phase 3: Scenario Management (1 week)**
   - Implementation of all predefined scenarios
   - Custom scenario creation
   - Parameter adjustment capabilities

4. **Phase 4: Testing and Refinement (1 week)**
   - Usability testing
   - Calculation verification
   - Performance optimisation

5. **Phase 5: Documentation and Deployment (1 week)**
   - User guide
   - Technical documentation
   - Deployment to production environment

## Appendix

### Key Metrics for Display

#### Primary TCO Metrics
- TCO per kilometre
- TCO per tonne-kilometre
- Lifetime TCO
- Annual operating cost
- Upfront cost difference
- Payback period

#### Emissions Metrics
- Lifetime emissions
- Emission savings lifetime
- Abatement cost ($/tonne CO₂)

#### Financial Metrics
- Net Present Value (NPV) of total costs
- Annual energy costs
- Maintenance costs
- Battery replacement timing and costs
- Residual value

#### Performance Metrics
- Energy consumption per km
- Payload efficiency (tonnes per MJ)

#### Policy Impact Metrics
- Effect of incentives on TCO
- Carbon price impact
- Social TCO (including externalities)
