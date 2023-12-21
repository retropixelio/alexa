import datetime
import dateutil.parser

def parse_iso_datetime(datetime_string: str):
    return dateutil.parser.isoparse(datetime_string)

# def parse_iso_date(date_string: str):
#     return datetime.isoformat(date_string)

def iso_from_datetime(dt: datetime.datetime):
    return dt.isoformat()