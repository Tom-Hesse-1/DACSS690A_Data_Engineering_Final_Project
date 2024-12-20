# -*- coding: utf-8 -*-

#fetching data from ADOT API
import requests
import sqlite3
import pandas as pd
from IPython.display import display
import uuid
import prefect
from prefect import flow
from prefect.tasks import task

api_key = "0b6432bf7c364303815ecfa236907291"

@task
def fetch_data(endpoint, api_key):
  url = f'https://az511.com/api/v2/get/{endpoint}?key={api_key}'
  response = requests.get(url)
  return response.json()
  pass

@flow
def fetch_flow(api_key):
  cameras_data = fetch_data('cameras', api_key)
  weather_stations_data = fetch_data('weatherstations', api_key)
  message_boards_data = fetch_data('messagesigns', api_key)
  events_data = fetch_data('event', api_key)
  alerts_data = fetch_data('alerts', api_key)
  return cameras_data, weather_stations_data, message_boards_data, events_data, alerts_data
  pass

conn = sqlite3.connect(str(uuid.uuid4()) + '.db')
cursor = conn.cursor()

@task
def create_cameras_table(cursor):
    create_cameras_table_sql = '''
    CREATE TABLE IF NOT EXISTS cameras (
      id INTEGER PRIMARY KEY,
      source TEXT,
      roadway TEXT,
      direction TEXT,
      latitude DOUBLE,
      longitude DOUBLE,
      location TEXT,
      views TEXT
    );
    '''
    cursor.execute(create_cameras_table_sql)
    pass

@task
def create_weather_stations_table(cursor):
    create_weather_stations_table_sql = '''
    CREATE TABLE IF NOT EXISTS weather_stations (
      id INTEGER PRIMARY KEY,
      cameraID TEXT,
      latitude REAL,
      longitude REAL,
      airTemperature TEXT,
      surfaceTemperature TEXT,
      windSpeed TEXT,
      windDirection TEXT,
      relativeHumidity TEXT,
      levelOfGrip TEXT,
      maxWindSpeed TEXT,
      lastUpdated TEXT
    );
    '''
    cursor.execute(create_weather_stations_table_sql)
    pass

@task
def create_message_boards_table(cursor):
    create_message_boards_table_sql = '''
    CREATE TABLE IF NOT EXISTS message_boards (
      id TEXT PRIMARY KEY,
      name TEXT,
      roadway TEXT,
      directionOfTravel TEXT,
      messages TEXT,
      latitude TEXT,
      longitude TEXT,
      lastUpdated INTEGER
    );
    '''
    cursor.execute(create_message_boards_table_sql)
    pass

@task
def create_events_table(cursor):
    create_events_table_sql = '''
    CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY not null on conflict ignore,
      organization TEXT,
      roadwayName TEXT,
      directionOfTravel TEXT,
      description TEXT,
      reported INTEGER,
      lastUpdated INTEGER,
      startDate INTEGER,
      plannedEndDate INTEGER,
      lanesAffected TEXT,
      latitude REAL,
      longitude REAL,
      latitudeSecondary REAL,
      longitudeSecondary REAL,
      eventType TEXT,
      eventSubType TEXT,
      isFullClosure INTEGER,
      severity TEXT,
      encodedPolyline TEXT,
      restrictions TEXT,
      detourPolyline TEXT,
      detourInstructions TEXT,
      recurrence TEXT,
      recurrenceSchedules TEXT,
      details TEXT,
      laneCount INTEGER
    );
    '''
    cursor.execute(create_events_table_sql)
    pass

@task
def create_alerts_table(cursor):
    create_alerts_table_sql = '''
    CREATE TABLE IF NOT EXISTS alerts (
      id INTEGER PRIMARY KEY,
      message TEXT,
      notes TEXT,
      startTime INTEGER,
      endTime INTEGER,
      regions TEXT,
      highImportance INTEGER,
      sendNotification INTEGER
    );
    '''
    cursor.execute(create_alerts_table_sql)
    pass

@task
def commit_changes(conn):
    conn.commit()
    pass

# Flow to execute the entire process
@flow
def setup_database():
    create_cameras_table(cursor)
    create_weather_stations_table(cursor)
    create_message_boards_table(cursor)
    create_events_table(cursor)
    create_alerts_table(cursor)

    commit_changes(conn)
    return conn
    pass

#loading cameras table
@task
def insert_cameras(data):
  for camera in data:
    cursor.execute("""
    INSERT OR IGNORE INTO cameras (id, source, roadway, direction, latitude, longitude, location, views)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (int(camera['Id']),
          camera['Source'],
          camera['Roadway'],
          camera['Direction'],
          camera['Latitude'],
          camera['Longitude'],
          str(camera['Location']),
          str(camera['Views'])))
  conn.commit()
  pass

#loading weather stations table
@task
def insert_weather_stations(data):
  for weather_station in data:
    cursor.execute("""
    INSERT OR IGNORE INTO weather_stations (Id, CameraID, Latitude, Longitude, AirTemperature, SurfaceTemperature, WindSpeed, WindDirection, RelativeHumidity, LevelOfGrip, MaxWindSpeed, LastUpdated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (int(weather_station['Id']),
          weather_station['CameraId'],
          weather_station['Latitude'],
          weather_station['Longitude'],
          weather_station['AirTemperature'],
          weather_station['SurfaceTemperature'],
          weather_station['WindSpeed'],
          weather_station['WindDirection'],
          weather_station['RelativeHumidity'],
          weather_station['LevelOfGrip'],
          weather_station['MaxWindSpeed'],
          weather_station['LastUpdated']))
    conn.commit()
  pass

#Loading Message Boards Data
@task
def insert_message_boards(data):
  for message_board in data:
    cursor.execute("""
    INSERT OR IGNORE INTO message_boards (Id, Name, Roadway, DirectionOfTravel, Messages, Latitude, Longitude, LastUpdated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (message_board['Id'],
          message_board['Name'],
          message_board['Roadway'],
          message_board['DirectionOfTravel'],
          str(message_board['Messages']),
          message_board['Latitude'],
          message_board['Longitude'],
          message_board['LastUpdated']))
    conn.commit()
  pass

#Loading Events Table
@task
def insert_events(data):
  for event in data:
      cursor.execute("""
      INSERT OR IGNORE INTO events (ID, Organization, RoadwayName, DirectionOfTravel, Description, Reported, LastUpdated, StartDate, PlannedEndDate, LanesAffected, Latitude, Longitude, LatitudeSecondary, LongitudeSecondary, EventType, EventSubType, IsFullClosure, Severity, EncodedPolyline, Restrictions, DetourPolyline, DetourInstructions, Recurrence, RecurrenceSchedules, Details, LaneCount)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """, (int(event['ID']),
            str(event['Organization']),
            str(event['RoadwayName']),
            str(event['DirectionOfTravel']),
            str(event['Description']),
            int(event['Reported']),
            int(event['LastUpdated']),
            int(event['StartDate']),
            str(event['PlannedEndDate']),
            str(event['LanesAffected']),
            event['Latitude'],
            event['Longitude'],
            event['LatitudeSecondary'],
            event['LongitudeSecondary'],
            event['EventType'],
            event['EventSubType'],
            int(event['IsFullClosure']),
            event['Severity'],
            event['EncodedPolyline'],
            str(event['Restrictions']),
            event['DetourPolyline'],
            str(event['DetourInstructions']),
            str(event['Recurrence']),
            str(event['RecurrenceSchedules']),
            event['Details'],
            str(event['LaneCount'])))
      conn.commit()
  pass

#Alerts Data table empty, no need to load

#Create unique messages table

@task
def create_unique_messages_table(cursor):
    create_unique_messages_table_sql = '''
    CREATE TABLE IF NOT EXISTS unique_messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      unique_message TEXT UNIQUE NOT NULL,
      message_count INTEGER NOT NULL
    );
    '''
    cursor.execute(create_unique_messages_table_sql)
    pass

#Query unique messages w/ counts from messages table

@task
def get_unique_messages():
  cursor.execute("""
  SELECT Messages, COUNT(*) as message_count
  FROM message_boards
  GROUP BY Messages;
  """)
  unique_messages_data = cursor.fetchall()
  return unique_messages_data
  plain_serializer_function_ser_schema

#Insert query ran above into unique_messages table
@task
def insert_unique_messages(unique_messages_data):
  for message, count in unique_messages_data:
    cursor.execute("""
    INSERT OR IGNORE INTO unique_messages (unique_message, message_count)
    VALUES (?,?);
    """, (message, count))
  pass

conn.commit()

#Create Unique_events table

@task
def create_unique_event_types_table(cursor):
  create_unique_event_types_table_sql = '''
  CREATE TABLE IF NOT EXISTS unique_event_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unique_event_type TEXT UNIQUE NOT NULL,
    event_type INTEGER NOT NULL
  );
  '''
  cursor.execute(create_unique_event_types_table_sql)
  pass

#Query unique events from events table
@task
def get_unique_event_types():
  cursor.execute("""
  SELECT EventType,
  COUNT(*) as event_type_count
  FROM events
  GROUP BY EventType;
  """)
  unique_events_data = cursor.fetchall()
  return unique_events_data
  pass

#Insert queried data into newly formed Unique_events table
@task
def insert_unique_event_types(unique_events_data):
  for event_type, count in unique_events_data:
    cursor.execute("""
    INSERT OR IGNORE INTO unique_event_types (unique_event_type, event_type)
    VALUES (?,?);
    """, (str(event_type), count))
    pass

conn.commit()

#Defining Main ETL Flow

@flow(name="ETL Flow")
def etl_flow():

  setup_database()

  cameras_data, weather_stations_data, message_boards_data, events_data, alerts_data = fetch_flow(api_key)

  insert_cameras(cameras_data)
  print("Cameras data inserted successfully.")

  insert_weather_stations(weather_stations_data)
  print("Weather stations data inserted successfully.")

  insert_message_boards(message_boards_data)
  print("Message boards data inserted successfully.")

  insert_events(events_data)
  print("Events data inserted successfully.")

  create_unique_messages_table(cursor)
  unique_messages_data = get_unique_messages()
  insert_unique_messages(unique_messages_data)

  create_unique_event_types_table(cursor)
  unique_events_data = get_unique_event_types()
  insert_unique_event_types(unique_events_data)

if __name__ == "__main__":
    etl_flow()

if __name__ == "__main__":
    etl_flow.serve(name="etl_deployment")
