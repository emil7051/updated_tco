# TCO Application Architecture & Data Flow

## Overview
The Total Cost of Ownership (TCO) application is a Streamlit-based web application that compares battery electric vehicles (BEV) and diesel trucks. It follows a layered architecture with clear separation of concerns.

## Architecture Diagram

```mermaid
flowchart TB
    %% User Interface Layer
    subgraph UI["🖥️ UI Layer (Streamlit)"]
        Main[main.py<br/>Router]
        Pages[Pages<br/>- Home<br/>- Cost Breakdown<br/>- Sensitivity]
        Sidebar[Sidebar Renderer<br/>Input Collection]
        Components[UI Components<br/>- Metric Cards<br/>- Summary Displays<br/>- Sensitivity Components]
    end

    %% Context Management
    subgraph Context["🔄 Context Management"]
        GetContext[get_context<br/>Cache Management]
        ContextBuilder[Context Builder<br/>UI Context Assembly]
        InputHash[Input Hash<br/>Change Detection]
    end

    %% Orchestration Layer
    subgraph Orchestration["⚙️ Orchestration"]
        CalcOrch[Calculation Orchestrator<br/>Coordinates Calculations]
    end

    %% Service Layer
    subgraph Services["📊 Service Layer"]
        TCOService[TCO Calculation Service<br/>Core Calculation Logic]
        ScenarioService[Scenario Service<br/>Parameter Application]
        DataCache[Data Cache Service<br/>Performance Optimisation]
    end

    %% Domain Layer
    subgraph Domain["💼 Domain Logic"]
        Finance[Finance Module<br/>- TCO Calculation<br/>- NPV<br/>- Acquisition Cost]
        Energy[Energy Module<br/>- Energy Costs<br/>- Emissions<br/>- Charging]
        Externalities[Externalities<br/>- Social Costs<br/>- Carbon Pricing]
        Sensitivity[Sensitivity Analysis<br/>- Single Parameter<br/>- Tornado<br/>- Metrics]
    end

    %% Data Access Layer
    subgraph DataAccess["💾 Data Access"]
        Repositories[Repositories<br/>- Vehicle Repository<br/>- Parameters Repository]
        DataLoading[Data Loading<br/>CSV Table Loading]
    end

    %% Data Storage
    subgraph Storage["📁 Data Storage"]
        CSVFiles[CSV Files<br/>- Vehicle Models<br/>- Financial Params<br/>- Battery Params<br/>- Charging Options<br/>- Infrastructure<br/>- Incentives]
    end

    %% Visualisation
    subgraph Plotters["📈 Visualisation"]
        Charts[Chart Builders<br/>- Cost Breakdown<br/>- Emissions<br/>- Sensitivity<br/>- Tornado<br/>- Key Metrics]
    end

    %% Data Flow
    User([👤 User]) --> Main
    Main --> Pages
    Pages --> GetContext
    
    User --> Sidebar
    Sidebar --> ContextBuilder
    ContextBuilder --> InputHash
    InputHash --> GetContext
    
    GetContext --> CalcOrch
    CalcOrch --> TCOService
    
    TCOService --> Finance
    TCOService --> Energy
    TCOService --> Externalities
    TCOService --> Sensitivity
    
    CalcOrch --> Repositories
    Repositories --> DataLoading
    DataLoading --> CSVFiles
    
    Sidebar --> ScenarioService
    ScenarioService --> DataCache
    
    Pages --> Components
    Pages --> Charts
    Charts --> Pages
    
    GetContext -.->|Cached Results| Pages

    %% Styling
    classDef ui fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px
    classDef service fill:#E3F2FD,stroke:#2196F3,stroke-width:2px
    classDef domain fill:#FFF3E0,stroke:#FF9800,stroke-width:2px
    classDef data fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px
    classDef viz fill:#FFE0E0,stroke:#F44336,stroke-width:2px
    
    class Main,Pages,Sidebar,Components ui
    class GetContext,ContextBuilder,InputHash,CalcOrch service
    class TCOService,ScenarioService,DataCache service
    class Finance,Energy,Externalities,Sensitivity domain
    class Repositories,DataLoading,CSVFiles data
    class Charts viz
```

## Data Flow Description

### 1. User Input Collection
1. User accesses the application through `main.py` which routes to different pages
2. **Sidebar Renderer** collects all user inputs:
   - Scenario selection
   - Vehicle selection (BEV model and comparison diesel)
   - Operating parameters (annual distance, vehicle lifetime)
   - Financial parameters (discount rate, fuel prices)
   - Charging configuration (single or mixed charging)
   - Infrastructure options
   - Fleet size and incentives

### 2. Context Building
1. **Context Builder** assembles UI context from inputs using builder pattern:
   - ScenarioBuilder
   - VehicleSelectionBuilder
   - ParameterInputBuilder
   - ChargingConfigurationBuilder
   - InfrastructureBuilder

2. **Input Hash** generates a hash of current inputs for cache invalidation

3. **get_context()** checks if inputs have changed:
   - If unchanged, returns cached results
   - If changed, triggers new calculations

### 3. Calculation Orchestration
1. **Calculation Orchestrator** coordinates the calculation flow:
   - Builds calculation requests for both BEV and diesel vehicles
   - Applies UI overrides to parameters
   - Calls TCO Calculation Service

### 4. Core Calculations
The **TCO Calculation Service** performs calculations in sequence:

1. **Energy Costs**:
   - Calculate energy cost per km
   - Calculate emissions (CO₂ per km, annual, lifetime)
   - Handle charging mix for BEVs

2. **Annual Costs**:
   - Energy costs
   - Maintenance costs
   - Registration and insurance
   - Apply operational incentives

3. **Acquisition Costs**:
   - Vehicle purchase price
   - Fees and taxes
   - Apply purchase incentives
   - Calculate residual value

4. **Battery Costs** (BEV only):
   - Battery degradation
   - Replacement costs with NPV

5. **Infrastructure Costs** (BEV only):
   - Charging infrastructure costs
   - Amortised per vehicle in fleet
   - Apply infrastructure incentives

6. **Externalities**:
   - Carbon emissions cost
   - Local air pollution costs
   - Noise pollution costs
   - Social TCO calculation

### 5. Comparison & Results
1. **Compare Vehicles**:
   - Calculate metrics for both BEV and diesel
   - Compute comparative metrics:
     - TCO savings
     - Payback period
     - Emissions reduction
     - Abatement cost

2. **Transform Results** for UI consumption

### 6. Visualisation
Results are displayed through:
- **Home Page**: Summary metrics and key comparisons
- **Cost Breakdown Page**: Detailed cost visualisations
- **Sensitivity Page**: Parameter sensitivity analysis

## Key Design Patterns

### Caching Strategy
- Input-based cache invalidation using hash
- Streamlit's `@st.cache_data` for data loading
- Session state for context caching

### Builder Pattern
- Used for constructing complex UI context
- Allows flexible parameter collection

### Repository Pattern
- Abstracts data access
- Enables future migration to different data sources

### Service Layer
- Encapsulates business logic
- Provides clean API for calculations

### Domain-Driven Design
- Clear separation of business domains
- Each module handles specific calculations

## Data Flow Optimisations

1. **Lazy Loading**: Data only loaded when needed
2. **Caching**: Results cached until inputs change
3. **Vectorised Operations**: Using pandas/numpy for calculations
4. **Modular Calculations**: Only recalculate what's needed

## Error Handling
- Custom exceptions (CalculationError, VehicleNotFoundError)
- Logging at each calculation step
- Graceful degradation for missing data 