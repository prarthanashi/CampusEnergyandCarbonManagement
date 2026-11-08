"""
database.py
-----------
Centralized database connection and SQL operations for the Campus Energy
and Carbon Management System.

All database queries use parameterized SQL (%s) to prevent SQL injection,
and transactions (commit/rollback) are implemented for all data modifications.
"""

import streamlit as st
import psycopg2
from psycopg2 import errors
import pandas as pd


def get_connection():
    """
    Establish and return a connection to the PostgreSQL database
    using credentials configured in .streamlit/secrets.toml.
    """
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        port=st.secrets["postgres"]["port"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"]
    )


def test_connection():
    """
    Test the database connection and return a tuple: (success: bool, message: str).
    """
    try:
        conn = get_connection()
        conn.close()
        return True, "Database connected successfully!"
    except Exception as exc:
        return False, str(exc)


# =====================================================================
# MODULE 2: BUILDING MANAGEMENT DATABASE OPERATIONS
# =====================================================================

def get_next_building_id():
    """
    Retrieve the next suggested integer ID for a new building.
    Defaults to 101 if the table is empty.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(building_id), 100) + 1 FROM building;")
            return cur.fetchone()[0]
    finally:
        conn.close()


def get_all_buildings():
    """
    Retrieve all campus buildings ordered by building_id.
    Returns a list of tuples: (building_id, building_name, building_type, location).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT building_id, building_name, building_type, location
                FROM building
                ORDER BY building_id ASC;
            """)
            return cur.fetchall()
    finally:
        conn.close()


def add_building(building_id, name, building_type, location):
    """
    Insert a new building record into the BUILDING table.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO building (building_id, building_name, building_type, location)
                VALUES (%s, %s, %s, %s);
            """, (building_id, name, building_type, location))
        conn.commit()
    except errors.UniqueViolation:
        conn.rollback()
        raise ValueError(f"A building with ID {building_id} already exists.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_building(building_id, name, building_type, location):
    """
    Update an existing building's details in the BUILDING table.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE building
                SET building_name = %s,
                    building_type = %s,
                    location = %s
                WHERE building_id = %s;
            """, (name, building_type, location, building_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_building(building_id):
    """
    Delete a building by building_id.
    Prevents deletion if existing energy readings reference this building.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Check for existing readings referencing this building
            cur.execute("SELECT COUNT(*) FROM energy_reading WHERE building_id = %s;", (building_id,))
            reading_count = cur.fetchone()[0]
            if reading_count > 0:
                raise ValueError(
                    f"Cannot delete building ID {building_id} because it has {reading_count} "
                    f"associated energy reading(s). Delete those readings first."
                )

            cur.execute("DELETE FROM building WHERE building_id = %s;", (building_id,))
        conn.commit()
    except errors.ForeignKeyViolation:
        conn.rollback()
        raise ValueError(
            f"Cannot delete building ID {building_id}: foreign key constraint prevents deletion "
            f"due to referencing records."
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =====================================================================
# MODULE 4: EMISSION FACTOR MANAGEMENT DATABASE OPERATIONS
# =====================================================================

def get_next_factor_id():
    """
    Retrieve the next suggested integer ID for a new emission factor.
    Defaults to 301 if the table is empty.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(factor_id), 300) + 1 FROM emission_factor;")
            return cur.fetchone()[0]
    finally:
        conn.close()


def get_all_emission_factors():
    """
    Retrieve all emission factors ordered by valid_from date ascending.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT factor_id, factor_name, kg_co2_per_kwh, valid_from
                FROM emission_factor
                ORDER BY valid_from ASC, factor_id ASC;
            """)
            return cur.fetchall()
    finally:
        conn.close()


def get_applicable_emission_factor(reading_date):
    """
    Find the latest emission factor whose valid_from date is less than or
    equal to the reading_date.
    Returns (factor_id, factor_name, kg_co2_per_kwh, valid_from) or None.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT factor_id, factor_name, kg_co2_per_kwh, valid_from
                FROM emission_factor
                WHERE valid_from <= %s
                ORDER BY valid_from DESC, factor_id DESC
                LIMIT 1;
            """, (reading_date,))
            return cur.fetchone()
    finally:
        conn.close()


def add_emission_factor(factor_id, factor_name, kg_co2_per_kwh, valid_from):
    """
    Insert a new emission factor into the EMISSION_FACTOR table.
    Validates non-negative emission rate.
    """
    if kg_co2_per_kwh < 0:
        raise ValueError("Emission factor (kg CO2/kWh) must be greater than or equal to zero.")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO emission_factor (factor_id, factor_name, kg_co2_per_kwh, valid_from)
                VALUES (%s, %s, %s, %s);
            """, (factor_id, factor_name, kg_co2_per_kwh, valid_from))
        conn.commit()
    except errors.UniqueViolation:
        conn.rollback()
        raise ValueError(f"An emission factor with name '{factor_name}' and valid date '{valid_from}' or ID {factor_id} already exists.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_emission_factor(factor_id, factor_name, kg_co2_per_kwh, valid_from):
    """
    Update an existing emission factor in the EMISSION_FACTOR table.
    """
    if kg_co2_per_kwh < 0:
        raise ValueError("Emission factor (kg CO2/kWh) must be greater than or equal to zero.")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE emission_factor
                SET factor_name = %s,
                    kg_co2_per_kwh = %s,
                    valid_from = %s
                WHERE factor_id = %s;
            """, (factor_name, kg_co2_per_kwh, valid_from, factor_id))
        conn.commit()
    except errors.UniqueViolation:
        conn.rollback()
        raise ValueError(f"An emission factor with name '{factor_name}' and valid date '{valid_from}' already exists.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_emission_factor(factor_id):
    """
    Delete an emission factor if it is not referenced by any energy reading
    in the READING_FACTOR table.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Check if this factor is referenced by any reading in READING_FACTOR
            cur.execute("SELECT COUNT(*) FROM reading_factor WHERE factor_id = %s;", (factor_id,))
            ref_count = cur.fetchone()[0]
            if ref_count > 0:
                raise ValueError(
                    f"Cannot delete emission factor ID {factor_id} because it is currently assigned "
                    f"to {ref_count} energy reading(s)."
                )

            cur.execute("DELETE FROM emission_factor WHERE factor_id = %s;", (factor_id,))
        conn.commit()
    except errors.ForeignKeyViolation:
        conn.rollback()
        raise ValueError(
            f"Cannot delete emission factor ID {factor_id}: foreign key constraint prevents deletion "
            f"due to referencing records."
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =====================================================================
# MODULE 3: ENERGY READING & FACTOR ASSIGNMENT DATABASE OPERATIONS
# =====================================================================

def get_next_reading_id():
    """
    Retrieve the next suggested integer ID for a new energy reading.
    Defaults to 201 if the table is empty.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(reading_id), 200) + 1 FROM energy_reading;")
            return cur.fetchone()[0]
    finally:
        conn.close()


def get_all_energy_readings():
    """
    Retrieve all energy readings with their building details and assigned
    emission factor. Uses LEFT JOIN to ensure any reading without factor assignment
    is still visible.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    e.reading_id,
                    b.building_id,
                    b.building_name,
                    b.building_type,
                    e.reading_date,
                    e.consumption_kwh,
                    f.factor_id,
                    f.factor_name,
                    f.kg_co2_per_kwh,
                    ROUND(e.consumption_kwh * COALESCE(f.kg_co2_per_kwh, 0), 3) AS emissions_kg
                FROM energy_reading e
                JOIN building b ON e.building_id = b.building_id
                LEFT JOIN reading_factor rf ON e.reading_id = rf.reading_id
                LEFT JOIN emission_factor f ON rf.factor_id = f.factor_id
                ORDER BY e.reading_date DESC, e.reading_id DESC;
            """)
            return cur.fetchall()
    finally:
        conn.close()


def add_energy_reading_with_factor(reading_id, building_id, reading_date, consumption_kwh):
    """
    Add an energy reading and automatically assign the latest applicable
    emission factor whose valid_from date <= reading_date.

    Both insertions into ENERGY_READING and READING_FACTOR are executed
    in a single database transaction. If no applicable factor exists,
    the transaction is not executed and a ValueError is raised.
    """
    if consumption_kwh < 0:
        raise ValueError("Electricity consumption (kWh) must be greater than or equal to zero.")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Step 1 & 2: Find latest applicable emission factor
            cur.execute("""
                SELECT factor_id, factor_name, valid_from
                FROM emission_factor
                WHERE valid_from <= %s
                ORDER BY valid_from DESC, factor_id DESC
                LIMIT 1;
            """, (reading_date,))
            factor_row = cur.fetchone()

            if not factor_row:
                raise ValueError(
                    f"No applicable emission factor found for date {reading_date}. "
                    f"Please add an emission factor with a 'Valid From' date on or before {reading_date}."
                )

            factor_id = factor_row[0]

            # Step 3: Insert into ENERGY_READING
            cur.execute("""
                INSERT INTO energy_reading (reading_id, building_id, reading_date, consumption_kwh)
                VALUES (%s, %s, %s, %s);
            """, (reading_id, building_id, reading_date, consumption_kwh))

            # Step 4: Insert factor assignment into READING_FACTOR
            cur.execute("""
                INSERT INTO reading_factor (reading_id, factor_id)
                VALUES (%s, %s);
            """, (reading_id, factor_id))

        conn.commit()
    except errors.UniqueViolation as uv:
        conn.rollback()
        err_msg = str(uv)
        if "energy_reading_building_id_reading_date_key" in err_msg or "reading_date" in err_msg:
            raise ValueError(
                f"A reading for this building on date {reading_date} already exists. "
                f"Duplicate readings on the same date are not allowed."
            )
        elif "energy_reading_pkey" in err_msg or "reading_id" in err_msg:
            raise ValueError(f"Reading ID {reading_id} already exists. Please choose a different ID.")
        else:
            raise ValueError(f"Unique constraint violation: {err_msg}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_energy_reading(reading_id, building_id, reading_date, consumption_kwh):
    """
    Update an existing energy reading and re-assign the applicable emission factor
    based on the reading_date.
    """
    if consumption_kwh < 0:
        raise ValueError("Electricity consumption (kWh) must be greater than or equal to zero.")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Find applicable factor for the updated date
            cur.execute("""
                SELECT factor_id
                FROM emission_factor
                WHERE valid_from <= %s
                ORDER BY valid_from DESC, factor_id DESC
                LIMIT 1;
            """, (reading_date,))
            factor_row = cur.fetchone()

            if not factor_row:
                raise ValueError(
                    f"No applicable emission factor found for date {reading_date}. "
                    f"An emission factor valid on or before {reading_date} is required."
                )

            factor_id = factor_row[0]

            # Update ENERGY_READING
            cur.execute("""
                UPDATE energy_reading
                SET building_id = %s,
                    reading_date = %s,
                    consumption_kwh = %s
                WHERE reading_id = %s;
            """, (building_id, reading_date, consumption_kwh, reading_id))

            # Update or insert into READING_FACTOR
            cur.execute("""
                INSERT INTO reading_factor (reading_id, factor_id)
                VALUES (%s, %s)
                ON CONFLICT (reading_id) DO UPDATE
                SET factor_id = EXCLUDED.factor_id;
            """, (reading_id, factor_id))

        conn.commit()
    except errors.UniqueViolation:
        conn.rollback()
        raise ValueError(f"A reading for this building on date {reading_date} already exists.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_energy_reading(reading_id):
    """
    Delete an energy reading. Deletes the corresponding record in READING_FACTOR
    first to respect the foreign key constraint.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Delete from reading_factor first
            cur.execute("DELETE FROM reading_factor WHERE reading_id = %s;", (reading_id,))
            # Delete from energy_reading
            cur.execute("DELETE FROM energy_reading WHERE reading_id = %s;", (reading_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =====================================================================
# MODULE 1 & 5: DASHBOARD & CARBON EMISSION CALCULATION OPERATIONS
# =====================================================================

def get_dashboard_summary_metrics():
    """
    Retrieve core KPIs for the dashboard:
    1. Total number of buildings (COUNT)
    2. Total electricity consumption in kWh (SUM)
    3. Total carbon emissions in kg CO2 (SUM with join)
    4. Average electricity consumption per reading in kWh (AVG)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Building count
            cur.execute("SELECT COUNT(*) FROM building;")
            total_buildings = cur.fetchone()[0] or 0

            # Total and average consumption
            cur.execute("""
                SELECT 
                    COALESCE(SUM(consumption_kwh), 0),
                    COALESCE(AVG(consumption_kwh), 0)
                FROM energy_reading;
            """)
            sum_row = cur.fetchone()
            total_kwh = float(sum_row[0] or 0.0)
            avg_kwh = float(sum_row[1] or 0.0)

            # Total carbon emissions calculated via SQL Join
            cur.execute("""
                SELECT COALESCE(SUM(e.consumption_kwh * f.kg_co2_per_kwh), 0)
                FROM energy_reading e
                JOIN reading_factor rf ON e.reading_id = rf.reading_id
                JOIN emission_factor f ON rf.factor_id = f.factor_id;
            """)
            total_emissions = float(cur.fetchone()[0] or 0.0)

            return {
                "total_buildings": total_buildings,
                "total_consumption_kwh": total_kwh,
                "total_emissions_kg": total_emissions,
                "avg_consumption_kwh": avg_kwh
            }
    finally:
        conn.close()


def get_building_consumption_breakdown():
    """
    Aggregate electricity consumption and carbon emissions grouped by building.
    Uses LEFT JOIN so buildings without readings are displayed with 0.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    b.building_name,
                    b.building_type,
                    COALESCE(SUM(e.consumption_kwh), 0) AS total_consumption_kwh,
                    COALESCE(SUM(e.consumption_kwh * f.kg_co2_per_kwh), 0) AS total_emissions_kg
                FROM building b
                LEFT JOIN energy_reading e ON b.building_id = e.building_id
                LEFT JOIN reading_factor rf ON e.reading_id = rf.reading_id
                LEFT JOIN emission_factor f ON rf.factor_id = f.factor_id
                GROUP BY b.building_id, b.building_name, b.building_type
                ORDER BY total_consumption_kwh DESC;
            """)
            rows = cur.fetchall()
            return pd.DataFrame(
                rows,
                columns=["Building Name", "Building Type", "Total Consumption (kWh)", "Total Emissions (kg CO2)"]
            )
    finally:
        conn.close()


def get_datewise_consumption_breakdown():
    """
    Aggregate electricity consumption and carbon emissions grouped by reading date.
    Ordered chronologically.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    e.reading_date,
                    SUM(e.consumption_kwh) AS total_kwh,
                    COALESCE(SUM(e.consumption_kwh * f.kg_co2_per_kwh), 0) AS total_emissions_kg
                FROM energy_reading e
                LEFT JOIN reading_factor rf ON e.reading_id = rf.reading_id
                LEFT JOIN emission_factor f ON rf.factor_id = f.factor_id
                GROUP BY e.reading_date
                ORDER BY e.reading_date ASC;
            """)
            rows = cur.fetchall()
            return pd.DataFrame(
                rows,
                columns=["Reading Date", "Total Consumption (kWh)", "Total Emissions (kg CO2)"]
            )
    finally:
        conn.close()


def get_detailed_carbon_emissions():
    """
    Module 5: Carbon Emission Calculation.
    Retrieves detailed records by joining BUILDING, ENERGY_READING,
    READING_FACTOR, and EMISSION_FACTOR.
    Calculates Carbon Emission (kg CO2) = Consumption (kWh) * Emission Factor.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    b.building_name,
                    b.building_type,
                    e.reading_date,
                    e.consumption_kwh,
                    f.factor_name,
                    f.kg_co2_per_kwh,
                    ROUND(e.consumption_kwh * f.kg_co2_per_kwh, 3) AS calculated_emissions_kg
                FROM building b
                JOIN energy_reading e ON b.building_id = e.building_id
                JOIN reading_factor rf ON e.reading_id = rf.reading_id
                JOIN emission_factor f ON rf.factor_id = f.factor_id
                ORDER BY e.reading_date DESC, b.building_name ASC;
            """)
            rows = cur.fetchall()
            return pd.DataFrame(
                rows,
                columns=[
                    "Building Name",
                    "Building Type",
                    "Reading Date",
                    "Consumption (kWh)",
                    "Factor Name",
                    "Emission Factor (kg CO2/kWh)",
                    "Calculated Emissions (kg CO2)"
                ]
            )
    finally:
        conn.close()


def get_buildingwise_carbon_emissions():
    """
    Module 5: Aggregate carbon emissions grouped by building.
    Uses SQL GROUP BY, SUM, AVG, and COUNT.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    b.building_name,
                    b.building_type,
                    COUNT(e.reading_id) AS total_readings,
                    ROUND(SUM(e.consumption_kwh), 2) AS total_consumption_kwh,
                    ROUND(AVG(e.consumption_kwh), 2) AS avg_consumption_kwh,
                    ROUND(SUM(e.consumption_kwh * f.kg_co2_per_kwh), 3) AS total_emissions_kg
                FROM building b
                JOIN energy_reading e ON b.building_id = e.building_id
                JOIN reading_factor rf ON e.reading_id = rf.reading_id
                JOIN emission_factor f ON rf.factor_id = f.factor_id
                GROUP BY b.building_id, b.building_name, b.building_type
                ORDER BY total_emissions_kg DESC;
            """)
            rows = cur.fetchall()
            return pd.DataFrame(
                rows,
                columns=[
                    "Building Name",
                    "Building Type",
                    "Total Readings",
                    "Total Consumption (kWh)",
                    "Avg Consumption (kWh)",
                    "Total Emissions (kg CO2)"
                ]
            )
    finally:
        conn.close()


def get_datewise_carbon_emissions():
    """
    Module 5: Aggregate carbon emissions grouped by date.
    Uses SQL GROUP BY, SUM, and COUNT.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    e.reading_date,
                    COUNT(e.reading_id) AS buildings_recorded,
                    ROUND(SUM(e.consumption_kwh), 2) AS total_consumption_kwh,
                    ROUND(SUM(e.consumption_kwh * f.kg_co2_per_kwh), 3) AS total_emissions_kg
                FROM energy_reading e
                JOIN reading_factor rf ON e.reading_id = rf.reading_id
                JOIN emission_factor f ON rf.factor_id = f.factor_id
                GROUP BY e.reading_date
                ORDER BY e.reading_date ASC;
            """)
            rows = cur.fetchall()
            return pd.DataFrame(
                rows,
                columns=[
                    "Reading Date",
                    "Buildings Recorded",
                    "Total Consumption (kWh)",
                    "Total Emissions (kg CO2)"
                ]
            )
    finally:
        conn.close()


# =====================================================================
# MODULE 6: REPORT GENERATION DATABASE OPERATIONS
# =====================================================================

def get_filtered_report_data(building_id=None, start_date=None, end_date=None):
    """
    Module 6: Report Generation.
    Filters energy and carbon records by building and date range.
    Parameters:
      building_id: int or None (if None, all buildings are included)
      start_date: date or None
      end_date: date or None
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT 
                    b.building_id,
                    b.building_name,
                    b.building_type,
                    b.location,
                    e.reading_date,
                    e.consumption_kwh,
                    f.factor_name,
                    f.kg_co2_per_kwh,
                    ROUND(e.consumption_kwh * f.kg_co2_per_kwh, 3) AS calculated_emissions_kg
                FROM building b
                JOIN energy_reading e ON b.building_id = e.building_id
                JOIN reading_factor rf ON e.reading_id = rf.reading_id
                JOIN emission_factor f ON rf.factor_id = f.factor_id
                WHERE (%s IS NULL OR b.building_id = %s)
                  AND (%s::date IS NULL OR e.reading_date >= %s)
                  AND (%s::date IS NULL OR e.reading_date <= %s)
                ORDER BY e.reading_date DESC, b.building_name ASC;
            """
            cur.execute(query, (building_id, building_id, start_date, start_date, end_date, end_date))
            rows = cur.fetchall()
            return pd.DataFrame(
                rows,
                columns=[
                    "Building ID",
                    "Building Name",
                    "Building Type",
                    "Location",
                    "Reading Date",
                    "Consumption (kWh)",
                    "Emission Factor Name",
                    "Emission Factor (kg CO2/kWh)",
                    "Calculated Emissions (kg CO2)"
                ]
            )
    finally:
        conn.close()


def get_min_max_reading_dates():
    """
    Retrieve the minimum and maximum reading dates available in ENERGY_READING.
    Returns (min_date, max_date).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT MIN(reading_date), MAX(reading_date) FROM energy_reading;")
            return cur.fetchone()
    finally:
        conn.close()
