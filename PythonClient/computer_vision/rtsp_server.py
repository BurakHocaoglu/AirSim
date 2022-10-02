#!/usr/bin/env python3

import sys
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
gi.require_version("GstRtspServer", "1.0")
from gi.repository import Gst, GstApp, GstRtspServer, GObject

import airsim
import traceback
import numpy as np

frame_size = 256 * 144 * 3

class AirSimMediaFactory(GstRtspServer.RTSPMediaFactory):

	def __init__(self):
		GstRtspServer.RTSPMediaFactory.__init__(self)
		self.client = airsim.VehicleClient()
		print("AirSim client is created.")

		self.requests = [
			airsim.ImageRequest("0", airsim.ImageType.Scene, compress=False)
		]
		print("The list of requests is created.")

		self.appsrc = None
		self.pipeline = None

	def do_create_element(self, uri):
		# s_src = "v4l2src ! video/x-raw,rate=30,width=320,height=240 ! videoconvert ! video/x-raw,format=I420"
		# s_h264 = "videoconvert ! vaapiencode_h264 bitrate=1000"
		# s_src = "videotestsrc ! video/x-raw,rate=30,width=256,height=144,format=I420"
		# s_src = "appsrc name=AirSimRtspSrv ! video/x-raw,rate=30,width=256,height=144,format=I420"

		s_src = "appsrc name=AirSimRtspSrv"
		s_h264 = "x264enc tune=zerolatency"
		self.pipeline = "( {s_src} ! queue max-size-buffers=1 name=q_enc ! {s_h264} ! rtph264pay name=pay0 pt=96 )".format(**locals())
		return Gst.parse_launch(pipeline)

	def do_media_configure(self, media):
		element = media.get_element()
		# appsrc = Gst.Bin.get_by_name_recurse_up("AirSimRtspSrv")

		self.appsrc = self.pipeline.get_by_cls(GstApp.AppSrc)[0]
		self.appsrc.set_property("format", Gst.Format.TIME)
		self.appsrc.set_caps(Gst.Caps.from_string("video/x-raw,rate=30,width=256,height=144,format=I420"))

		# ??????????????????????
		appsrc.connect("need-data", self.need_data_cb)

	def need_data_cb(self):
		pass

	# def request_images(self):
	# 	responses = self.client.simGetImages(self.requests)

class GstServer(object):

	def __init__(self):
		self.server = GstRtspServer.RTSPServer()
		self.server.set_address("192.168.1.47")
		self.server.set_service("8554")

		self.factory = AirSimMediaFactory()
		self.factory.set_shared(True)

		self.mounts = self.server.get_mount_points()
		self.mounts.add_factory("/airsim-test", self.factory)

		self.server.attach(None)

if __name__ == "__main__":
	loop = GObject.MainLoop()
	GObject.threads_init()
	# Gst.init(None)
	Gst.init(sys.argv)

	airsim_media_server = GstServer()
	print("Server is created.")

	loop.run()