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
        self.worldmsg = None

    def _thread_function(self):
        sleep(2)
        # pass
        if not self.world_actor:
            logging.debug("Creating World Actor")
            self.world_actor = self.createActor(World)
        self.send(self.myAddress, "start")
        logging.debug("Sending 'start'")

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

    @overrides
    def __init__(self):
        super().__init__()

    @overrides
    def receiveMessage(self, msg, sender):
        logging.info("World got: %s", msg)
        if isinstance(msg, tuple):
            self.send(msg[0], msg[1] + " world!")


def run_example(systembase=None):
    """Main function running the example"""
    asys = ActorSystem(systembase, logDefs=logcfg)
    hello_thread = asys.createActor(HelloThread)
    try:
        for i in range(1, 1001):
            before = datetime.now()
            greeting = asys.ask(hello_thread, "are you there?", timedelta(minutes=5))
            print(greeting)
            after = datetime.now()
            time_hello_1 = after - before
            print(f"Round {i} of HelloThread took {time_hello_1.total_seconds()} s.")
            # sleep(1)
    finally:
        asys.shutdown()


if __name__ == "__main__":
    import sys

    run_example(sys.argv[1] if len(sys.argv) > 1 else None)
