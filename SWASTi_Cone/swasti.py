import os
import time

import astropy.constants as ac
import astropy.units as u
import numpy as np
import pfsspy
import requests
import sunpy
import urllib.request
import warnings

from astropy.io import fits
from astropy.coordinates import SkyCoord
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from numba import njit
from scipy import interpolate
from sunpy.coordinates import frames
from sunpy.coordinates.sun import carrington_rotation_time

warnings.filterwarnings("ignore")

@njit
def Compute_MinAngularDistance(t, p, clf_th, clf_phi):
    cth = [clf_th[j]*np.pi/180. for j in range(len(clf_th))]
    cph = [clf_phi[j]*np.pi/180. for j in range(len(clf_phi))]
    csth = [np.sin(t)*np.sin(cth[j]) + np.cos(t)*np.cos(cth[j])*np.cos(p - cph[j]) for j in range(len(cth))]
    ang  = np.zeros(len(csth))
    for i in range(len(csth)):
        if csth[i] > 1.0: ang[i] = np.arccos(1.0)
        else: ang[i] = np.arccos(csth[i])
    return np.min(ang)
def Compute_WSAVelocity(WSA_Param_dict, d_2D, f_2D):
        v0 = WSA_Param_dict['SWTI_WSA_VMIN']
        v1 = WSA_Param_dict['SWTI_WSA_VMAX']
        al = WSA_Param_dict['SWTI_WSA_ALPHA']
        be = WSA_Param_dict['SWTI_WSA_BETA']
        w  = WSA_Param_dict['SWTI_WSA_W']

        den = (1.0 + f_2D)**al
        exp_term = (d_2D/w)**be
        num = (1.0 - 0.8*np.exp(-exp_term))**3
        v_2D = v0 + (v1*num)/den
        return v_2D
def Compute_HuX(V_in, R_arr, Phi_arr, Omega):
    r_sun = ac.R_sun.to('km').value
    dr = R_arr[1] - R_arr[0]
    dphi = np.abs(Phi_arr[1] - Phi_arr[0])
    V_HUX = np.zeros([len(R_arr), len(Phi_arr)])
    V_HUX[0,:] = V_in # velocity at R = 21.5 Rsun ~ 0.1 AU
    for ri in range(1,len(R_arr)):
        for i in range(len(Phi_arr)-1):
            V_HUX[ri, i] = V_HUX[ri-1,i] + ((dr*r_sun*Omega)/dphi)*((V_HUX[ri-1,i+1] - V_HUX[ri-1,i])/V_HUX[ri-1,i])
        V_HUX[ri, len(Phi_arr)-1] = V_HUX[ri-1,len(Phi_arr)-1] + ((dr*r_sun*Omega)/dphi)*((V_HUX[ri-1,0] - V_HUX[ri-1,len(Phi_arr)-1])/V_HUX[ri-1,len(Phi_arr)-1]) # Boundary condition.
    return V_HUX

def find_gong_file_by_cr(cr, CR_day):

    base = "https://gong.nso.edu/data/magmap/QR/nqs/"

    month0 = datetime.strptime(CR_day, "%Y%m")
    year = month0.year + (month0.month -2) // 12
    month = (month0.month -2) % 12 + 1
    month1 = month0.replace(year=year, month=month)
       
    year = month0.year + (month0.month) // 12
    month = (month0.month) % 12 + 1
    month2 = month0.replace(year=year, month=month)
    
    months = [
        month0,
        month1,
        month2,
    ]

    for m in months:
        day = m.strftime("%Y%m")

        month_url = f"{base}{day}/"
        r = requests.get(month_url, timeout=10)
        if r.status_code != 200:
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # 1) loop over subdirectories (mrnqsYYMMDD/)
        for a_dir in soup.find_all("a"):
            sub = a_dir.get("href", "")
            if not (sub.startswith("mrnqs") and sub.endswith("/")):
                continue

            sub_url = f"{month_url}{sub}"

            r2 = requests.get(sub_url, timeout=10)
            if r2.status_code != 200:
                continue

            soup2 = BeautifulSoup(r2.text, "html.parser")

            # 2) look for file with c<CR>
            for a_file in soup2.find_all("a"):
                fname = a_file.get("href", "")
                if (
                    fname.endswith(".fits.gz")
                    and f"c{cr}_" in fname
                ):
                    return (f"https://gong.nso.edu/data/magmap/QR/nqs/"f"{day}/{sub + fname}")

    raise FileNotFoundError(f"Map for CR {cr} not found at https://gong.nso.edu/data/magmap/QR/nqs/ , please use a downloaded map if available.")

class swasti:
    def __init__(self, fname):
        #print("Starting SWASTi Computation")
        self.ini_fname = fname
        self.process_ini_file() 
    def process_ini_file(self):
        # Initialize empty dictionaries
        self.swasti_run = {}
        self.wsa_inputs = {}
        self.cme_inputs = {}

        # Keep track of which section we're in
        current_dict_ = None

        with open(self.ini_fname, 'r') as f:
            for line_ in f:
                line_ = line_.strip()
                # Skip blank lines
                if not line_:continue

                # Detect sections
                if line_.startswith("[") and line_.endswith("]"):
                    section_ = line_[1:-1].strip()
                    if section_ == "SWASTi Run":current_dict_ = self.swasti_run
                    elif section_ == "WSA Parameters":current_dict_ = self.wsa_inputs
                    elif section_ == "CME Parameters":current_dict_ = self.cme_inputs
                    else:current_dict_ = None
                    continue
            # Process key-value pairs
                if ":" in line_ and current_dict_ is not None:
                    key_, value_ = line_.split(":", 1)
                    key_ = key_.strip()
                    value_ = value_.strip()
                # Try to cast to float or int if numeric
                    if value_.replace('.', '', 1).isdigit():
                        if '.' in value_:value_ = float(value_)
                        else:value_ = int(value_)
                    current_dict_[key_] = value_
   
    def get_map_data(self):
    	if S.swasti_run['SWTI_INPUT_MAP'] =='ADAPT':
    	    given_date_ = datetime.strptime(self.swasti_run['SWTI_MAP_TIME'], "%Y-%m-%d %H:%M")
    	    adaptCR_year_ = given_date_.year
    	    self.CR_time_ = given_date_.strftime("%Y%m%d%H%M") 
    	    self.mg_fname = f'adapt_{self.CR_time_}.fts.gz'

    	    if os.path.exists(self.mg_fname):
    	        print(f"The magnetogram file {self.mg_fname} already exists and will be used for processing")

    	    else:
    	        url = f"https://gong.nso.edu/adapt/maps/gong/{adaptCR_year_}/"
    	        response = requests.get(url)
    	        response.raise_for_status()
    	        soup = BeautifulSoup(response.text, "html.parser")
	    
    	        # Extract all hrefs that look like files
    	        adapt_fit_files_ = [a['href'] for a in soup.find_all('a', href=True)]
	    
    	        # Filter by prefix and date string
    	        adapt_urls = [f for f in adapt_fit_files_ 
    	        if f.startswith('adapt41311') and self.CR_time_ in f
    	        ] 
		    
    	        for adapt_url in adapt_urls:
    	            try:
    	                urllib.request.urlretrieve(url+adapt_url, self.mg_fname)
    	                print(f"Downloaded the magnetogram from: {adapt_url}")
    	                break
    	            except Exception as e:
    	                print(f"Failed to download from {adapt_url}: {e}")
    	            else:
    	                print("Failed to download the Central meridian magnetogram from all URLs.")  
		         
    	elif S.swasti_run['SWTI_INPUT_MAP'] =='GONG':
    	    given_date_ = datetime.strptime(self.swasti_run['SWTI_MAP_TIME'], "%Y-%m-%d %H:%M")
    	    cr_number = sunpy.coordinates.sun.carrington_rotation_number(given_date_) 
    	    self.cr = int(cr_number)
    	    
    	    CRs = carrington_rotation_time(self.cr + 0.5)
    	    CR_day  = CRs.strftime("%Y%m")       # YYYYMM
            
    	    adaptCR_year_ = given_date_.year
    	    self.CR_time_ = given_date_.strftime("%Y%m%d%H%M") 
    	    self.mg_fname = f'gong_{self.CR_time_}.fts.gz'
    	    
    	    if os.path.exists(self.mg_fname):
    	        print(f"The magnetogram file {self.mg_fname} already exists and will be used for processing")
    	    else:
    	        url = find_gong_file_by_cr(self.cr, CR_day)
    	        try:
    	            urllib.request.urlretrieve(url, self.mg_fname)
    	            print(f"Downloaded the magnetogram from: {url}")
    	        except Exception as e:
    	            print(f"Failed to download from {url}: {e}")
    	else:
    	    print("Map should be GONG or ADAPT")
    	    exit()
            
    def process_map_data(self):
    	if S.swasti_run['SWTI_INPUT_MAP'] =='ADAPT':
            adapt_fits_ = fits.open(self.mg_fname)
            data_header_pairs_ = [(map_slice, adapt_fits_[0].header) for map_slice in adapt_fits_[0].data]
            mid_cr_ = adapt_fits_[0].header['MAPCR']
            end_cr_ = adapt_fits_[0].header['MAPCREDG']
            adaptMapseq_ = []
            for i in range(len(data_header_pairs_)):
                map_scrh_ = sunpy.map.GenericMap(data_header_pairs_[i][0], data_header_pairs_[i][1])
                map_scrh_.meta['ctype1'] =  'CRLN-CAR'
                map_scrh_.meta['ctype2'] =  'CRLT-CAR'
                map_scrh_.meta['rsun_ref'] = 6.957e8   # meters (IAU nominal)
                adaptMapseq_.append(map_scrh_)
            aMap_car_ = adaptMapseq_[6]
            self.input_map = pfsspy.utils.car_to_cea(aMap_car_, method='interp') # This is ADAPT Input Map required for PFSSPY
    	elif S.swasti_run['SWTI_INPUT_MAP'] =='GONG':
            gong_map = sunpy.map.Map(self.mg_fname)
            mid_cr_ = gong_map.meta.get('CRCENTER', 'Default Value')
            end_cr_ = gong_map.meta.get('CREDGE', 'Default Value')
            gong_map.meta['bunit'] = 'G'
            gong_map.meta['cunit1'] = 'degree'
            self.input_map = sunpy.map.Map(gong_map.data-np.mean(gong_map.data), gong_map.meta)
    	else:
            print("Map should be GONG or ADAPT")
            exit()
    	    
    	start_cr_ = 2*mid_cr_ - end_cr_
    	self.t_start = sunpy.coordinates.sun.carrington_rotation_time(start_cr_)
    	self.t_end = sunpy.coordinates.sun.carrington_rotation_time(end_cr_)
    	self.t_mid = sunpy.coordinates.sun.carrington_rotation_time(mid_cr_)
    	print("Map Starting Time : ", self.t_start.value)
    	print("Map Ending Time : ", self.t_end.value)
    	print("Map Mid Time:", self.t_mid.value) 
        
   
    def trace_bfields(self):
         #%% Define pfsspy Grid
        nrho_, nth_, nphi_ = 100,180, 360
        rss_, r0_  = 2.50*ac.R_sun, 1.0*ac.R_sun
   
        #%% Solving PFSS to get the Output
        input_ = pfsspy.Input(self.input_map, nrho_, (rss_/ac.R_sun).value)
        self.output = pfsspy.pfss(input_)      
        
        #%% Generating meshgrid to trace open fieldlines
        # Create 1D theta, phi arrays
        phi_ = np.linspace(0.0, 2.0*np.pi, nphi_)
        phi_ = phi_[:-1] + np.diff(phi_) / 2
        theta_ = np.arcsin(np.linspace(-0.98, 0.98, nth_, endpoint=False) + 1/nth_)
        theta_, phi_ = np.meshgrid(theta_, phi_, indexing='ij')
        self.theta, self.phi = theta_ * u.rad, phi_ * u.rad
        

        # Mesh into 2D arrays
        seeds_op_ = SkyCoord(radius=rss_, lat=self.theta.ravel(), lon=self.phi.ravel(),
                    frame=self.output.coordinate_frame)
        seeds_cl_ = SkyCoord(radius=r0_, lat=self.theta.ravel(), lon=self.phi.ravel(),
                    frame=self.output.coordinate_frame)

        #%% Generating fieldlines and tracing it
        tracer_ = pfsspy.tracing.FortranTracer(step_size=0.5)
        self.flines = tracer_.trace(seeds_op_, self.output)
        self.flines_cl = tracer_.trace(seeds_cl_, self.output)
    def classify_bfields(self):
        self.mask = self.flines.connectivities.astype(bool).reshape(self.theta.shape)
        self.mask_op = self.flines.connectivities.astype(int)
        mask_cl_ = self.flines_cl.connectivities.astype(int)
        n_cl_ = len(mask_cl_) - np.sum(mask_cl_)
        clf_lat_ = np.zeros(2*n_cl_)
        clf_lon_ = np.zeros(2*n_cl_)
        clf_cnt_ = 0
        for fl in self.flines_cl:
            if fl.is_open:pass
            else:
                crds_ = fl.coords
                if len(crds_)>0:
                    clf_lat_[clf_cnt_] = crds_[0].lat.value # values in degree?
                    clf_lon_[clf_cnt_] = crds_[0].lon.value # values in degree?
                    clf_lat_[clf_cnt_+1] = crds_[-1].lat.value # values in degree?
                    clf_lon_[clf_cnt_+1] = crds_[-1].lon.value # values in degree?
                    clf_cnt_ += 2

        # Get solar surface latitude and B field at those points for open field lines
        self.phi_solar = np.ones_like(self.phi) * np.nan
        self.phi_solar[self.mask] = self.flines.open_field_lines.solar_feet.lon
        self.theta_solar = np.ones_like(self.theta) * np.nan
        self.theta_solar[self.mask] = self.flines.open_field_lines.solar_feet.lat
        self.r_in = np.ones_like(self.theta.value) * ac.R_sun * np.nan
        self.r_in[self.mask] = self.flines.open_field_lines.solar_feet.radius
        self.Br_in = np.ones_like(self.theta.value) * np.nan
        self.Br_in[self.mask] = self.output.get_bvec(self.flines.open_field_lines.solar_feet)[:,0]

        # Get source surface latitude and B field at those points for open field lines
        self.phi_ss = np.ones_like(self.phi) * np.nan
        self.phi_ss[self.mask] = self.flines.open_field_lines.source_surface_feet.lon
        self.theta_ss = np.ones_like(self.theta) * np.nan
        self.theta_ss[self.mask] = self.flines.open_field_lines.source_surface_feet.lat
        self.r_out = np.ones_like(self.theta.value) * ac.R_sun * np.nan
        self.r_out[self.mask] = self.flines.open_field_lines.source_surface_feet.radius
        self.Br_out = np.ones_like(self.theta.value) * np.nan
        self.Br_out[self.mask] = self.output.get_bvec(self.flines.open_field_lines.source_surface_feet)[:,0]

        #To eliminate padded zeros for not valid closed field lines -- Why not valid??
        self.clf_lat_fin = np.trim_zeros(clf_lat_)
        self.clf_lon_fin = np.trim_zeros(clf_lon_)
    def wsa_params(self):
        self.d_2D = np.zeros(len(self.theta_ss[self.mask]))
        for i in range(len(self.theta_ss[self.mask])):
            self.d_2D[i] = Compute_MinAngularDistance(self.theta_solar[self.mask][i].value,\
                                                      self.phi_solar[self.mask][i].value,\
                                                      self.clf_lat_fin, self.clf_lon_fin)
        self.exp_fac = self.r_in[self.mask]*self.r_in[self.mask]*self.Br_in[self.mask]
        self.exp_fac *= 1./(self.r_out[self.mask]*self.r_out[self.mask]*self.Br_out[self.mask])
    def get_2D_fields(self):
        #Define new grid for input to PLUTO/HuX
        dt_ = self.t_end - self.t_start
        n_hr_ = int(dt_.value * 24)
        ny_ = 150
        x_ = np.linspace(0.0, 2.0*np.pi, n_hr_)
        y_ = np.linspace(-(75.0/180.0)*np.pi, (75/180.)*np.pi, ny_)  #Open fieldlines start from around +/-77 deg
        xx_, yy_ = np.meshgrid(x_, y_, indexing='ij')

        #Remove duplicated from theta and phi and d_2D, exp_fac : np.unique
        points_ = np.stack(([p.value for p in self.phi_ss[self.mask]], 
                            [t.value for t in self.theta_ss[self.mask]]), axis=1)

        #Interpolate D and fs on the new grid.
        self.d_2D_arr =  interpolate.griddata(points_, self.d_2D, (xx_, yy_), method='linear',fill_value=np.median(self.d_2D))
        self.fs_2D_arr = interpolate.griddata(points_, np.abs(self.exp_fac), (xx_, yy_), method='linear',fill_value=np.median(self.exp_fac))
        
        #Obtain the points on Sun corresponding to location of Earth at L1.
        obs_time_ = self.t_start + dt_*np.linspace(10**(-6), 1-10**(-6), n_hr_)#, endpoint=False)
        self.SBElat = np.zeros(len(obs_time_))
        self.SBElon = np.zeros(len(obs_time_))
        for i in range(len(obs_time_)):
            coord = sunpy.coordinates.ephemeris.get_earth(time=obs_time_[i]).transform_to(frames.HeliographicCarrington(observer='earth'))
            self.SBElat[i] = coord.lat.value*(np.pi/180.) # in radians
            self.SBElon[i] = coord.lon.value*(np.pi/180.) # in radians

        d_function = interpolate.RegularGridInterpolator((x_, y_), self.d_2D_arr)
        d_sbe = np.zeros(n_hr_)
        d_sbe = d_function((self.SBElon,self.SBElat))
        self.wsa_inputs.update({'SWTI_WSA_W':float(np.median(d_sbe))})

        v_2D_arr = Compute_WSAVelocity(self.wsa_inputs, self.d_2D_arr, self.fs_2D_arr) # This is WSA velocity on new grid
        Br_rss_2D = interpolate.griddata(points_, self.Br_out[self.mask], (xx_, yy_), method='nearest') # This is Br value on new grid

        return x_, y_, v_2D_arr, Br_rss_2D
    def get_hux_velocity(self, x, y, v2D):
        dt_ = self.t_end - self.t_start
        n_hr_ = int(dt_.value * 24)
        v_function = interpolate.RegularGridInterpolator((x, y), v2D)
        v_sbe = np.zeros(n_hr_)
        v_sbe = v_function((self.SBElon, self.SBElat))
        n_r, n_phi = 1024, len(self.SBElon)
        R_arr = np.linspace(21.5, 215.0, n_r)
        Phi_arr = np.linspace(np.min(self.SBElon), np.max(self.SBElon), n_phi)###
        V_in_func = interpolate.interp1d(self.SBElon, np.flip(v_sbe), kind='cubic')
        V_in = V_in_func(Phi_arr)

        omega=(2*np.pi)/(dt_.value*24*3600)
        self.V_HUX = Compute_HuX(V_in, R_arr, Phi_arr, omega)
       
        ####### Rotation #######
        r_sun=ac.R_sun.to('km').value
        rot_theta = omega * ((21.5-1.0)*(r_sun)/np.min(v2D))
        rot_deg =   5+(rot_theta*180/np.pi)
        self.rot_index = int(len(Phi_arr)*rot_deg/360)
        V_HUX_ = np.roll(self.V_HUX[-1,:], -self.rot_index)
        self.V_HUX = np.flip(V_HUX_)
    def write_earth_latitudes(self, fname_):
        dt_ = self.t_end - self.t_start
        n_5min = int(dt_.value * 24 * 12)  # 5-minute intervals
        obs_time_ = self.t_start + dt_ * np.linspace(10**(-6), 1 - 10**(-6), n_5min, endpoint=True)
        with open(fname_, "w") as fg:
            for t in obs_time_:
                # Calculate Earth's latitude in Heliographic Carrington coordinates
                coord = sunpy.coordinates.ephemeris.get_earth(time=t).transform_to(
                    frames.HeliographicCarrington(observer='earth'))
                lat_radians = (90 + coord.lat.value) * np.pi / 180
                fg.write(f"{lat_radians:.5f}\n")
    def write_mhd_input(self,Br_rss_2D, fsw_param, fpath = "MHD_Input"):
        r_beg, r_end, nr_mhd = 0.1, 2.1, 150
        dt_ = self.t_end - self.t_start
        n_hr_ = int(dt_.value * 24)
        ny_ = 150        
        v_mhd = Compute_WSAVelocity(self.wsa_inputs, self.d_2D_arr, self.fs_2D_arr) 
        v_mhd = np.roll(v_mhd, -self.rot_index, axis=0)
        v_rot = 0.1*ac.au.to('km').value * ((2*np.pi)/(dt_.value*24*3600))     #km/s 

        #V_fsw is in km/s and B_fsw is in nT.
        Br_mhd = np.sign(np.roll(Br_rss_2D, -self.rot_index, axis=0))*fsw_param['B_fsw']*(v_mhd/fsw_param['V_fsw'])
        Bp_mhd = np.zeros(shape=((Br_mhd).shape))
        y_ = np.linspace(-(75.0/180.0)*np.pi, (75/180.)*np.pi, ny_)  
        for i in range (0, ny_):
            Bp_mhd[:,i] = -(Br_mhd[:,i]/v_mhd[:,i])*v_rot*np.sin(y_[i]*np.pi/180)

        del_r = (r_end-r_beg)/(nr_mhd)               
        ntheta = ny_+1
        nphi = n_hr_+1
        r_mhd = np.linspace(r_beg-2.0*del_r, r_beg+2.0*del_r, 4, endpoint=True)
        phi_mhd = np.linspace(0.0, 2.0*np.pi, nphi)
        th_mhd = np.linspace(0.5*np.pi-(-75.0/180.0)*np.pi, 0.5*np.pi-(75/180.)*np.pi, ntheta)

        mg_date_ = datetime.strptime(self.swasti_run['SWTI_MAP_TIME'], "%Y-%m-%d %H:%M")
        mg_time_ = mg_date_.strftime("%Y%m%d%H%M")
        ###################################### SAVING GRID.OUT #####################################
        fg1 = open(fpath+"/"+"grid_"+mg_time_+".out", "w")
        fg1.write("# DIMENSIONS: \t3\n")
        fg1.write("# GEOMETRY: \tSPHERICAL\n")
        fg1.write("3\n")
        for i in range(0, 3):
            fg1.write("%d\t%lf\t%lf\n"%(i+1, r_mhd[i], r_mhd[i+1]))
        n_theta = 0
        fg1.write("%d\n"%(ntheta-1))
        for i in range(ntheta-2, -1, -1):   # NOTE THIS IS GOING REVERSE TO ENSURE +90 degree (Mag) --> 0 (PLUTO Grid)
            n_theta += 1
            fg1.write("%d\t%lf\t%lf\n"%(n_theta, th_mhd[i+1], th_mhd[i]))
        n_phi=0
        fg1.write("%d\n"%(nphi-1))
        for i in range(0, nphi-1):
            n_phi += 1
            fg1.write("%d\t%lf\t%lf\n"%(n_phi, phi_mhd[i], phi_mhd[i+1]))
        fg1.close()

        ###################################### SAVING INPUT FIELDS #####################################
        Br_input = np.empty([Br_mhd.shape[0], Br_mhd.shape[1], 3])
        Bp_input = np.empty([Bp_mhd.shape[0], Bp_mhd.shape[1], 3])
        v_input = np.empty([v_mhd.shape[0], v_mhd.shape[1], 3])
        for i in range (0, 3):
            Br_input[:,:,i] = Br_mhd
            Bp_input[:,:,i] = Bp_mhd
            v_input[:,:,i] = v_mhd
        Br_mhd_flt = np.float32(Br_input)
        Br_mhd_flt.tofile(fpath+"/"+"Br_"+mg_time_+".flt", sep="")
        v_mhd_flt = np.float32(v_input)
        v_mhd_flt.tofile(fpath+"/"+"Vr_"+mg_time_+".flt", sep="")
        Bp_mhd_flt = np.float32(Bp_input)
        Bp_mhd_flt.tofile(fpath+"/"+"Bp_"+mg_time_+".flt", sep="")
        latfname = os.path.join(fpath, "Earth_lat_5min_"+mg_time_+".txt")
        self.write_earth_latitudes(latfname)
        
    def generate_grid_file(self,fname='swasti.grd'):

    	try:
    	    with open("swasti.grd", "r") as f:
    	        lines = f.readlines()
    	except Exception as e:
    	    print(f"swasti.grd not found")  
    	    exit()
    	
    	t_start_dt = datetime.strptime(self.t_start.value, "%Y-%m-%d %H:%M:%S.%f")
    	t_end_dt   = datetime.strptime(self.t_end.value, "%Y-%m-%d %H:%M:%S.%f")
    	self.cr_period = (t_end_dt - t_start_dt).total_seconds()
    	cme_onset_time = datetime.strptime(self.cme_inputs["SWTI_CME_onset"], "%Y-%m-%d %H:%M")
    	self.cme_onset = (cme_onset_time - t_start_dt).total_seconds()
    	
    	# Build parameter dict from your parsed dictionaries
    	params = {
    	"SWTI_MAP_DATETIME"   : str(self.CR_time_),
    	"SWTI_MAP_TIMEPERIOD" : str(self.cr_period),
    	"SWTI_Speed_fsw"      : self.wsa_inputs.get("SWTI_WSA_VMAX", "600.0")
    	}
    	if self.swasti_run['SWTI_INCLUDE_CME'] == "YES":
    	    params.update({
    	    "SWTI_CME1_lat"   : self.cme_inputs.get("SWTI_CME_lat", "0.0"),
    	    "SWTI_CME1_lon"   : self.cme_inputs.get("SWTI_CME_lon", "0.0"),
    	    "SWTI_CME1_width" : self.cme_inputs.get("SWTI_CME_width", "0.0"),
    	    "SWTI_CME1_speed" : self.cme_inputs.get("SWTI_CME_speed", "0.0"),
    	    "SWTI_CME1_onset" : str(self.cme_onset),
    	    })
    	#-----------------------
    	# Find [Parameters] section
    	# -----------------------------
    	start = None
    	for idx, line in enumerate(lines):
    	    if line.strip() == "[Parameters]":
    	    	start = idx + 1
    	    	break
    	if start is None:
    	    print("No [Parameters] section found in pluto.ini")
    	    return
    	# -----------------------------
    	# Replace lines until next [Section]
    	# -----------------------------
    	i = start
    	while i < len(lines):
    	    line = lines[i].strip()
    	    # If parameter-like line
    	    if line and not line.startswith("#") and " " in line:
    	    	key = line.split()[0]
    	    	if key in params:
    	    	    # rewrite line with proper spacing
    	    	    value = params[key]
    	    	    lines[i] = f"{key:<22} {value}\n"
    	    i += 1
    	    # Write result back
    	with open("pluto.ini", "w") as f:
    	    f.writelines(lines)
    	    
    def save_ascii_files(self):
        start_dt = self.t_start.to_datetime()
        end_dt   = self.t_end.to_datetime()

        N = len(self.V_HUX)

        # Time step from start to end
        delta = (end_dt - start_dt) / (N - 1)

        date_range = [start_dt + i * delta for i in range(N)]

        # --- Prepare output file ---
        os.makedirs('SWASTi_Results', exist_ok=True)
        filename = os.path.join('SWASTi_Results', 'HuX_result.out')

        # Parse start/end time strings
        start_time = datetime.strptime(self.t_start.value, "%Y-%m-%d %H:%M:%S.%f")
        end_time   = datetime.strptime(self.t_end.value, "%Y-%m-%d %H:%M:%S.%f")

        wsa = self.wsa_inputs

        with open(filename, 'w') as f:
            f.write("Solar Wind Parameters\n")
            f.write("------------------------------------------------\n")
            f.write(f"Start Time: {start_time}\n")
            f.write(f"End Time:   {end_time}\n")
            f.write(f"V_min:      {wsa['SWTI_WSA_VMIN']: <10}\n")
            f.write(f"V_max:      {wsa['SWTI_WSA_VMAX']: <10}\n")
            f.write(f"Beta:       {wsa['SWTI_WSA_BETA']: <10}\n")
            f.write(f"Alpha:      {wsa['SWTI_WSA_ALPHA']: <10}\n")
            f.write(f"W:          {wsa['SWTI_WSA_W']: <10}\n")
            f.write("------------------------------------------------\n")

            # Write header of the velocity table
            f.write("Time, HUX Velocity [km/s]\n")

            # --- Write rows manually ---
            for dt, vel in zip(date_range, self.V_HUX):
                f.write(f"{dt}, {vel}\n")
            
        

if __name__ == "__main__":
    # STEP 0 : STARTING COMPUTATION!
    S = swasti('swasti.ini')

    #STEP 1: 
    start_s1 = time.time()
    print("-----------------------------------------------------------------")
    print("Step 1: Adding Input Magnetogram [%s] ... ... ..."%S.swasti_run['SWTI_INPUT_MAP']) 
    S.get_map_data()
    S.process_map_data()
    end_s1 = time.time()
    print("Step 1 : Adding Input Magnetogram Done - Time Taken : %2.fs"%(end_s1-start_s1))
    print("-----------------------------------------------------------------")

    #STEP 2 : 
    start_s2 = time.time()
    print('Step 2 : Tracing fieldlines ... ... ...')
    S.trace_bfields()
    end_s2 = time.time()
    print("Step 2 : Tracing fieldlines Done - Time Taken : %2.fs"%(end_s2-start_s2))
    print("-----------------------------------------------------------------")

    #STEP 3 :
    start_s3 = time.time()
    print("Step 3 : Classifying fieldlines ... ... ...")
    S.classify_bfields()
    print("Number of Open fieldlines : %d"%(np.sum(S.mask_op)))
    print("Number of Closed fieldlines : %d"%(len(S.clf_lat_fin)//2))
    end_s3 = time.time()
    print("Step 3: Classifying fieldlines Done - Time taken: %2.fs"%(end_s3-start_s3))
    print("-----------------------------------------------------------------")

    #STEP 4 :
    start_s4 = time.time()
    print("Step 4 : Computing WSA parameters ... ... ...")
    S.wsa_params()
    end_s4 = time.time()
    print("Step 4 : Computed WSA paramters Done - Time Taken: %.2fs"%(end_s4-start_s4))
    print("-----------------------------------------------------------------")

    #STEP 5 :
    start_s5 = time.time()
    print("Step 5 : Computing 2D Velocity and B fields ... ... ...")
    x, y, v2D, b2D = S.get_2D_fields()
    end_s5 = time.time()
    print("Step 5 : Computed 2D Velocity and B fields Done - Time Taken: %.2fs"%(end_s5-start_s5))
    print("-----------------------------------------------------------------")

    #STEP 6 :
    start_s6 = time.time()
    print("Step 6 : Computing HuX Velocity ... ... ...")
    S.get_hux_velocity(x, y, v2D)
    end_s6 = time.time()
    print("Step 6 : Computed HuX Velocity Done - Time Taken: %.2fs"%(end_s6-start_s6))
    print("-----------------------------------------------------------------")

    #STEP 7 :
    
    if S.swasti_run['SWTI_RUN_MHD'] =='YES':
        start_s7 = time.time()
        fsw_param = {'V_fsw':650, 'B_fsw':300, 'rho_fsw':200, 'P_in':6}
        print("Step 7 : Creating MHD Input Files ... ... ...")
        mhd_inp_path = "MHD_Input"
        os.makedirs(mhd_inp_path, exist_ok=True)
        S.write_mhd_input(b2D, fsw_param, fpath=mhd_inp_path)
        S.generate_grid_file()
        end_s7 = time.time()
        print("Step 7 : Created MHD Input Files Done - Time Taken:%.2fs"%(end_s7-start_s7))
        print("-----------------------------------------------------------------")
        
    #else:
        #print("No MHD Run selected. SWASTi Run Completed.")
        #print("-----------------------------------------------------------------")


    S.save_ascii_files()
   
    
    
