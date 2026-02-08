#!/bin/bash

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
swasti_container="SWASTi_Run_${TIMESTAMP}"
MAPTIME_RAW=$(grep "^SWTI_MAP_TIME" swasti.ini | awk -F': ' '{print $2}')
MAPTIME=$(date -d "$MAPTIME_RAW" +"%Y%m%dT%H%M")
RUN_MHD=$(grep "^SWTI_RUN_MHD" swasti.ini | awk -F': ' '{print $2}' | tr -d '\r' | xargs)
output_dir="SWASTi_outputs_${MAPTIME}"
swasti_image="swasti:v00"

MAPTIME_=${MAPTIME/T/}

MAPNAME=$(grep "^SWTI_INPUT_MAP" swasti.ini | awk -F': ' '{print $2}' | tr -d '\r' | xargs | tr '[:upper:]' '[:lower:]')

MAPFILE_NAME="${MAPNAME}_${MAPTIME_}.fts.gz"
MAPFILE="$(pwd)/${MAPFILE_NAME}"

FILE_MOUNT=""

if [ -f "$MAPFILE" ]; then
    FILE_MOUNT="-v ${MAPFILE}:/app/swasti_run/${MAPFILE_NAME}"
fi


nohup docker run --network=host \
  --name "$swasti_container" \
  -v "$(pwd)/swasti.ini:/app/swasti_run/swasti.ini" \
  $FILE_MOUNT \
  $swasti_image \
  > swasti_run.log 2>&1 &


echo "Running SWASTi $swasti_container" 
mkdir -p "$output_dir"
until docker ps --format '{{.Names}}' | grep -w "$swasti_container" >/dev/null; do
    sleep 2
done
until docker exec "$swasti_container" test -f "/app/swasti_run/SWASTi_Results/HuX_result.out"; do
    sleep 100
done
docker cp "$swasti_container:/app/swasti_run/SWASTi_Results/." "$output_dir/" >/dev/null 2>&1
echo "Copied SWASTi HuX results to $output_dir/"

sync_log_file() {
    while docker inspect -f '{{.State.Running}}' "$swasti_container" 2>/dev/null | grep -q "true"; do	
	if docker exec "$swasti_container" sh -c "[ -f /app/swasti_run/pluto.0.log ]"; then
            docker cp "$swasti_container:/app/swasti_run/pluto.0.log" "$output_dir/swasti_mhd.log" >/dev/null 2>&1
        fi
        sleep 60 
    done
}

monitor_SWASTi_results() {
    while docker inspect -f '{{.State.Running}}' "$swasti_container" | grep -q "true"; do
        sleep 100
    done
    docker cp "$swasti_container:/app/swasti_run/SWASTi_Results/." "$output_dir/" >/dev/null 2>&1
    echo "Copied SWASTi MHD results to $output_dir/"       

}
if [ "${RUN_MHD}" = "YES" ]; then 
    sync_log_file &
    monitor_SWASTi_results &
fi
# Wait for both background jobs to finish
wait

mv "swasti_run.log" "$output_dir"
