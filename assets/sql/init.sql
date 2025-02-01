-- init.sql
DO $$ 
BEGIN
    -- Create role if doesn't exist
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${POSTGRES_ROLE}') THEN
        CREATE ROLE ${POSTGRES_ROLE} WITH LOGIN PASSWORD '${POSTGRES_PWD}';
    END IF;
END
$$;

-- Grant privileges
ALTER ROLE ${POSTGRES_ROLE} WITH SUPERUSER;

-- Create tables
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    address_id INT,
    name VARCHAR(100),
    surname VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    photo_path VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS addresses (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100),
    postal_code VARCHAR(10),
    street_and_house_number VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS searches (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    name VARCHAR(150),
    location VARCHAR(100),
    property_types VARCHAR(50)[],
    rent_types VARCHAR(50)[],
    date_range_start DATE,
    date_range_end DATE,
    districts VARCHAR(50)[],
    min_price INT CHECK (min_price >= 0),
    max_price INT CHECK (max_price >= 0),
    min_size INT CHECK (min_size >= 0),
    max_size INT CHECK (max_size >= 0),
    wg_types VARCHAR(50)[],
    gender_preference VARCHAR(10) DEFAULT 'egal',
    smoking_preference VARCHAR(10) DEFAULT 'egal',
    age_min INT CHECK (age_min >= 0),
    age_max INT CHECK (age_max >= 0),
    only_with_images BOOLEAN DEFAULT FALSE,
    exclude_contacted_ads BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    total_found INT DEFAULT 0,
    new_listings INT DEFAULT 0,
    last_run TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS individual_listings (
    id SERIAL PRIMARY KEY,
    search_config_id INT REFERENCES searches(id),
    listing_id VARCHAR(100) UNIQUE,
    listing_title VARCHAR(255),
    listing_url VARCHAR(255),
    location VARCHAR(255),
    price INT CHECK (price >= 0),
    size INT CHECK (size >= 0),
    rental_start_date DATE,
    deposit INT CHECK (deposit >= 0) DEFAULT 0,
    utilities INT CHECK (utilities >= 0) DEFAULT 0,
    other_costs INT CHECK (other_costs >= 0) DEFAULT 0,
    buyout INT CHECK (buyout >= 0) DEFAULT 0,
    schufa_required BOOLEAN DEFAULT FALSE,
    availability_status VARCHAR(100) DEFAULT 'Unknown',
    online_since VARCHAR(100) DEFAULT 'Unknown',
    location_details TEXT DEFAULT NULL,
    room_details TEXT DEFAULT NULL,
    flat_life_details TEXT DEFAULT NULL,
    contacted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key constraints
ALTER TABLE users 
ADD CONSTRAINT fk_address 
FOREIGN KEY (address_id) 
REFERENCES addresses(id);

-- Grant permissions to role
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${POSTGRES_ROLE};
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ${POSTGRES_ROLE};