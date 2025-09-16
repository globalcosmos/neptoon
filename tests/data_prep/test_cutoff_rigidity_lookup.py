from neptoon.data_prep.cutoff_rigidity_lookup import GVLookup


def test_gv_get_interpolate():
    lat = 10
    lon = 10
    lookup = GVLookup()
    gv = lookup.get_gv(lat=lat, lon=lon)
    assert gv == 15.06


def test_gv_get_exact():
    lat = 45
    lon = 0
    lookup = GVLookup()
    gv = lookup.get_gv(lat=lat, lon=lon)
    assert gv == 4.97
