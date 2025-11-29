import argparse
import logging
from pathlib import Path

from sep.sepd import Packet, Parser

READ_CHUNK_SIZE = 2**16


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to binary file to parse as sepd.", type=Path)
    return parser.parse_args()


def _handle_packet(packet: Packet) -> None:
    print("** PACKET **")
    if packet.frame_number is not None:
        print(f"FrameNumber = {packet.frame_number}")
    if packet.time_stamp is not None:
        print(f"TimeStamp = {packet.time_stamp}")

    # Add handling of other Smart Eye Pro data here. See the `Packet` datatype
    # for what data is available, or consult the Programmer's Guide. Note that
    # a `Packet` will only contain data for output data that is selected in
    # Smart Eye Pro, and may additionally be subject to limitations imposed by
    # the Smart Eye Pro license. Furthermore, most data is only available when
    # the Smart Eye Pro system is in a tracking state.
    print("============")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    )
    args = _parse_args()
    path: Path = args.path
    parser = Parser()
    with path.open("rb") as f:
        while True:
            chunk = f.read(READ_CHUNK_SIZE)
            if len(chunk) == 0:
                break  # EOF
            for packet in parser.parse_stream(chunk):
                _handle_packet(packet)
    if parser.flush_stream():
        # If parser has any state when we have read the entire file then the
        # input was not complete.
        raise RuntimeError("Incomplete data stream.")
    print("All done.")


if __name__ == "__main__":
    main()
