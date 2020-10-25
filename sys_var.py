# Master list of high-level variables, for admin use only

# ----------- Datalogger Tables -----------

indoor_raw = [['id', 'integer primary key'],
 ['date_time', 'timestamp'],
 ['pi_serial', 'text'],
 ['location', 'text'],
 ['drybulb', 'real'],
 ['rh', 'real'],
 ['wetbulb', 'real'],
 ['dewpoint', 'real'],
 ['vpd', 'real'],
 ['white_light', 'real'],
 ['lux', 'real'],
 ['rh_req_for_vpd', 'real']]

indoor_day = [['index', 'DATE'],
 ['drybulb_max', 'REAL'],
 ['drybulb_max_time', 'TIME'],
 ['drybulb_min', 'REAL'],
 ['drybulb_min_time', 'TIME'],
 ['drybulb_range', 'REAL'],
 ['drybulb_period', 'REAL'],
 ['drybulb_rate', 'REAL'],
 ['drybulb_mean', 'REAL'],
 ['rh_max', 'REAL'],
 ['rh_max_time', 'TIME'],
 ['rh_min', 'REAL'],
 ['rh_min_time', 'TIME'],
 ['rh_range', 'REAL'],
 ['rh_period', 'REAL'],
 ['rh_rate', 'REAL'],
 ['rh_mean', 'REAL'],
 ['wetbulb_max', 'REAL'],
 ['wetbulb_max_time', 'TIME'],
 ['wetbulb_min', 'REAL'],
 ['wetbulb_min_time', 'TIME'],
 ['wetbulb_range', 'REAL'],
 ['wetbulb_period', 'REAL'],
 ['wetbulb_rate', 'REAL'],
 ['wetbulb_mean', 'REAL'],
 ['dewpoint_max', 'REAL'],
 ['dewpoint_max_time', 'TIME'],
 ['dewpoint_min', 'REAL'],
 ['dewpoint_min_time', 'TIME'],
 ['dewpoint_range', 'REAL'],
 ['dewpoint_period', 'REAL'],
 ['dewpoint_rate', 'REAL'],
 ['dewpoint_mean', 'REAL'],
 ['vpd_max', 'REAL'],
 ['vpd_max_time', 'TIME'],
 ['vpd_min', 'REAL'],
 ['vpd_min_time', 'TIME'],
 ['vpd_range', 'REAL'],
 ['vpd_period', 'REAL'],
 ['vpd_rate', 'REAL'],
 ['vpd_mean', 'REAL'],
 ['white_light_max', 'REAL'],
 ['white_light_max_time', 'REAL'],
 ['white_light_min', 'REAL'],
 ['white_light_min_time', 'REAL'],
 ['white_light_range', 'REAL'],
 ['white_light_period', 'REAL'],
 ['white_light_rate', 'REAL'],
 ['white_light_mean', 'REAL'],
 ['lux_max', 'REAL'],
 ['lux_max_time', 'REAL'],
 ['lux_min', 'REAL'],
 ['lux_min_time', 'REAL'],
 ['lux_range', 'REAL'],
 ['lux_period', 'REAL'],
 ['lux_rate', 'REAL'],
 ['lux_mean', 'REAL'],
 ['dewpoint', 'REAL'],
 ['drybulb', 'REAL'],
 ['rh', 'REAL'],
 ['wetbulb', 'REAL'],
 ['vpd', 'REAL']]

outdoor_raw = [['id', 'integer primary key'],
 ['date_time', 'timestamp'],
 ['drybulb', 'real'],
 ['rh', 'real'],
 ['clouds', 'real'],
 ['rain', 'real'],
 ['wind', 'real'],
 ['status', 'text'],
 ['sunrise', 'timestamp'],
 ['sunset', 'timestamp'],
 ['wetbulb', 'real'],
 ['dewpoint', 'real'],
 ['vpd', 'real']]

outdoor_day = [['index', 'DATE'],
 ['drybulb_max', 'REAL'],
 ['drybulb_max_time', 'TIME'],
 ['drybulb_min', 'REAL'],
 ['drybulb_min_time', 'TIME'],
 ['drybulb_range', 'REAL'],
 ['drybulb_period', 'REAL'],
 ['drybulb_rate', 'REAL'],
 ['drybulb_mean', 'REAL'],
 ['rh_max', 'REAL'],
 ['rh_max_time', 'TIME'],
 ['rh_min', 'REAL'],
 ['rh_min_time', 'TIME'],
 ['rh_range', 'REAL'],
 ['rh_period', 'REAL'],
 ['rh_rate', 'REAL'],
 ['rh_mean', 'REAL'],
 ['clouds_max', 'REAL'],
 ['clouds_max_time', 'TIME'],
 ['clouds_min', 'REAL'],
 ['clouds_min_time', 'TIME'],
 ['clouds_range', 'REAL'],
 ['clouds_period', 'REAL'],
 ['clouds_rate', 'REAL'],
 ['clouds_mean', 'REAL'],
 ['rain_max', 'REAL'],
 ['rain_max_time', 'TIME'],
 ['rain_min', 'REAL'],
 ['rain_min_time', 'TIME'],
 ['rain_range', 'REAL'],
 ['rain_period', 'REAL'],
 ['rain_rate', 'REAL'],
 ['rain_mean', 'REAL'],
 ['wind_max', 'REAL'],
 ['wind_max_time', 'TIME'],
 ['wind_min', 'REAL'],
 ['wind_min_time', 'TIME'],
 ['wind_range', 'REAL'],
 ['wind_period', 'REAL'],
 ['wind_rate', 'REAL'],
 ['wind_mean', 'REAL'],
 ['wetbulb_max', 'REAL'],
 ['wetbulb_max_time', 'TIME'],
 ['wetbulb_min', 'REAL'],
 ['wetbulb_min_time', 'TIME'],
 ['wetbulb_range', 'REAL'],
 ['wetbulb_period', 'REAL'],
 ['wetbulb_rate', 'REAL'],
 ['wetbulb_mean', 'REAL'],
 ['dewpoint_max', 'REAL'],
 ['dewpoint_max_time', 'TIME'],
 ['dewpoint_min', 'REAL'],
 ['dewpoint_min_time', 'TIME'],
 ['dewpoint_range', 'REAL'],
 ['dewpoint_period', 'REAL'],
 ['dewpoint_rate', 'REAL'],
 ['dewpoint_mean', 'REAL'],
 ['vpd_max', 'REAL'],
 ['vpd_max_time', 'TIME'],
 ['vpd_min', 'REAL'],
 ['vpd_min_time', 'TIME'],
 ['vpd_range', 'REAL'],
 ['vpd_period', 'REAL'],
 ['vpd_rate', 'REAL'],
 ['vpd_mean', 'REAL'],
 ['sun', 'REAL']]

check_datalogger = {
    'indoor_raw': indoor_raw,
    'indoor_day': indoor_day,
    'outdoor_raw': outdoor_raw,
    'outdoor_day': outdoor_day,
}


# ----------- Webserver Tables -----------

houseplants = [
 ['name', 'text'],                      # 1
 ['species', 'text'],                   # 2
 ['location', 'text'],                  # 3
 ['purchased_from', 'text'],            # 4
 ['purchase_date', 'timestamp'],        # 5
 ['water_schedule_in_days', 'integer'], # 6
 ['last_watered', 'timestamp'],         # 7
 ['substrate', 'text'],                 # 8
 ['pot_size', 'real'],                  # 9
 ['leaf_temp_offset', 'integer'],       # 10
 ['pic_path', 'text'],                  # 11
 ['has_pic', 'smallint'],               # 12
 ['days_since_last_water', 'integer'],  # 13
 ['need_water', 'smallint'],            # 14
 ['water_warning', 'smallint'],         # 15
 ['ignore', 'smallint'],                # 16
 ['death', 'smallint'],                 # 17
 ['last_repot_date', 'timestamp']       # 18
]

my_journal = [
 ['date', 'timestamp'],                 # 1
 ['title', 'text'],             # 2
 ['plant', 'text'],             # 3
 ['body', 'text'],                      # 4
 ['has_pic', 'smallint'],               # 5
 ['pic_path', 'text']          # 6
]

other_locations = [
 ['name', 'text']
]

check_webserver = {
    'houseplants': houseplants,
    'my_journal': my_journal,
    'other_locations': other_locations
}