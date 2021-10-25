import cv2
import os
import time
import subprocess
from data_getters.mountains import get_mountain_data
from debug_tools import p_e, p_i, p_line
from location_handler import plot_to_map, get_mountains_in_sight, get_raster_data
from povs import primary_pov, debug_pov
from im import get_image_shape
from tools.color_map import create_route_texture, \
    create_color_gradient_image, colors_to_coordinates


def render_dem(panorama_path, mode, mountains):
    start_time = time.time()
    panorama_filename = panorama_path.split('/')[-1].split('.')[0]
    folder = 'exports/%s/' % panorama_filename
    gpx_file = 'data/hikes/%s.gpx' % panorama_filename

    try:
        os.mkdir(folder)
    except FileExistsError:
        pass

    dem_file, coordinates, pov_settings = get_mountain_data('data/dem-data.json',
                                                            panorama_filename)
    f = dem_file.lower()
    if not f.endswith('.png') and not f.endswith('.jpg'):
        p_e('please provide a .png file')
        return

    panorama = cv2.imread(panorama_path)
    image_width, image_height = get_image_shape(panorama)
    pov_filename = '/tmp/pov_file.pov'
    render_shape = [image_width, image_height]

    raster_data = get_raster_data(dem_file, coordinates, pov_settings[1])
    if not raster_data:
        return
    pov = [pov_filename, folder, render_shape, pov_settings]
    pov_params = [dem_file, pov, raster_data]

    if mode == 'debug':
        route_texture, texture_bounds = create_route_texture(dem_file, gpx_file, True)
        pov_filename, folder, _, _ = pov
        with open(pov_filename, 'w') as pf:
            pov = debug_pov(dem_file, route_texture, texture_bounds, raster_data[1][3])
            pf.write(pov)
            pf.close()
        out_filename = '%srender-debug.png' % folder
        params = [pov_filename, out_filename, [2400, 2400], 'color']
        execute_pov(params)
    else:
        pov_filename, folder, im_dimensions, pov_settings = pov
        with open(pov_filename, 'w') as pf:
            if mode == 1:
                pov_mode = 'depth'
                pov = primary_pov(dem_file, raster_data, pov_settings, pov_mode)
                out_filename = '%srender-%s.png' % (folder, pov_mode)
                params = [pov_filename, out_filename, im_dimensions, pov_mode]
                pf.write(pov)
                pf.close()
                execute_pov(params)
            elif mode == 2:
                pov_mode = 'height'
                pov = primary_pov(dem_file, raster_data, pov_settings, pov_mode)
                out_filename = '%srender-%s.png' % (folder, pov_mode)
                params = [pov_filename, out_filename, im_dimensions, 'color']
                pf.write(pov)
                pf.close()
                execute_pov(params)
            elif mode == 3:
                pov_mode = 'texture'
                gpx_exists = os.path.isfile('%s' % gpx_file)
                if gpx_exists:
                    route_texture, texture_bounds = create_route_texture(dem_file, gpx_file)
                    pov_params[1][3].append(route_texture)
                    pov_params[1][3].append(texture_bounds)
                    pov = primary_pov(dem_file, raster_data, pov_settings, pov_mode)
                    out_filename = '%srender-%s.png' % (folder, pov_mode)
                    params = [pov_filename, out_filename, im_dimensions, 'color']
                    pf.write(pov)
                    pf.close()
                    execute_pov(params)
                else:
                    p_e('Could not find corresponding GPX')
                    return
            elif mode == 4:
                pov_mode = 'gradient'
                out_filename = '%srender-%s.png' % (folder, pov_mode)
                gradient_render = os.path.isfile('%s' % out_filename)
                gradient_path, _ = create_color_gradient_image()
                if not gradient_render:
                    pov_settings.append(gradient_path)
                    pov = primary_pov(dem_file, raster_data, pov_settings, pov_mode)
                    params = [pov_filename, out_filename, im_dimensions, pov_mode]
                    pf.write(pov)
                    pf.close()
                    execute_pov(params)
                locs = colors_to_coordinates(gradient_path, folder, dem_file)
                mountains_in_sight = get_mountains_in_sight(locs, mountains)
                plot_filename = '%s%s.html' % (folder, panorama_filename)
                plot_to_map(mountains_in_sight, coordinates, plot_filename)
            else:
                pf.close()
                return
    stats = [
        'Information about completed task: \n',
        'File:      %s' % panorama_filename,
        'Mode:      %s' % mode,
        'Duration:  %i seconds' % (time.time() - start_time)
        ]
    p_line(stats)


def execute_pov(params):
    pov_filename, out_filename, dimensions, mode = params
    out_width, out_height = dimensions
    p_i('Generating %s' % out_filename)
    if mode == 'color' or mode == 'gradient':
        subprocess.call(['povray', '+W%d' % out_width, '+H%d' % out_height,
                         'Output_File_Type=N Bits_Per_Color=16 +Q8 +UR +A',
                         '-GA',
                         '+I' + pov_filename, '+O' + out_filename])
    else:
        subprocess.call(['povray', '+W%d' % out_width, '+H%d' % out_height,
                         'Output_File_Type=N Bits_Per_Color=16 Display=off',
                         '-GA',
                         'Antialias=off Quality=0 File_Gamma=1.0',
                         '+I' + pov_filename, '+O' + out_filename])
