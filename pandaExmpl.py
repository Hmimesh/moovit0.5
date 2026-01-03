import pandas as pd
import datetime as dt
gtfs_Files_Lcation = './gtfs_data/gtfs_extracted_data'

calendar = pd.read_csv(
    gtfs_Files_Lcation+'/calendar.txt'
)

trips = pd.read_csv(
    gtfs_Files_Lcation+'/trips.txt'
)

stop_times = pd.read_csv(
    gtfs_Files_Lcation+'/stop_times.txt'
)

routes = pd.read_csv(
    gtfs_Files_Lcation+'/routes.txt'
) 

stops = pd.read_csv(
    gtfs_Files_Lcation+'/stops.txt'
)

date = 20260104 #YYYYMMDD

weekDay = pd.to_datetime(str(date)).day_name().lower()

activeServices = calendar[
    (calendar['start_date'] <= date)&
    (calendar['end_date'] >= date)&
    (calendar[weekDay] == 1)
]['service_id']

print(len(activeServices))