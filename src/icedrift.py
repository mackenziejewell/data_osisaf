# DEPENDENCIES:
import xarray as xr
import numpy as np
import numpy.ma as ma
import cartopy
import cartopy.crs as ccrs
from datetime import datetime, timedelta

# FUNCTIONS:
def grab_projection(ds, quiet = True):

    """Grab projection info from OSI-SAF sea ice motion data.
    create cartopy projection for x, y coordinates of OSI SAF sea ice drift data

INPUT: 
- ds: data opened with xarray
- quiet: bool, whether or not to supress print statements (default: True)

OUTPUT:
- projection: cartopy projection from data projection info

Latest recorded update:
06-19-2024
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


def grab_OSISAF_drift(date=datetime(2000,1,1), 
                      main_path = '/Volumes/Seagate_Jewell/KenzieStuff/OSI-SAF/'):
    
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

DEPENDENCIES:
import numpy as np
import numpy.ma as ma
import cartopy
import cartopy.crs as ccrs
import xarray as xr
from datetime import datetime, timedelta

Latest recorded update:
06-19-2024
    """
    
    # find dates before and after specified day
    # since ice displacement is calculated across these two days
    before = date - timedelta(days = 1)
    after  = date + timedelta(days = 1)

    # strip year/month infor to find subfolder
    year = after.year
    month = '{:02d}'.format(after.month)
    
    # construct filename
    file = f"{year}/{month}/ice_drift_nh_polstere-625_multi-oi_{before.strftime('%Y%m%d1200')}-{after.strftime('%Y%m%d1200')}.nc"

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