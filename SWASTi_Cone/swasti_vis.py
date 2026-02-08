import os
import pandas as pd
import glob
import matplotlib.dates as mdates
import shutil
import numpy as np
import matplotlib.pyplot as plt
import imageio.v2 as iio
from datetime import timedelta
from PIL import Image
from io import BytesIO
from matplotlib import gridspec
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import warnings
warnings.filterwarnings("ignore")
import pyPLUTO as pp

with open("/app/swasti_run/SWASTi_Results/HuX_result.out", "r") as file:
    lines = file.readlines()

for line in lines:
    if "Start Time" in line:
        t_start = line.split(":", 1)[1].strip()
    if "End Time" in line:
        t_end = line.split(":", 1)[1].strip()
        
t_start = pd.to_datetime(t_start)
t_end = pd.to_datetime(t_end)

nr, nt, nphi, n_vtk, unit_vel, unit_rho = 150, 61, 181, 125, 250.0, 10.0
folder = "/app/swasti_run/"
output_folder = "/app/swasti_run/SWASTi_Results"
Vr_max, Vr_min, rho_max, rho_min = 1050, 200, 61, 0
mhd_r, mhd_phi, mhd_theta = np.linspace(0.1, 2.1, nr), np.linspace(0, 2 * np.pi, nphi), np.linspace(-np.pi/3, np.pi/3, nt)

phi, r = np.meshgrid(mhd_phi, mhd_r)
theta, r_rt = np.meshgrid(mhd_theta, mhd_r) 


matches = glob.glob("/app/swasti_run/PlasmaParam_L1*.dat")
if not matches:
    raise FileNotFoundError("No file found matching PlasmaParam_L1*.dat")
filepath = matches[0]
dest_path = os.path.join(output_folder, os.path.basename(filepath))
shutil.copy(filepath, dest_path)
with open(dest_path, "r") as f:
    original_data = f.read()

header = (
    "SWASTi MHD results\n"
    "------------------------------------------------\n"
    f"Start Time: {t_start}\n"
    f"End Time:   {t_end}\n"
    "------------------------------------------------\n"
)

with open(dest_path, "w") as f:
    f.write(header + original_data)

    
logo = Image.open("/app/swasti_run/SWASTi_logo.png")

def create_polar_subplot(fig, ax, X, Y, data, vmin, vmax, cmap, xlabel, cbar_label):
    levels = np.linspace(vmin, vmax, 200)
    img = ax.contourf(X, Y, data, levels=levels, vmin=vmin, vmax=vmax, cmap=cmap)
    ax.set_theta_zero_location('E')
    ax.scatter(0, 1, marker='o', s=120, fc='b', ec='white', label='Earth')
    ax.scatter(0, 0, marker='o', s=120, fc='red', label='Sun')
    ax.set_thetagrids(range(0, 360, 60), fontsize=15)
    ax.tick_params(pad=18)
    ax.set_rgrids([1], labels=None, fontsize=0)
    ax.set_xlabel(xlabel, fontsize=15)
    ax.minorticks_on()
    ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1), fontsize=12)
    ax.grid(alpha=0.6)
    cbar = fig.colorbar(img, ax=ax, orientation='vertical', shrink=0.7, pad=0.1, extend='both')
    cbar.set_label(cbar_label, fontsize=15)
    cbar.ax.tick_params(labelsize=14) 

def create_gif(TP, t_start):

    time_factor = 0.04 * 598400

    rphi_path = os.path.join(output_folder, 'SWASTI_MHD_rphi.gif')
    rtheta_path = os.path.join(output_folder, 'SWASTI_MHD_rtheta.gif')

    with iio.get_writer(rphi_path, mode='I', duration=0.2) as writer_rphi, \
         iio.get_writer(rtheta_path, mode='I', duration=0.2) as writer_rtheta:

        for j in range(0, 200):

            time_sec = (j * time_factor) - TP
            if time_sec <= 0:
                continue

            current_time = t_start + timedelta(seconds=time_sec)
            time_str = current_time.strftime("%d/%m/%Y %H:%M:%S")

            D_mhd = pp.Load(path=folder, nout=j, datatype='vtk', text=False)

            # ================= r–phi plot =================
            fig = plt.figure(figsize=(15, 8))
            gs = gridspec.GridSpec(1, 2, top=0.97, bottom=0.06, left=0.06, right=0.94, wspace=0.2)
            ax1 = fig.add_subplot(gs[0, 0], projection='polar')
            ax2 = fig.add_subplot(gs[0, 1], projection='polar')

            create_polar_subplot(fig, ax1, phi, r, D_mhd.rho[:, 30, :] * unit_rho * r**2, rho_min, rho_max, 'Spectral_r', "(a)", "Scaled Density [N/cm]")

            create_polar_subplot(fig, ax2, phi, r, D_mhd.vx1[:, 30, :] * unit_vel, Vr_min, Vr_max, 'Spectral_r', "(b)", "Velocity [km/s]")

            plt.figtext(0.5, 0.02, f"Time: {time_str}", ha="center", fontsize=20)
            fig.add_artist(AnnotationBbox(OffsetImage(logo, zoom=0.15),(0.07, 0.9), xycoords='figure fraction', frameon=False))

            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=300)
            buf.seek(0)
            writer_rphi.append_data(iio.imread(buf))
            plt.close(fig)

            # ================= r–theta plot =================
            fig = plt.figure(figsize=(15, 8))
            gs = gridspec.GridSpec(1, 2, top=0.97, bottom=0.06,
                                   left=0.06, right=0.94, wspace=0.2)
            ax1 = fig.add_subplot(gs[0, 0], projection='polar')
            ax2 = fig.add_subplot(gs[0, 1], projection='polar')

            create_polar_subplot(fig, ax1, theta, r_rt, D_mhd.rho[:, :, 0] * unit_rho * r_rt**2, rho_min, rho_max, 'Spectral_r', "(a)", "Scaled Density [N/cm]")

            create_polar_subplot(fig, ax2, theta, r_rt, D_mhd.vx1[:, :, 0] * unit_vel, Vr_min, Vr_max, 'Spectral_r', "(b)", "Velocity [km/s]" )

            ax1.set_thetamin(-90)
            ax1.set_thetamax(90)
            ax2.set_thetamin(-90)
            ax2.set_thetamax(90)

            plt.figtext(0.5, 0.02, f"Time: {time_str}", ha="center", fontsize=20)
            fig.add_artist(AnnotationBbox(OffsetImage(logo, zoom=0.15),(0.07, 0.9), xycoords='figure fraction', frameon=False))

            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=300)
            buf.seek(0)
            writer_rtheta.append_data(iio.imread(buf))
            plt.close(fig)

            del D_mhd

    print("SWASTI_MHD_rphi.gif and SWASTI_MHD_rtheta.gif saved")



CR_time_period = (t_end - t_start).total_seconds()

create_gif(CR_time_period, t_start)    
    
D0_cone = pd.read_csv(filepath, sep="\t")

def convert_to_datetime(df, start_time):

    t0_code = df['#  t [sec]']
    df['t0_dt'] = start_time + pd.to_timedelta(t0_code, unit='s')
    return df

uvel = 1.0
urho = 1.0
uT = 7.517e+06 / 1.0e6
umag = 1.0

D0_cone = convert_to_datetime(D0_cone, t_start)
D0_cone['BMAG'] = np.sqrt(D0_cone['B1 [nT]']**2 + D0_cone['B2 [nT]']**2 + D0_cone['B3 [nT]']**2)
D0_cone['Temp'] = (D0_cone['PRS [nPa]'] / D0_cone['RHO [cm^-3]']) * uT

fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
colors = ['green', 'blue', 'red']
labels = ["Velocity (km/s)", "Density (cm⁻³)", "IMF (nT)"]

mask_v = D0_cone['V1 [km/s]'] != 0
axes[0].plot(D0_cone['t0_dt'][mask_v], D0_cone['V1 [km/s]'][mask_v] * uvel, color=colors[0], linewidth=1.5, label="Velocity")
axes[0].set_ylabel(labels[0], fontsize=16)
axes[0].legend(fontsize=16)
axes[0].tick_params(axis='x', labelsize=14)
axes[0].tick_params(axis='y', labelsize=14)

mask_rho = D0_cone['RHO [cm^-3]'] != 0
axes[1].plot(D0_cone['t0_dt'][mask_rho], D0_cone['RHO [cm^-3]'][mask_rho] * urho, color=colors[1], linewidth=1.5, label="Density")
axes[1].set_ylabel(labels[1], fontsize = 16)
axes[1].legend(fontsize=16)
axes[1].tick_params(axis='x', labelsize=14)
axes[1].tick_params(axis='y', labelsize=14)

mask_b = D0_cone['BMAG'] != 0
axes[2].plot(D0_cone['t0_dt'][mask_b], D0_cone['BMAG'][mask_b] * umag, color=colors[2], linewidth=1.5, label="IMF")
axes[2].set_ylabel(labels[2], fontsize = 16)
axes[2].legend(fontsize=16)
axes[2].tick_params(axis='x', labelsize=14)
axes[2].tick_params(axis='y', labelsize=14)
axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

plt.xticks(rotation=45)
plt.minorticks_on()
fig.suptitle(f"SWASTi MHD", fontsize=20, fontweight='bold')

logo_box = OffsetImage(logo, zoom=0.12)
annotation_box = AnnotationBbox(logo_box, (0.95, 0.9), xycoords='figure fraction', frameon=False)
fig.add_artist(annotation_box)

plt.subplots_adjust(left=0.1, right=0.9, top=0.95, bottom=0.1, hspace=0.15)
output_path1 = os.path.join(output_folder,'Analysis.png')
plt.savefig(output_path1, dpi=300)
print("Analysis.png saved")
plt.close()



