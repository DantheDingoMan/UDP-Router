#!/usr/bin/env python3
"""Router implementation using UDP sockets"""
'''
Author: Aidan Schooling
'''

import argparse
import logging
import pathlib
import random
import select
import socket
import struct
import time

from typing import Tuple, Set, Dict


THIS_HOST = None
BASE_PORT = 4300
ROUTES = {}

def read_config_file(filename: str) -> Tuple[Set, Dict]:
    global ROUTES
    """
    Read config file

    :param filename: name of the configuration file
    :return tuple of the (neighbors, routing table)
    """
    neighbor =[]
    score = []
    currenttable = ''
    routdict = {}
    global THIS_HOST
    if THIS_HOST == None:

        THIS_HOST = '127.0.0.1'
    try:
        
        
        with open(filename) as f:
            lines = f.read()

        test2 = []
        tests = lines.split("\n\n")

        for i in tests:
            test2.append(i.splitlines())

        for i in test2:

            if THIS_HOST == i[0]:

                
                for x in i[1:]:

                    split = x.split()

                    routdict[split[0]] = [int(split[1]), split[0]]
                    
                    neighbor.append(split[0])



        return (set(neighbor), routdict)


        
    except:
        print("error2")
        raise FileNotFoundError("Could not find the specified configuration file data/projects/routing/wrong_file.txt")


def format_update(routing_table: dict) -> bytes:
    """
    Format update message

    :param routing_table: routing table of this router
    :returns the formatted message
    """
    bytes = bytearray()
    bytes.append(0)

    for i in routing_table:
        splitsource = routing_table[i][1].split(".")

        for x in splitsource:

            bytes.append(int(x))
        bytes.append(routing_table[i][0])

    return bytes



def parse_update(msg: bytes, neigh_addr: str, routing_table: dict) -> bool:
    """
    Update routing table
    
    :param msg: message from a neighbor
    :param neigh_addr: neighbor's address
    :param routing_table: this router's routing table
    :returns True is the table has been updated, False otherwise
    """
    update = False
    
    msgarray = bytearray(msg)
    updateddict = {}
    del msgarray[0]
  

    index = 0
    addr = ''
    for i in msgarray:
        if index == 4:
            addr = addr[:-1]
            updateddict[addr] = i
            index = 0
            addr = ''
        else:
            addr += str(i) + '.'

            index+=1


    for i in updateddict:
        #need to acount that the path is only through the other table
        if i in routing_table:
            
            if routing_table[i][0] > (updateddict[i]  + routing_table[neigh_addr][0]):
                
                routing_table[i][0] = updateddict[i] + routing_table[neigh_addr][0]
                update = True
                
        else:
            
            routing_table[i] = [updateddict[i] + routing_table[neigh_addr][0], i]
            print(i)
            print('newroute', routing_table[i])
            print('entire table', routing_table)

        

    return update


def send_update(node: str) -> None:
    """
    Send update
    
    :param node: recipient of the update message
    """
    global ROUTES
    #need to get the routing table included somehow
    msg = format_update(ROUTES)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((THIS_HOST,BASE_PORT))
        sock.sendto(msg, (node, BASE_PORT + int(node[-1])))


def format_hello(msg_txt: str, src_node: str, dst_node: str) -> bytes:
    """
    Format hello message
    
    :param msg_txt: message text
    :param src_node: message originator
    :param dst_node: message recipient
    """
    bytes = bytearray()
    bytes.append(1)
    splitsource1 = src_node.split(".")
    splitsource2 = dst_node.split(".")
    for x in splitsource1:
        bytes.append(int(x))
    for x in splitsource2:
        bytes.append(int(x))    

    msg = bytearray(msg_txt.encode())



    return bytes + msg

def parse_hello(msg: bytes, routing_table: dict) -> str:
    """
    Parse the HELLO message

    :param msg: message
    :param routing_table: this router's routing table
    :returns the action taken as a string



    ### parse_hello()

    * Parse a message to deliver.
    * The function must parse the message and extract the destination address.
    * If *this* router is the destination, return (and print) the message, else forward it further
    * Look up the destination address in the routing table and return the next hop address.
    """
    print('msg', msg)

    print('routing', routing_table)

    msgarray = bytearray(msg)
    
    del msgarray[0]
  
    receive = msg[1:5]
    receivedStruct = list(struct.unpack('!bbbb', receive))
    
    send = msg[5:9]
    sendingStruct = list(struct.unpack('!bbbb', send))

    receivesend = []
    message = msg[9:]


    
    receivesend.append(receivedStruct)
    receivesend.append(sendingStruct)
    

    

    bytes = bytearray()
    destination = ""
    source = ""

    for i in receivesend[0]:
        source += str(i) + "."
    for i in receivesend[1]:
        destination += str(i) + "."
    
    destination = destination[:-1]
    source = source[:-1]
    
    compiledhello = (message.decode(), source, destination)
    




    if THIS_HOST == destination:
        return f"Received {compiledhello[0]} from {compiledhello[1]}"
    else:
        send_hello(compiledhello[0], compiledhello[1], compiledhello[2], routing_table)
        return f"Forwarded {compiledhello[0]} to {compiledhello[2]}"




def send_hello(msg_txt: str, src_node: str, dst_node: str, routing_table: dict) -> None:
    """
    Send a message

    :param mst_txt: message to send
    :param src_node: message originator
    :param dst_node: message recipient
    :param routing_table: this router's routing table
    """
    #Why no work
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((THIS_HOST, BASE_PORT))
        msg = format_hello(msg_txt, src_node, dst_node)
        
        

        sock.sendto(msg, (routing_table.get(dst_node)[1], BASE_PORT +int(dst_node[-1])))


def print_status(routing_table: dict) -> None:
    """
    Print status

    :param routing_table: this router's routing table
    """
    print("Rout----------value")
    for i in routing_table:
        print(i, " ", routing_table[i][0],)
    

def route(neighbors: set, routing_table: dict, timeout: int = 5):
    """
    Router's main loop

    :param neighbors: this router's neighbors
    :param routing_table: this router's routing table
    :param timeout: default 5
    """
    ubuntu_release = [
        "Groovy Gorilla",
        "Focal Fossa",
        "Eoam Ermine",
        "Disco Dingo",
        "Cosmic Cuttlefish",
        "Bionic Beaver",
        "Artful Aardvark",
        "Zesty Zapus",
        "Yakkety Yak",
        "Xenial Xerus",
    ]
    global ROUTES
    ROUTES = routing_table
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((THIS_HOST, BASE_PORT + int(THIS_HOST[-1])))
    socks = [sock]
    #change so that the ourting table is unnesssary
    for i in neighbors:
        print("Update sent to neighbors")
        send_update(i)
    
    print_status(routing_table)
    while socks:
        filepath, ip, err= select.select(socks, [], [], timeout)
        if random.randint(0, 30) < 10:
            print_status(routing_table)
            time.sleep(random.randint(1, 4))
            send_hello(random.choice(ubuntu_release), THIS_HOST, str(random.choice(list(neighbors))), routing_table)
            

        else:
            for i in filepath:
                packet, addr = sock.recvfrom(1024)
                if packet:
                    kindofmessage = packet[0]
                    if kindofmessage == 1:
                        print(parse_hello(packet, routing_table))
                    if kindofmessage == 0:
                        time.sleep(random.randint(1, 5))
                        updated = parse_update(packet, addr[0], routing_table)
                        print(updated)
                        for i in neighbors:
                            send_update(i)
                        print_status(routing_table)
                        

    sock.close()
    


def main():
    """Main function"""
    arg_parser = argparse.ArgumentParser(description="Parse")
    arg_parser.add_argument("-c", "--debug", action="store_true", help="Enable logging.DEBUG mode")
    arg_parser.add_argument("filepath", type=str, help="path to file")
    arg_parser.add_argument("ip", type=str, help="client ip")
    args = arg_parser.parse_args()
    

    global THIS_HOST 
    THIS_HOST = args.ip
    route(read_config_file(args.filepath)[0], read_config_file(args.filepath)[1], timeout=5)



if __name__ == "__main__":
    main()
