#coding=utf-8
'''
    monitor server health and report to master.

    @author: leotse
'''
import os
import time
import json
import socket
import urllib2
import commands

import config

# get local ip address
SERVER_IP = socket.gethostbyname(socket.gethostname())

def monitor_controller():
    monitor_result_str = monitor_server_info()
    report_to_syncer(monitor_result_str)

def report_to_syncer(monitor_result_str):
    post_data = {}
    post_data["server_name"] = config.SERVER_NAME
    post_data["server_ip"] = SERVER_IP
    post_data["server_status"] = config.HealthStatus.SICK if monitor_result_str else config.HealthStatus.HEALTH
    post_data["server_symptom"] = monitor_result_str

    invoke_report_api(post_data)
    
def monitor_server_info():
    monitor_result_str = ""
    # disk monitor
    disk_info_dict = disk_info()
    if disk_info_dict["Used"] >= str(config.DISK_USAGE_THRESHOLD):
        monitor_result_str += "Disk used {disk_used}.\t".format(disk_used=disk_info_dict["Used"])
    # cpu usage monitor
    cpu_usage = cpu_usage_info()
    if cpu_usage >= str(config.CPU_USAGE_THRESHOLD):
        monitor_result_str += "CPU used {cpu_used}.\t".format(cpu_used=cpu_usage)

    return monitor_result_str

'''
API: health_report
method: GET
request: {"server_name":"server name", "server_ip":"module ip", "status":"health/sick", 
                "symptom":"null/i.e. nginx stop work.."}
response: {"status":"success/failed"}
'''
def invoke_report_api(post_data):
    api_name = config.API_NAME
    # url
    gateway = "{ip_addr}:{port}".format(ip_addr=config.HAWKEYE_HOST, port=config.HAWKEYE_PORT)

    url = "http://{gateway}/{api}".format(gateway=gateway, api=api_name)

    post_data_str_list = []
    for k, v in post_data.iteritems():
        post_data_str_list.append(k + "=" + v)
    post_data_str = "&".join(post_data_str_list)
    http_command = 'curl "{url}/?{post_data}"'.format(url=url, post_data=post_data_str)    

    rt, res = commands.getstatusoutput(http_command)
    
    return rt == 0, res

def cpu_load_info():
    '''
    /proc/loadavg:
    1.60 1.49 1.56 1/8100 24998
    
    The first three columns measure CPU and IO utilization of the last one, five, and 10 minute periods. 
    The fourth column shows the number of currently running processes and the total number of processes. 
    The last column displays the last process ID used.
    '''
    load_info_dict = {}
    with open("/proc/loadavg", "r") as f:
        info = f.read().split()
        load_info_dict["lavg_1"] = float(info[0])
        load_info_dict["lavg_5"] = float(info[1])
        load_info_dict["lavg_15"] = float(info[2])
        load_info_dict["nr"] = info[3]
        load_info_dict["last_pid"] = int(info[4])

    return load_info_dict

def get_time_list():
    """
    Fetches a list of time units the cpu has spent in various modes
    Detailed explanation at http://www.linuxhowtos.org/System/procstat.htm
    """
    cpuStats = file("/proc/stat", "r").readline()
    columns = cpuStats.replace("cpu", "").split(" ")
    return map(int, filter(None, columns))

def delta_time(interval):
    """
    Returns the difference of the cpu statistics returned by getTimeList
    that occurred in the given time delta
    """
    timeList1 = get_time_list()
    time.sleep(interval)
    timeList2 = get_time_list()
    return [(t2-t1) for t1, t2 in zip(timeList1, timeList2)]

def cpu_usage_info():
    """
    Returns the cpu load as a value from the interval [0.0, 1.0]
    """
    interval = 0.1
    dt = list(delta_time(interval))
    idle_time = float(dt[3])
    total_time = sum(dt)
    cpu_usage = 1-(idle_time/total_time)
    return cpu_usage

def mem_info():
    '''
    /proc/meminfo:
    MemTotal:       131989500 kB
    MemFree:          720196 kB
    Buffers:         3834844 kB
    Cached:         40816752 kB
    SwapCached:       638056 kB
    Active:         66954704 kB
    ...
    '''
    mem_info_dict = {}
    with open("/proc/meminfo") as f:
        for line in f.readlines():
            key = line.split(":")[0]
            value = line.split(":")[1].split()[0]
            mem_info_dict[key] = float(value)
    
    mem_info_dict["MemUsed"] = mem_info_dict['MemTotal'] - mem_info_dict['MemFree'] - mem_info_dict['Buffers'] - mem_info_dict['Cached']
    mem_info_dict["Used_Per"] = round((mem_info_dict['MemUsed']) / (mem_info_dict['MemTotal']), 5)
    
    return mem_info_dict

def disk_info():
    disk_info_dict = {}
    dinfo = os.statvfs("/")
    disk_info_dict["Available"] = dinfo.f_bsize * dinfo.f_bavail
    disk_info_dict["Capacity"] = dinfo.f_bsize * dinfo.f_blocks
    disk_info_dict["Used"] = dinfo.f_bsize * dinfo.f_bfree
    disk_info_dict["Avai_per"] = dinfo.f_bavail / dinfo.f_blocks
    
    return disk_info_dict
    

if __name__ == "__main__":
    monitor_controller()
