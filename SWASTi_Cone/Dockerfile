FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git vim build-essential python3-dev \
    libxml2-dev libxslt-dev \
    libhdf5-dev libc6 libc6-dev libstdc++6 libgcc1 \
    openmpi-bin libopenmpi-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/lib/openmpi/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/lib/openmpi/lib"

RUN useradd -m -s /bin/bash nonrootuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir git+https://github.com/GiMattia/PyPLUTO.git

COPY swasti.py swasti_vis.py \
     pluto swasti.grd definitions.h entrypoint.sh swasti.sh /app/swasti_run/
COPY SWASTi_logo.png /app/swasti_run/

RUN chmod +x /app/swasti_run/pluto /app/swasti_run/entrypoint.sh && \
    chown -R nonrootuser:nonrootuser /app

USER nonrootuser
CMD ["/app/swasti_run/entrypoint.sh"]
