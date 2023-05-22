"""Demonstration of the "hanging Actor message" issue

Run this from the top level as:
   $ python examples/hellogoodbye.py  [system-base-name]

   where system-base-name in (multiprocTCPBase, multiprocUDPBase, multiprocQueuBase)
"""

import logging
from datetime import datetime, timedelta
from threading import Thread
from time import sleep

from overrides import overrides  # type: ignore
from thespian.actors import Actor, ActorSystem

from logsetup import logcfg


class HelloThread(Actor):
    """Actor sending the string \"Hello\" when receiving a msg.
    This one is starting a thread sending the message to World."""

    @overrides
    def __init__(self):
        super().__init__()
        self.thread_sending_msg = Thread(target=self._thread_function, daemon=True)
        self.sender = None
        self.world_actor = None

    def _thread_function(self):
        if not self.world_actor:
            self.world_actor = self.createActor(World)
        worldmsg = (self.sender, "Hello from thread,")
        logging.info("Hello is trying to send %s to %s", worldmsg, self.world_actor)
        self.send(self.world_actor, worldmsg)

    @overrides
    def receiveMessage(self, msg, sender):
        logging.info("Hello1 got: %s", msg)
        self.sender = sender
        if msg == "are you there?":
            self.thread_sending_msg = Thread(target=self._thread_function, daemon=True)
            self.thread_sending_msg.start()


class Hello(Actor):
    """Actor sending the string \"Hello\" when receiving a msg.
    This one is for comparison."""

    @overrides
    def __init__(self):
        super().__init__()
        self.sender = None
        self.world_actor = None

    @overrides
    def receiveMessage(self, msg, sender):
        logging.info("Hello got: %s", msg)
        self.sender = sender
        if msg == "are you there?":
            if not self.world_actor:
                self.world_actor = self.createActor(World)
            worldmsg = (self.sender, "Hello,")
            logging.info("Hello is trying to send %s to %s", worldmsg, self.world_actor)
            self.send(self.world_actor, worldmsg)


class World(Actor):
    """Actor sending the string \" world!\" when receiving a msg"""

    @overrides
    def receiveMessage(self, msg, sender):
        if isinstance(msg, tuple):
            orig_sender, pre_world = msg
            self.send(orig_sender, pre_world + " world!")


class Goodbye(Actor):
    """Actor sending the string \"Goodbye\" when receiving a msg"""

    @overrides
    def receiveMessage(self, msg, sender):
        self.send(sender, "Goodbye")


def run_example(systembase=None):
    """Main function running the example"""
    asys = ActorSystem(systembase, logDefs=logcfg)
    hello = asys.createActor(Hello)
    hello_thread = asys.createActor(HelloThread)
    goodbye = asys.createActor(Goodbye)
    for i in range(0, 999):
        before = datetime.now()
        greeting = asys.ask(hello, "are you there?", timedelta(seconds=5))
        print(greeting + "\n" + asys.ask(goodbye, None, timedelta(milliseconds=100)))
        after = datetime.now()
        time_hello = after - before
        print(f"Round {i} of Hello took {time_hello.total_seconds()} s.")
        before = datetime.now()
        greeting = asys.ask(hello_thread, "are you there?", timedelta(seconds=5))
        print(greeting + "\n" + asys.ask(goodbye, None, timedelta(milliseconds=100)))
        after = datetime.now()
        time_hello_1 = after - before
        print(f"Round {i} of HelloThread took {time_hello_1.total_seconds()} s.")
        sleep(i)
    asys.shutdown()


if __name__ == "__main__":
    import sys

    run_example(sys.argv[1] if len(sys.argv) > 1 else None)
