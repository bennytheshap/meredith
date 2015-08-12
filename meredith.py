#!/usr/bin/env python
import argparse
import sys
import socket

from random import randint

from ouimeaux.environment import Environment
from ouimeaux.utils import matcher
from ouimeaux.signals import receiver, statechange, devicefound
from ouimeaux.utils import get_ip_address


def mainloop(source, target):
    source_matcher = matcher(source)
    target_matcher = matcher(target)
    random_port = randint(54300, 54499)
    
    env = Environment(bind="%s:%d"%(get_ip_address(), random_port))


    @receiver(devicefound)
    def found(sender, **kwargs):
        if source_matcher(sender.name) or target_matcher(sender.name):
            print "Found device:", sender.name

    @receiver(statechange)
    def something_happened(sender, **kwargs):
        if source_matcher(sender.name):
            state = 1 if kwargs.get('state') else 0
            print "{} state is {state}".format(sender.name, state=state)
            set_target_state(target, state)

    #this will intentionally not stop after it finds a first match so that we can use common prefixes to form groups
    def set_target_state(name, state):
        for switch_name in env.list_switches():
            if target_matcher(switch_name):
                switch = env.get_switch(switch_name)
                switch.set_state(state)

        if len(env.list_bridges()) > 0:
            bridge = env.get_bridge(env.list_bridges()[0])
            for light_name in bridge.bridge_get_lights():
                if target_matcher(light_name):
                    print "telling target (via bridge) to set state to %s"%state
                    light = bridge.bridge_get_lights()[light_name]
                    bridge.light_set_state(light, state=state, dim=254 if state==1 else None)

    try:
        env.start()
        #env.upnp.server
        env.discover(1)
        sock = env.upnp.server._socket
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        env.discover(10)
        env.wait()
    except (KeyboardInterrupt, SystemExit):
        print "Goodbye!"
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("WeMo State Mirrorer")
    parser.add_argument("source", metavar="SOURCE",
                        help="Name (fuzzy matchable)"
                             " of the source WeMo device")
    parser.add_argument("target", metavar="TARGET",
                        help="Name (fuzzy matchable)"
                             " of the target WeMo device")
    args = parser.parse_args()
    mainloop(args.source, args.target)