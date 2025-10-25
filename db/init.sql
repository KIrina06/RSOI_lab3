-- Создаем отдельные базы данных для каждого сервиса
CREATE DATABASE cars_db;
CREATE DATABASE rental_db;
CREATE DATABASE payment_db;

-- База данных для Cars Service
\c cars_db;

CREATE TABLE IF NOT EXISTS cars
(
    id                  SERIAL PRIMARY KEY,
    car_uid             uuid UNIQUE NOT NULL,
    brand               VARCHAR(80) NOT NULL,
    model               VARCHAR(80) NOT NULL,
    registration_number VARCHAR(20) NOT NULL,
    power               INT,
    price               INT         NOT NULL,
    type                VARCHAR(20)
        CHECK (type IN ('SEDAN', 'SUV', 'MINIVAN', 'ROADSTER')),
    availability        BOOLEAN     NOT NULL
);

INSERT INTO cars (car_uid, brand, model, registration_number, power, price, type, availability) VALUES
('109b42f3-198d-4c89-9276-a7520a7120ab', 'Mercedes Benz', 'GLA 250', 'ЛО777Х799', 249, 3500, 'SEDAN', true),
('a7c6c5d4-3b3a-4d2e-8c1f-9b8a7b6c5d4e', 'BMW', 'X5', 'A123BC177', 300, 5000, 'SUV', true),
('b8d7e6f5-4c4b-5e3f-9d2e-8c1f0a9b8c7d', 'Toyota', 'Camry', 'B456DE777', 180, 2500, 'SEDAN', true)
ON CONFLICT (car_uid) DO NOTHING;

-- База данных для Rental Service
\c rental_db;

CREATE TABLE IF NOT EXISTS rental
(
    id          SERIAL PRIMARY KEY,
    rental_uid  uuid UNIQUE              NOT NULL,
    username    VARCHAR(80)              NOT NULL,
    payment_uid uuid                     NOT NULL,
    car_uid     uuid                     NOT NULL,
    date_from   TIMESTAMP WITH TIME ZONE NOT NULL,
    date_to     TIMESTAMP WITH TIME ZONE NOT NULL,
    status      VARCHAR(20)              NOT NULL
        CHECK (status IN ('IN_PROGRESS', 'FINISHED', 'CANCELED'))
);

-- База данных для Payment Service
\c payment_db;

CREATE TABLE IF NOT EXISTS payment
(
    id          SERIAL PRIMARY KEY,
    payment_uid uuid        NOT NULL,
    status      VARCHAR(20) NOT NULL
        CHECK (status IN ('PAID', 'CANCELED')),
    price       INT         NOT NULL
);