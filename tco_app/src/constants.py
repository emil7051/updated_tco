from enum import Enum, unique

@unique
class Drivetrain(str, Enum):
    """Enumeration of valid drivetrain identifiers used throughout the codebase.
    Keeping them centralised avoids magic strings and naming drift.
    """

    BEV = "BEV"
    DIESEL = "Diesel"
    ALL = "All"


@unique
class FuelType(str, Enum):
    """Enumeration of fuel-type identifiers used in the emissions tables."""

    ELECTRICITY = "electricity"
    DIESEL = "diesel"


# Common data-frame column names (only a few to start; extend as the codebase is refactored)
VEHICLE_DRIVETRAIN_COL = "vehicle_drivetrain"
VEHICLE_TYPE_COL = "vehicle_type"
CHARGING_ID_COL = "charging_id"
INFRASTRUCTURE_ID_COL = "infrastructure_id"

__all__ = [
    "Drivetrain",
    "FuelType",
    "VEHICLE_DRIVETRAIN_COL",
    "VEHICLE_TYPE_COL",
    "CHARGING_ID_COL",
    "INFRASTRUCTURE_ID_COL",
] 