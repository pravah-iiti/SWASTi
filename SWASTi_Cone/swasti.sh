#!/bin/bash
cd /app/swasti_run || exit 1
if [ -d "SWASTi_Results" ]; then
	exit 0
fi

if [ -f swasti.ini ]; then

    LOGFILE="swasti_run.log"
    exec > >(tee -a "$LOGFILE") 2>&1

    echo "-----------------------------------------------------------------"
    echo "          ███████╗██╗    ██╗ █████╗ ███████╗████████╗ ██         "
    echo "          ██╔════╝██║    ██║██╔══██╗██╔════╝╚══██╔══╝            "
    echo "          ███████╗██║ █╗ ██║███████║███████╗   ██║    ██         "
    echo "          ╚════██║██║███╗██║██╔══██║╚════██║   ██║    ██         "
    echo "          ███████║╚███╔███╔╝██║  ██║███████║   ██║    ██         "
    echo "          ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝   ╚═╝               "
    echo "-----------------------------------------------------------------"
    echo "                   Starting SWASTi Computation..."
    echo "-----------------------------------------------------------------"
    sleep 1
    
    CURRENT_TIME=$(date -u +"%Y-%m-%d %H:%M:%S")
    echo "UTC time: $CURRENT_TIME"

    python -u swasti.py
    status=$?
    if [ $status -ne 0 ]; then
        echo "SWASTi coronal model run failed with exit code $status"
        exit 1
    fi


    MHD_RUN=$(grep -i 'SWTI_RUN_MHD' swasti.ini | cut -d ':' -f 2 | tr -d '[:space:]')
    if [ "$MHD_RUN" = "YES" ]; then
        if [ -f pluto.ini ]; then
            N_proc=$(grep -i 'SWTI_NPROCS' swasti.ini | cut -d ':' -f 2 | tr -d '[:space:]')
            N_proc=${N_proc:-4}
            echo "Step 8 : Starting SWASTi MHD Run with $N_proc processors"
            mpiexec -n "$N_proc" ./pluto -no-x3par > /dev/null 2>&1
            status=$?
            echo "MHD log data in swasti_mhd.log"

            if [ $status -eq 0 ]; then
                echo "Step 8 : SWASTi MHD Run completed"
            else
                echo "Step 8 : SWASTi MHD run aborted with exit code $status"
                exit 1
            fi
        
            echo "-----------------------------------------------------------------"
            echo "Step 9 : Visualizing SWASTi MHD results"
            python -u swasti_vis.py
            status=$?
        
            if [ $status -ne 0 ]; then
                echo "Step 9 : Visualization failed with error code $status"
                exit 1
            else
                echo "Step 9 : Visualization SWASTi MHD results completed"
            fi

            echo "Copying data and sleep for 2 minutes"
            sleep 120
            echo "SWASTi simulation completed"
            echo "-----------------------------------------------------------------"
            exit 0
            
        else
            echo "pluto.ini not found"
            echo "!SWASTi simulation exited"
            echo "-----------------------------------------------------------------"
            exit 1
        fi
    else
        echo "NO MHD run selected"
        echo "SWASTi simulation completed"
        echo "Copying data and sleep for 2 minutes"
        sleep 120
        echo "-----------------------------------------------------------------"
        exit 0

    fi
else
    echo "swasti.ini not found"
    echo "!SWASTi simulation aborted"
    echo "-----------------------------------------------------------------"
    exit 1
fi
