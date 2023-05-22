"""Demonstration of the "hanging Actor message" issue

Run this from the top level as:
   $ python examples/hellogoodbye.py  [system-base-name]
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
        self.worldmsg = None

    def _thread_function(self):
        sleep(0.5)
        if not self.world_actor:
            self.world_actor = self.createActor(World)
        self.send(self.myAddress, "start")

    @overrides
    def receiveMessage(self, msg, sender):
        logging.info("HelloThread got: %s", msg)
        self.sender = sender
        if msg == "are you there?":
            self.worldmsg = (self.sender, "Hello from thread,")
            self.thread_sending_msg = Thread(target=self._thread_function, daemon=True)
            self.thread_sending_msg.start()
        elif msg == "start":
            logging.info(
                "HelloThread is trying to send %s to %s",
                self.worldmsg,
                self.world_actor,
            )
            self.send(self.world_actor, self.worldmsg)


class World(Actor):
    """Actor sending the string \" world!\" when receiving a msg"""

    def _thread_function(self):
        sleep(0.5)
        self.send(self.sender, self.pre_world + " world!")

    @overrides
    def __init__(self):
        super().__init__()
        self.thread_sending_msg = Thread(target=self._thread_function, daemon=True)
        self.sender = None
        self.pre_world = None

    @overrides
    def receiveMessage(self, msg, sender):
        if isinstance(msg, tuple):
            self.sender, self.pre_world = msg
            self.thread_sending_msg = Thread(target=self._thread_function, daemon=True)
            self.thread_sending_msg.start()


class Goodbye(Actor):
    """Actor sending the string \"Goodbye\" when receiving a msg"""

    @overrides
    def receiveMessage(self, msg, sender):
        self.send(sender, "Goodbye")


def run_example(systembase=None):
    """Main function running the example"""
    asys = ActorSystem(systembase, logDefs=logcfg)
    hello_thread = asys.createActor(HelloThread)
    goodbye = asys.createActor(Goodbye)
    try:
        for i in range(1, 10001):
            before = datetime.now()
            greeting = asys.ask(hello_thread, "are you there?", timedelta(seconds=5))
            print(greeting + "\n" + asys.ask(goodbye, None, timedelta(seconds=5)))
            after = datetime.now()
            time_hello_1 = after - before
            print(f"Round {i} of HelloThread took {time_hello_1.total_seconds()} s.")
            sleep(i)
    finally:
        asys.shutdown()


if __name__ == "__main__":
    import sys

    run_example(sys.argv[1] if len(sys.argv) > 1 else None)
