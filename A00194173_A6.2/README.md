# A6.2 – Hotel Reservation System

## Run
python Source/app.py <input_path>

## Lint
flake8 Source
pylint Source

## Unit Tests
python -m unittest discover Test/Unit

## Coverage
coverage run -m unittest discover Test/Unit
coverage report