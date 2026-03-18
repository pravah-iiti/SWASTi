#define  PHYSICS                        MHD
#define  DIMENSIONS                     3
#define  GEOMETRY                       SPHERICAL
#define  BODY_FORCE                     VECTOR
#define  COOLING                        NO
#define  RECONSTRUCTION                 LINEAR
#define  TIME_STEPPING                  RK2
#define  NTRACER                        1
#define  PARTICLES                      NO
#define  USER_DEF_PARAMETERS            10

/* -- physics dependent declarations -- */

#define  EOS                            IDEAL
#define  ENTROPY_SWITCH                 NO
#define  DIVB_CONTROL                   EIGHT_WAVES
#define  BACKGROUND_FIELD               NO
#define  AMBIPOLAR_DIFFUSION            NO
#define  RESISTIVITY                    NO
#define  HALL_MHD                       NO
#define  THERMAL_CONDUCTION             NO
#define  VISCOSITY                      NO
#define  ROTATING_FRAME                 NO

/* -- user-defined parameters (labels) -- */

#define  SWTI_MAP_DATETIME              0
#define  SWTI_Speed_fsw                 1
#define  SWTI_Density_fsw               2
#define  SWTI_Pressure_in               3
#define  SWTI_MAP_TIMEPERIOD            4
#define  SWTI_CME1_lat                  5
#define  SWTI_CME1_lon                  6
#define  SWTI_CME1_width                7
#define  SWTI_CME1_speed                8
#define  SWTI_CME1_onset                9

/* [Beg] user-defined constants (do not change this line) */

#define  WARNING_MESSAGES               NO
#define  UNIT_VELOCITY                  250.0e5
#define  UNIT_DENSITY                   (10.0*CONST_mp)
#define  UNIT_LENGTH                    CONST_au
#define  ID_NZ_MAX                      654
#define  POST_PROCESSING                NO
#define  INTERNAL_BOUNDARY              YES

/* [End] user-defined constants (do not change this line) */
