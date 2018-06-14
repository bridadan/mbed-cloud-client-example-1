#!/usr/bin/env python

from __future__ import print_function
from builtins import int
import os
import sys
import argparse
import time
import datetime

from mbed_cloud import ConnectAPI

class Types_v1(object):
    HEAP = 0
    ALL_THREADS = 1
    CURRENT_THREAD = 2
    CPU = 3

class Heap_v1(object):
    def __init__(self, buffer):
        self.current_size = buffer.read_uint32()
        self.max_size = buffer.read_uint32()
        self.total_size = buffer.read_uint32()
        self.reserved_size = buffer.read_uint32()
        self.alloc_cnt = buffer.read_uint32()
        self.alloc_fail_cnt = buffer.read_uint32()

class Thread_v1(object):
    def __init__(self, buffer):
        self.id = buffer.read_uint32()
        self.state = buffer.read_uint32()
        self.priority = buffer.read_uint32()
        self.stack_size = buffer.read_uint32()
        self.stack_space = buffer.read_uint32()

class AllThreads_v1(object):
    def __init__(self, buffer):
        number_of_threads = buffer.read_uint32()
        self.threads = []
        for thread_index in range(number_of_threads):
            self.threads.append(Thread_v1(buffer))

class CPU_v1(object):
    def __init__(self, buffer):
        self.uptime = buffer.read_uint64()
        self.idle_time = buffer.read_uint64()
        self.sleep_time = buffer.read_uint64()
        self.deep_sleep_time = buffer.read_uint64()

class Buffer(object):
    def __init__(self, buffer):
        self._buffer = buffer
        self._index = 0

    def read_uint8(self):
        result = int(self._buffer[self._index].encode('hex'), 16)
        self._index += 1
        return result

    def read_uint32(self):
        result = self.read_uint8()
        result += self.read_uint8() << 8
        result += self.read_uint8() << 16
        result += self.read_uint8() << 24
        return result

    def read_uint64(self):
        result = self.read_uint8()
        result += self.read_uint8() << 8
        result += self.read_uint8() << 16
        result += self.read_uint8() << 24
        result += self.read_uint8() << 32
        result += self.read_uint8() << 40
        result += self.read_uint8() << 48
        result += self.read_uint8() << 56
        return result

class DeviceMetric_v1(object):
    def __init__(self, buffer):
        self.entries = []
        self.timestamp = buffer.read_uint64()
        num_entries = buffer.read_uint8()

        for _ in range(num_entries):
            type = buffer.read_uint8()

            if type == Types_v1.HEAP:
                self.entries.append(Heap_v1(buffer))
            if type == Types_v1.ALL_THREADS:
                self.entries.append(AllThreads_v1(buffer))
            if type == Types_v1.CURRENT_THREAD:
                self.entries.append(Thread_v1(buffer))
            if type == Types_v1.CPU:
                self.entries.append(CPU_v1(buffer))


def main():
    # Set your API key in the ".mbed_cloud_config.json" file
    connect_api = ConnectAPI()
    connect_api.start_notifications()
    data = connect_api.get_resource_value_async("0164001e39cb000000000001001002d5", "/26250/0/4014")

    while not data.is_done:
        time.sleep(0.1)
    buffer = Buffer(data.value)
    version = buffer.read_uint8()

    if version == 1:
        metrics = DeviceMetric_v1(buffer)
        print(datetime.datetime.fromtimestamp(metrics.timestamp))
        for metric in metrics.entries:
            if metric.__class__.__name__ == 'AllThreads_v1':
                for thread in metric.threads:
                    print(thread.__dict__)
            else:
                print(metric.__dict__)
    else:
        print("Unknown version %d" % (version))


if __name__ == '__main__':
    sys.exit(main())
