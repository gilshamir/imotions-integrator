# SEP Remote Control and Packet Reception Verification Guide
This guide provides instructions for:
1. **[Remote Control via RPC](#1-remote-control-via-rpc)**: Connecting to SEP, starting tracking, and enabling UDP logging.
2. **[Verification of Packet Reception via UDP](#2-verification-of-packet-reception-via-udp)**: Starting the UDP client to verify packet reception.

For more information on scripts, executables, tools, and prerequisites, refer to the [Additional Resources](#additional-resources) section below.

## 1. Remote Control via RPC

### Step 1: Start SEP
* Start Camera / Load Recording
* Define WCS

### Step 2: Start the RPC Client (CLI)
**Alternative 1**: Using a Python script
```
cd "C:\Program Files\Smart Eye\Smart Eye Pro X.X\API\Examples\PythonExamples\CLI"

py .\command_line.py
```

**Alternative 2**: Using an executable
```
cd "C:\Program Files\Smart Eye\Smart Eye Pro X.X\API\Examples\bin"

& .\CLI.exe
```

### Step 3: Connect to SEP
```
# Connect to the IP address and RPC port where SEP is running
connect 127.0.0.1 8100

# Verify the connection
ping

# You should receive the reply "pong"
```
### Step 4: Start Tracking
```
# Start tracking
start_tracking

# Verify that tracking is enabled
get_state

# You should receive the reply "The system is tracking"
```
### Step 5: Enable UDP Logging
```
# Enable UDP logging of frame number and time stamp
open_data_stream_udp 127.0.0.1 5001 FrameNumber;TimeStamp
```

## 2. Verification of Packet Reception via UDP
**Alternative 1**: Using a Python script
```
cd "C:\Program Files\Smart Eye\Smart Eye Pro X.X\API\Examples\PythonExamples\SocketClient"

py .\main.py UDP --addr 127.0.0.1 --port 5001

# You should now see packets arriving like this:
# ============
# ** PACKET **
# FrameNumber = 1828
# TimeStamp = 1824707016
# ============

```

**Alternative 2**: Using an executable
```
cd "C:\Program Files\Smart Eye\Smart Eye Pro X.X\API\Examples\bin"

& .\SocketClient.exe UDP 5001 127.0.0.1

# You should now see packets arriving like this:
# Packet type = 4, Total size = 28 (Header size = 8 + Data size = 20)
# FrameNumber             1734
# TimeStamp               1809024929
```

## Additional Resources

### Tools and Prerequisites
#### SEP
SEP functions as a <u>server</u> in this setup, accepting connections via RPC and serving TCP/UDP packets.

To issue commands to SEP, start the SEP instance intended for control. Additionally, connect a camera or load a recording, and define a WCS. Without these steps, tracking cannot begin, and SEP will not output any TCP/UDP packets.

#### Python Scripts
To connect <u>clients</u> to the SEP server using Python scripts, a Python installation is required.

Python 3.12 is recommended. The installation can be checked in the terminal with `python -V`. 
If Python is not already installed, install it. The latest release should be chosen, and the box to add Python to the path should be ticked.

*Note*: If running `python -V` results in an error message indicating the command is not recognized, ensure that `C:\Users\<Your.Username>\AppData\Local\Programs\Python\Python312\` is included in the PATH variable:

1. Press Win and type Env -> click on "Edit the system environment variables".
2. Click on Environment variables.
3. Double-click on Path and ensure that only one Python directory is listed.

##### command_line.py
This is the command line interface, where a <u>RPC client</u> connection to SEP can be made and commands can be issued.

##### sep-py
This is the Python module, where a <u>UDP client</u> connection to SEP can be made. The sep-py module has to be installed to receive and parse TCP/UDP packets sent by SEP. The steps to do so are outlined here: `C:\Program Files\Smart Eye\Smart Eye Pro X.X\API\Examples\PythonExamples\SocketClient\README.md`

Install sep-py:
```
pip install "C:\Program Files\Smart Eye\Smart Eye Pro X.X\API\Examples\PythonExamples\sep_py-X.X.0-py3-none-any.whl"
```

#### Executables
To connect <u>clients</u> to the SEP server using executables, no prerequisites are needed.

### Documentation
* Programmers' Guide:  
    `C:\Program Files\Smart Eye\Smart Eye Pro X.X\Doc\ProgrammersGuide.pdf`

* CLI help:  
    Type `help` or `help <topic>` in the SEP Python CLI

* Socket Client README:  
    `C:\Program Files\Smart Eye\Smart Eye Pro X.X\API\Examples\PythonExamples\SocketClient\README.md`

### Python Scripts
`C:\Program Files\Smart Eye\Smart Eye Pro X.X\API\Examples\PythonExamples\`
* `CLI\`
    * `command_line.py` - Example command line interface for controlling SEP via RPC
* `SocketClient\`
    * `main.py` - Example socket client for receiving packets from SEP via TCP/UDP

### Executables
`C:\Program Files\Smart Eye\Smart Eye Pro X.X\API\Examples\bin\`
* `CLI.exe` - Example command line interface for controlling SEP via RPC
* `SocketClient.exe` - Example socket client for receiving packets from SEP via TCP/UDP