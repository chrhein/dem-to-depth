import rasterio
from src.location_handler import convert_coordinates


def get_raster_data(dem_file, coordinates):
    # load raster data
    ds_raster = rasterio.open(dem_file)

    # get resolution (points per square meter)
    resolution = ds_raster.transform[0]

    # get coordinate reference system
    crs = int(ds_raster.crs.to_authority()[1])

    # convert lat_lon to grid coordinates in the interval [0, 1]
    camera_lat_lon = convert_coordinates(ds_raster, crs,
                                         coordinates[0], coordinates[1], True)
    look_at_lat_lon = convert_coordinates(ds_raster, crs, coordinates[2],
                                          coordinates[3], False)
    raster_left, raster_bottom, raster_right, raster_top = ds_raster.bounds

    # get total sample points across x and y axis
    total_distance_e_w = raster_right - raster_left
    total_distance_n_s = raster_top - raster_bottom

    max_height = camera_lat_lon[-1]

    coordinates_and_dem = [*camera_lat_lon[:3], *look_at_lat_lon[:3], dem_file]

    return [coordinates_and_dem, ds_raster, total_distance_n_s,
            total_distance_e_w, resolution, max_height]
