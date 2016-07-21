# Custom Trip Timetables

http://g.raphaelli.com/rt/

## Load GTFS Feed

First, you'll need a GTFS feed.  For Philly, grab SEPTA's at http://www3.septa.org/developer/.

Now create some tables.  https://developers.google.com/transit/gtfs/reference/ has details on what these columns mean.

```sql
CREATE TABLE calendar (
    service_id character varying(255) NOT NULL,
    monday boolean NOT NULL,
    tuesday boolean NOT NULL,
    wednesday boolean NOT NULL,
    thursday boolean NOT NULL,
    friday boolean NOT NULL,
    saturday boolean NOT NULL,
    sunday boolean NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL
);

CREATE TABLE routes (
    route_id character varying(255) NOT NULL,
    agency_id character varying(255),
    route_short_name character varying(255),
    route_long_name character varying(255),
    route_desc character varying(1023),
    route_type integer NOT NULL,
    route_url character varying(255),
    route_color character varying(6),
    route_text_color character varying(6)
);

CREATE TABLE stop_times (
    trip_id character varying(255) NOT NULL,
    arrival_time character varying(9),
    departure_time character varying(9),
    stop_id character varying(255) NOT NULL,
    stop_sequence integer NOT NULL,
    stop_headsign character varying(255),
    pickup_type integer,
    drop_off_type integer,
    shape_dist_traveled numeric(20,10),
    timepoint boolean
);

CREATE TABLE stops (
    stop_id character varying(255) NOT NULL,
    stop_code character varying(50),
    stop_name character varying(255) NOT NULL,
    stop_desc character varying(255),
    stop_lat numeric(12,9) NOT NULL,
    stop_lon numeric(12,9) NOT NULL,
    zone_id character varying(50),
    stop_url character varying(255),
    location_type integer,
    parent_station character varying(255),
    stop_timezone character varying(50),
    wheelchair_boarding integer
);

CREATE TABLE trips (
    route_id character varying(255) NOT NULL,
    service_id character varying(255) NOT NULL,
    trip_id character varying(255) NOT NULL,
    trip_headsign character varying(255),
    trip_short_name character varying(255),
    direction_id integer,
    block_id character varying(255),
    shape_id character varying(255),
    wheelchair_accessible integer,
    bikes_allowed integer
);
```

And load them. This can generate the copy commands needed:

```sh
for table in calendar routes stop_times stops trips; do
  columns=$(head -1 ${table}.txt | tr -d '\015\012')
cat <<EOF
\copy $table ($columns) FROM '$table.txt' WITH (HEADER true, FORMAT csv);
EOF
done
```

The actually commands vary across feeds as some columns are optional.  There are a number of projects that do this with
one command like https://github.com/OpenTransitTools/gtfsdb

Now Fire it up:
```sh
FLASK_APP=table FLASK_DEBUG=1 python -m flask run
```

And finally open `index.html` in a browser.
