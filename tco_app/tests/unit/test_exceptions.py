"""Tests for custom exceptions from Work Package 5."""

from tco_app.src.exceptions import (
    CalculationError,
    DataNotFoundError,
    InvalidVehicleError,
    ParameterError,
    ScenarioError,
    TCOBaseException,
)


class TestTCOBaseException:
    """Test the base exception class."""

    def test_base_exception_inheritance(self):
        """Test that TCOBaseException inherits from Exception."""
        assert issubclass(TCOBaseException, Exception)

    def test_base_exception_instantiation(self):
        """Test that TCOBaseException can be instantiated."""
        exc = TCOBaseException("Test message")
        assert str(exc) == "Test message"


class TestDataNotFoundError:
    """Test DataNotFoundError exception."""

    def test_inheritance(self):
        """Test that DataNotFoundError inherits from TCOBaseException."""
        assert issubclass(DataNotFoundError, TCOBaseException)

    def test_basic_instantiation(self):
        """Test basic instantiation with just message."""
        exc = DataNotFoundError("Data not found")
        assert str(exc) == "Data not found"
        assert exc.key is None
        assert exc.dataframe_name is None

    def test_full_instantiation(self):
        """Test instantiation with all parameters."""
        exc = DataNotFoundError(
            "Vehicle not found", key="VEH001", dataframe_name="vehicle_models"
        )
        assert str(exc) == "Vehicle not found"
        assert exc.key == "VEH001"
        assert exc.dataframe_name == "vehicle_models"


class TestCalculationError:
    """Test CalculationError exception."""

    def test_inheritance(self):
        """Test that CalculationError inherits from TCOBaseException."""
        assert issubclass(CalculationError, TCOBaseException)

    def test_basic_instantiation(self):
        """Test basic instantiation."""
        exc = CalculationError("Calculation failed")
        assert str(exc) == "Calculation failed"
        assert exc.calculation_type is None

    def test_with_calculation_type(self):
        """Test instantiation with calculation type."""
        exc = CalculationError("Division by zero", calculation_type="energy_cost")
        assert str(exc) == "Division by zero"
        assert exc.calculation_type == "energy_cost"


class TestInvalidVehicleError:
    """Test InvalidVehicleError exception."""

    def test_inheritance(self):
        """Test that InvalidVehicleError inherits from TCOBaseException."""
        assert issubclass(InvalidVehicleError, TCOBaseException)

    def test_basic_instantiation(self):
        """Test basic instantiation."""
        exc = InvalidVehicleError("Invalid vehicle data")
        assert str(exc) == "Invalid vehicle data"
        assert exc.vehicle_id is None

    def test_with_vehicle_id(self):
        """Test instantiation with vehicle ID."""
        exc = InvalidVehicleError("Missing range data", vehicle_id="VEH001")
        assert str(exc) == "Missing range data"
        assert exc.vehicle_id == "VEH001"


class TestScenarioError:
    """Test ScenarioError exception."""

    def test_inheritance(self):
        """Test that ScenarioError inherits from TCOBaseException."""
        assert issubclass(ScenarioError, TCOBaseException)

    def test_instantiation(self):
        """Test basic instantiation."""
        exc = ScenarioError("Invalid scenario configuration")
        assert str(exc) == "Invalid scenario configuration"


class TestParameterError:
    """Test ParameterError exception."""

    def test_inheritance(self):
        """Test that ParameterError inherits from TCOBaseException."""
        assert issubclass(ParameterError, TCOBaseException)

    def test_basic_instantiation(self):
        """Test basic instantiation."""
        exc = ParameterError("Invalid parameter value")
        assert str(exc) == "Invalid parameter value"
        assert exc.parameter_name is None
        assert exc.value is None

    def test_full_instantiation(self):
        """Test instantiation with all parameters."""
        exc = ParameterError(
            "Value out of range", parameter_name="discount_rate", value=-0.1
        )
        assert str(exc) == "Value out of range"
        assert exc.parameter_name == "discount_rate"
        assert exc.value == -0.1


class TestExceptionChaining:
    """Test exception chaining with custom exceptions."""

    def test_raise_from_chain(self):
        """Test that exceptions can be chained properly."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise CalculationError("Calculation failed") from e
        except CalculationError as calc_err:
            assert str(calc_err) == "Calculation failed"
            assert isinstance(calc_err.__cause__, ValueError)
            assert str(calc_err.__cause__) == "Original error"

    def test_exception_context_preservation(self):
        """Test that exception context is preserved."""

        def failing_function():
            raise ValueError("Inner error")

        try:
            try:
                failing_function()
            except ValueError:
                raise DataNotFoundError("Data processing failed")
        except DataNotFoundError as data_err:
            assert str(data_err) == "Data processing failed"
            # Should have context from the original ValueError
            assert data_err.__context__ is not None
