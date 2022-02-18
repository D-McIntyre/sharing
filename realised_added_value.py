import os
import sys
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import netCDF4

### Which data to read in


gcm = sys.argv[1]
var = sys.argv[2]

rcp = 'historical'


### Some preparations

processed_path = '/g/data/wj02/PROCESSED_FILES'
if var in ['pr', 'tasmin', 'tasmax', 'rsds']:
    inputs_or_outputs = 'climate_inputs'
    reference_data = 'AWAP'
elif var in ['sm', 'etot', 'e0', 'qtot']:
    inputs_or_outputs = 'awra_outputs'
    reference_data = 'AWRA_v6.1'
    
if var == "pr":
    var2="rain_day"
elif var== "tasmax":
    var2="temp_max_day"
elif var== "tasmin":
    var2="temp_min_day"



# Which data to read in
if var in ['pr', 'qtot', 'etot', 'e0']:
    apply_function = ["max","min","pctl05","pctl10", "pctl90","pctl95"]
elif var in ['tasmin', 'tasmax', 'rsds', 'sfcWind', 'sm']:
    apply_function = ["max","mean","min","pctl05","pctl10", "pctl90","pctl95"] 


### Read in monthly data - historical reference

years_to_readin = np.arange(1976, 2006)
ds_reference=xr.Dataset()
for i in range(len(apply_function)):
    files = [os.path.join(processed_path, reference_data, '%s_%s_year' % (reference_data, var2)+str(apply_function[i])+'_%s.nc' % (yr)) \
         for yr in years_to_readin]
    ds_reference[str(apply_function[i])] = xr.open_mfdataset(files)[var2].load()
    print(str(apply_function[i]))

ds_reference=ds_reference.resample(time="AS").mean()
ds_reference=ds_reference.rename({"latitude":"lat","longitude":"lon"})
ds_reference=ds_reference.reindex(lat=list(reversed(ds_reference.lat)))
ds_reference


### Read in CCAM uncorrected data

years_to_readin = np.arange(1975, 2006)
ds_gdd=xr.Dataset()
for i in range(len(apply_function)):
    files = [os.path.join(processed_path, "CCAM-BEFOREBC", inputs_or_outputs, gcm, rcp, 'CCAM-BEFOREBC_%s_%s_year' % (gcm,var)+str(apply_function[i])+'_%s.nc' % (yr)) \
         for yr in years_to_readin]
    ds_gdd[str(apply_function[i])] = xr.open_mfdataset(files)[var].load() 

ds_gdd=ds_gdd.resample(time="AS").mean()
ds_gdd

### Read in bias corrected data
years_to_readin = np.arange(1975, 2006)
ds_gcm_bc=xr.Dataset()
for i in range(len(apply_function)):
    files = [os.path.join(processed_path, 'CCAM-ISIMIP2b', inputs_or_outputs, gcm, rcp, 'CCAM-ISIMIP2b_%s_%s_year' % (gcm,var)+str(apply_function[i])+'_%s.nc' % (yr)) \
         for yr in years_to_readin]
    ds_gcm_bc[str(apply_function[i])] = xr.open_mfdataset(files)[var].load() 

ds_gcm_bc=ds_gcm_bc.resample(time="AS").mean()


ds_reference=ds_reference.assign_coords(lat=ds_gdd.lat, lon=ds_gdd.lon)
### Calculate Added Value

ds_added_value=np.sqrt(((ds_gdd-ds_reference)**2).mean(dim="time"))-np.sqrt(((ds_gcm_bc-ds_reference)**2).mean(dim="time"))

years_to_readin = np.arange(2036, 2066)
ds_ccam_future=xr.Dataset()
# /g/data/wj02/PROCESSED_FILES/ISIMIP2b/awra_outputs/ACCESS1-0/historical/ISIMIP2b_ACCESS1-0_e0_monmax_1974.nc
for i in range(len(apply_function)):
    files = [os.path.join(processed_path, "CCAM-BEFOREBC", inputs_or_outputs, gcm, "rcp85", 'CCAM-BEFOREBC_%s_%s_year' % (gcm,var)+str(apply_function[i])+'_%s.nc' % (yr)) \
         for yr in years_to_readin]
    ds_ccam_future[str(apply_function[i])] = xr.open_mfdataset(files)[var].load() #loads pre-loads the data

ds_ccam_future=ds_ccam_future.resample(time="AS").mean()

years_to_readin = np.arange(2036, 2066)
ds_ccam_bc_future=xr.Dataset()
# /g/data/wj02/PROCESSED_FILES/ISIMIP2b/awra_outputs/ACCESS1-0/historical/ISIMIP2b_ACCESS1-0_e0_monmax_1974.nc

for i in range(len(apply_function)):
    files = [os.path.join(processed_path, "CCAM-ISIMIP2b", inputs_or_outputs, gcm, "rcp85", 'CCAM-ISIMIP2b_%s_%s_year' % (gcm,var)+str(apply_function[i])+'_%s.nc' % (yr)) \
         for yr in years_to_readin]
    ds_ccam_bc_future[str(apply_function[i])] = xr.open_mfdataset(files)[var].load() #loads pre-loads the data

ds_ccam_bc_future=ds_ccam_bc_future.resample(time="AS").mean()

PAV=ds_ccam_future.mean(dim="time")-ds_ccam_bc_future.mean(dim="time")

RAV=ds_added_value*np.abs(PAV)/((ds_reference.std(dim="time"))**2)

ds_path = '/g/data/er4/dm1346/REALISED_ADDED_VALUES/'

# fig.tight_layout()
fn = os.path.join(ds_path, 'realised_added_value_CCAM-ISIMIP2b_%s_%s.nc' % (gcm, var))
RAV.to_netcdf(path=fn, format='netcdf4',engine='netcdf4')