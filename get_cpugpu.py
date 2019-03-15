# -*- coding: utf-8 -*-
import time
import subprocess
import re
import sys
import csv
import argparse
import threading
import os
import signal

def get_device():  #获取设备ID
    cmd_devices = 'adb devices'.split()
    p_devices = subprocess.Popen(cmd_devices, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p_devices.wait()
    devices = p_devices.stdout.readlines()
    p_devices.stdout.close()
    for item in devices:
        if item.find('\tdevice') >= 0:
            pattern = re.compile(r'(\S*)\s')
            device_id = re.match(pattern,item).group(1)
            return device_id
    print u'设备序列号未找到'
    sys.exit()

# 获取当前应用的包名
def get_package():
    cmd_package = 'adb shell dumpsys activity | grep mFocusedActivity'.split()
    p_package = subprocess.Popen(cmd_package, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p_package.wait()
    p_out = p_package.stdout.readlines()
    p_package.stdout.close()
    for item in p_out:
        pattern_package = re.compile(r'.*u0\s+([^\s]+)/')
        package_name = pattern_package.match(item).group(1)
        return package_name

# 获取手机名
def get_phone():
    cmd_phone = 'adb shell getprop ro.product.model'.split()
    p_phone = subprocess.Popen(cmd_phone, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p_phone.wait()
    p_out = p_phone.stdout.readlines()
    p_phone.stdout.close()
    for item in p_out:
        phone_name = item.strip('\n')

    phone_map = {
        'Mi Note 3': 'xmnote3',
        'OPPO R11': 'opr11',
        'SM-G9500': 'sms8'
    }

    return phone_map[phone_name]

# 创建cpu的csv路径
def create_cpu_csv_path(phone_name,package_name,arg_number):
    app_map = {
        'com.ss.android.ugc.aweme' : 'dyin',
        'video.like' : 'like',
        'com.smile.gifmaker' : 'ks',
        'com.duowan.minivideo' :'soda'
    }
    app_name = app_map[package_name]
    root_dir = sys.path[0]
    file_dir = os.path.join(root_dir,'cpugpu_file')
    cmd_dir = 'mkdir -p {}'.format(file_dir).split()
    p_dir = subprocess.Popen(cmd_dir)
    p_dir.wait()
    cpu_csv_path = os.path.join(file_dir,phone_name + app_name + '_android_viewcpu_' + arg_number + '.csv')
    return cpu_csv_path

# 创建gpu的csv路径
def create_gpu_csv_path(phone_name,package_name,arg_number):
    app_map = {
        'com.ss.android.ugc.aweme': 'dyin',
        'video.like': 'like',
        'com.smile.gifmaker': 'ks',
        'com.duowan.minivideo':'soda'
    }
    app_name = app_map[package_name]
    # 获取脚本当前路径
    root_dir = sys.path[0]
    file_dir = os.path.join(root_dir, 'cpugpu_file')
    cmd_dir = 'mkdir -p {}'.format(file_dir).split()
    p_dir = subprocess.Popen(cmd_dir)
    p_dir.wait()
    gpu_csv_path = os.path.join(file_dir,phone_name + app_name + '_android_viewgpu_' + arg_number + '.csv')
    return gpu_csv_path

# 收集cpu信息，并写入csv
def collect_cpu_msg(arg_collect_time,package_name,device_id,cpu_csv_path):
    cpu_str = '0'
    begin = time.time()

    with open(cpu_csv_path, 'wb') as cpu_csv_file:
        while True:
            now_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
            cmd_cpu = 'adb -s {} shell top -n 1 | grep {}'.format(device_id,package_name).split()
            child = subprocess.Popen(cmd_cpu,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            child.wait()
            child_out = child.stdout.readlines()
            child.stdout.close()
            for item in child_out:
                if item.find(package_name) > 0:
                    if item.find('%') > 0:  # 获取CPU占用百分比
                        pattern = re.compile(r'.*(\d+)%')
                        cpu_str = re.match(pattern,item).group(1)
                break
            # print 'cpu:{}'.format(cpu_str)
            time.sleep(1)
            end = time.time()

            csv_writer = csv.writer(cpu_csv_file)  #输出cpu信息
            csv_writer.writerow([str(now_time),cpu_str])

            # if end-begin >= int(arg_collect_time):
            #     break

# 收集gpu信息，并写入csv
def collect_gpu_msg(arg_collect_time,device_id,gpu_csv_path):
    utilization_arg_1 = ""
    utilization_arg_2 = ""
    gpu_frequency = ""
    load = ""
    begin = time.time()

    with open(gpu_csv_path, 'wb') as gpu_csv_file:
        while True:
            now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

            # 获取load、utilization_arg_1、utilization_arg_2
            cmd_load = 'adb -s {} shell cat /sys/class/kgsl/kgsl-3d0/gpubusy'.format(device_id).split()
            child_load = subprocess.Popen(cmd_load,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            child_load.wait()
            child_load_out = child_load.stdout.readlines()
            child_load.stdout.close()
            for item in child_load_out:
                if len(item)>2:
                    pattern_laod = re.compile(r'\s+(\d+)\s+(\d+)')
                    utilization_arg_1 = re.match(pattern_laod,item).group(1)
                    utilization_arg_2 = re.match(pattern_laod, item).group(2)
                break
            if utilization_arg_2 != '0':
                load = str(round((float(utilization_arg_1) / float(utilization_arg_2)) * 100, 2))
            else:
                load = '0'

            #获取frequency
            cmd_frequency = 'adb -s {} shell cat /sys/class/kgsl/kgsl-3d0/gpuclk'.format(device_id).split()
            child_frequency = subprocess.Popen(cmd_frequency, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            child_frequency.wait()
            child_frequency_out = child_frequency.stdout.readlines()
            child_load.stdout.close()
            for item in child_frequency_out:
                if len(item)>2:
                    frequency_out = item.strip()
                    gpu_frequency = str(int(frequency_out)/1000000)
                break
            # print 'gpu:{}'.format(load)
            time.sleep(1)
            end = time.time()

            csv_writer = csv.writer(gpu_csv_file)  #输出gpu信息
            csv_writer.writerow([str(now_time),utilization_arg_1,utilization_arg_2,load,gpu_frequency])
            # if end-begin >= int(arg_collect_time):
            #     break

def quit(num,stack):
    print u'结束进程'
    sys.exit()

# 开启cpu线程
class Cpu_Thread(threading.Thread):
    def __init__(self, arg_collect_time, package_name, device_id, cpu_csv_path):
        super(Cpu_Thread,self).__init__()
        self.collect_time = arg_collect_time
        self.package_name = package_name
        self.device_id = device_id
        self.cpu_csv_path = cpu_csv_path

    def run(self):
        collect_cpu_msg(self.collect_time, self.package_name, self.device_id, self.cpu_csv_path)

# 开启gpu线程
class Gpu_Thread(threading.Thread):
    def __init__(self, arg_collect_time, device_id, gpu_csv_path):
        threading.Thread.__init__(self)
        self.collect_time = arg_collect_time
        self.device_id = device_id
        self.gpu_csv_path = gpu_csv_path

    def run(self):
        collect_gpu_msg(self.collect_time, self.device_id, self.gpu_csv_path)


def main():

    # 定义argparse
    parser = argparse.ArgumentParser(description='获取进程的CPUGPU占用脚本')
    parser.add_argument('--collect-time', '-t', dest='collect_time', help='信息采集时间，以秒为单位，整数')
    parser.add_argument('--number','-n', dest='number',required = True,help='信息收集的次数')
    args = parser.parse_args()
    #获取参数
    if args.collect_time is not None:
        param_collect_time = args.collect_time
    else:
        param_collect_time = '15'

    param_number = args.number

    signal.signal(signal.SIGINT, quit)

    device_id = get_device()
    package_name = get_package()
    phone_name = get_phone()
    cpu_csv_path = create_cpu_csv_path(phone_name,package_name,param_number)
    gpu_csv_path = create_gpu_csv_path(phone_name,package_name,param_number)

    #采集信息
    threads = []

    temp_thread_cpu = Cpu_Thread(param_collect_time, package_name, device_id, cpu_csv_path)
    temp_thread_cpu.setDaemon(True)
    temp_thread_cpu.start()
    threads.append(temp_thread_cpu)

    temp_thread_gpu = Gpu_Thread(param_collect_time, device_id, gpu_csv_path)
    temp_thread_gpu.setDaemon(True)
    temp_thread_gpu.start()
    threads.append(temp_thread_gpu)

    time.sleep(int(param_collect_time))

    # for t in threads:
    #     t.join()

    # collect_cpu_msg(param_collect_time,param_package_name,device_id,param_csv_path)
    # collect_gpu_msg(param_collect_time,device_id,param_csv_path)

if __name__ == '__main__':
    main()