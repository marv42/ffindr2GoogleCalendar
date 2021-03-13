TITLE = "title"
LINK = "link"
DESCRIPTION = "description"
AUTHOR = "author"
CATEGORY = "category"
DATE_START = "dateStart"
DATE_END = "dateEnd"
LOCATION = "location"
GEO_LAT = "geo:lat"
GEO_LONG = "geo:long"


class EventData:
    title = u''
    link = u''
    description = u''
    author = u''
    category = u''
    date_start = u''
    date_end = u''
    location = u''
    geo_lat = u''
    geo_long = u''

    @staticmethod
    def strip(event_data):
        event_data.title = event_data.title.strip()
        event_data.link = event_data.link.strip()
        event_data.description = event_data.description.strip()
        event_data.author = event_data.author.strip()
        event_data.category = event_data.category.strip()
        event_data.date_start = event_data.date_start.strip()
        event_data.date_end = event_data.date_end.strip()
        event_data.location = event_data.location.strip()
        event_data.geo_lat = event_data.geo_lat.strip()
        event_data.geo_long = event_data.geo_long.strip()
        return event_data
