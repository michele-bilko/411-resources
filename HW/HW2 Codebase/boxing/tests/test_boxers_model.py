from contextlib import contextmanager
import re
import sqlite3
import pytest

from boxing.models.boxers_model import (
    Boxer,
    create_boxer,
    delete_boxer,
    get_leaderboard,
    get_boxer_by_id,
    get_boxer_by_name,
    get_weight_class,
    update_boxer_stats
)

@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []

    # Mock the get_db_connection context manager
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn

    mocker.patch("boxing.models.boxers_model.get_db_connection", mock_get_db_connection)
    return mock_cursor

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()


def test_create_boxer(mock_cursor):
    """Test creating a new boxer in the database."""
    create_boxer(name="Bob", weight=220, height=71, reach=71.0, age=25)
    
    mock_cursor.execute.assert_any_call(
        "SELECT 1 FROM boxers WHERE name = ?", 
        ("Bob",)
    )
    
    insert_sql_call = [call for call in mock_cursor.execute.call_args_list 
                      if "INSERT INTO boxers" in call[0][0]][0]
    
    expected_sql = normalize_whitespace("""
        INSERT INTO boxers (name, weight, height, reach, age)
        VALUES (?, ?, ?, ?, ?)
    """)
    actual_sql = normalize_whitespace(insert_sql_call[0][0])
    assert actual_sql == expected_sql
    
    insert_params = insert_sql_call[0][1]
    assert insert_params == ("Bob", 220, 71, 71.0, 25)



def test_create_dupe_boxer(mock_cursor):
    """Test error when creating a boxer with a duplicate name."""
    # Mock that the boxer already exists
    mock_cursor.fetchone.return_value = (1, "Bob", 220, 71, 71.0, 25)
    
    with pytest.raises(ValueError, match="Boxer with name 'Bob' already exists"):
        create_boxer(name="Bob", weight=220, height=71, reach=71.0, age=25)


def test_create_boxer_invalid_age(mock_cursor):
    """Test error for creating invalid age boxer"""
    with pytest.raises(ValueError, match="Invalid age: 17. Must be between 18 and 40."):
        create_boxer(name="Young Bob", weight=150, height=70, reach=70.0, age=17)
    with pytest.raises(ValueError, match="Invalid age: 41. Must be between 18 and 40."):
        create_boxer(name="Old Bob", weight=150, height=70, reach=70.0, age=41)

def test_create_boxer_invalid_height(mock_cursor):
    """Test error when creating a boxer with invalid height."""
    with pytest.raises(ValueError, match="Invalid height: 0. Must be greater than 0."):
        create_boxer(name="Short Bob", weight=150, height=0, reach=70.0, age=25)
    
    with pytest.raises(ValueError, match="Invalid height: -5. Must be greater than 0."):
        create_boxer(name="Negative Bob", weight=150, height=-5, reach=70.0, age=25)

def test_create_boxer_invalid_weight(mock_cursor):
    """Test error when creating a boxer with invalid weight."""
    with pytest.raises(ValueError, match="Invalid weight: 124. Must be at least 125."):
        create_boxer(name="Light Bob", weight=124, height=70, reach=70.0, age=25)

def test_create_boxer_invalid_reach(mock_cursor):
    """Test error when creating a boxer with invalid reach."""
    with pytest.raises(ValueError, match="Invalid reach: 0.0. Must be greater than 0."):
        create_boxer(name="Armless Bob", weight=150, height=70, reach=0.0, age=25)
    
    with pytest.raises(ValueError, match="Invalid reach: -10.0. Must be greater than 0."):
        create_boxer(name="Negative Arms Bob", weight=150, height=70, reach=-10.0, age=25)

def test_delete_boxer(mock_cursor):
    """Deleting a boxer from the database"""
    mock_cursor.fetchone.return_value = (1,)
    delete_boxer(1)
    #Correct SQL query was called
    mock_cursor.execute.assert_any_call("SELECT id FROM boxers WHERE id = ?", (1,))
    mock_cursor.execute.assert_any_call("DELETE FROM boxers WHERE id = ?", (1,))

def test_delete_boxer_nothing(mock_cursor):
    """Check that correct error comes up when deleting boxer that doesn't exist"""
    mock_cursor.fetchone.return_value = None
    
    with pytest.raises(ValueError, match="Boxer with ID 999 not found."):
        delete_boxer(999)
    
def test_get_leaderboard(mock_cursor):
    """Test getting sorted leaderboard by wins"""
    mock_cursor.fetchall.return_value = [
        (1, "Bob", 220, 71, 71.0, 30, 50, 48, 0.96),
        (2, "Dave", 210, 75, 78.0, 35, 62, 57, 0.92),
        (3, "Charles", 150, 68, 72.0, 38, 50, 50, 1.0)
    ]
    result = get_leaderboard()
    #Check correct query is called
    expected_query = normalize_whitespace("""
        SELECT id, name, weight, height, reach, age, fights, wins,
               (wins * 1.0 / fights) AS win_pct
        FROM boxers
        WHERE fights > 0
        ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query
    assert len(result) == 3
    assert result[0]['id'] == 1
    assert result[0]['name'] == "Bob"
    assert result[0]['weight_class'] == "HEAVYWEIGHT"
    assert result[0]['win_pct'] == 96.0

def test_get_leaderboard_invalid(mock_cursor):
    """Test invalid sort"""
    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid_sort"):
        get_leaderboard(sort_by="invalid_sort")

def test_get_boxer_by_id(mock_cursor):
    """Test retrieving a boxer by ID."""
    mock_cursor.fetchone.return_value = (1, "Bob", 220, 71, 71.0, 30)
    
    boxer = get_boxer_by_id(1)
    
    #Check if correct SQL query
    expected_query = normalize_whitespace("""
        SELECT id, name, weight, height, reach, age
        FROM boxers WHERE id = ?
    """)
    
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query
    assert mock_cursor.execute.call_args[0][1] == (1,)
    
    # Check boxer object
    assert boxer.id == 1
    assert boxer.name == "Bob"
    assert boxer.weight == 220
    assert boxer.height == 71
    assert boxer.reach == 71.0
    assert boxer.age == 30
    assert boxer.weight_class == "HEAVYWEIGHT"


def test_get_boxer_by_id_bad(mock_cursor):
    """Test error when retrieving a non-existent boxer by ID."""
    mock_cursor.fetchone.return_value = None
    
    with pytest.raises(ValueError, match="Boxer with ID 999 not found."):
        get_boxer_by_id(999)


def test_get_boxer_by_name(mock_cursor):
    """Test retrieving a boxer by name."""
    mock_cursor.fetchone.return_value = (1, "Bob", 220, 71, 71.0, 30)
    
    boxer = get_boxer_by_name("Bob")
    
    # Check for correct SQL query
    expected_query = normalize_whitespace("""
        SELECT id, name, weight, height, reach, age
        FROM boxers WHERE name = ?
    """)
    
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query
    assert mock_cursor.execute.call_args[0][1] == ("Bob",)
    
    # Check boxer object
    assert boxer.id == 1
    assert boxer.name == "Bob"
    assert boxer.weight == 220
    assert boxer.height == 71
    assert boxer.reach == 71.0
    assert boxer.age == 30
    assert boxer.weight_class == "HEAVYWEIGHT"


def test_get_boxer_by_name_bad(mock_cursor):
    """Test error when retrieving a non-existent boxer by name."""
    mock_cursor.fetchone.return_value = None
    
    with pytest.raises(ValueError, match="Boxer 'Unknown Boxer' not found."):
        get_boxer_by_name("Unknown Boxer")


def test_get_weight_class(mock_cursor):
    """Test determining the weight class based on weight."""
    assert get_weight_class(125) == "FEATHERWEIGHT"
    assert get_weight_class(133) == "LIGHTWEIGHT"
    assert get_weight_class(166) == "MIDDLEWEIGHT"
    assert get_weight_class(203) == "HEAVYWEIGHT"
    
    # Edge cases
    assert get_weight_class(132) == "FEATHERWEIGHT"
    assert get_weight_class(165) == "LIGHTWEIGHT"
    assert get_weight_class(202) == "MIDDLEWEIGHT"


def test_get_weight_class_bad(mock_cursor):
    """Test error when determining weight class with invalid weight."""
    with pytest.raises(ValueError, match="Invalid weight: 124. Weight must be at least 125."):
        get_weight_class(124)
    
    with pytest.raises(ValueError, match="Invalid weight: 0. Weight must be at least 125."):
        get_weight_class(0)
    
    with pytest.raises(ValueError, match="Invalid weight: -10. Weight must be at least 125."):
        get_weight_class(-10)


def test_update_boxer_stats(mock_cursor):
    """Test updating a boxer's fight statistics."""
    mock_cursor.fetchone.return_value = (1,)
    
    update_boxer_stats(1, "win")
    
    # Check for correct SQL query
    win_sql_call = [call for call in mock_cursor.execute.call_args_list 
                   if "UPDATE boxers SET fights = fights + 1, wins = wins + 1" in call[0][0]][0]
    
    expected_win_sql = normalize_whitespace("""
        UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?
    """)
    actual_win_sql = normalize_whitespace(win_sql_call[0][0])
    assert actual_win_sql == expected_win_sql
    assert win_sql_call[0][1] == (1,)
    
    mock_cursor.reset_mock()
    mock_cursor.fetchone.return_value = (1,)
    
    update_boxer_stats(1, "loss")
    
    # Corrcet SQL query check
    loss_sql_call = [call for call in mock_cursor.execute.call_args_list 
                    if "UPDATE boxers SET fights = fights + 1 WHERE id = ?" in call[0][0]][0]
    
    expected_loss_sql = normalize_whitespace("""
        UPDATE boxers SET fights = fights + 1 WHERE id = ?
    """)
    actual_loss_sql = normalize_whitespace(loss_sql_call[0][0])
    assert actual_loss_sql == expected_loss_sql
    assert loss_sql_call[0][1] == (1,)


def test_update_boxer_stats_bad(mock_cursor):
    """Test errors when updating boxer stats."""
    # Test invalid
    with pytest.raises(ValueError, match="Invalid result: draw. Expected 'win' or 'loss'."):
        update_boxer_stats(1, "draw")
    
    # Test non-existent
    mock_cursor.fetchone.return_value = None
    with pytest.raises(ValueError, match="Boxer with ID 999 not found."):
        update_boxer_stats(999, "win")