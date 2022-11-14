#

#
__name__ = "acdsee_helper"
__version__ = "v0.1a0"
__name_version__ = f"{__name__} {__version__}"


# Exif/IPTC (and other) tags we are interested in.
ACDSEE_CATEGORIES_TAG = 'Xmp.acdsee.categories'
ACDSEE_KEYWORDS_TAG = 'Xmp.acdsee.keywords'
DC_SUBJECT_TAG = 'Xmp.dc.subject'
EXIF_GPS_LATITUDE_TAG = 'Xmp.exif.GPSLatitude'
EXIF_GPS_LONGITUDE_TAG = 'Xmp.exif.GPSLongitude'
IPTCEXT_EVENT_TAG = 'Xmp.iptcExt.Event'
IPTCEXT_PERSON_TAG = 'Xmp.iptcExt.PersonInImage'
IPTC_GEO_COUNTRY_CODE_TAG = 'Xmp.iptc.CountryCode'
IPTC_GEO_LOCATION_TAG = 'Xmp.iptc.Location'
LR_SUBJECT_TAG = 'Xmp.lr.hierarchicalSubject'
PS_GEO_CITY_TAG = 'Xmp.photoshop.City'
PS_GEO_COUNTRY_TAG = 'Xmp.photoshop.Country'
PS_GEO_STATE_TAG = 'Xmp.photoshop.State'
XMP_CREATOR_TOOL_TAG = "Xmp.xmp.CreatorTool"
