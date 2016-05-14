#!/usr/bin/env python
import argparse
import sys
import socket
import itertools

from random import randint

from ouimeaux.environment import Environment
from ouimeaux.utils import matcher
from ouimeaux.signals import receiver, statechange, devicefound
from ouimeaux.utils import get_ip_address

triggers = {
    'Loft Steps':['Loft Bridge', 'Loft Lamp']
}


def mainloop():
    #source_matcher = matcher(source)
    random_port = randint(54300, 54499)

    env = Environment(bind="%s:%d"%(get_ip_address(), random_port), with_cache=False)


    @receiver(devicefound)
    def found(sender, **kwargs):
        all_targets = []
        for target in triggers.values():
            if isinstance(target, list):
                all_targets.extend(target)
            else:
                all_targets.append(target)

        for key in (triggers.keys() + all_targets):
            if matcher(key)(sender.name):
                print "Found device:", sender.name

    @receiver(statechange)
    def something_happened(sender, **kwargs):
        print "Something happened with %s"%sender
        for key in triggers.keys():
            if matcher(key)(sender.name):
                state = 1 if kwargs.get('state') else 0
                print "{} state is {state}".format(sender.name, state=state)
                if isinstance(triggers[key], list):
                    for target in triggers[key]:
                        set_target_state(target, state)
                else:
                    set_target_state(triggers[key], state)


    #this will intentionally not stop after it finds a first match so that we can use common prefixes to form groups
    def set_target_state(name, state):
        print "!!!  Set '%s' State = %s"%(name, state)
        for switch_name in env.list_switches():
            if matcher(name)(switch_name):
                print "Found a switch matching name %s" % name
                switch = env.get_switch(switch_name)
                switch.set_state(state)

        if len(env.list_bridges()) > 0:
            bridge = env.get_bridge(env.list_bridges()[0])
            for light_name in bridge.bridge_get_lights():
                if matcher(name)(light_name):
                    print "telling target (via bridge) to set state to %s"%state
                    light = bridge.bridge_get_lights()[light_name]
                    bridge.light_set_state(light, state=state, dim=254 if state==1 else None)

    try:
        print "Starting..."
        env.start()
        #env.upnp.server
        env.discover(2)
        sock = env.upnp.server._socket
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print "\t... discovering nearby devices"
        env.discover(10)
        print "Entering main loop"
        env.wait()
    except (KeyboardInterrupt, SystemExit):
        print "Goodbye!"
        sys.exit(0)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser("WeMo State Mirrorer")
    # parser.add_argument("source", metavar="SOURCE",
    #                     help="Name (fuzzy matchable)"
    #                          " of the source WeMo device")
    # parser.add_argument("target", metavar="TARGET",
    #                     help="Name (fuzzy matchable)"
    #                          " of the target WeMo device")
    # args = parser.parse_args()
    mainloop()
