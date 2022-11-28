

__name__ = "acdsee_helper"
__version__ = "v0.1a0"
__name_version__ = f"{__name__} {__version__}"


"""
Exif/XMP/IPTC (and other) tags we are interested in.

With `pyexiv2` these have to be read using different class methods - read_exif(),
read_xmp(), read_iptc() - and written with different class methods - write_exif(),
write_xmp(), write_iptc(). The prefix tells you which to use.

`MetaData` uses these traits and reads all the different types into a single
meta data dictionary. When it writes them out again it splits the dictionary
into pieces and use the appropriate function.

And yes, we have to split the location hierarchy between IPTC and PS otherwise
they don't update correctly.
"""
ACDSEE_CATEGORIES_TAG = 'Xmp.acdsee.categories'
ACDSEE_KEYWORDS_TAG = 'Xmp.acdsee.keywords'
DC_SUBJECT_TAG = 'Xmp.dc.subject'
EXIF_GPS_LATITUDE_TAG = 'Xmp.exif.GPSLatitude'
EXIF_GPS_LONGITUDE_TAG = 'Xmp.exif.GPSLongitude'
EXIF_MAKE_TAG = "Exif.Image.Make"
EXIF_MODEL_TAG = "Exif.Image.Model"
IPTCEXT_EVENT_TAG = 'Xmp.iptcExt.Event'
IPTCEXT_PERSON_TAG = 'Xmp.iptcExt.PersonInImage'
IPTC_GEO_COUNTRY_CODE_TAG = 'Iptc.Application2.CountryCode'
IPTC_GEO_LOCATION_TAG = 'Iptc.Application2.SubLocation'
LR_SUBJECT_TAG = 'Xmp.lr.hierarchicalSubject'
PS_GEO_CITY_TAG = 'Xmp.photoshop.City'
PS_GEO_COUNTRY_TAG = 'Xmp.photoshop.Country'
PS_GEO_STATE_TAG = 'Xmp.photoshop.State'
XMP_CREATOR_TOOL_TAG = "Xmp.xmp.CreatorTool"
