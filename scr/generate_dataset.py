from scr.crud_elevator import ElevatorStateManager
import random
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv
import os

load_dotenv()


class GenerateDataset:
    """Generates a dataset of elevator states based on specified parameters.

    The dataset is created and stored in a database using the ElevatorStateManager.

    Attributes:
        elevator (ElevatorStateManager): An instance of ElevatorStateManager for database interaction.
        floor_capacities (dict): Mapping of floor types to capacities.
        floor_types (dict): Mapping of floor numbers to floor types.
        rows_generated (int): Number of elevator states to generate.
        floor_number (int): Total number of floors in the building.
        min_time_interval_seconds (int): Minimum time interval in seconds between elevator states.
        max_time_interval_seconds (int): Maximum time interval in seconds between elevator states.
        interval_per_floor_seconds (float): Time interval per floor in seconds.
        peak_hours (list): List of dictionaries representing peak hours intervals.
        peak_multiplier (float): Multiplier for peak hours intervals.
        random_minutes_range (dict): Range of random minutes added to intervals.
        weight_list (list): List of weights assigned to each floor based on capacities.
        current_floor (int): Current floor in the elevator simulation.
        demand_floor (int): Floor where the elevator is in demand.
        start_time (datetime): Start time for the elevator simulation.
        next_floor (int): Next floor to which the elevator will move.
    """
    def __init__(self) -> None:
        """Initializes the GenerateDataset class."""

        DATABASE_URL = os.getenv("DATABASE_URL")
        self.elevator = ElevatorStateManager(database_url=DATABASE_URL)
        self.load_elevator_variables()

    def load_elevator_variables(self):
        """Loads elevator-related variables from a JSON file."""
        try:
            with open("./scr/elevator_variables.json", "r") as json_file:
                data = json.load(json_file)

            # Validate structure
            if not all(
                key in data
                for key in [
                    "floor_capacities",
                    "floor_types",
                    "rows_generated",
                    "floor_number",
                    "min_time_interval_seconds",
                    "max_time_interval_seconds",
                    "peak_hours",
                    "peak_multiplier",
                    "random_minutes_range",
                ]
            ):
                raise ValueError("Invalid JSON structure.")

            # Validate floor_capacities
            if not isinstance(data["floor_capacities"], dict):
                raise ValueError("Invalid 'floor_capacities' data type.")
            for floor_type, capacity in data["floor_capacities"].items():
                if not isinstance(capacity, int) or capacity <= 0:
                    raise ValueError(f"Invalid capacity for {floor_type}.")

            # Validate floor_types
            if not isinstance(data["floor_types"], dict):
                raise ValueError("Invalid 'floor_types' data type.")
            for floor_number, floor_type in data["floor_types"].items():
                if not isinstance(floor_number, str) or not isinstance(floor_type, str):
                    raise ValueError("Invalid floor type mapping.")

            # Validate rows_generated
            if (
                not isinstance(data["rows_generated"], int)
                or data["rows_generated"] <= 0
            ):
                raise ValueError("Invalid 'rows_generated' value.")

            # Validate floor_number
            if not isinstance(data["floor_number"], int) or data["floor_number"] <= 0:
                raise ValueError("Invalid 'floor_number' value.")
            
            # Validate negative_floor_number
            if not isinstance(data["negative_floor_number"], int) or data["negative_floor_number"] > 0:
                raise ValueError("Invalid 'negative_floor_number' value.")


            # Validate time intervals
            for interval_key in [
                "min_time_interval_seconds",
                "max_time_interval_seconds",
            ]:
                if not isinstance(data[interval_key], int) or data[interval_key] <= 0:
                    raise ValueError(f"Invalid '{interval_key}' value.")

            # Validate interval_per_floor_seconds
            if (
                not isinstance(data["interval_per_floor_seconds"], (int, float))
                or not 0 <= data["interval_per_floor_seconds"]
            ):
                raise ValueError("Invalid 'interval_per_floor_seconds' value.")

            # Validate peak_hours
            if not isinstance(data["peak_hours"], list) or not all(
                isinstance(interval, dict) for interval in data["peak_hours"]
            ):
                raise ValueError("Invalid 'peak_hours' format.")
            for peak_interval in data["peak_hours"]:
                if (
                    not all(key in peak_interval for key in ["start", "end"])
                    or not isinstance(peak_interval["start"], int)
                    or not isinstance(peak_interval["end"], int)
                ):
                    raise ValueError("Invalid peak hour interval.")

            # Validate peak_multiplier
            if (
                not isinstance(data["peak_multiplier"], (int, float))
                or not 0 <= data["peak_multiplier"] <= 1
            ):
                raise ValueError("Invalid 'peak_multiplier' value.")

            # Validate random_minutes_range
            if (
                not isinstance(data["random_minutes_range"], dict)
                or not all(
                    key in data["random_minutes_range"] for key in ["min", "max"]
                )
                or not isinstance(data["random_minutes_range"]["min"], int)
                or not isinstance(data["random_minutes_range"]["max"], int)
            ):
                raise ValueError("Invalid 'random_minutes_range' format.")

            # Assign variables as attributes
            self.floor_capacities = data["floor_capacities"]
            self.floor_types = data["floor_types"]
            self.rows_generated = data["rows_generated"]
            self.floor_number = data["floor_number"]
            self.negative_floor_number = data["negative_floor_number"]
            self.min_time_interval_seconds = data["min_time_interval_seconds"]
            self.max_time_interval_seconds = data["max_time_interval_seconds"]
            self.interval_per_floor_seconds = data["interval_per_floor_seconds"]
            self.peak_hours = data["peak_hours"]
            self.peak_multiplier = data["peak_multiplier"]
            self.random_minutes_range = data["random_minutes_range"]
            print("self.negative_floor_number",self.negative_floor_number)
            print("all variables were loaded correctly")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise ValueError(f"Error loading elevator variables: {str(e)}")

    def floor_weights_mapping(self):
        """Maps floor types to weights based on room capacities."""
        floor_capacities_mapping = {
            floor: self.floor_capacities.get(
                self.floor_types.get(str(floor), "Residential")
            )
            for floor in range(self.negative_floor_number, self.floor_number)
        }
        # Calculate weights based on room capacities
        min_capacity = min(floor_capacities_mapping.values())
        max_capacity = max(floor_capacities_mapping.values())

        # Set a base weight for all floors
        base_weight = 1 / self.floor_number

        # Map floors to weights
        floor_weights_mapping = {
            floor: base_weight
            + (capacity - min_capacity) / (max_capacity - min_capacity)
            for floor, capacity in floor_capacities_mapping.items()
        }

        # Normalize weights so that the sum is 1
        total_weight = sum(floor_weights_mapping.values())
        floor_weights_mapping = {
            floor: round(weight / total_weight,3)
            for floor, weight in floor_weights_mapping.items()
        }
        self.weight_list = list(floor_weights_mapping.values())
        print("self.weight_list",self.weight_list)
        
        
    def pick_random_floor_weighted(self):
        """Picks a random floor based on weights assigned to each floor."""

        random_floor = random.choices(
            range(self.negative_floor_number, self.floor_number), weights=self.weight_list
        )[0]
        return random_floor

    def pick_next_door(self):
        """Picks the next floor, ensuring it is different from the demand floor."""
        while True:
            next_floor = random.choices(
                range(self.negative_floor_number, self.floor_number ), weights=self.weight_list
            )[0]
            print("next_floor",next_floor)
            if next_floor != self.demand_floor:
                break
        return next_floor

    def obtain_table_last_state(self):
        """Obtains the last recorded elevator state from the database or generates initial values."""

        last_state = self.elevator.get_last_elevator_state()

        if last_state:
            self.current_floor = last_state.next_floor
            self.demand_floor = last_state.demand_floor
            self.start_time = last_state.call_datetime
        else:
            self.current_floor = self.pick_random_floor_weighted()
            self.demand_floor = self.pick_random_floor_weighted()
            self.start_time = datetime.today()

    def calculate_interval_minutes(self):
        """Calculates the time interval in minutes between elevator states."""

        current_floor_distance = abs(self.current_floor - self.demand_floor)
        current_floor_interval_lag = (
            self.min_time_interval_seconds if current_floor_distance <= 1 
            else min(
                self.max_time_interval_seconds,
                current_floor_distance * self.interval_per_floor_seconds,
            )
        ) / 60  # Convert seconds to minutes

        # Calculate time interval based on the absolute difference between next_floor and demand_floor
        next_floor_distance = abs(self.next_floor - self.demand_floor) 
        next_floor_interval_lag = (
            self.min_time_interval_seconds
            if next_floor_distance <= 1
            else min(
                self.max_time_interval_seconds,
                next_floor_distance * self.interval_per_floor_seconds,
            )
        ) / 60  # Convert seconds to minutes

        # Assuming self.start_time is a datetime object
        if any(
            interval["start"] <= self.start_time.hour < interval["end"]
            for interval in self.peak_hours
        ):
            peak_interval_multiplier = self.peak_multiplier
        else:
            peak_interval_multiplier = 1.0  # No multiplier outside of peak hours
        random_minutes = random.randint(
            self.random_minutes_range["min"], self.random_minutes_range["max"]
        )
        interval_minutes = (
            random_minutes * peak_interval_multiplier
            + current_floor_interval_lag
            + next_floor_interval_lag
        )  # Time interval between states
        return interval_minutes

    def generate_elevator_states(self):
        """Generates elevator states based on specified parameters and stores them in the database."""

        self.load_elevator_variables()
        self.floor_weights_mapping()
        self.obtain_table_last_state()

        for i in range(1, self.rows_generated + 1):
            self.next_floor = self.pick_next_door()
            interval_minutes = self.calculate_interval_minutes()

            call_datetime = self.start_time + timedelta(minutes=interval_minutes)
            print(self.current_floor,self.demand_floor,self.next_floor)
            created_state = self.elevator.create_elevator_state(
                current_floor=int(self.current_floor),
                demand_floor=int(self.demand_floor),
                next_floor=int(self.next_floor),
                date_str=call_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            )
            print("created_state: ", created_state)

            # Update current_floor and demand_floor for the next state
            self.current_floor = self.next_floor
            self.demand_floor = self.pick_random_floor_weighted()
            self.start_time = call_datetime


if __name__ == "__main__":
    generator = GenerateDataset()
    generator.generate_elevator_states()
