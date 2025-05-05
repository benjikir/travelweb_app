from sqlalchemy import SQlalchemy


#SQLite database export


CREATE TABLE IF NOT EXISTS "Countries" (
    "country_id" INTEGER PRIMARY KEY NOT NULL,
    "country_code3" integer NOT NULL,
    "country" TEXT NOT NULL,
    "flag_url" TEXT NOT NULL,
    "currency" TEXT NOT NULL,
    "continent" TEXT,
    "capital" TEXT
);


-- Original schema: public
-- This is the user Table.
CREATE TABLE IF NOT EXISTS "Users" (
    "user_id" INTEGER PRIMARY KEY,
    "username" TEXT,
    "email" TEXT UNIQUE,
    "profile_url" TEXT,
    "created_at" TEXT
);


CREATE TABLE IF NOT EXISTS "Trips" (
    "trip_id" INTEGER PRIMARY KEY NOT NULL,
    "trip_name" TEXT,
    "user_id" integer,
    "country_id" integer,
    "startdate" TEXT,
    "enddate" TEXT
);


CREATE TABLE IF NOT EXISTS "User_countries" (
    "user_id" INTEGER PRIMARY KEY NOT NULL,
    "country_id" integer
);


-- Original schema: public
CREATE TABLE IF NOT EXISTS "Locations" (
    "location_id" INTEGER PRIMARY KEY,
    "loc_name" TEXT,
    "user_id" integer,
    "country_id" integer,
    "image_url" TEXT
);


-- Foreign key constraints
-- Note: SQLite requires foreign_keys pragma to be enabled:
-- PRAGMA foreign_keys = ON;

-- ALTER TABLE "Countries" ADD CONSTRAINT "fk_Countries_country_id" FOREIGN KEY("country_id") REFERENCES "Trips"("country_id");
-- ALTER TABLE "Locations" ADD CONSTRAINT "fk_Locations_country_id" FOREIGN KEY("country_id") REFERENCES "Countries"("country_id");
-- ALTER TABLE "Locations" ADD CONSTRAINT "fk_Locations_user_id" FOREIGN KEY("user_id") REFERENCES "Users"("user_id");
-- ALTER TABLE "Trips" ADD CONSTRAINT "fk_Trips_user_id" FOREIGN KEY("user_id") REFERENCES "Users"("user_id");
-- ALTER TABLE "User_countries" ADD CONSTRAINT "fk_User_countries_country_id" FOREIGN KEY("country_id") REFERENCES "Countries"("country_id");
-- ALTER TABLE "User_countries" ADD CONSTRAINT "fk_User_countries_user_id" FOREIGN KEY("user_id") REFERENCES "Users"("user_id");


