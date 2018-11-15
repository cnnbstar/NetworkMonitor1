#!/usr/bin/env python27
# -*- coding: utf-8 -*-

'''
获取CPU，内存，C/D盘剩余可使用容量
'''

import wmi
import os
import sys
import platform
import time
import win32com.client as client

class DataPollster(object):
    '''
    Windows 主机系统主要数据抓取 如CPU，内存，磁盘等
    '''

    def get_cpu(self):
        # Initilization
        c = wmi.WMI()
        data_dict = {}

        for cpu in c.Win32_Processor():
            device = cpu.DeviceID.lower()
            # Get cpu_usage
            data_dict[device] = {'volume':float(cpu.LoadPercentage), 'unit':'%'}
        #return data_dict
        return 'cpu load:'+str(cpu.LoadPercentage)

    def get_mem(self):
        c = wmi.WMI ()
        cs = c.Win32_ComputerSystem()
        os = c.Win32_OperatingSystem()
        pfu = c.Win32_PageFileUsage()

        data_dict = {}
        data_dict["MemTotal"] = {'volume':float(cs[0].TotalPhysicalMemory) / (1024*1024), 'unit':'MB'}
        data_dict["MemFree"] = {'volume':float(os[0].FreePhysicalMemory)/1024, 'unit':'MB'}
        data_dict["SwapTotal"] = {'volume':float(pfu[0].AllocatedBaseSize), 'unit':'MB'}
        data_dict["SwapFree"] = {'volume':float(pfu[0].AllocatedBaseSize - pfu[0].CurrentUsage), 'unit':'MB'}
        #return {'data':data_dict, 'timestamp':time.asctime(time.localtime())}
        return  'Memory Free:'+str(int(os[0].FreePhysicalMemory)/1024)+'MB'

    def get_disk(self):
        c = wmi.WMI ()

        data_dict = {}
        data_dict['total_available'] = 0
        data_dict['total_capacity'] = 0
        data_dict['total_free'] = 0

        #  DriveType=3 : "Local Disk",
        for disk in c.Win32_LogicalDisk (DriveType=3):
            data_dict['total_available'] += round(float(disk.FreeSpace) / (1024*1024*1024), 2)
            data_dict['total_capacity'] += round(float(disk.Size) / (1024*1024*1024), 2)
            data_dict['total_free'] += round(float(disk.FreeSpace) / (1024*1024*1024), 2)

            dev_tmp = {}
            dev_tmp['dev'] = disk.DeviceID
            dev_tmp['available'] = {'volume':round(float(disk.FreeSpace) / (1024*1024*1024), 2), 'unit':'GB'}
            dev_tmp['capacity'] = {'volume':round(float(disk.Size) / (1024*1024*1024), 2), 'unit':'GB'}
            dev_tmp['free'] = {'volume':round(float(disk.FreeSpace) / (1024*1024*1024), 2), 'unit':'GB'}
            dev_tmp['fstype'] = disk.FileSystem
            dev_tmp['mnt'] = ''
            dev_tmp['used'] = round(long(disk.FreeSpace) / long(disk.Size), 2)

            data_dict[disk.DeviceID] = dev_tmp

        com = client.Dispatch("WbemScripting.SWbemRefresher")
        obj = client.GetObject("winmgmts:\\root\cimv2")
        diskitems = com.AddEnum(obj, "Win32_PerfFormattedData_PerfDisk_LogicalDisk").objectSet

        com.Refresh()
        for item in diskitems:
            if item.Name in data_dict:
                data_dict[item.Name]['io_stat'] = {}
                data_dict[item.Name]['io_stat']['r/s'] = {'volume':float(item.DiskReadsPerSec), 'unit':''}
                data_dict[item.Name]['io_stat']['w/s'] = {'volume':float(item.DiskWritesPerSec), 'unit':''}
                data_dict[item.Name]['io_stat']['rkB/s'] = {'volume':(float(item.DiskReadBytesPerSec) / 1024), 'unit':'KB/s'}
                data_dict[item.Name]['io_stat']['wkB/s'] = {'volume':(float(item.DiskWriteBytesPerSec) / 1024), 'unit':'KB/s'}
        #return {'data':data_dict, 'timestamp':time.asctime(time.localtime())}
        return 'C Available:'+str(int(data_dict['C:']['available']['volume']))+'GB'+\
               '\nD Available:'+str(int(data_dict['D:']['available']['volume']))+'GB'


    def get_net(self):
        c = wmi.WMI ()
        com = client.Dispatch("WbemScripting.SWbemRefresher")
        obj = client.GetObject("winmgmts:\\root\cimv2")
        items = com.AddEnum(obj, "Win32_PerfRawData_Tcpip_NetworkInterface").objectSet

        data_dict = {}
        interfaces = []
        for interface in c.Win32_NetworkAdapterConfiguration (IPEnabled=1):
            #print interface.IPAddress[0]
            interfaces.append(interface.Description)

        net_bytes_in = 0
        net_bytes_out = 0
        net_pkts_in = 0
        net_pkts_out = 0

        com.Refresh()
        for item in items:
            if item.Name in interfaces:
                #print 'Name:%s -> B_in:%s, B_out:%s, P_in:%s, P_out:%s' %(item.Name, item.BytesReceivedPerSec, item.BytesSentPerSec, item.PacketsReceivedPerSec, item.PacketsSentPerSec)
                net_bytes_in += long(item.BytesReceivedPerSec)
                net_bytes_out += long(item.BytesSentPerSec)
                net_pkts_in += long(item.PacketsReceivedPerSec)
                net_pkts_out += long(item.PacketsSentPerSec)

        time.sleep(1)

        net_bytes_in_cur = 0
        net_bytes_out_cur = 0

        com.Refresh()
        for item in items:
            if item.Name in interfaces:
                net_bytes_in = long(item.BytesReceivedPerSec) - net_bytes_in
                net_bytes_in_cur += long(item.BytesReceivedPerSec)
                net_bytes_out = long(item.BytesSentPerSec) - net_bytes_out
                net_bytes_out_cur += long(item.BytesSentPerSec)
                net_pkts_in = long(item.PacketsReceivedPerSec) - net_pkts_in
                net_pkts_out = long(item.PacketsSentPerSec) - net_pkts_out

        data_dict['net_bytes_in'] = {'volume':net_bytes_in/1024, 'unit':'KB/s'}
        #data_dict['net_bytes_in_sum'] = {'volume':net_bytes_in_cur/1024, 'unit':'KB'}
        data_dict['net_bytes_out'] = {'volume':net_bytes_out/1024, 'unit':'KB/s'}
        #data_dict['net_bytes_out_sum'] = {'volume':net_bytes_out_cur, 'unit':'B'}
        #data_dict['net_pkts_in'] = {'volume':net_pkts_in, 'unit':'p/s'}
        #data_dict['net_pkts_out'] = {'volume':net_pkts_out, 'unit':'p/s'}

        #return {'data':data_dict, 'timestamp':time.asctime(time.localtime())}
        return data_dict['net_bytes_in']

    def main(self):
        print self.get_cpu()
        print self.get_mem()
        print self.get_disk()
        #print self.get_net()

if __name__ == '__main__':
    myData = DataPollster()
    myData.main()

