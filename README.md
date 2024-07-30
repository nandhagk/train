# Railways Maintenance Scheduling System

Project aims to develop a software prototype to automate the scheduling of six-monthly maintenance activities for the Southern Railways.
The system will allocate maintenance tasks to appropriate time slots in the railway timetable, ensuring efficient use of available maintenance windows and adherence to scheduling constraints.

## Setup

### Requirements

- python >= 3.12 (To run the server)
- pip (To install additional dependencies)

### Download the source code:

`git clone https://github.com/nandhagk/train.git`

### Install dependencies

`pip install -r requirements.txt`

### Initialize data

**NOTE**: This data has been scraped from what documents we were provided, it doesn't contain the full dataset!

```
cd src
python -m train init data/mas_sections.json
python -m train create-windows data/slots.dat 180 --clear
```

### Run server

```
python -m train
```

Navigate to localhost:5432 and fill in the input data file

**NOTE**: This is similar to using the schedule command in the cli

## Supported Format for the Input

- We support both .csv and .xlsx files
- We expect the exact same headers provided in the excel file provided to us
- (We also support a simpler format which only takes in the required headers, refer to file_management.py to learn more)
