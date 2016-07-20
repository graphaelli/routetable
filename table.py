import os

import flask
import psycopg2
import psycopg2.extras

from crossdomain import crossdomain
import db

app = flask.Flask(__name__)


db.initialize(os.getenv('DATABASE_URL', 'postgres://localhost'))


QUERY_RT = """
    WITH stops_begin AS (
        SELECT stop_id, stop_name, ST_Distance(
            ST_Transform(ST_SetSRID(ST_MakePoint(%(start_lon)s, %(start_lat)s), 4326), 2163),
            ST_Transform(ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326), 2163)
        ) AS distance
        FROM stops
        WHERE ST_Distance(
            ST_Transform(ST_SetSRID(ST_MakePoint(%(start_lon)s, %(start_lat)s), 4326), 2163),
            ST_Transform(ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326), 2163)
        ) < 800
    ), stops_end_choices AS (
        SELECT stop_id
        FROM stops
        WHERE
            ST_Distance(
                ST_Transform(ST_SetSRID(ST_MakePoint(%(end_lon)s, %(end_lat)s), 4326), 2163),
                ST_Transform(ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326), 2163)
            ) < 800
    ), complete_trip AS (
        SELECT routes.route_short_name, stops_begin.stop_name AS begin_stop_name, times_begin.departure_time, stops_begin.distance AS begin_distance,
                ROW_NUMBER() OVER (PARTITION BY trips_begin.trip_id ORDER BY stops_begin.distance) AS trip_stop_order,
                stops_end.stop_name AS end_stop_name, times_end.arrival_time, ST_Distance(
                    ST_Transform(ST_SetSRID(ST_MakePoint(%(end_lon)s, %(end_lat)s), 4326), 2163),
                    ST_Transform(ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326), 2163)
                ) AS end_distance, calendar.*
        FROM stops_begin
        JOIN stop_times times_begin
          ON stops_begin.stop_id = times_begin.stop_id
        JOIN trips trips_begin
          ON times_begin.trip_id = trips_begin.trip_id
        JOIN routes
          ON trips_begin.route_id = routes.route_id
        JOIN stop_times times_end
          ON trips_begin.trip_id = times_end.trip_id
        JOIN stops stops_end
          ON times_end.stop_id = stops_end.stop_id
        JOIN calendar
          ON trips_begin.service_id = calendar.service_id
        WHERE times_end.stop_id IN (SELECT stop_id FROM stops_end_choices)
        AND times_begin.departure_time < times_end.arrival_time
        AND calendar.monday
        ORDER BY times_begin.departure_time
    )
    SELECT route_short_name, begin_stop_name, departure_time, begin_distance, end_stop_name, arrival_time, end_distance
    FROM complete_trip
    WHERE trip_stop_order = 1
    """


@app.route('/rt/<src_lat>,<src_lon>;<dst_lat>,<dst_lon>', methods=['GET', 'OPTIONS'])
@crossdomain(origin='*')
def route_table(src_lat, src_lon, dst_lat, dst_lon):
    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(QUERY_RT, {
            'start_lat': src_lat, 'start_lon': src_lon,
            'end_lat': dst_lat, 'end_lon': dst_lon
        })
        return flask.jsonify(cursor.fetchall())
