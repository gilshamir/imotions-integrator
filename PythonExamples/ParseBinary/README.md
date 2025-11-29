# ParseBinary

Example showing how to parse a binary file in _sepd_ format using the
`sepd.Parser` class.

Generally Smart Eye Pro does not produce binary files in _sepd_ format, but it is
possible to create such a file by e.g. capturing TCP/UDP socket output. In
particular the .log files created by Smart Eye Pro for text logging are **not**
written as binary _sepd_.

An example "FRAME_NUMBER_TIMESTAMP.bin" file is included in this directory,
representing a single _sepd_ packet with the following content:

```
   SEFrameNumber = 41686
   SETimeStamp = 8479050983
```

## Setup

1. Copy this example to a location with write access (e.g. the Desktop).
1. Install Python 3.12.
2. (Optional) Setup a virtual environment:
   ```
   > python -m venv venv
   > .\venv\Scripts\activate
   ```
3. Install the `sep-py` wheel (replace "X.Y.Z" with the SEP version):
   ```
   > pip install "C:\Program Files\Smart Eye\Smart Eye Pro X.Y\API\Examples\PythonExamples\sep_py-X.Y.Z-py3-none-any.whl"
   ```

## Run

```
> python .\main.py .\FRAME_NUMBER_TIMESTAMP.bin
```
