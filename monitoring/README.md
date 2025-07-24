# Disk space monitoring and Deletion

`/data` monitoring on all servers is already being done by the same cronjob for Grafana.

This adds the function off deleting old files if the `/data` usage is above 75%, down to 50%, on `tpc01-11`.

We assume a max data rate of 100 MB/s. Each tpc server has a total `/data` space of ~ 11168 GB.

It should take ~ 8 hours to fill 25%, thus running the script once per shift should be enough.