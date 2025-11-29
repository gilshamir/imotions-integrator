# SocketClient

An example for receiving SEP output data (sepd) through a socket (TCP/UDP)
connection using the `TCPClient` and/or `UDPClient` classes.

## Setup

1. Copy this example to a location with write access (e.g. the Desktop).
1. Install Python 3.12.
2. (Optional) Setup a virtual environment:
   ```
   > python -m venv venv
   > .\venv\Scripts\activate
   ```
3. Install the `sep-py` wheel (replace "X.Y" with the SEP version):
   ```
   > pip install "C:\Program Files\Smart Eye\Smart Eye Pro X.Y\API\Examples\PythonExamples\sep_py-X.Y.0-py3-none-any.whl"
   ```

## Run

First start Smart Eye Pro and setup logging to either UDP or TCP.

Then run the example:

```
> python .\main.py TCP|UDP [--addr addr] [--port port]
```
