"""Custom exceptions for the TCO application."""

from typing import Any


class TCOBaseException(Exception):
    """Base exception for all TCO-specific errors."""

    pass


class DataNotFoundError(TCOBaseException):
    """Raised when expected data is not found in DataFrame."""

    def __init__(self, message: str, key: str = None, dataframe_name: str = None):
        self.key = key
        self.dataframe_name = dataframe_name
        super().__init__(message)


class CalculationError(TCOBaseException):
    """Raised when a calculation fails."""

    def __init__(self, message: str, calculation_type: str = None):
        self.calculation_type = calculation_type
        super().__init__(message)


class InvalidVehicleError(TCOBaseException):
    """Raised when vehicle data is invalid or incomplete."""

    def __init__(self, message: str, vehicle_id: str = None):
        self.vehicle_id = vehicle_id
        super().__init__(message)


class ScenarioError(TCOBaseException):
    """Raised when scenario configuration is invalid."""

    pass


class ParameterError(TCOBaseException):
    """Raised when a parameter value is invalid."""

    def __init__(self, message: str, parameter_name: str = None, value: Any = None):
        self.parameter_name = parameter_name
        self.value = value
        super().__init__(message)


class VehicleNotFoundError(TCOBaseException):
    """Raised when a specific vehicle is not found in the data."""

    def __init__(self, message: str, vehicle_id: str = None):
        self.vehicle_id = vehicle_id
        super().__init__(message)
