# 🌞 **SWASTi**

Space Weather Adaptive Simulation (SWASTi) framework is a three-dimensional physics based heliospheric model intended for space weather analysis and modelling.
<p align="center">
<img src=./SWASTI.jpg width="500" height = "550">
</p>

This system integrates a semi-empirical coronal domain with a PLUTO code-based MHD heliospheric domain ([Mignone et al. 2007](https://doi.org/10.1086/513316)) , enabling simulations from the solar corona to the interplanetary medium. The CME module is incorporated into a self-consistent solar wind background in SWASTi. SWASTi does it using the following steps (1-3 for setting up solar wind and 4th is an optional CME injection.)

1. The ambient solar wind module of SWASTi employs photospheric magnetograms (GONG, ADAPT, etc.) as observational inputs. The Potential Field Source Surface (PFSS) model ([Altschuler & Newkirk 1969](https://doi.org/10.1007/bf00145734),  [Stansby et al. 2020](https://doi.org/10.21105/joss.02732)) is employed to determine the global magnetic field structure in the lower solar corona (from 1 to 2.5 R).

2. The WSA model ([Arge 2003](https://doi.org/10.1063/1.1618574)) is implemented to establish inner boundary conditions at 21.5 R for the onward MHD-based heliospheric domain. In particular, the WSA model generates the velocity profile at 0.1 AU for a given magnetic flux tube. 

3. The PLUTO code is employed to implement the heliospheric model (0.1-2.1 AU) using finite-volume methods to solve the ideal MHD equations. SWASTi also utilises the Heliospheric Upwind eXtrapolation (HUX) model ([Riley & Lionello 2011](https://doi.org/10.1007/s11207-011-9766-x)) as an alternative method for modelling the inner heliosphere. 

4. We model CMEs in SWASTi using an elliptical cone method. This model represents the CME as a simple, non-magnetic ellipsoidal structure, which is introduced into the MHD domain as a homogeneous plasma cloud with uniform radial velocity ($V_{CME}$), constant density ($\rho_{CME}$), and temperature ($T_{CME}$). For more details, please refer to [Mayank et al. (2022)](https://doi.org/10.3847/1538-4365/ac8551),
[Mayank et al. (2023)](https://doi.org/10.3847/1538-4365/ad08c7) and [Mayank et al. (2025)](https://doi.org/10.1007/s12036-025-10107-2)

<br>

---

## 📦 Installation

⚠️ **Platform Compatibility:** Currently, **SWASTi is only compatible with Linux-based systems**.

### Prerequisites

Before proceeding, ensure that **Docker Engine** is installed and running on your system.

* **Check Installation:** Run `docker --version` in your terminal. If the command is not found, install Docker Engine from the [official website](https://docs.docker.com/engine/install/ubuntu/).
* **Linux Permissions:**
    > **Note:** If you receive a *'permission denied'* error when running Docker commands, configure your system to run Docker as a non-root user by following [these post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/).

---

### Setup Steps

To set up SWASTi, follow these steps to prepare the environment:

1.  **Pull the Docker Image**
    
    Retrieve the official SWASTi image from Docker Hub by running:

    `docker pull pravahiiti/swasti:latest`
   

2.  **Download Required Files**
    
    You need to download two specific files from the [SWASTi GitHub Repository](https://github.com/pravah-iiti/SWASTi) and place them in your working directory:

    * `swasti.ini`: The initialization and configuration file.
    * `swasti_run.sh`: The bash script used to load the configuration and execute the simulation within the Docker container.

<br>

---

## Contributors

<br>

- PI : Dr. Bhargav Vaidya (PI Pravah lab, IIT Indore)
- Developer : Dr. Prateek Mayank (NASA Jack Eddy Postdoctoral Fellow at UCAR CPAESS & SWx TREC, University of Colorado Boulder)  

  **Contributors**  
- Dr. Argyadeep Paul (Post-doc fellow, Université Paris-Saclay)
- Jithu J Athalathil (PhD Pravah lab, IIT Indore)
- Navanit A V (MSc Pravah lab, IIT Indore)
- Sirsha Nandy (PhD Pravah lab, IIT Indore)
- Aniket Sharma (PhD Pravah lab, IIT Indore)
- Asif Mohamed Mandayapuram (PhD Pravah lab, IIT Indore and Scientist SAC,ISRO)

<br>

---

## 🚀 How to Run

<br>

1. **Configure the simulation**

    Edit the `swasti.ini` file as described in the [Configuration Guide](https://github.com/pravah-iiti/SWASTi/tree/main#%EF%B8%8F-configuration-guide) section below.  
  
    SWASTi can either use a magnetic field map provided by the user or automatically download the required map from the source. If a map file is not provided, SWASTi will automatically download the appropriate map based on the settings in swasti.ini.
    
    If you want to provide your own map, place the map file in the same directory as swasti.ini. The map file must follow the naming convention:

    inputmap_YYYYMMDDHHmm.fts.gz

    where:

        - inputmap must be either adapt or gong (in lower case) and must match the value of SWTI_INPUT_MAP in swasti.ini

        - YYYYMMDDHHmm must exactly match the value of SWTI_MAP_TIME specified in swasti.ini

    If the date and time in the map filename do not match *SWTI_INPUT_MAP* AND *SWTI_MAP_TIME*, SWASTi will ignore the local map file and attempt to download the required map automatically.


2. **Run SWASTi**

    Execute the main script which runs the SWASTi simulation inside the docker.
  
    `bash ./swasti_run.sh &`

    This creates a container named `SWASTi_Run_{TIME}` where TIME is the start time of the script execution and runs SWASTi inside it. The active container details can be checked with the command `docker ps`.

3. **Copy files from the Docker container**

    After the run completes, you can copy the files to your local system:
 
    `docker cp <container_name>:/app/swasti_run/ <local_destination>`

    These files containes VTK files with the complete 3D outputs from the MHD PLUTO run.

4. **Clean up files**

    To remove the container permanently:
 
    `docker rm <container_name>`


<br>

---

## Simulation Domain and Output Details 

<br>

The SWASTi simulation domain extends up to 2.1 AU in the radial direction.  

The spatial extent of the MHD simulation domain is as follows:
- Radial: 0.1 to 2.1 AU, with 150 grids
- Latitude: −60° to +60°, with a resolution of 2°
- Longitude: 0° to 360°, with a resolution of 2°

When the MHD simulation is enabled:

3D MHD output files are generated with a time cadence of 6.648 hours.  
Plasma parameters extracted at the L1 point are saved with a cadence of 5 minutes in the file `PlasmaParam_L1_YYYYMMDDHHmm.dat`.

<br>

---

## Solar Wind and CME Parameters

<br>

The fast solar wind speed in the MHD simulation is set equal to the peak WSA speed specified in the swasti.ini file.

- The background solar wind plasma number density is fixed at $200 \rm{cm}^{−1}$
- The background thermal pressure is kept constant at $6.0 \rm{nPa}$
- The CME density at injection is set to $2.0 \times 10^{-21} \rm{gcm}^{-3}$
- The CME temperature at injection is $0.8 \rm{MK}$

<br>

---

## 📊 Results & Analysis

<br>

All simulation outputs are written to a timestamped directory named: **`SWASTi_outputs_{SWTI_MAP_TIME}`**, where the value of *SWTI_MAP_TIME* is as specified in *swasti.ini*.

```text
SWASTi_outputs_YYYYMMDDTHHmm/
├── 📄 HuX_result.out                   # HUX model output
├── 📄 PlasmaParam_L1_YYYYMMDDHHmm.dat  # MHD plasma parameters at L1
├── 🖼️ Analysis.png                     # Time series at Earth (V, ρ, B)
├── 🎞️ SWASTI_MHD_rphi.gif              # Ecliptic plane evolution
├── 🎞️ SWASTI_MHD_rtheta.gif            # Meridional plane evolution
├── 📝 swasti_mhd.log                   # PLUTO MHD simulation log
└── 📝 swasti_run.log                   # SWASTi execution log

```


<br>

### `HuX_result.out`
Contains the solar wind parameters obtained from the HUX model run.

**Columns:** 
- Time [ $\rm{UTC}$ ]
- HUX Velocity [ $\rm{km/s}$ ]

<br>

### `PlasmaParam_L1_YYYYMMDDHHmm.dat`
Contains plasma parameters at L1 extracted from the MHD simulation.

**Columns:** 
- t [ $\rm{sec}$ ] Time since the Start Time as noted in the header
- V1 [ $\rm{km/s}$ ] Velocity component x
- V2 [ $\rm{km/s}$ ] Velocity component y
- V3 [ $\rm{km/s}$ ] Velocity component z
- B1 [ $\rm{nT}$ ] Magnetic field component x
- B2 [ $\rm{nT}$ ] Magnetic field component y
- B3 [ $\rm{nT}$ ] Magnetic field component z
- PRS [ $\rm{nPa}$ ] Plasma pressure
- RHO [ $\rm{cm}^{-3}$ ] Plasma density

⚠️ The file is generated only if *SWTI_RUN_MHD* = *YES*.

<br>

### `Analysis.png`
- Solar wind bulk speed
- Plasma density
- Magnetic field components

⚠️ The file is generated only if *SWTI_RUN_MHD* = *YES*.

<br>

### `SWASTI_MHD_rphi.gif`
Shows the temporal evolution of:
- Scaled plasma density
- Bulk speed  

in the **ecliptic plane** ($\rm{r}-\phi \ \rm{plane}$). 

⚠️ The file is generated only if *SWTI_RUN_MHD* = *YES*.

<br>


### `SWASTI_MHD_rtheta.gif`
Shows the temporal evolution of:
- Scaled plasma density
- Bulk speed  

in the **Meridional plane**, passing through Earth ($\rm{r}-\theta \ \rm{plane}$).

⚠️ The file is generated only if *SWTI_RUN_MHD* = *YES*.

<br>

### `swasti_mhd.log`
Log file for the PLUTO MHD simulation, including solver status and runtime information.

⚠️The file is generated only if *SWTI_RUN_MHD* = *YES*.

<br>

### `swasti_run.log`
Main SWASTi execution log, recording configuration parsing, model execution steps, and workflow status.


<br>

---

## ⚙️ Configuration Guide

<br>

All runtime parameters for SWASTi are controlled through the **`swasti.ini`** file.
This document explains each section and parameter in detail.

<br>


## `[SWASTi Run]` Section


<br>

### **SWTI_INPUT_MAP**:

**Options:** `ADAPT` | `GONG`

**Description:** Specifies the magnetic field map source.

* `ADAPT` → Uses ADAPT magnetic field maps
* `GONG`  → Uses GONG synoptic maps

<br>

### **SWTI_MAP_TIME**: 

**Format:** `YYYY-MM-DD HH:mm`

**Behavior:**

* If `SWTI_INPUT_MAP = ADAPT`
  → Treated as the central meridian time. Ensure a valid ADAPT map exists.

* If `SWTI_INPUT_MAP = GONG`
  → The Carrington Rotation containing this time is automatically selected.

<br>

### **SWTI_RUN_MHD**:

**Options:** `YES` | `NO`

* `YES` → Runs the PLUTO MHD model (full MHD output)
* `NO`  → Runs HUX solar wind model only

<br>

### **SWTI_NPROCS**:

**Type:** Integer

**Description:** Number of CPU cores used for the PLUTO MHD simulation.

⚠️ Applicable only when  `SWTI_RUN_MHD = YES`, otherwise ignored

<br>

**SWTI_INCLUDE_CME**:

**Options:** `YES` | `NO`

* `YES` → Injects a CME using specified CME parameters
* `NO`  → No CME included

⚠️ *Applicable only when* `SWTI_RUN_MHD = YES`, otherwise ignored

<br>


## `[WSA Parameters]` Section

<br>

Controls the Wang-Sheeley-Arge (WSA) solar wind speed model.

$V_{SW} = V_{min} + \frac{V_{max}}{ (1 + f_{s})^\alpha } \times \left[ (1.0-0.8\times e^{-(\frac{D}{w})^\beta})^3\right]$


| Symbol | Description                               |
| ------ | ----------------------------------------- |
| $V_{SW}$ | Solar wind speed (km/s)                 |
| $f_s$  | Areal expansion factor                    |
| D    | Angular distance to coronal hole boundary   |

<br>

### **SWTI_WSA_ALPHA**:

**Type:** Float

**Description:** WSA parameter **$\alpha$**

<br>

### **SWTI_WSA_BETA**:

**Type:** Float

**Description:** WSA parameter **$\beta$**

<br>

### **SWTI_WSA_VMIN**:

**Type:** Float

**Description:** WSA parameter $V_{min}$

<br>

### **WTI_WSA_VMAX**:

**Type:** Float

**Description:** WSA parameter $V_{max}$

<br>

## `[CME Parameters]` Section

All the values should be in the Heliocentric Earth Equatorial (HEEQ). The HEEQ coordinate system is a Sun-centered reference frame in which longitude is measured from the Sun-Earth line and latitude is measured relative to the solar equatorial plane. 

<br>

### **SWTI_CME_lat**: 

**Type:** Float

**Description:** CME latitude (degrees)

**Range:** `-60 → 60` 

Although SWASTi allows latitude inputs between −90° and 90°, the simulation domain spans only −60° to 60°. CMEs specified outside the simulation bounds may be only partially represented within the domain and should be avoided.

<br>

### **SWTI_CME_lon**:

**Type:** Float

**Description:** CME longitude (degrees)

**Range:** `0 → 360`

<br>

### **SWTI_CME_width**:

**Type:** Float

**Description:** Half angular width of the CME (degrees)

**Range:** `0 → 90`

<br>

### **SWTI_CME_speed**:

**Type:** Float

**Description:** Initial CME injection speed (km/s)

**Range:** `>= 0`

<br>

### **SWTI_CME_onset**:

**Format:** `YYYY-MM-DD HH:mm`

**Description:** CME injection time at **21.5 solar radii** 

<br>

---

## ©️ Citation and Usage Policy 

<br>

If you use any data, results, figures, or derived products from these SWASTi simulations
in publications, presentations, or reports, please cite the following papers:

- [Mayank et al. (2022)](https://doi.org/10.3847/1538-4365/ac8551)
- [Mayank et al. (2023)](https://doi.org/10.3847/1538-4365/ad08c7)
- [Mayank et al. (2025)](https://doi.org/10.1007/s12036-025-10107-2)


Proper citation is required for any scientific or public use of the simulation outputs.

<br>

---

## 📧 Contact Information 

<br>

For further details or collaboration related to SWASTi simulations, please contact:

Dr. Bhargav Vaidya  
Pravah Lab  
Department of Astronomy, Astrophysics and Space Engineering    
Indian Institute of Technology Indore  

Email: bvaidya@iiti.ac.in

<br>

---

## About Us 

<br>

The SWASTi codebase and all associated simulation frameworks are developed and
maintained at `Pravah Lab`, Department of Astronomy, Astrophysics and
Space Engineering, Indian Institute of Technology Indore (IIT Indore).

Pravah Lab focuses on numerical modeling of astrophysical jets, heliophysics, space weather,
and astrophysical plasma simulations.

---

