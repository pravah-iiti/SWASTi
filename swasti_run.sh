#!/bin/bash

#Check swasti.ini exist
if [ ! -f "swasti.ini" ]; then
    echo "Error: swasti.ini not found in $(pwd)"
    exit 1
fi

#check swasti.ini is not empty
if [ ! -s "swasti.ini" ]; then
    echo "Error: swasti.ini is empty"
    exit 1
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
swasti_container="SWASTi_Run_${TIMESTAMP}"

cleanup() {
    local status=$?
    echo "Job terminating."

    jobs -pr | xargs -r kill 2>/dev/null || true
    if docker inspect -f '{{.State.Running}}' "$swasti_container" 2>/dev/null | grep -q "true"; then
        echo "Stopping docker container $swasti_container."
        docker kill "$swasti_container" >/dev/null 2>&1 || true
        docker wait "$swasti_container" >/dev/null 2>&1 || true
    fi
    echo "Stopped docker." 
    
    echo "Job terminated." >> "$output_dir/swasti_run.log" 2>&1

    exit $status
}

trap cleanup INT TERM

MAPTIME_RAW=$(sed -n 's/^SWTI_MAP_TIME: *//p' swasti.ini | tr -d '\r' | xargs)
MAPTIME=$(date -d "$MAPTIME_RAW" +"%Y%m%dT%H%M")
RUN_MHD=$(awk -F': *' '/^SWTI_RUN_MHD/ {print $2}' swasti.ini | tr -d '\r' | xargs)

output_dir="SWASTi_outputs_${MAPTIME}"
if [ -d "$output_dir" ]; then
    echo "Error: Output directory '$output_dir' already exists. Exiting."
    exit 1
fi

swasti_image="pravahiiti/swasti:latest"

MAPTIME_=${MAPTIME/T/}
MAPNAME=$(awk -F': *' '/^SWTI_INPUT_MAP/ {print $2}' swasti.ini | tr -d '\r' | xargs | tr '[:upper:]' '[:lower:]')
if [ "$MAPNAME" = "adapt" ]; then
    EXT="fts.gz"
elif [ "$MAPNAME" = "gong" ]; then
    EXT="fits.gz"
else
    echo "Error: Unknown SWTI_INPUT_MAP type '$MAPNAME'"
    exit 1
fi

MAPFILE_NAME="${MAPNAME}_${MAPTIME_}.${EXT}"
MAPFILE="$(pwd)/${MAPFILE_NAME}"

FILE_MOUNT=""

if [ -f "$MAPFILE" ]; then
    FILE_MOUNT="-v ${MAPFILE}:/app/swasti_run/${MAPFILE_NAME}"
fi

mkdir -p "$output_dir"

nohup docker run --network=host \
  --name "$swasti_container" \
  -v "$(pwd)/swasti.ini:/app/swasti_run/swasti.ini" \
  $FILE_MOUNT \
  $swasti_image \
  > "$output_dir/swasti_run.log" 2>&1 &


echo "Running SWASTi $swasti_container" 

until docker inspect "$swasti_container" >/dev/null 2>&1; do
    sleep 2
done

until docker exec "$swasti_container" test -f "/app/swasti_run/SWASTi_Results/HuX_result.out"; do
    sleep 5
    if docker inspect -f '{{.State.Running}}' "$swasti_container" 2>/dev/null | grep -q "false"; then
        echo "docker stopped abruptly before HUX completed. Exiting..."
        exit 1
    fi
done

docker cp "$swasti_container:/app/swasti_run/SWASTi_Results/." "$output_dir/" >/dev/null 2>&1
echo "Copied SWASTi HuX results to $output_dir/"

sync_log_file() {
    while docker inspect -f '{{.State.Running}}' "$swasti_container" 2>/dev/null | grep -q "true"; do	
	if docker exec "$swasti_container" sh -c "[ -f /app/swasti_run/pluto.0.log ]"; then
            docker cp "$swasti_container:/app/swasti_run/pluto.0.log" "$output_dir/swasti_mhd.log" >/dev/null 2>&1
        fi
        sleep 5
    done
}

monitor_SWASTi_results() {
    while docker inspect -f '{{.State.Running}}' "$swasti_container" | grep -q "true"; do
        sleep 5
    done
    docker cp "$swasti_container:/app/swasti_run/SWASTi_Results/." "$output_dir/" >/dev/null 2>&1
    echo "Copied SWASTi MHD results to $output_dir/"
}

if [ "${RUN_MHD}" = "YES" ]; then 
    sync_log_file &
    monitor_SWASTi_results &
fi

docker wait "$swasti_container" >/dev/null
wait
