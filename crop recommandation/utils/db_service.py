"""
Database service for KrishiMitra AI.
Manages user authentication, past seasonal planting decisions,
and multi-season fertilizer history using SQLite.
"""

import os
import sqlite3
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

DB_PATH = "data/farm_database.db"

class DatabaseService:
    """Handles all persistent SQLite operations for users and farm histories."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns SQLite connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hashes password with PBKDF2-HMAC-SHA256 and unique salt."""
        if salt is None:
            salt = os.urandom(16).hex()
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()
        return pwd_hash, salt

    def _init_db(self):
        """Creates tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT NOT NULL,
                default_location TEXT DEFAULT 'Pune',
                phone TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. Planting decisions history table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS crop_planting_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                season_name TEXT NOT NULL,
                year INTEGER NOT NULL,
                crop_name TEXT NOT NULL,
                marathi_name TEXT DEFAULT '',
                category TEXT DEFAULT '',
                location TEXT DEFAULT '',
                soil_type TEXT DEFAULT '',
                ph REAL DEFAULT 7.0,
                n REAL DEFAULT 50.0,
                p REAL DEFAULT 40.0,
                k REAL DEFAULT 50.0,
                temperature REAL DEFAULT 26.0,
                rainfall REAL DEFAULT 100.0,
                fertilizers_applied TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            # 3. Past 3 seasons fertilizer history table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fertilizer_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                season_label TEXT NOT NULL,
                season_crop TEXT DEFAULT '',
                fertilizers_used TEXT DEFAULT '[]',
                intensity TEXT DEFAULT 'Standard/Balanced',
                organic_manure_used INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, season_label)
            );
            """)

            conn.commit()

        # Seed a demo account if database is fresh
        self._seed_demo_user()

    def _seed_demo_user(self):
        """Creates a sample demo farmer account with realistic historical data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = 'farmer_demo'")
            user = cursor.fetchone()
            if not user:
                pwd_hash, salt = self._hash_password("kisan123")
                cursor.execute("""
                INSERT INTO users (username, password_hash, salt, full_name, default_location, phone)
                VALUES (?, ?, ?, ?, ?, ?)
                """, ("farmer_demo", pwd_hash, salt, "Ramesh Patil", "Baramati (Pune)", "9876543210"))
                user_id = cursor.lastrowid

                # Seed sample past seasons for demonstration
                # Season 1: Kharif 2025 - Soybean
                cursor.execute("""
                INSERT INTO crop_planting_history 
                (user_id, season_name, year, crop_name, marathi_name, category, location, soil_type, ph, n, p, k, temperature, rainfall, fertilizers_applied, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, "Kharif 2025", 2025, "Soybean", "सोयाबीन", "Oilseed / Legume",
                    "Baramati (Pune)", "Medium Black (Vertisol)", 7.4, 45.0, 38.0, 60.0, 27.5, 120.0,
                    "DAP (50 kg/acre) + Rhizobium bio-fertilizer", "Good harvest; fixed residual atmospheric nitrogen in soil."
                ))

                # Season 2: Rabi 2025-26 - Wheat
                cursor.execute("""
                INSERT INTO crop_planting_history 
                (user_id, season_name, year, crop_name, marathi_name, category, location, soil_type, ph, n, p, k, temperature, rainfall, fertilizers_applied, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, "Rabi 2025-26", 2025, "Wheat", "गहू", "Cereal Food Grain",
                    "Baramati (Pune)", "Medium Black (Vertisol)", 7.4, 52.0, 35.0, 58.0, 22.0, 45.0,
                    "Urea split doses (2 bags/acre) + Single Super Phosphate (SSP)", "Rotated after Soybean legume bed."
                ))

                # Seed past 3 seasons fertilizer history
                sample_fert = [
                    ("Season -1 (Previous Season: Rabi 2025-26)", "Wheat", json.dumps(["Urea", "Single Super Phosphate (SSP)"]), "Standard/Balanced", 1),
                    ("Season -2 (Kharif 2025)", "Soybean", json.dumps(["DAP (Di-Ammonium Phosphate)", "Compost / Farmyard Manure (FYM)"]), "Standard/Balanced", 1),
                    ("Season -3 (Rabi 2024-25)", "Chickpea (Chana)", json.dumps(["Single Super Phosphate (SSP)", "Zinc Sulfate"]), "Low", 0),
                ]
                for s_label, s_crop, f_used, inten, org in sample_fert:
                    cursor.execute("""
                    INSERT INTO fertilizer_history (user_id, season_label, season_crop, fertilizers_used, intensity, organic_manure_used)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, s_label, s_crop, f_used, inten, org))

                conn.commit()

    # --- User Authentication Methods ---
    def register_user(self, username: str, password: str, full_name: str, default_location: str = "Pune", phone: str = "") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Registers a new farmer user account."""
        clean_user = username.strip().lower()
        if not clean_user or len(clean_user) < 3:
            return False, "Username must be at least 3 characters long.", None
        if not password or len(password) < 4:
            return False, "Password must be at least 4 characters long.", None
        if not full_name.strip():
            return False, "Please provide your Full Name.", None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (clean_user,))
            if cursor.fetchone():
                return False, f"Username '{clean_user}' is already registered. Please login.", None

            pwd_hash, salt = self._hash_password(password)
            cursor.execute("""
            INSERT INTO users (username, password_hash, salt, full_name, default_location, phone)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (clean_user, pwd_hash, salt, full_name.strip(), default_location.strip(), phone.strip()))
            user_id = cursor.lastrowid
            conn.commit()

            user_dict = {
                "id": user_id,
                "username": clean_user,
                "full_name": full_name.strip(),
                "default_location": default_location.strip(),
                "phone": phone.strip()
            }
            return True, "Registration successful! Welcome to KrishiMitra AI.", user_dict

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Authenticates an existing farmer user."""
        clean_user = username.strip().lower()
        if not clean_user or not password:
            return False, "Please enter both username and password.", None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (clean_user,))
            row = cursor.fetchone()
            if not row:
                return False, "User not found. Please register an account.", None

            stored_hash = row["password_hash"]
            salt = row["salt"]
            computed_hash, _ = self._hash_password(password, salt)

            if computed_hash == stored_hash:
                user_dict = {
                    "id": row["id"],
                    "username": row["username"],
                    "full_name": row["full_name"],
                    "default_location": row["default_location"],
                    "phone": row["phone"]
                }
                return True, f"Welcome back, {row['full_name']}!", user_dict
            else:
                return False, "Incorrect password. Please try again.", None

    # --- Crop Planting Decision Methods ---
    def save_planting_decision(
        self,
        user_id: int,
        season_name: str,
        year: int,
        crop_name: str,
        marathi_name: str = "",
        category: str = "",
        location: str = "",
        soil_type: str = "",
        ph: float = 7.0,
        n: float = 50.0,
        p: float = 40.0,
        k: float = 50.0,
        temperature: float = 26.0,
        rainfall: float = 100.0,
        fertilizers_applied: str = "",
        notes: str = ""
    ) -> int:
        """Saves the crop that the farmer has finally decided to plant for the season."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO crop_planting_history (
                user_id, season_name, year, crop_name, marathi_name, category,
                location, soil_type, ph, n, p, k, temperature, rainfall,
                fertilizers_applied, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, season_name, year, crop_name, marathi_name, category,
                location, soil_type, ph, n, p, k, temperature, rainfall,
                fertilizers_applied, notes
            ))
            record_id = cursor.lastrowid
            conn.commit()
            return record_id

    def get_user_planting_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Returns all past seasons of planted crops for the user, newest first."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM crop_planting_history 
            WHERE user_id = ? 
            ORDER BY planted_at DESC, id DESC
            """, (user_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def delete_planting_record(self, record_id: int, user_id: int) -> bool:
        """Deletes a specific planting history record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM crop_planting_history WHERE id = ? AND user_id = ?", (record_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    # --- Past 3 Seasons Fertilizer History Methods ---
    def save_fertilizer_season(
        self,
        user_id: int,
        season_label: str,
        season_crop: str,
        fertilizers_used: List[str],
        intensity: str = "Standard/Balanced",
        organic_manure_used: bool = False
    ) -> bool:
        """Saves or updates fertilizer usage for a given past season."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO fertilizer_history (user_id, season_label, season_crop, fertilizers_used, intensity, organic_manure_used, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, season_label) DO UPDATE SET
                season_crop = excluded.season_crop,
                fertilizers_used = excluded.fertilizers_used,
                intensity = excluded.intensity,
                organic_manure_used = excluded.organic_manure_used,
                updated_at = CURRENT_TIMESTAMP
            """, (
                user_id, season_label, season_crop,
                json.dumps(fertilizers_used), intensity, 1 if organic_manure_used else 0
            ))
            conn.commit()
            return True

    def get_user_fertilizer_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieves fertilizer usage history across past 3 seasons."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM fertilizer_history 
            WHERE user_id = ? 
            ORDER BY id ASC
            """, (user_id,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                try:
                    d["fertilizers_used"] = json.loads(d["fertilizers_used"])
                except Exception:
                    d["fertilizers_used"] = []
                results.append(d)
            return results
