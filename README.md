
# RSTP Streaming

This example allows you to stream frames via RTSP.
Supported single client.

## Installation

```
sudo apt-get install gstreamer-1.0 gir1.2-gst-rtsp-server-1.0 libgirepository1.0-dev
python3 -m pip install -r requirements.txt
```

## Usage

Run the application using webcam:

```
python3 main.py
```

Run the application using video:

```
python3 main.py --video <video path>
```
To see the streamed frames, use a RSTP Client (e.g. VLC Network Stream) with the following link

```
rtsp://localhost:8554/preview
```

