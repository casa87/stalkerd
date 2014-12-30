#!/bin/env python
# -*- coding: UTF-8 -*-


from gevent import monkey
monkey.patch_all()

import json
import psutil
import gevent
import zerorpc
import gevent.subprocess as subprocess


class Stalkerd:

    def process_list(self):
        """list all process"""
        process = psutil.get_pid_list()
        output = {}
        for pid in process:
            try:
                p = psutil.Process(pid)
                output[pid] = {"name": p.name(),
                               "cmd": " ".join(p.cmdline()),
                               "memory": p.get_memory_percent(),
                               "cpu": dict(p.get_cpu_times()._asdict())}
            except:
                pass
        return output

    def process(self, pid):
        """get details about a specific process"""
        if int(pid) not in psutil.pids():
            return {}
        data = {}
        p = psutil.Process(int(pid))
        data['name'] = p.name()
        data['cmd'] = p.cmdline()
        data['status'] = p.status()
        data['create'] = p.create_time()
        data['cpu'] = dict(p.get_cpu_times()._asdict())
        data['memory'] = {"percent": p.memory_percent(),
                          "details": dict(p.memory_info()._asdict())}
        data['maps'] = []
        for map_file in p.memory_maps():
            data['maps'].append(dict(map_file._asdict()))
        data['file'] = []
        for file_open in p.open_files():
            data['file'].append(dict(file_open._asdict()))
        data['connections'] = []
        for connect in p.connections():
            data['connections'].append(dict(connect._asdict()))
        data['io'] = dict(p.io_counters()._asdict())
        data['ctx'] = dict(p.num_ctx_switches()._asdict())
        data['threads'] = p.num_threads()
        data['fd'] = p.num_fds()
        return data

    @zerorpc.stream
    def trace(self, pid=None, ppid=None):
        """trace a proccess id or ppid"""
        cmdline = ['sysdig', '-s', '2000', '-j']
        if pid:
            cmdline += ['proc.pid=%s' % pid]
        if ppid:
            cmdline += ['proc.ppid=%s' % ppid]
        cmd = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        try:
            for line in iter(cmd.stdout.readline, ""):
                if line.startswith('['):
                    line = line[1:]
                if line[-2] == ',': 
                    yield json.loads(line[:-2])
        except:
            cmd.kill()


if __name__ == '__main__':
    s = zerorpc.Server(Stalkerd())
    s.bind("tcp://0.0.0.0:5000")
    s.run()
