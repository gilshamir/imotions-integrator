import argparse
import logging
from typing import Optional, Union

from sep.sepd import Packet
from sep.socket import EndOfStreamError, TCPClient, UDPClient

TCP_DEFAULT_ADDR = "127.0.0.1"
TCP_DEFAULT_PORT = 5002
UDP_DEFAULT_ADDR = "0.0.0.0"
UDP_DEFAULT_PORT = 5555


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "socket_type",
        help="Socket type of SEP data connection.",
        choices=["UDP", "TCP"],
        default="TCP",
    )
    addr_help = (
        f"Socket address (default TCP: '{TCP_DEFAULT_ADDR}', UDP: '{UDP_DEFAULT_ADDR}')"
    )
    port_help = (
        f"Socket port (default TCP: {TCP_DEFAULT_PORT}, UDP: {UDP_DEFAULT_PORT})"
    )
    parser.add_argument("--addr", help=addr_help, type=str)
    parser.add_argument("--port", help=port_help, type=int)
    return parser.parse_args()


def _create_client(
    socket_type: str, addr: Optional[str], port: Optional[int]
) -> Union[TCPClient, UDPClient]:
    if socket_type == "TCP":
        addr = addr if addr else TCP_DEFAULT_ADDR
        port = port if port else TCP_DEFAULT_PORT
        logging.info(f"Creating TCPClient for '{addr}:{port}'...")
        return TCPClient(addr, port, timeout=50.0)
    elif socket_type == "UDP":
        addr = addr if addr else UDP_DEFAULT_ADDR
        port = port if port else UDP_DEFAULT_PORT
        logging.info(f"Creating UDPClient for '{addr}:{port}'...")
        return UDPClient(addr, port, timeout=50.0)
    else:
        raise ValueError(f"Unexpected socket_type: '{socket_type}'")


def _print_packet(packet: Packet) -> None:
    print("** PACKET **")
    if packet.frame_number is not None:
        print(f"FrameNumber = {packet.frame_number}")
    if packet.time_stamp is not None:
        print(f"TimeStamp = {packet.time_stamp}")
    if packet.closest_world_intersection is not None:
        print(f"ClosestWorldIntersection = {packet.closest_world_intersection}")
    if packet.all_world_intersections:
        # Note: The AllWorldIntersections data is sorted closest to farthest
        # away. The first entry will be the same as ClosestWorldIntersection.
        print("AllWorldIntersections:")
        for intersection in packet.all_world_intersections:
            print(f" - {intersection}")

    # Add handling of other Smart Eye Pro data here. See the `Packet` datatype
    # for what data is available, or consult the Programmer's Guide. Note that
    # a `Packet` will only contain data for output data that is selected in
    # Smart Eye Pro, and may additionally be subject to limitations imposed by
    # the Smart Eye Pro license. Furthermore, most data is only available when
    # the Smart Eye Pro system is in a tracking state.
    print("============")


def _run_client(client: Union[TCPClient, UDPClient]) -> None:
    # Connect client to start receiving packets.
    client.connect()
    logging.info("Receiving packets...")

    # Handle packets by continuously calling receive.
    try:
        while True:
            packet = client.receive()
            _print_packet(packet)
    except EndOfStreamError:
        logging.info("Remote end closed the stream, shutting down.")
    except TimeoutError:
        logging.info("Connection timed out, shutting down.")
    except KeyboardInterrupt:
        logging.info("Caught keyboard interrupt, shutting down.")
    finally:
        # When we are done with client, disconnect.
        client.disconnect()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    )
    args = _parse_args()
    client = _create_client(args.socket_type, args.addr, args.port)
    _run_client(client)


if __name__ == "__main__":
    main()
