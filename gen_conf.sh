#!/bin/bash
timestamp=$(date +%Y-%m-%d-%H:%M:%S)
hostaddr=$(/sbin/ifconfig eth0|grep Bcast|awk '{print $2}'|awk -F ':' '{print $2}')
supervisord_conf_file=/etc/supervisord.conf
supervisor_conf_dir=/etc/supervisor.d/
supervisord_init_file=/etc/init.d/supervisord
master_conf_file=/etc/supervisor.d/weed-master.conf
volume_conf_file=/etc/supervisor.d/weed-volume.conf
weedfs_api_conf_file=/etc/supervisor.d/weed-api.conf
weeddir=/data/weedfs
weed_bin_dir=/data/weedfs/bin
weed_logs_dir=/data/weedfs/logs
mport=9333
vport=8080
mkdir -p $weeddir $weed_bin_dir  $weed_logs_dir $supervisor_conf_dir $weeddir/{master,volume}
master_group=(10.0.31.10 10.0.31.11 10.0.31.12)

peer_select() {
peer=${master_group[@]/$hostaddr/}
for p in ${peer[@]}
do
  echo -e "$p:9333,\c"
done
}

gen_master_conf() {
peer_str=$(peer_select)
peers=$(echo ${peer_str%%,})

cat >$master_conf_file<<EOF
[program:weedfs-master]
directory = $weeddir
command =  $weed_bin_dir/weed master -mdir $weeddir/data/master -ip.bind=$hostaddr -ip=$hostaddr  -port=$mport -peers="$peers" -defaultReplication="001"
autorestart = true
redirect_stderr = true
stdout_logfile = $weed_logs_dir/weed-master-$mport-stdout.log
stderr_logfile = $weed_logs_dir/weed-master-$mport-stderr.log
;generated at $timestamp
EOF
}

gen_weedfs_api_conf() {
cat >$weedfs_api_conf_file<<EOF
[program:weedfs-api]
directory = /data/weedfs/api
command = /usr/local/bin/gunicorn  --access-logfile /data/weedfs/logs/api_access.log --worker-class gevent -b "$hostaddr:80" -w 8 weed_api:app
autorestart = true
redirect_stderr = true
stdout_logfile = /data/weedfs/logs/weed-api-stdout.log
stderr_logfile = /data/weedfs/logs/weed-api-stderr.log
;generated at $timestamp
EOF
}

gen_volume_conf() {
cat >$volume_conf_file<<END
[program:weedfs-volume]
directory = $weeddir
command =  $weed_bin_dir/weed volume -dir $weeddir/data/volume -ip=$hostaddr -port 8080 -publicUrl="$hostaddr:8080" -ip.bind=$hostaddr -mserver=10.0.31.10:9333 -max=40
autorestart = true
redirect_stderr = true
stdout_logfile = $weed_logs_dir/weed-volume-$vport-stdout.log
stderr_logfile = $weed_logs_dir/weed-volume-$vport-stderr.log
;generated at $timestamp
END
}

gen_supervisord_conf() {
cat >$supervisord_conf_file <<ENF
[supervisord]
logfile = /tmp/supervisord.log
logfile_maxbytes = 50MB
logfile_backups=10
loglevel = info
pidfile = /tmp/supervisord.pid
minfds = 65530
minprocs = 200
identifier = supervisor
directory = /tmp
nocleanup = true
childlogdir = /tmp

[unix_http_server]
file=/tmp/supervisor.sock 

[inet_http_server]       
port=$hostaddr:9001  
username=super          
password=superpass               
[supervisord]
logfile=/tmp/supervisord.log 
logfile_maxbytes=50MB        
logfile_backups=10           
loglevel=info               
pidfile=/tmp/supervisord.pid 

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=http://$hostaddr:9001 
username=super              
password=superpass              
prompt=supervisor-$hostaddr        
history_file=~/.sc_history  

[include]
files = /etc/supervisor.d/*.conf
;generated at $timestamp
ENF
}

#gen_supervisord_conf
#gen_master_conf
#gen_volume_conf
#gen_weedfs_api_conf
eval $1
