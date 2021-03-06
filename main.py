import threading
import logging
import argparse
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib

log = logging.getLogger(__name__)


parser = argparse.ArgumentParser()
parser.add_argument(
    "-vid",
    "--video",
    type=str,
    help="The path of the video file"
)
args = parser.parse_args()

class RtspSystem(GstRtspServer.RTSPMediaFactory):
    def __init__(self, **properties):
        super(RtspSystem, self).__init__(**properties)
        log.info("init rtsp system")
        self.frame = None
        self.number_frames = 0
        self.fps = 30
        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
        self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                             'caps=video/x-raw,format=BGR,width=300,height=300,framerate={}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96'.format(self.fps)

    def send_frame(self, data):
        self.frame = data

    def start(self):
        t = threading.Thread(target=self._thread_rtsp)
        t.start()

    def _thread_rtsp(self):
        loop = GLib.MainLoop()
        loop.run()

    def on_need_data(self, src, length):
        #log.info("In on_need_data")
        data = self.frame.tobytes()
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        buf.duration = self.duration
        timestamp = self.number_frames * self.duration
        buf.pts = buf.dts = int(timestamp)
        buf.offset = timestamp
        self.number_frames += 1
        retval = src.emit('push-buffer', buf)
        #    log.info('pushed buffer, frame {}, duration {} ns, durations {} s'.format(self.number_frames,
        #                                                                           self.duration,
        #                                                                           self.duration / Gst.SECOND))
        if retval != Gst.FlowReturn.OK:
            print(retval)

    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)

    def do_configure(self, rtsp_media):
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name('source')
        appsrc.connect('need-data', self.on_need_data)


class RTSPServer(GstRtspServer.RTSPServer):
    def __init__(self, **properties):
        super(RTSPServer, self).__init__(**properties)
        self.rtsp = RtspSystem()
        self.rtsp.set_shared(True)
        self.get_mount_points().add_factory("/preview", self.rtsp)
        self.attach(None)
        Gst.init(None)
        self.rtsp.start()

    def send_frame(self, frame):
        self.rtsp.send_frame(frame)

if __name__ == "__main__":
    from pathlib import Path
    import cv2

    print("Start RTSP server")
    server = RTSPServer()
    if args.video is not None:
        capture = cv2.VideoCapture(args.video)
        capture.set(cv2.CAP_PROP_FPS, 10)
    else:    
        capture = cv2.VideoCapture(0)
    
    print("Start stream")
    while True:
        ret, frame = capture.read()
        if ret:
            frame = cv2.resize(frame, dsize=(300,300))
            # print("Number of frames: ", num_frame, end= "/r")
            server.send_frame(frame)
        else:
            print("Read frame failed")
            break
    print("Stream stopped")
