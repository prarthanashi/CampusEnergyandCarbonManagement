"""
database.py
-----------
Centralized PostgreSQL connection and SQL operations for the
Campus Energy & Carbon Management System.

Current schema:
BUILDING, ENERGY_READING, EMISSION_SOURCE, EMISSION_FACTOR, ACTIVITY

Electricity readings are tracked separately from direct carbon emissions.
Carbon emissions are calculated only from ACTIVITY records:
quantity * emission_factor.factor_value.
"""

import streamlit as st
import psycopg2
import pandas as pd
from psycopg2 import errors


# ---------------------------------------------------------------------
# CONNECTION
# ---------------------------------------------------------------------

def get_connection():
    """Connect to PostgreSQL using .streamlit/secrets.toml."""
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        port=st.secrets["postgres"]["port"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"]
    )


def test_connection():
    """Return (True, message) if the database connection works."""
    try:
        conn = get_connection()
        conn.close()
        return True, "Database connected successfully!"
    except Exception as exc:
        return False, str(exc)


# ---------------------------------------------------------------------
# BUILDING MANAGEMENT
# ---------------------------------------------------------------------

def get_next_building_id():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(building_id), 100) + 1 FROM building;"
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def get_all_buildings():
    """Return (building_id, building_name, building_type)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT building_id, building_name, building_type
                FROM building
                ORDER BY building_id;
            """)
            return cur.fetchall()
    finally:
        conn.close()


def add_building(building_id, name, building_type):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO building (building_id, building_name, building_type)
                VALUES (%s, %s, %s);
            """, (building_id, name, building_type))
        conn.commit()
    except errors.UniqueViolation:
        conn.rollback()
        raise ValueError("That building ID or building name already exists.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_building(building_id, name, building_type):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE building
                SET building_name = %s, building_type = %s
                WHERE building_id = %s;
            """, (name, building_type, building_id))
            if cur.rowcount == 0:
                raise ValueError("The selected building no longer exists.")
        conn.commit()
    except errors.UniqueViolation:
        conn.rollback()
        raise ValueError("That building name is already in use.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_building(building_id):
    """The foreign keys prevent deletion when readings or activities exist."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM building WHERE building_id = %s;",
                (building_id,)
            )
        conn.commit()
    except errors.ForeignKeyViolation:
        conn.rollback()
        raise ValueError(
            "This building has energy readings or activities. "
            "Delete those records first."
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------
# ELECTRICITY CONSUMPTION MONITORING
# ---------------------------------------------------------------------

def get_next_reading_id():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(reading_id), 200) + 1 FROM energy_reading;"
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def get_all_energy_readings():
    """
    Return rows in this order:
    reading_id, building_id, building_name, building_type,
    reading_date, consumption_kwh.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.reading_id, b.building_id, b.building_name,
                       b.building_type, e.reading_date, e.consumption_kwh
                FROM energy_reading e
                JOIN building b ON b.building_id = e.building_id
                ORDER BY e.reading_date DESC, e.reading_id DESC;
            """)
            return cur.fetchall()
    finally:
        conn.close()


def add_energy_reading(reading_id, building_id, reading_date, consumption_kwh):
    if consumption_kwh < 0:
        raise ValueError("Electricity consumption cannot be negative.")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO energy_reading
                    (reading_id, building_id, reading_date, consumption_kwh)
                VALUES (%s, %s, %s, %s);
            """, (reading_id, building_id, reading_date, consumption_kwh))
        conn.commit()
    except errors.UniqueViolation:
        conn.rollback()
        raise ValueError(
            "This reading ID or building/date combination already exists."
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_energy_reading(reading_id, building_id, reading_date,
                          consumption_kwh):
    if consumption_kwh < 0:
        raise ValueError("Electricity consumption cannot be negative.")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE energy_reading
                SET building_id = %s, reading_date = %s,
                    consumption_kwh = %s
                WHERE reading_id = %s;
            """, (building_id, reading_date, consumption_kwh, reading_id))
            if cur.rowcount == 0:
                raise ValueError("The selected reading no longer exists.")
        conn.commit()
    except errors.UniqueViolation:
        conn.rollback()
        raise ValueError(
            "This building already has a reading for that date."
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_energy_reading(reading_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM energy_reading WHERE reading_id = %s;",
                (reading_id,)
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------
# EMISSION SOURCES AND STATIC EMISSION FACTORS
# ---------------------------------------------------------------------

def get_emission_sources_with_factors():
    """
    Return source_id, source_name, measurement_unit, factor_id,
    factor_value and factor_unit for the read-only factor table.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.source_id, s.source_name, s.measurement_unit,
                       f.factor_id, f.factor_value, f.factor_unit
                FROM emission_source s
                JOIN emission_factor f ON f.source_id = s.source_id
                ORDER BY s.source_id;
            """)
            return cur.fetchall()
    finally:
        conn.close()


# Alias for pages that use the shorter function name.
def get_all_emission_sources_with_factors():
    return get_emission_sources_with_factors()


# ---------------------------------------------------------------------
# ACTIVITY ENTRY AND CARBON EMISSION CALCULATION
# ---------------------------------------------------------------------

def get_next_activity_id():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(activity_id), 500) + 1 FROM activity;"
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def add_activity(activity_id, building_id, source_id,
                 activity_date, quantity, factor_id):
    """Insert an activity after checking that its factor belongs to its source."""
    if quantity < 0:
        raise ValueError("Activity quantity cannot be negative.")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM emission_factor
                WHERE factor_id = %s AND source_id = %s;
            """, (factor_id, source_id))
            if cur.fetchone() is None:
                raise ValueError(
                    "The selected emission factor does not belong to this source."
                )

            cur.execute("""
                INSERT INTO activity
                    (activity_id, building_id, source_id,
                     activity_date, quantity, factor_id)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                activity_id, building_id, source_id,
                activity_date, quantity, factor_id
            ))
        conn.commit()
    except errors.UniqueViolation:
        conn.rollback()
        raise ValueError("That activity ID already exists.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_activity(activity_id, building_id, source_id,
                    activity_date, quantity, factor_id):
    if quantity < 0:
        raise ValueError("Activity quantity cannot be negative.")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM emission_factor
                WHERE factor_id = %s AND source_id = %s;
            """, (factor_id, source_id))
            if cur.fetchone() is None:
                raise ValueError(
                    "The selected emission factor does not belong to this source."
                )

            cur.execute("""
                UPDATE activity
                SET building_id = %s, source_id = %s, activity_date = %s,
                    quantity = %s, factor_id = %s
                WHERE activity_id = %s;
            """, (
                building_id, source_id, activity_date,
                quantity, factor_id, activity_id
            ))
            if cur.rowcount == 0:
                raise ValueError("The selected activity no longer exists.")
        conn.commit()
    except errors.UniqueViolation:
        conn.rollback()
        raise ValueError("That activity conflicts with an existing record.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_activity(activity_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM activity WHERE activity_id = %s;",
                (activity_id,)
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_all_activities_with_emissions():
    """
    Return a DataFrame containing activity details and calculated emissions.
    Emissions = quantity * factor_value.
    """
    conn = get_connection()
    try:
        query = """
            SELECT a.activity_id, a.building_id, a.source_id, a.factor_id,
                   b.building_name, s.source_name,
                   a.activity_date, a.quantity, s.measurement_unit,
                   f.factor_value, f.factor_unit,
                   ROUND((a.quantity * f.factor_value)::numeric, 3)
                       AS calculated_emissions
            FROM activity a
            JOIN building b ON b.building_id = a.building_id
            JOIN emission_source s ON s.source_id = a.source_id
            JOIN emission_factor f ON f.factor_id = a.factor_id
            ORDER BY a.activity_date DESC, a.activity_id DESC;
        """
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------
# DASHBOARD / REPORT GENERATION
# ---------------------------------------------------------------------

def get_building_consumption_breakdown():
    """
    Return each building's electricity consumption and direct emissions.
    The two totals are aggregated separately to avoid multiplying rows
    when a building has several electricity readings and activities.
    """
    conn = get_connection()
    try:
        query = """
            WITH energy_totals AS (
                SELECT building_id, SUM(consumption_kwh) AS total_kwh
                FROM energy_reading
                GROUP BY building_id
            ),
            emission_totals AS (
                SELECT a.building_id,
                       SUM(a.quantity * f.factor_value) AS total_emissions
                FROM activity a
                JOIN emission_factor f ON f.factor_id = a.factor_id
                GROUP BY a.building_id
            )
            SELECT b.building_name, b.building_type,
                   COALESCE(e.total_kwh, 0) AS total_consumption_kwh,
                   COALESCE(c.total_emissions, 0) AS total_emissions_kg
            FROM building b
            LEFT JOIN energy_totals e ON e.building_id = b.building_id
            LEFT JOIN emission_totals c ON c.building_id = b.building_id
            ORDER BY total_consumption_kwh DESC;
        """
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


def get_monthly_dashboard_data():
    """Return monthly electricity totals and direct emissions totals."""
    conn = get_connection()
    try:
        query = """
            WITH monthly_energy AS (
                SELECT DATE_TRUNC('month', reading_date)::date AS month,
                       SUM(consumption_kwh) AS total_consumption
                FROM energy_reading
                GROUP BY DATE_TRUNC('month', reading_date)
            ),
            monthly_emissions AS (
                SELECT DATE_TRUNC('month', a.activity_date)::date AS month,
                       SUM(a.quantity * f.factor_value) AS total_emissions
                FROM activity a
                JOIN emission_factor f ON f.factor_id = a.factor_id
                GROUP BY DATE_TRUNC('month', a.activity_date)
            )
            SELECT COALESCE(e.month, c.month) AS month,
                   COALESCE(e.total_consumption, 0) AS total_consumption_kwh,
                   COALESCE(c.total_emissions, 0) AS total_emissions_kg
            FROM monthly_energy e
            FULL OUTER JOIN monthly_emissions c ON e.month = c.month
            ORDER BY month;
        """
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


# Backward-compatible name if the dashboard page still imports this function.
def get_datewise_consumption_breakdown():
    return get_monthly_dashboard_data()


def get_dashboard_summary_metrics():
    """Return simple totals if another page still needs these metrics."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM building;")
            total_buildings = cur.fetchone()[0]

            cur.execute("""
                SELECT COALESCE(SUM(consumption_kwh), 0),
                       COALESCE(AVG(consumption_kwh), 0)
                FROM energy_reading;
            """)
            total_kwh, average_kwh = cur.fetchone()

            cur.execute("""
                SELECT COALESCE(SUM(a.quantity * f.factor_value), 0)
                FROM activity a
                JOIN emission_factor f ON f.factor_id = a.factor_id;
            """)
            total_emissions = cur.fetchone()[0]

            return {
                "total_buildings": total_buildings,
                "total_consumption_kwh": float(total_kwh or 0),
                "avg_consumption_kwh": float(average_kwh or 0),
                "total_emissions_kg": float(total_emissions or 0)
            }
    finally:
        conn.close()
