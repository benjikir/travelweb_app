
import json
import sqlite3
import pycountry  # To convert 2-letter to 3-letter codes
import os

DATABASE_NAME = 'travel_webapp.sqlite'  # Make sure this matches your db.py and init_db.py
JSON_FILE_PATH = 'countries_data.json'  # Path to your JSON file


def seed_database():
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: JSON data file not found at {JSON_FILE_PATH}")
        return

    if not os.path.exists(DATABASE_NAME):
        print(f"Error: Database file not found at {DATABASE_NAME}. Please run init_db.py first.")
        return

    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return
    except FileNotFoundError:
        print(f"Error: {JSON_FILE_PATH} not found.")
        return

    countries_to_insert = data.get("countries", {}).get("country", [])

    if not countries_to_insert:
        print("No country data found in the JSON file.")
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # Ensure foreign key support is on if relevant for other operations, though not directly for this insert
    cursor.execute("PRAGMA foreign_keys = ON;")

    inserted_count = 0
    skipped_count = 0
    error_count = 0

    print(f"Starting to seed {len(countries_to_insert)} countries...")

    for country_data in countries_to_insert:
        country_code_alpha2 = country_data.get("countryCode")
        country_name = country_data.get("countryName")
        currency_code = country_data.get("currencyCode")
        # population = country_data.get("population") # Your DB schema doesn't have population
        capital = country_data.get("capital")
        continent_name = country_data.get("continentName")
        # flag_url is not in your JSON, so it will be NULL or default if your table defines it

        if not country_code_alpha2 or not country_name:
            print(f"Skipping entry due to missing countryCode or countryName: {country_data}")
            error_count += 1
            continue

        # Convert 2-letter code to 3-letter code using pycountry
        country_code_alpha3 = None
        try:
            country_obj = pycountry.countries.get(alpha_2=country_code_alpha2)
            if country_obj:
                country_code_alpha3 = country_obj.alpha_3
            else:
                # Some codes in your list might be special or not standard ISO 3166-1 alpha-2
                # For example, 'AX' (Åland Islands) is officially under Finland for some purposes
                # but pycountry has it. 'XK' (Kosovo) is user-assigned.
                # If pycountry doesn't find it, we might have to skip or handle it.
                # As a fallback, try to use the name if code is problematic for lookup
                try:
                    country_obj_by_name = pycountry.countries.search_fuzzy(country_name)[0]
                    country_code_alpha3 = country_obj_by_name.alpha_3
                    print(
                        f"Note: Used fuzzy name search for '{country_name}' (Code: {country_code_alpha2}), found alpha_3: {country_code_alpha3}")
                except (LookupError, IndexError):
                    print(
                        f"Warning: Could not find a 3-letter code for {country_name} (Code: {country_code_alpha2}). Skipping.")
                    error_count += 1
                    continue
        except Exception as e:
            print(f"Error looking up country code {country_code_alpha2} for {country_name}: {e}. Skipping.")
            error_count += 1
            continue

        if not country_code_alpha3:  # Double check after attempts
            print(f"Still no alpha_3 for {country_name}. Skipping.")
            error_count += 1
            continue

        # Check if country_code3 already exists to prevent duplicates from this script
        # Your DB UNIQUE constraint is the ultimate guard.
        cursor.execute("SELECT country_id FROM Countries WHERE country_code3 = ?", (country_code_alpha3,))
        if cursor.fetchone():
            # print(f"Skipping {country_name} ({country_code_alpha3}) - code already exists.")
            skipped_count += 1
            continue

        # Optionally, check by name too if names should also be unique from this seed
        cursor.execute("SELECT country_id FROM Countries WHERE LOWER(country) = ?", (country_name.lower(),))
        if cursor.fetchone():
            # print(f"Skipping {country_name} ({country_code_alpha3}) - name already exists.")
            skipped_count += 1
            continue

        try:
            cursor.execute("""
                INSERT INTO Countries (country_code3, country, currency, capital, continent, flag_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (country_code_alpha3, country_name, currency_code, capital, continent_name,
                  None))  # Assuming no flag_url in JSON
            inserted_count += 1
        except sqlite3.IntegrityError as e:
            # This would catch DB-level UNIQUE constraint violations if not caught by above checks
            print(f"Skipping {country_name} ({country_code_alpha3}) due to database integrity error: {e}")
            skipped_count += 1
        except Exception as e:
            print(f"An unexpected error occurred for {country_name}: {e}")
            error_count += 1

    conn.commit()
    conn.close()

    print("\n--- Seeding Summary ---")
    print(f"Successfully inserted: {inserted_count} countries.")
    print(f"Skipped (already exist or data issue): {skipped_count} countries.")
    print(f"Errors (could not process): {error_count} countries.")
    print("Database seeding process completed.")


if __name__ == '__main__':
    seed_database()