# DEPENDENCIES:
import xarray as xr
import numpy as np
import numpy.ma as ma
import cartopy
import cartopy.crs as ccrs
from datetime import datetime, timedelta
from siphon.catalog import TDSCatalog

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

def open_remote_file(date):
    
    """Use siphon to open remote files from thredds server:
    https://thredds.met.no/thredds/catalog/osisaf/met.no/ice/drift_lr/merged/

INPUT: 
- date: datetime object for desired file

OUTPUT:
- ds: xarray dataset

Latest recorded update:
10-24-2024
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
    
    return ds


def open_local_file(date, main_path = '/Volumes/Seagate_Jewell/KenzieStuff/OSI-SAF/'):
    
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

OUTPUT:
- data: dictionary with key variables

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
    ds = xr.open_dataset(main_path+file)
    ds.close()

    # save to dictionary
    data = {}
    data['proj'] = grab_projection(ds)
    data['x'] = ds.xc.values*1000
    data['y'] = ds.yc.values*1000
    data['dx'] = ds.dX.values[0,:,:]
    data['dy'] = ds.dY.values[0,:,:]
    data['ds'] = ds
    
    return data