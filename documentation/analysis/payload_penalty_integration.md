# Payload Penalty Integration into TCO Calculations

## Overview
This document describes the implementation of payload penalty calculations into the Total Cost of Ownership (TCO) analysis. Payload penalties account for the economic impact when Battery Electric Vehicles (BEVs) have lower payload capacity compared to their diesel counterparts.

## Implementation Details

### 1. Calculation Service Changes
- Modified `TCOCalculationService.compare_vehicles()` to calculate payload penalties during vehicle comparison
- Payload penalties are only calculated when comparing BEV vs Diesel vehicles
- The penalty calculation uses the existing `calculate_payload_penalty_costs` function from `domain.finance_payload`

### 2. Data Transfer Objects (DTOs)
- Added `payload_penalties: Optional[Dict[str, Any]]` field to `ComparisonResult` DTO
- This field contains all payload penalty metrics including:
  - `has_penalty`: Boolean indicating if penalty applies
  - `payload_difference`: Absolute difference in tonnes
  - `payload_difference_percentage`: Percentage reduction
  - `additional_operational_cost_lifetime`: Total additional cost over vehicle lifetime
  - `additional_operational_cost_annual`: Annual additional cost
  - Other detailed metrics for labour, opportunity costs, etc.

### 3. Visualisation Updates

#### Cost Breakdown Chart
- Modified `create_cost_breakdown_chart()` to accept optional `payload_penalties` parameter
- Added "Payload Penalty" as a new cost component in the lifetime cost breakdown
- Only shows for BEV when payload penalty exists

#### Annual Costs Chart
- Modified `create_annual_costs_chart()` to include annual payload penalty costs
- Updates the chart title to indicate when payload penalties are included
- Payload penalties are added to BEV annual operating costs

### 4. User Interface Updates

#### Cost Breakdown Page
- Displays informational message when payload penalties are applied
- Shows payload capacity reduction percentage and additional lifetime costs
- Explains the impact in terms of additional trips required

#### Home Page
- Added warning message about payload considerations
- Displays the financial impact of reduced payload capacity
- Helps users understand the practical implications

## Calculation Logic

The payload penalty calculation considers:
1. **Additional Trips**: When BEV has less payload, more trips are needed to transport the same freight
2. **Additional Operating Costs**: More trips mean higher energy, maintenance, and other operating costs
3. **Labour Costs**: Additional driver hours required for extra trips
4. **Opportunity Costs**: Lost revenue from reduced carrying capacity

## Impact on TCO

When payload penalties exist:
- The BEV's lifetime TCO is adjusted upward by the `additional_operational_cost_lifetime`
- TCO savings calculations reflect this adjustment
- Price parity calculations account for the additional costs
- Per-tonne-km metrics are adjusted based on effective payload ratio

## Testing

Created comprehensive tests in `test_tco_calculation_payload.py` to verify:
- Payload penalties are correctly calculated when BEV has less capacity
- No penalties are applied when BEV has equal or greater capacity
- TCO savings reflect the payload penalty adjustments

## Future Enhancements

Potential improvements could include:
1. More detailed breakdown of payload penalty components in visualisations
2. Sensitivity analysis showing impact of payload differences on TCO
3. Fleet-level analysis considering mixed fleet strategies
4. Integration with route optimisation to minimise payload penalty impact 