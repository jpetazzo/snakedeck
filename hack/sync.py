#!/usr/bin/env python

import json
import os
import socket
import struct
import sys
import time

sync_address = "224.0.19.4"
sync_port = 19004
sync_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sync_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sync_socket.bind(("0.0.0.0", sync_port))
sync_address_as_bytes = socket.inet_aton(sync_address)
sync_sockopt = struct.pack('4sL', sync_address_as_bytes, socket.INADDR_ANY)
sync_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, sync_sockopt)

sync_channel = sys.argv[1]
sync_message = sys.argv[2]


def send_sync_message(data):
	data["serial"] = int(time.time())
	data["actor"] = "SYNC{}@{}".format(os.getpid(), socket.gethostname())
	data["label"] = sync_message
	data.pop("emoji", None)
	print(f"Sending: {data}")
	data_as_bytes = json.dumps(data).encode("utf-8")
	sync_socket.sendto(data_as_bytes, (sync_address, sync_port))
	print ("Sent!")


send_sync_message(dict(sync=sync_channel))


while True:
	print("Waiting for sync message...")
	data_as_bytes = sync_socket.recv(1024)
	data = json.loads(data_as_bytes.decode("utf-8"))
	print("Got sync message on channel {!r}".format(data["sync"]))
	print(data)
	if data["sync"] == sync_channel:
		send_sync_message(data)
		exit(0)
