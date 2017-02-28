#!/usr/bin/env python
#coding=utf-8
#Auth:zp

import os,sys,atexit,getopt
from getpass import getuser
import ConfigParser,fnmatch,requests
from time import sleep,strftime,localtime
from psutil import pid_exists,Process,NoSuchProcess

#进程监控自动启动
__Version="Eye v1.0 (c) 2016 @Zp"

def Usage():
    use_name = sys.argv[0] 
    if '/' in use_name:
	use_name = use_name.split('/')[-1]
    print '''Usage: %s <command> [<args>]"
Options:
  -v|--version=<version> Show eye version and exit"
  -h|--help

Commands:
Some commands take arguments. Pass no args or -h for usage."
   i                   Eye Processes list"
   start MASK[,...]    Start app or process"
   stop  MASK[,...]    Stop app or process"
   delete MASK[,...]   Delete app or process"
   load [CONF, ...]    Load config (run eye-daemon if not) (foreground load)"
   '''%use_name
#restart MASK[,...]  Restart app or process"
def Daemonize(pidfile,stdin='/dev/null',stdout='/dev/null',stderr='/dev/null'):
    try:
       pid = os.fork()
       if pid > 0:
	  sys.exit(0)
    except OSError,e:
       sys.stderr.write("fork #1 failed (%d) %s\n " %(e.errno, e.strerror))
       sys.exit(0)
 
    os.chdir('.')
    os.umask(0)
    os.setsid()
 
    try:
       pid = os.fork()
       if pid > 0:
	  sys.exit(0)
    except OSError,e:
       sys.stderr.write("fork #2 failed (%d) %s\n " %(e.errno, e.strerror))
       sys.exit(0)
 
    if not stderr:stderr = stdout
    si = file(stdin, "r")
    so = file(stdout, "w+")
    se = file(stderr, "a+")

    #atexit.register(Del_pid(pidfile))
    getpid = str(os.getpid())
    f = open("%s"%pidfile,"w")
    print >> f,"%s"% getpid
    print "start with pid :[%s]" % getpid
    f.close()

    sys.stderr.flush()
    sys.stdout.flush()

    os.dup2(si.fileno(),sys.stdin.fileno())
    os.dup2(so.fileno(),sys.stdout.fileno())
    os.dup2(se.fileno(),sys.stderr.fileno())

def Del_pid(pidfile):
    os.remove(pidfile)

def Main(CHECK_HEALTH,CHECK_ADDRESS,CHECK_RESTATUS,ALARM,ALARM_ADDRESS,APP_NAME,Eye_dir,PID_FILE,RUN_START,RUN_STOP,INTERVAL,format_time,pidfile):
    try:
       pidfile = "%s/%s"%(Eye_dir,pidfile)
       Daemonize(pidfile,stdout="%s/eye.log"%Eye_dir,stderr="%s/eye.err"%Eye_dir)
       Runer(CHECK_HEALTH,CHECK_ADDRESS,CHECK_RESTATUS,ALARM,ALARM_ADDRESS,APP_NAME,Eye_dir,PID_FILE,RUN_START,RUN_STOP,INTERVAL)
    except Exception,e:
       print "%sError:%s"%(format_time,str(e))

def Runer(CHECK_HEALTH,CHECK_ADDRESS,CHECK_RESTATUS,ALARM,ALARM_ADDRESS,APP_NAME,Eye_dir,PID_FILE,RUN_START,RUN_STOP,INTERVAL):
    while True:
	  try:
	    Pid_F = file(PID_FILE,"r").readlines()
            pid = int(Pid_F[0])
            if not pid_exists(pid):
	       Cmd(RUN_START)
	       continue
	    t1 , p1 = get_cpu(pid)
	    if CHECK_HEALTH == "on":
	      req = requests.get(CHECK_ADDRESS)
	      try:
	         stat = int(CHECK_RESTATUS)
		 if req.status_code != stat:
	            Cmd(RUN_STOP)
		    Cmd(RUN_START)
	            if ALARM == "on":
		       res = requests.post(ALARM_ADDRESS,{"msg":"%s检测失败,PID:%s"%(CHECK_ADDRESS,pid)})
		    else:
                       pass
	      except:
	         stat = str(CHECK_RESTATUS)
		 if req.content.strip('\n') != stat:
	            Cmd(RUN_STOP)
		    Cmd(RUN_START)
	            if ALARM == "on":
		       res = requests.post(ALARM_ADDRESS,{"msg":"%s检测失败,PID:%s"%(CHECK_ADDRESS,pid)})
		    else:
                       pass 
	  except Exception,e:
	       print(str(e))
	       Cmd(RUN_STOP)
	       Cmd(RUN_START)
          sleep(float(INTERVAL))
          if pid_exists(pid):
	     t2 , p2 = get_cpu(pid)
	     cpu = round(100.00 * (p2 - p1)/(t2 - t1) * int(get_cpu_core_num()),2)
             file("%s/.%s.stat"%(Eye_dir,APP_NAME),'wb').write(str(cpu))

def Cmd(command):
    os.system("%s"%command)

def Proc_exist(proc_name,Eye_dir):
    try:
       for x in os.listdir(Eye_dir):
           if fnmatch.fnmatch(x,'*.mid'):
              if(x.split('.')[1] == proc_name):
	         f = open("%s/%s.pid"%(Eye_dir,proc_name),"r").readlines()
                 if pid_exists(int(f[0])):
		    print "名称[%s]PID[%s]已存在......"%(proc_name,int(f[0]))
	            return True
                 else:
	            return False
    except:
       return False
def load(Eye_dir,setids=0):
    try:
	if setids == 1:
	   eyefile = "%s.eye"% sys.argv[2]
	else:
	   eyefile = sys.argv[2]
        app_name = "%s"%(eyefile)
	if(app_name.split('.')[-1] != "eye"):
	   print("配置文件错误,应是以.eye结尾的文件")
	   sys.exit(1)
        if os.path.isfile(eyefile):
           config = ConfigParser.ConfigParser()
           config.read(eyefile)
	   format_time = [strftime("%Y-%m-%d %H:%M:%S",localtime())]
	   APP_NAME  = config.get('main','app_name')
	   if(app_name.split('.')[0] != APP_NAME):
              print("配置%s需要在当前目录且文件名称和配置文件的APP_NAME一致,如:test.eye app_name=test."%(eyefile))
	      sys.exit(1)
           app_name_exis = Proc_exist(APP_NAME,Eye_dir)
	   if app_name_exis is True:
	      sys.exit(1)
	   PID_FILE  = config.get('main','pid_file')
	   RUN_START = config.get('main','run_start')
	   RUN_STOP  = config.get('main','run_stop')
	   INTERVAL  = config.get('main','interval')
	   
	   CHECK_HEALTH = config.get('main','health')
	   if CHECK_HEALTH == "on":
	      CHECK_ADDRESS = config.get('main','health_address')
	      CHECK_RESTATUS = config.get('main','restatus')
           else:
	      CHECK_ADDRESS = 0
	      CHECK_RESTATUS = 0
	   ALARM = config.get('main','alarm')
	   if ALARM == "on": 
	      ALARM_ADDRESS = config.get('main','alarm_address')
           else:
              ALARM_ADDRESS = 0
	   if not PID_FILE or not RUN_START or not RUN_STOP or not INTERVAL:
              print("参数配置不正确!")
	      sys.exit(1)
	   if not os.path.isfile(PID_FILE):
              Cmd(RUN_START)
	   try:
              Pid_F = file(PID_FILE,"r").readlines()
	   except OSError:
              print("PID文件读取错误...")
              sys.exit(0)
	   try:
	      os.unlink("%s/%s.pid"%(Eye_dir,APP_NAME))
              os.symlink("%s"% PID_FILE,"%s/%s.pid"%(Eye_dir,APP_NAME))
	   except OSError:
              os.symlink("%s"% PID_FILE,"%s/%s.pid"%(Eye_dir,APP_NAME))

           Main(CHECK_HEALTH,CHECK_ADDRESS,CHECK_RESTATUS,ALARM,ALARM_ADDRESS,APP_NAME,Eye_dir,PID_FILE,RUN_START,RUN_STOP,INTERVAL,format_time,pidfile=".%s.mid"% APP_NAME)
        else:
           print("配置文件不存在...")
    except Exception,e:
          print("配置文件读取错误...")

def get_cpu(pid):
   tot_staff = file('/proc/stat','r').read()
   tot_cpu = tot_staff.split('\n')[0].split(' ')
   totalCpuTime = 0
   for i in tot_cpu[2:]:
     totalCpuTime = totalCpuTime + int(i)

   staff = file('/proc/%d/stat'%pid,'r').read()
   total_sum = str(staff).strip('\n')
   number = total_sum.split(' ')
   processCpuTime = int(number[14]) + int(number[15]) + int(number[16]) + int(number[17])
   
   return (totalCpuTime,processCpuTime)
def get_cpu_core_num():
    core_num = 0
    with open('/proc/cpuinfo') as f:
       for line in f:
          if line.startswith('processor'):
	     core_num += 1
    return core_num

def total_mem():
   with open('/proc/meminfo') as f:
       for line in f:
	   if line.startswith('MemTotal'):
	      return int(line.split()[1])
def pid_mem(pid):
   with open("/proc/%d/status"%pid) as f:
	for line in f:
	   if line.startswith('VmRSS'):
	      return int(line.split()[1])
def pid_cpu(Eye_dir,proc_name):
   with open("%s/.%s.stat"%(Eye_dir,proc_name),'rb') as f:
        for line in f:
	   return line
def i(Eye_dir):
    try:
       for x in os.listdir(Eye_dir):
	 if fnmatch.fnmatch(x,'*.mid'):
            proc_name = x.split('.')[1]
	    a =[i for i in os.listdir(Eye_dir) if fnmatch.fnmatch(i,'%s.pid'%proc_name)]
	    if a:
	      try:
	         f = open("%s/%s.pid"%(Eye_dir,proc_name),"r").readlines()
	         g = open("%s/%s"%(Eye_dir,a[0]),"r").readlines()
	         PID_EXISTS = pid_exists(int(g[0]))
	         process = Process(int(f[0]))
	         x = localtime(process.create_time())
	         create_time = strftime('%Y-%m-%d %H:%M:%S',x)
	         cpu = 0
		 if os.path.exists("%s/.%s.stat"%(Eye_dir,proc_name)):
		    cpu = pid_cpu(Eye_dir,proc_name)
	         mem = round(pid_mem(int(f[0]))/1024.00,2)
	         if PID_EXISTS:
	            if process.status() == 'sleeping':
		       status = 'up'
	               print'''[%s] 
	  .................... \033[92m %s \033[0m(%s%%, %sM, <%s>, [%s])'''%(proc_name,status,cpu,mem,int(f[0]),create_time)
	      except NoSuchProcess:
	         status = 'down'
	         print'''[%s] 
	  .................... \033[91m %s \033[0m(0.0%%, 0.0%%, <%s> )'''%(proc_name,status,int(f[0]))
	    else:
		status = '(not monitoring)'
		print'''[%s]
          .................... %s'''%(proc_name,status)
       app_list = [ x for x in os.listdir(Eye_dir) if fnmatch.fnmatch(x,'*.mid') ]
       if not app_list:
           print('objects not found!(load config ...)')  
    except Exception,e:
       print("Eye list:%s"%e)

def start(Eye_dir):
    try:
       app_name = sys.argv[2]
       for x in os.listdir(Eye_dir):
          if fnmatch.fnmatch(x,'*.mid'):
	     if(x.split('.')[1] == app_name):
		try:
                   f=open("%s/%s"%(Eye_dir,x),"r").readlines()
	           p = Process(int(f[0]))
		   print("名称[%s]PID[%s]正在运行......"%(app_name,int(f[0])))
		   sys.exit(0)
	        except NoSuchProcess:
		   load(Eye_dir,setids=1)
		   sys.exit(0)
       else:
          print("start [%s],objects not found!"%app_name)
    except Exception,e:
       print("command:start,objects not found!",e)

def stop(Eye_dir):
    try:
       app_name = sys.argv[2]
       for x in os.listdir(Eye_dir):
          if fnmatch.fnmatch(x,'*.mid'):
             if(x.split('.')[1] == app_name):
                f=open("%s/.%s.mid"%(Eye_dir,app_name),"r").readlines()
                if pid_exists(int(f[0])):
                   p = Process(int(f[0]))
                   p.kill()
		if os.path.isfile('%s/%s.pid'%(Eye_dir,app_name)):
	           os.unlink("%s/%s.pid"%(Eye_dir,app_name))
                else:
                   print("名称[%s]未运行......"%(app_name,))
		   sys.exit(0)
       app_list = [x for x in os.listdir(Eye_dir) if fnmatch.fnmatch(x,'.%s.mid'%app_name)]
       if not app_list:
          print("stop [%s],objects not found!"%app_name)
    except Exception,e:
       print("command:kill,objects not found!")

def delete(Eye_dir):
    try:
       app_name = sys.argv[2]
       app_list = True
       for x in os.listdir(Eye_dir):
          if fnmatch.fnmatch(x,'*.mid'):
             if(x.split('.')[1] == app_name):
                f = open("%s/%s"%(Eye_dir,x),"r").readlines()
                if pid_exists(int(f[0])):
                   print("名称[%s]正在运行......"%(app_name))
		   sys.exit(0)
		if os.path.isfile("%s/%s.pid"%(Eye_dir,app_name)):
		   os.remove("%s/%s.pid"%(Eye_dir,app_name))
		if os.path.isfile("%s/.%s.mid"%(Eye_dir,app_name)):
		   os.remove("%s/.%s.mid"%(Eye_dir,app_name))
		if os.path.isfile("%s/.%s.stat"%(Eye_dir,app_name)):
		   os.remove("%s/.%s.stat"%(Eye_dir,app_name))
	        app_list = False
       if app_list:
          print("delete [%s],objects not found!"%app_name)
    except Exception,e:
       print("command:delete,%s"%e)
        
if __name__ == "__main__":
   try:
       opts,args = getopt.getopt(sys.argv[1:],"hv", ["help","version"])
       option = ['i','start','stop','load','delete'] 
       
       if not opts and not args:
          Usage() 
	  sys.exit(0)
       if args:
          if(args[0] in option):
	     get_user = getuser()
	     Eye_dir = "/home/%s/.eye"%(get_user)
	     if not os.path.exists(Eye_dir):
		os.makedirs(Eye_dir)
	     eval(args[0])(Eye_dir)
          else:
             print '''Could not find command "%s".'''% args[0]

       for opt,arg in opts:  
           if opt in ("-h", "--help"):
              Usage() 
              sys.exit(1) 
           elif opt in ("-v", "--version"):  
              print(__Version)
   except getopt.GetoptError,e:
       print(str(e))
       sys.exit(0)
