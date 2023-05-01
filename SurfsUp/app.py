# Import the dependencies.
import datetime as dt
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///SurfsUp/Resources/hawaii.sqlite", echo=False)
metadata = MetaData()

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect = True)


# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB


#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
      """List all available api routes."""
      
      return (
        f"Welcome to the Hawaii Climate API Analysis! <br/>"  
        f"Available Routes:<br/>"
        f"Precipitation: /api/v1.0/precipitation<br/>"
        f"List of Stations: /api/v1.0/stations<br/>"
        f"Temperature for one year: /api/v1.0/tobs<br/>"
        f"Temperature start date(yyyy-mm-dd): /api/v1.0/yyyy-mm-dd<br/>"
        f"Temperature start to end dates(yyyy-mm-dd): /api/v1.0/yyyy-mm-dd/yyyy-mm-dd"
    )
      
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last year"""
    session = Session(engine)
    # Finding most recent date in the data set.
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
    most_recent_date
    # Calculating date one year from the last date in data set.
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    one_year_ago.date()
    # Querying to retrieve the data and precipitation scores
    results = session.query(Measurement.date, Measurement.prcp).\
    filter(Measurement.date >= one_year_ago.date()).all()
    # Dict with date as the key and prcp as the value
    last_year_precipitation = []
    for result in results:
        precipitation_dict = {}
        precipitation_dict[result.date] = result.prcp
        last_year_precipitation.append(precipitation_dict)

    session.close()

    return jsonify(last_year_precipitation)  

@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations."""

    session = Session(engine)
    results = session.query(Station.name).all()
    # Unraveling results into a 1D array and convert to a list
    station_count_list = list(np.ravel(results))

    session.close()

    return jsonify(station_count_list)   

@app.route("/api/v1.0/tobs")
def temp_monthly():
    """Returning temperature observations (tobs) for previous year."""

    session = Session(engine)
    # Finding most recent date in the data set.
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
    most_recent_date
    # Calculating date one year from the last date in data set.
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    one_year_ago.date()

    # Designing a query to find the most active stations (i.e. what stations have the most rows?)
    # Listing stations and the counts in descending order.
    station_count = session.query(Measurement.station, Station.name, func.count(Measurement.id)).\
    filter(Measurement.station == Station.station).\
    group_by(Measurement.station).\
    order_by(func.count(Measurement.id).desc()).all()

    station_activity = [{"station_id": result[0], "station_name": result[1],"station_count": result[2]} for result in station_count]
    most_active = station_activity[0]['station_id']

    results = session.query(Measurement.station,Station.name, Measurement.date, Measurement.tobs).\
    filter(Measurement.date >= one_year_ago.date()).\
    filter(Measurement.station == Station.station).\
    filter(Measurement.station == most_active).all()

    session.close()
    
    tobs = list(np.ravel(results))

    return jsonify(tobs) 
@app.route("/api/v1.0/<start>") 
@app.route("/api/v1.0/<start>/<end>") 
def stats(start=None, end=None):
    """Return TMIN, TAVG, TMAX."""

    session = Session(engine)

    sel = [func.min(Measurement.tobs), 
       func.max(Measurement.tobs), 
       func.round(func.avg(Measurement.tobs),2)]
    
    if end is None:
         results = session.query(*sel).\
        filter(Measurement.date >= start).all()
    else:
        results = session.query(*sel).\
        filter(Measurement.date.between(start,end))

    session.close()
    
    stats_list = list(results)

    return jsonify(stats_list)

if __name__ == '__main__':
    app.run()
