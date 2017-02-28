#Eye Load Profiles 
[main]
app_name  = ems 
pid_file  = /home/work/ems/logs/app.pid
run_start = cd /home/work/ems && ./control start
run_stop  = cd /home/work/ems && ./control stop
interval  = 2.5

#
#Health Check
#
health = off
#Health Check address
health_address = http://127.0.0.1:1900/health
#Health Check return status, the default will detect the url status code
restatus = ok
#
#
alarm = off
#Alarm address 
alarm_address = http://127.0.0.1:1900/wechat/sender 
#
#cpu_max = 
#mem_max = 
#
#
