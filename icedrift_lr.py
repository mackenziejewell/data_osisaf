# DEPENDENCIES:
import xarray as xr
import numpy as np
import numpy.ma as ma
import cartopy
import cartopy.crs as ccrs
from datetime import datetime, timedelta
from siphon.catalog import TDSCatalog
from metpy.units import units

# FUNCTIONS:

def construct_filename(date):
    
    # find dates before and after specified day
    # since ice displacement is calculated across these two days
    before = date - timedelta(days = 1)
    after  = date + timedelta(days = 1)
    
    # construct filename
    file = f"ice_drift_nh_polstere-625_multi-oi_{before.strftime('%Y%m%d1200')}-{after.strftime('%Y%m%d1200')}.nc"

    return file
    

def grab_projection(ds, quiet = True):

    """Create cartopy projection from xarray ds containing OSI-SAF sea ice motion data.

INPUT: 
- ds: data opened with xarray
- quiet: bool, whether or not to supress print statements (default: True)

OUTPUT:
- projection: cartopy projection from data projection info

Latest recorded update:
10-24-2024
    """
    
    # grab projection info
    #---------------------
    CRS = ds.Polar_Stereographic_Grid.attrs

    # grab parameters from crs spatial attributes
    central_meridian = int(CRS['straight_vertical_longitude_from_pole'])
    standard_parallel = int(CRS['standard_parallel'])
    
    if quiet != True:
        print(f'>>> data provided in polar_stereographic projection')
        print(f'  - straight_vertical_longitude_from_pole: {central_meridian}')
        print(f'  - standard_parallel: {standard_parallel}')
        
    # create projection from info
    projection = ccrs.NorthPolarStereo(central_longitude=central_meridian,
                                       true_scale_latitude=standard_parallel)

    return projection

def extract_data_from_ds(ds, include_units = False):
        
        """Extract data from OSI-SAF sea ice motion data.
        INPUT: 
        - ds: xarray dataset
        - include_units: bool, whether or not to return data with units

        OUTPUT:
        - data: dictionary with provided variables

        Latest recorded update:
        10-25-2024
            """
        # save to dictionary
        data = {}
        data['proj'] = grab_projection(ds)
        data['ds'] = ds

        # convert all positions to meters
        data['x0'] = (ds.xc.values * units(ds['xc'].units)).to('m')
        data['y0'] = (ds.yc.values * units(ds['yc'].units)).to('m')
        data['xx0'], data['yy0'] = np.meshgrid(data['x0'], data['y0'])

        data['dx'] = (ds.dX.values[0,:,:]* units(ds['dX'].units)).to('m')
        
        # make sure to use updated y values
        # previous (dY) pointed backward
        # it seems this only applies in older files?
        if 'dY_v1p4' in list(ds.variables):
            data['dy'] = (ds.dY_v1p4.values[0,:,:]* units(ds['dY'].units)).to('m')
        else:
            data['dy'] = (ds.dY.values[0,:,:]* units(ds['dY'].units)).to('m')

        # reported final coordinates
        data['lat1'] = ds.lat1.values[0,:,:] * units(ds['lat1'].units)
        data['lon1'] = ds.lon1.values[0,:,:] * units(ds['lon1'].units)

        # reported initial coordinates
        data['lat0'] = ds.lat.values * units(ds['lat'].units)
        data['lon0'] = ds.lon.values * units(ds['lon'].units)

        # dates of first and final positions
        [t0, t1] = ds.time_bnds.values[0]
        # these dt values are supposed to give adjustments (order of hours)
        # to t0, t1 based on different satellite overpass times
        # but right now, dt0, dt1 appear to empty?
        time0 = t0 + ds.dt0.values[0,:,:]
        time1 = t1 + ds.dt1.values[0,:,:]

        # times of first, middle and final positions
        data['time0'] = t0
        data['time1'] = t1
    
        return data

def estimate_velocity(data):
    """Estimate velocity from OSI-SAF sea ice motion data dictionary.
    INPUT:
    - data: dictionary with provided variables
    OUTPUT:
    - data: dictionary, now including estimated velocity
    Latest recorded update:
    10-25-2024
    """
    # estimate halfway positions
    dX = np.copy(data['dx'])
    dY = np.copy(data['dy'])
    # set NaNs as zero displacement
    dX[np.isnan(dX)] = 0 * units('m')
    dY[np.isnan(dY)] = 0 * units('m')

    data['xmid'] = data['xx0'] + dX/2
    data['ymid'] = data['yy0'] + dY/2
    data['timemid'] = data['time0'] + (data['time1']-data['time0'])/2

    # estimate final positions
    data['x1'] = data['xx0'] + data['dx']
    data['y1'] = data['yy0'] + data['dy']

    # estimated velocities
    delta_t = (((data['time1']-data['time0'])/ np.timedelta64(1, 'D')) * units('day')) # roughly 2 days
    data['dt'] = delta_t
    data['u'] = (data['dx'] / delta_t).to('cm/s')
    data['v'] = (data['dy'] / delta_t).to('cm/s')

    return data

def open_remote_file(date, include_units = False):
    
    """Use siphon to open remote files from thredds server:
    https://thredds.met.no/thredds/catalog/osisaf/met.no/ice/drift_lr/merged/

INPUT: 
- date: datetime object for desired file
- include_units: bool, whether or not to return data with units

OUTPUT:
- data: dictionary with position, velocity, projection info

Latest recorded update:
10-25-2024
    """

    # parse thredds server catalog
    Y = date.year
    m = date.month
    
    # if desired day is on eve of new year, 
    # search in next year's catalog
    if (date.month == 12) & (date.day == 31):
        Y+=1
        m=1

    # construct catalog url
    catalog_url = f'https://thredds.met.no/thredds/catalog/osisaf/met.no/ice/drift_lr/merged/{Y}/{str(m).zfill(2)}/catalog.xml'
    
    # grab file list from catalog
    catalog = TDSCatalog(catalog_url)
    files = catalog.datasets
    
    # check that file is in catalog, otherwise warn
    desired_file = construct_filename(date)
    if desired_file not in list(files):
        print(f'!!! {construct_filename(date)} not in file list for {Y}/{str(m).zfill(2)} catalog')
    else:
        download_file = files[list(files).index(desired_file)]
    
    # open as xarray file
    ds = download_file.remote_access(use_xarray=True)
    
    # extract provided fields from dataset
    data = extract_data_from_ds(ds, include_units = include_units)

    # estimate velocity
    data = estimate_velocity(data)
    
    # remove units if desired
    if not include_units:
        for key in data.keys():
            if key not in ['proj', 'ds', 'time0', 'time1', 'timemid']:
                data[key] = data[key].magnitude

    return data


def open_local_file(date, main_path = '/Volumes/Seagate_Jewell/KenzieStuff/OSI-SAF/', include_units = False):
    
    """Grab OSI-SAF sea ice motion from locally-stored files. Assumes directory structure: 
    
    main_path
    ├── year1
    │   ├── month1
    │   │     ├── day1 file
    │   │     ├── day2 file
    │   │     ├── ...
    │   ├── ...
    ├── ...
    
INPUT: 
- date: datetime object for desired file
- main_path: path to locally-stored files
- include_units: bool, whether or not to return data with units

OUTPUT:
- data: dictionary with position, velocity, projection info

Latest recorded update:
10-24-2024
    """

    # strip year/month infor to find subfolder
    before = date - timedelta(days = 1)
    after  = date + timedelta(days = 1)
    year = after.year
    month = '{:02d}'.format(after.month)
    
    # construct filename
    file = f"{year}/{month}/" + construct_filename(date)

    # open dataset
    try:
        ds = xr.open_dataset(main_path+file)
        ds.close()
    except:
        print(f'!!! {file} not found in {main_path}')
        return None
    
    # extract provided fields from dataset
    data = extract_data_from_ds(ds, include_units = include_units)

    # estimate velocity
    data = estimate_velocity(data)
    
    # remove units if desired
    if not include_units:
        for key in data.keys():
            if key not in ['proj', 'ds', 'time0', 'time1', 'timemid']:
                data[key] = data[key].magnitude
        
    return data


    # I *****THINK**** from what I can tell from user manual,
    # https://osisaf-hl.met.no/sites/osisaf-hl/files/user_manuals/osisaf_cdop2_ss2_pum_sea-ice-drift-lr_v1p8.pdf
    # lat, lon of grid reference start lats/lons (lat0, lon0)
    # then lat1, lon1 show final coordinates after displacement between times t0 to t1
    # similarly, xc, yc would reference start coords (x0, y0)
    # and projected displacements dX and dY would be equivalent to displacement toward final coords x1, y1

    # Additionally, displacements are calculate over roughly 48-hr periods (from 12:00 to 12:00)
    # times t0, t1 listed in time bounds
    # but with different satellite overpass times, should adjust t0, t1 by dt0, dt1
    # but when I have inspected these variables, they are all 0 or 'NaT' (not a time)
    # so I'm not sure how to adjust for this 9Will figure out later!)



    return data