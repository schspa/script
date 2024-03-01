#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#
#   get-ina226-power.py --- Description
#
#   Copyright (C) 2024, Schspa, all rights reserved.
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os
import sys
import time
import click
import pyftdi
from pyftdi.gpio import GpioAsyncController
from pyftdi.i2c import I2cController
import subprocess
from pprint import pprint
import traceback

def read_power(dev_filter='', port=2):
    # Instantiate an I2C controller
    i2c = I2cController()

    # Configure the first interface (IF/1) of the FTDI device as an I2C master
    #i2c.configure('ftdi://ftdi:2232h/1')
    i2c.configure('ftdi://ftdi:4232:%s/%d' % (dev_filter, port))

    # Get a port to an I2C slave device
    slave = i2c.get_port(0x47)

    # Send one byte, then receive one byte
    # slave.exchange([0x04], 1)

    # Write a register to the I2C slave
    slave.write_to(0x05, b'\x64\x00')
    slave.write_to(0x00, b'\x42\x95')

    # Read a register from the I2C slave
    # slave.read_from(0x00, 1)
    out = slave.read_from(0x4, 2)
    current = int(out[0]) << 8
    current += int(out[1])
    current = current * 0.2

    out = slave.read_from(0x2, 2)
    voltage = int(out[0]) << 8
    voltage += int(out[1])
    voltage = voltage * 1.25
    print('current: {:.2f} mA voltage: {:.2f} mV power: {:.2f} mW'.format(current, voltage, current * voltage/1000))

    pass

def get_fdti_filter(tty):
    status, path = subprocess.getstatusoutput('udevadm info -q path %s' %(tty))
    if status != 0:
        return ''

    ftdi_path = os.path.abspath(os.path.join('/sys%s' %(path), os.pardir, os.pardir, os.pardir, os.pardir))

    status, busnum = subprocess.getstatusoutput('cat %s' %(os.path.join(ftdi_path, 'busnum')))
    if status != 0:
        return ''
    status, devnum = subprocess.getstatusoutput('cat %s' %(os.path.join(ftdi_path, 'devnum')))
    if status != 0:
        return ''

    return '%x:%x:' % (int(busnum), int(devnum))

def get_ina226_power(tty, port = 2):
    ftdi_filter = get_fdti_filter(tty)
    try:
        read_power(ftdi_filter, port);
    except pyftdi.usbtools.UsbToolsError as e:
        print(e)
        traceback.print_exc()
        pass

@click.command()
@click.argument('tty', type=click.Path(exists=True))
@click.option('port', '--port', type=int, default=2)
def get_power_cli(tty, port):
    return get_ina226_power(tty, port)

if __name__ == '__main__':
    get_power_cli()
