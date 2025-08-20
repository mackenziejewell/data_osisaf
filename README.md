
# data_osisaf
Scripts for downloading, opening, read data files from EUMETSAT Ocean and Sea Ice Satellite Application Facility (OSI SAF)

### To build matching environment:

(1) Navigate to folder in terminal and run:
conda env create --file=environment.yml

(2) Optional: if running in Jupyter Notebook environment
After creating the environment, you will next need to add it to the list of available kernels. 
This does not happen automatically. In the command line, run:
python -m ipykernel install --user --name <NAME>
* Make sure to replace <NAME> with the name of the environment

If conda command not recognized by default with terminal launch:
source /opt/anaconda3/bin/activate

(3) Optional, to update environment file after modifying packages:
conda env export > environment.yml

   
# icedrift_lr.py

Global Low Resolution Sea Ice Drift OSI-405-c

This opens nc files from the Global Low Resolution Sea Ice Drift data product. 

DOI: 10.15770/EUM_SAF_OSI_NRT_2007

https://osi-saf.eumetsat.int/products/osi-405-c

More info on the product:
https://osisaf-hl.met.no/osi-405-c-desc 

This dataset shall be referred to as the **low resolution sea ice drift product of the EUMETSAT Ocean and Sea Ice Satellite Application Facility (OSI SAF, https://osi-saf.eumetsat.int)**.
<br>
The motion tracking methodology (CMCC) is published and shall be cited as <br>**Lavergne, et al. (2010):** <br>Lavergne, T., Eastwood, S., Teffah, Z., Schyberg, H. and L.-A. Breivik (2010), Sea ice motion from low resolution satellite sensors: an alternative method and its validation in the Arctic. J. Geophys. Res., 115, C10032, doi:10.1029/2009JC005958.
