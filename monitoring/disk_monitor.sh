for t in tpc;
do
  for h in sbnd-${t}{01..10};
  do
     ping -c 1 -W 1 $h > /dev/null && [[ $? == 0 ]] && echo "Monitoring disks on $h" && ssh sbnd@$h -o ConnectTimeout=1 "python3 /home/nfs/sbnd/nevis_continuous_readout_monitoring/disk_monitor.py";
   done 2> /dev/null;
done