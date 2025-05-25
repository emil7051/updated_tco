# Sensitivity Page Render Function Refactoring Plan

## Current Issues

The `render()` function in `ui/pages/sensitivity.py` has a cyclomatic complexity of 23 (D rating), making it difficult to understand, test, and maintain. The function is 200+ lines long and handles multiple responsibilities.

## Problems Identified

1. **Too many responsibilities:**
   - Context extraction (22 variables)
   - Parameter selection UI
   - Range calculation for 6 different parameters
   - Chart creation
   - Result display

2. **Deeply nested conditionals:**
   - Main if/else for payload vs other parameters
   - Nested if/elif blocks for each parameter type
   - Error handling mixed with business logic

3. **Code duplication:**
   - Similar range calculation patterns repeated
   - Parameter extraction patterns duplicated

4. **Poor separation of concerns:**
   - UI logic mixed with business calculations
   - Validation logic embedded in rendering

## Refactoring Strategy

### Step 1: Extract Context Management

```python
@dataclass
class SensitivityContext:
    """Encapsulates all context data for sensitivity analysis."""
    bev_results: dict
    diesel_results: dict
    bev_vehicle_data: pd.DataFrame
    diesel_vehicle_data: pd.DataFrame
    bev_fees: pd.DataFrame
    diesel_fees: pd.DataFrame
    charging_options: pd.DataFrame
    infrastructure_options: pd.DataFrame
    financial_params_with_ui: pd.DataFrame
    battery_params_with_ui: pd.DataFrame
    emission_factors: pd.DataFrame
    incentives: pd.DataFrame
    selected_charging: int
    selected_infrastructure: int
    annual_kms: float
    truck_life_years: int
    discount_rate: float
    fleet_size: int
    charging_mix: dict
    apply_incentives: bool
    
    @classmethod
    def from_context(cls, ctx: dict) -> 'SensitivityContext':
        """Create from context dictionary."""
        return cls(**{k: ctx[k] for k in cls.__dataclass_fields__})
```

### Step 2: Extract Parameter Range Calculators

```python
class ParameterRangeCalculator:
    """Calculates parameter ranges for sensitivity analysis."""
    
    def __init__(self, num_points: int = 11):
        self.num_points = num_points
    
    def calculate_annual_distance_range(self, base_value: float) -> List[float]:
        """Calculate range for annual distance parameter."""
        min_val = max(1000, base_value * 0.5)
        max_val = base_value * 1.5
        return self._create_range(min_val, max_val, base_value, round_digits=0)
    
    def calculate_diesel_price_range(self, financial_params: pd.DataFrame) -> List[float]:
        """Calculate range for diesel price parameter."""
        base_value = self._get_financial_param(
            financial_params, 
            ParameterKeys.DIESEL_PRICE
        )
        min_val = max(0.5, base_value * 0.7)
        max_val = base_value * 1.3
        return self._create_range(min_val, max_val, base_value, round_digits=2)
    
    def calculate_electricity_price_range(
        self, 
        bev_results: dict, 
        charging_options: pd.DataFrame,
        selected_charging: int
    ) -> List[float]:
        """Calculate range for electricity price parameter."""
        base_value = self._get_electricity_base_price(
            bev_results, 
            charging_options, 
            selected_charging
        )
        min_val = max(0.05, base_value * 0.7)
        max_val = base_value * 1.3
        return self._create_range(min_val, max_val, base_value, round_digits=2)
    
    def _create_range(
        self, 
        min_val: float, 
        max_val: float, 
        base_value: float, 
        round_digits: int
    ) -> List[float]:
        """Create parameter range with base value included."""
        step = (max_val - min_val) / (self.num_points - 1)
        param_range = [
            round(min_val + i * step, round_digits) 
            for i in range(self.num_points)
        ]
        if base_value not in param_range:
            param_range.append(round(base_value, round_digits))
            param_range.sort()
        return param_range
```

### Step 3: Extract Sensitivity Analyzers

```python
class SensitivityAnalyzer:
    """Handles sensitivity analysis for different parameters."""
    
    def __init__(self, context: SensitivityContext, range_calculator: ParameterRangeCalculator):
        self.context = context
        self.range_calculator = range_calculator
    
    def analyze_payload_effect(self) -> go.Figure:
        """Analyze sensitivity with payload effect."""
        distances = self.range_calculator.calculate_annual_distance_range(
            self.context.annual_kms
        )
        return create_payload_sensitivity_chart(
            self.context.bev_results,
            self.context.diesel_results,
            self.context.financial_params_with_ui,
            distances,
        )
    
    def analyze_parameter(self, param_type: str) -> Tuple[List[float], go.Figure]:
        """Analyze sensitivity for a specific parameter."""
        range_methods = {
            "Annual Distance (km)": self._get_distance_range,
            "Diesel Price ($/L)": self._get_diesel_range,
            "Electricity Price ($/kWh)": self._get_electricity_range,
            "Vehicle Lifetime (years)": self._get_lifetime_range,
            "Discount Rate (%)": self._get_discount_range,
        }
        
        if param_type not in range_methods:
            raise ValueError(f"Unknown parameter type: {param_type}")
        
        param_range = range_methods[param_type]()
        chart = self._create_sensitivity_chart(param_type, param_range)
        
        return param_range, chart
```

### Step 4: Refactored Main Function

```python
def render():
    """Render sensitivity analysis page."""
    # Step 1: Load and validate context
    context = SensitivityContext.from_context(get_context())
    
    # Step 2: Display header and info
    _display_header()
    
    # Step 3: Get parameter selection
    sensitivity_param = _get_parameter_selection()
    
    # Step 4: Initialize components
    range_calculator = ParameterRangeCalculator(num_points=11)
    analyzer = SensitivityAnalyzer(context, range_calculator)
    
    # Step 5: Perform analysis based on selection
    if sensitivity_param == "Annual Distance (km) with Payload Effect":
        _display_payload_sensitivity(analyzer)
    else:
        _display_parameter_sensitivity(analyzer, sensitivity_param, context)


def _display_header():
    """Display page header and information."""
    st.subheader("Sensitivity Analysis")
    st.info(
        "Sensitivity Analysis helps understand how changes in key parameters "
        "affect the TCO comparison."
    )


def _get_parameter_selection() -> str:
    """Get user's parameter selection."""
    return st.selectbox(
        "Select Parameter for Sensitivity Analysis",
        [
            "Annual Distance (km)",
            "Diesel Price ($/L)",
            "Electricity Price ($/kWh)",
            "Vehicle Lifetime (years)",
            "Discount Rate (%)",
            "Annual Distance (km) with Payload Effect",
        ],
    )


def _display_payload_sensitivity(analyzer: SensitivityAnalyzer):
    """Display payload sensitivity analysis."""
    chart = analyzer.analyze_payload_effect()
    st.plotly_chart(
        chart,
        use_container_width=True,
        key="payload_sensitivity_chart",
    )
    st.markdown(
        "Values below 1.0 indicate BEV is more cost-effective. "
        "The gap between the lines shows the economic impact of "
        "payload limitations at higher utilisation."
    )


def _display_parameter_sensitivity(
    analyzer: SensitivityAnalyzer, 
    param_type: str, 
    context: SensitivityContext
):
    """Display standard parameter sensitivity analysis."""
    param_range, chart = analyzer.analyze_parameter(param_type)
    
    # Display chart
    st.plotly_chart(
        chart,
        use_container_width=True,
        key=f"{param_type.lower().replace(' ', '_')}_sensitivity",
    )
    
    # Display interpretation
    _display_sensitivity_interpretation(param_type, param_range, context)
```

## Benefits of Refactoring

1. **Reduced Complexity:**
   - Main function reduced from 200+ lines to ~30 lines
   - Cyclomatic complexity reduced from 23 to ~5

2. **Improved Testability:**
   - Each component can be unit tested independently
   - Mock dependencies easily

3. **Better Maintainability:**
   - Clear separation of concerns
   - Single responsibility for each class/function
   - Easy to add new parameter types

4. **Enhanced Readability:**
   - Self-documenting code structure
   - Clear flow of execution
   - Reduced nesting levels

## Implementation Plan

1. **Phase 1: Extract Classes (1 day)**
   - Create `SensitivityContext` dataclass
   - Create `ParameterRangeCalculator` class
   - Create `SensitivityAnalyzer` class

2. **Phase 2: Refactor Main Function (1 day)**
   - Break down `render()` into smaller functions
   - Implement new structure
   - Ensure backward compatibility

3. **Phase 3: Testing (1 day)**
   - Write unit tests for each new class
   - Test edge cases for parameter calculations
   - Integration testing with UI

4. **Phase 4: Documentation (0.5 day)**
   - Add comprehensive docstrings
   - Create usage examples
   - Update any related documentation

## Success Metrics

- Cyclomatic complexity reduced to B rating or better (≤10)
- Function length reduced to <50 lines
- Test coverage increased for sensitivity module
- No regression in functionality
