from dataclasses import dataclass
import logging
import sqlite3
from typing import Any, List

from boxing.utils.sql_utils import get_db_connection
from boxing.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Boxer:
    """
    A class to represent a boxer.

    Attributes:
        id (int): The unique identifier for the boxer.
        name (str): The boxer's name.
        weight (int): The boxer's weight in pounds.
        height (int): The boxer's height in inches.
        reach (float): The boxer's reach in inches.
        age (int): The boxer's age in years.
        weight_class (str, optional): The boxer's weight class determined from weight.
    """

    id: int
    name: str
    weight: int
    height: int
    reach: float
    age: int
    weight_class: str = None

    def __post_init__(self):
        self.weight_class = get_weight_class(self.weight)  # Automatically assign weight class


def create_boxer(name: str, weight: int, height: int, reach: float, age: int) -> None:
    """Creates new boxer in the boxers table.

    Args:
        name (str): The boxer's name.
        weight (int): The boxer's weight in pounds.
        height (int): The boxer's height in inches.
        reach (float): The boxer's reach in inches.
        age (int): The boxer's age in years.

    Raises:
        ValueError: Invalid field or a boxer with the same name already exists
        sqlite3.Error: Database error
    """
    logger.info(f"Received request to create a new boxer: {name}")

    if weight < 125:
        logger.warning(f"Invalid weight provided: {weight}")
        raise ValueError(f"Invalid weight: {weight}. Must be at least 125.")
    if height <= 0:
        logger.warning(f"Invalid height provided: {height}")
        raise ValueError(f"Invalid height: {height}. Must be greater than 0.")
    if reach <= 0:
        logger.warning(f"Invalid reach provided: {reach}")
        raise ValueError(f"Invalid reach: {reach}. Must be greater than 0.")
    if not (18 <= age <= 40):
        logger.warning(f"Invalid age provided: {age}")
        raise ValueError(f"Invalid age: {age}. Must be between 18 and 40.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the boxer already exists (name must be unique)
            logger.info(f"Checking if boxer '{name}' already exists")
            cursor.execute("SELECT 1 FROM boxers WHERE name = ?", (name,))
            if cursor.fetchone():
                logger.error(f"Boxer with name '{name}' already exists")
                raise ValueError(f"Boxer with name '{name}' already exists")

            logger.info(f"Inserting boxer '{name}' into database")
            cursor.execute("""
                INSERT INTO boxers (name, weight, height, reach, age)
                VALUES (?, ?, ?, ?, ?)
            """, (name, weight, height, reach, age))

            conn.commit()
            logger.info(f"Boxer created successfully: {name}")

    except sqlite3.IntegrityError:
        logger.error(f"Boxer, {name}, already exists.")
        raise ValueError(f"Boxer with name '{name}' already exists")

    except sqlite3.Error as e:
        logger.error(f"Error while creating boxer: {e}")
        raise e


def delete_boxer(boxer_id: int) -> None:
    """Deletes a boxer from the database
    
    Args: 
        boxer_id (int): ID of the boxer to delete

    Raises:
        ValueError: Boxer with the provided ID does not exist
        sqlite3.Error: Database error
    """

    logger.info(f"Received request to delete boxer with ID {boxer_id}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            logger.info(f"Checking if boxer with ID {boxer_id} exists")
            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.warning(f"Attempted to delete a boxer that does not exist with ID {boxer_id}.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            logger.info(f"Deleting boxer with ID {boxer_id}")
            cursor.execute("DELETE FROM boxers WHERE id = ?", (boxer_id,))
            conn.commit()
            logger.info(f"Boxer with ID {boxer_id} successfully deleted.")
    except sqlite3.Error as e:
        logger.error(f"Error while deleting boxer: {e}")
        raise e


def get_leaderboard(sort_by: str = "wins") -> List[dict[str, Any]]:
    """Gets leaderboard of boxers sorted by criteria specified

    Args:
        sort_by (str, optional): Desired sorting criteria, "wins" or "win_pct" and defaults to "wins"
    
    Returns:
        List[dict[str, Any]]: List of dictionaries representing boxers with stats

    Raises:
        ValueError: sort_by parameter is invalid
        sqlite3.Error: Database error
    """
    logger.info(f"Retrieving leaderboard sorted by '{sort_by}'")
    query = """
        SELECT id, name, weight, height, reach, age, fights, wins,
               (wins * 1.0 / fights) AS win_pct
        FROM boxers
        WHERE fights > 0
    """

    if sort_by == "win_pct":
        query += " ORDER BY win_pct DESC"
        logger.info("Sorting leaderboard by win percentage")
    elif sort_by == "wins":
        query += " ORDER BY wins DESC"
        logger.info("Sorting leaderboard by total wins")
    else:
        logger.error(f"Invalid sort_by paramter: {sort_by}")
        # logger.warning("Provided argument for sort_by is invalid.")
        raise ValueError(f"Invalid sort_by parameter: {sort_by}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger.info("Attempting to create a leaderboard for all boxers")
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info(f"Retrieved {len(rows)} boxers for leaderboard")

        leaderboard = []
        for row in rows:
            boxer = {
                'id': row[0],
                'name': row[1],
                'weight': row[2],
                'height': row[3],
                'reach': row[4],
                'age': row[5],
                'weight_class': get_weight_class(row[2]),  # Calculate weight class
                'fights': row[6],
                'wins': row[7],
                'win_pct': round(row[8] * 100, 1)  # Convert to percentage
            }
            leaderboard.append(boxer)

        logger.info(f"Leaderboard created with {len(leaderboard)} boxers")
        return leaderboard

    except sqlite3.Error as e:
        logger.error(f"Error while creating leaderboard: {e}")
        raise e


def get_boxer_by_id(boxer_id: int) -> Boxer:
    """Gets boxer from database by ID

    Args:
        boxer_id (int): ID for desired boxer

    Returns:
        Boxer: Corresponding Boxer object to boxer_id
    
    Raises:
        ValueError: Boxer cannot be found
        sqlite3.Error: Database error
    
    """
    logger.info(f"Retrieving boxer by ID {boxer_id}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE id = ?
            """, (boxer_id,))

            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                logger.info(f"Successfully retrieved boxer: {boxer.name} (ID: {boxer.id})")
                return boxer
            else:
                logger.warning(f"Boxer with ID {boxer_id} not found")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

    except sqlite3.Error as e:
        logger.error(f"Database error for getting boxer ID {boxer_id}: {e}")
        raise e


def get_boxer_by_name(boxer_name: str) -> Boxer:
    """Gets boxer from database by name
    
    Args:
        boxer_name (str): Name of boxer we want to get

    Returns:
        Boxer: Corresponding Boxer object to boxer_name

    Raises:
        ValueError: Boxer cannot be found
        sqlite3.Error: Database error 
    
    """
    logger.info(f"Retrieving boxer with name '{boxer_name}'")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE name = ?
            """, (boxer_name,))

            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                logger.info(f"Successfully retrieved boxer: {boxer.name} (ID: {boxer.id})")
                return boxer
            else:
                logger.warning(f"Boxer '{boxer_name}' not found")
                raise ValueError(f"Boxer '{boxer_name}' not found.")

    except sqlite3.Error as e:
        logger.error(f"Database error for getting boxer '{boxer_name}': {e}")
        raise e


def get_weight_class(weight: int) -> str:
    """Get weight class based on boxer's weight

    Args:
        weight (int): Boxer's weight in pounds

    Returns:
        str: Weight class corresponding to weight

    Raises:
        ValueError: Invalid weight (less than 125 pounds)
    """
    logger.debug(f"Determining weight class for weight: {weight}")
    if weight >= 203:
        weight_class = 'HEAVYWEIGHT'
    elif weight >= 166:
        weight_class = 'MIDDLEWEIGHT'
    elif weight >= 133:
        weight_class = 'LIGHTWEIGHT'
    elif weight >= 125:
        weight_class = 'FEATHERWEIGHT'
    else:
        logger.warning(f"Invalid weight for weight class: {weight}")
        raise ValueError(f"Invalid weight: {weight}. Weight must be at least 125.")

    logger.debug(f"Weight class: {weight_class} determined")
    return weight_class


def update_boxer_stats(boxer_id: int, result: str) -> None:
    """Update boxer's fighting stats after the end of a match

    Args:
        boxer_id (int): ID of boxer whose stats we want to update
        result (str): Result of the fight as either 'win' or 'loss'

    Raises:
        ValueError: Result is invalid or boxer with boxer_id does not exist
        sqlite3.Error: Database error
    
    """
    logger.info(f"Updating fight stats for boxer {boxer_id} with result: {result}")
    if result not in {'win', 'loss'}:
        logger.error(f"Invalid result: {result} from fight")
        raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            logger.info(f"Checking if boxer with {boxer_id} exists")
            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.warning(f"Boxer with ID {boxer_id} not found")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            if result == 'win':
                logger.info(f"Updating win stat for boxer ID {boxer_id}")
                cursor.execute("UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?", (boxer_id,))
            else:  # result == 'loss'
                logger.info(f"Updating loss stat for boxer ID {boxer_id}")
                cursor.execute("UPDATE boxers SET fights = fights + 1 WHERE id = ?", (boxer_id,))

            conn.commit()
            logger.info(f"Updated stats for boxer ID {boxer_id}")

    except sqlite3.Error as e:
        logger.error(f"Database error while updating stats for {boxer_id}: {e}")
        raise e
