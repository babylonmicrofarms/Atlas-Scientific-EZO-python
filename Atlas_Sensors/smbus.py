#!/usr/bin/python3
from time import sleep
from smbus2 import SMBus, i2c_msg
import logging

import code

class AtlasSMBus(object):
	long_timeout = 0.9         	# the timeout needed to query readings and calibrations
	short_timeout = 0.3         # timeout for regular commands
	default_bus = 1         	# the default bus for I2C on the newer Raspberry Pis, certain older boards use bus 0
	default_address = 99     	# the default address for the sensor
	current_addr = default_address

	response_codes = {
		255: 'no data to send', 
		254: 'still processing, not ready', 
		2: 'syntax error', 
		1: 'successful request'
	}

	def __init__(self, address=default_address, bus=default_bus):
		self.logger = logging.getLogger('read-sensors')
		self.logger.debug("Pure Python EZO Wrapper")
		self.bus_num = bus
		
		self.set_i2c_address(address)


	def set_i2c_address(self, addr):
		self.current_addr = addr

	def write(self, cmd):
		# Convert the string, to an array of integers
		cmdarray = list(bytes(cmd,"UTF-8"))
		# Make an i2c write message object
		# print("Writing data: %r" % cmdarray)
		write = i2c_msg.write(self.current_addr, cmdarray )
		# Attempt to actually do the write
		try:
			with SMBus(self.bus_num) as bus:
				bus.i2c_rdwr(write)
				# bus.write_block_data(self.current_addr,0, cmdarray)
		except OSError:
			self.logger.error("AtlasSMBus I2C Error!")
			return -1

	def read(self, num_of_bytes=31):
		# Make an i2c read message object to read 8 bytes back from the sensor address
		read = i2c_msg.read(self.current_addr, num_of_bytes)
		# Initiate read on the i2c bus
		data = []
		try:
			with SMBus(self.bus_num) as bus:
				# bus.i2c_rdwr(read)
				data = bus.read_i2c_block_data(self.current_addr, 0, num_of_bytes)
				# data = bus.read_block_data(self.current_addr, 0)
				# d = bus.read_byte(self.current_addr)
				# while d != 0:
				# 	data.append(d)
				# 	d = bus.read_byte(self.current_addr)

		except OSError:
			self.logger.error("AtlasSMBus I2C Error!")
			return "I2C OSError"

		# print(data)
		# return data
		# The response code is the first character in the buffer
		# 1 is good, 2 is malformed command, 254 is needs more time, and 255 is no data
		rc = data[0]
		last = data[len(data)-1]
		# print(last)
		if last == 255:
			# print("Bad Read, returned garbage data, but no device errors")
			return "BAD READ"
		elif rc == 1 and last != 255:
			self.logger.debug("AtlasSMBus Command Successful! RC: {} --> {}".format(rc,self.response_codes[rc]) )
			# Slice the buffer returned from the read, convert to ascii, and remove null characters
			# print(read.buf[1:16].decode('ascii').rstrip('\x00'))
			# print(read)
			# print(type(read))
			# print(len(read.buf))
			# result = read.buf[1:24].decode('ascii').rstrip('\x00')
			result = "".join(list(map(lambda x: chr(x), data[1:] ))).rstrip('\x00')
			return result
		elif rc != 1:
			# Check for wildly wrong response codes
			if rc not in list(response_codes.keys()):
				self.logger.error(f"Garbled RC: {rc}, probable communication error.")
				return "BAD READ"
			# Return to the user the error code if error occured
			self.logger.error("Error {} --> {}".format(rc,self.response_codes[rc]))
			return "Error {} --> {}".format(rc,self.response_codes[rc])


	def query(self, cmdstring):
		self.write(cmdstring)
		# the read and calibration commands require a longer timeout
		if((cmdstring.upper().startswith("R")) or
			(cmdstring.upper().startswith("CAL"))):
			sleep(self.long_timeout)
		elif cmdstring.upper().startswith("SLEEP"):
			# Just return sleep if activating sleep mode
			# Don't do the read or else it will wake sensor back up
			return "sleep mode"
		elif cmdstring.upper().startswith("IMPORT"):
			sleep(self.short_timeout)
			return self.read(num_of_bytes=1)
		else:
			sleep(self.short_timeout)
		return self.read()


	def list_i2c_devices(self):
		i2c_devices = []
		# Iterate through the I2C address space
		for i in range (0,128):
			# Try and read a byte of data
			# If read fails a device with that address isnt on the bus
			try:
				with SMBus(1) as bus:
					bus.read_byte_data(i,0)
				i2c_devices.append(i)
			except IOError:
				pass
			sleep(0.05)
		return i2c_devices


		
def main():
	from time import sleep
		# creates the I2C port object, specify the address or bus if necessary
	device = AtlasSMBus() 
	# print(">> Atlas Scientific sample code")
	# print(">> Any commands entered are passed to the board via I2C except:")
	# print(">>   List_addr lists the available I2C addresses.")
	# print(">>   Address,xx changes the I2C address the Raspberry Pi communicates with.")
	# print(">>   Poll,xx.x command continuously polls the board every xx.x seconds")
	# print(" where xx.x is longer than the %0.2f second timeout." % AtlasSMBus.long_timeout)
	# print(">> Pressing ctrl-c will stop the polling")
	code.interact(local=locals())	
	# main loop
	# while True:
	# 	input_cmd = input("Enter command: ")

	# 	if input_cmd.upper().startswith("LIST_ADDR"):
	# 		devices = device.list_i2c_devices()
	# 		for i in range(len (devices)):
	# 			print(devices[i])

	# 	# address command lets you change which address the Raspberry Pi will poll
	# 	elif input_cmd.upper().startswith("ADDRESS"):
	# 		addr = int(str.split(input_cmd, ',')[1])
	# 		device.set_i2c_address(addr)
	# 		print("I2C address set to " + str(addr))

	# 	# continuous polling command automatically polls the board
	# 	elif input_cmd.upper().startswith("POLL"):
	# 		delaytime = float(str.split(input_cmd, ',')[1])

	# 		# check for polling time being too short, change it to the minimum timeout if too short
	# 		if delaytime < AtlasSMBus.long_timeout:
	# 			print("Polling time is shorter than timeout, setting polling time to %0.2f" % AtlasSMBus.long_timeout)
	# 			delaytime = AtlasSMBus.long_timeout

	# 		# get the information of the board you're polling
	# 		info = str.split(device.query("I"), ",")[1]
	# 		print("Polling %s sensor every %0.2f seconds, press ctrl-c to stop polling" % (info, delaytime))

	# 		try:
	# 			while True:
	# 				print(device.query("R"))
	# 				sleep(delaytime - AtlasSMBus.long_timeout)
	# 		except KeyboardInterrupt: 		# catches the ctrl-c command, which breaks the loop above
	# 			print("Continuous polling stopped")

	# 	# if not a special keyword, pass commands straight to board
	# 	else:
	# 		if len(input_cmd) == 0:
	# 			print("Please input valid command.")
	# 		else:
	# 			try:
	# 				print(device.query(input_cmd))
	# 			except IOError:
	# 				print("Query failed \n - Address may be invalid, use List_addr command to see available addresses")


if __name__ == '__main__':
	# main()
	device = AtlasSMBus() 
	code.interact(local=locals())
