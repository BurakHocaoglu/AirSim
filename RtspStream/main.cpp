// Copied from
// https://github.com/GStreamer/gst-rtsp-server/blob/master/examples/test-appsrc.c

extern "C" {
	#include <gst/gst.h>
	#include <gst/rtsp-server/rtsp-server.h>
}

#include "common/common_utils/StrictMode.hpp"
STRICT_MODE_OFF
#ifndef RPCLIB_MSGPACK
#define RPCLIB_MSGPACK clmdep_msgpack
#endif // !RPCLIB_MSGPACK
#include "rpc/rpc_error.h"
STRICT_MODE_ON

#include "vehicles/multirotor/api/MultirotorRpcLibClient.hpp"
#include "common/common_utils/FileSystem.hpp"
#include "json.hpp"

#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <vector>
#include <memory>
#include <string>
#include <thread>

using json = nlohmann::json;
using namespace msr::airlib;

// -----------------------------------------------------------------------------------
// AirSim typedefs
typedef ImageCaptureBase::ImageRequest ImageRequest;
typedef ImageCaptureBase::ImageResponse ImageResponse;
typedef ImageCaptureBase::ImageType ImageType;
typedef common_utils::FileSystem FileSystem;

// AirSim and GStreamer fused context
typedef struct AirSimStreamContext {
	std::unique_ptr<msr::airlib::RpcLibClientBase> client;
	// std::unique_ptr<msr::airlib::MultirotorRpcLibClient> client;
	std::vector<ImageRequest> requests;
	GstClockTime timestamp;
	int frame_size;
	int height;
	int width;
	int channels;
} AirSimStreamContext;

void navigation_func(AirSimStreamContext *ctx);

// Utility variables
std::chrono::high_resolution_clock::time_point start;
json rtsp_opts;
AirSimStreamContext *ctx = NULL;
// -----------------------------------------------------------------------------------

static void need_data(GstElement *appsrc, guint unused, AirSimStreamContext *ctx) {
	const std::vector<ImageResponse>& response = ctx->client->simGetImages(ctx->requests);
	if (response.size() > 0) {
		GstBuffer *buffer;
		GstFlowReturn ret;
		gsize fill_ret;

		buffer = gst_buffer_new_allocate(NULL, ctx->frame_size, NULL);
		fill_ret = gst_buffer_fill(buffer, 0, response[0].image_data_uint8.data(), ctx->frame_size);

		if (fill_ret == 0) {
			g_print("Buffer[NULL: %d] fill assertion fail (Fill size: %lu, Frame size: %d)!", 
				(int)(buffer == nullptr), response[0].image_data_uint8.size(), ctx->frame_size);

			gst_buffer_unref(buffer);
			return;
		}

		GST_BUFFER_PTS(buffer) = ctx->timestamp;
		GST_BUFFER_DURATION(buffer) = gst_util_uint64_scale_int(1, GST_SECOND, rtsp_opts["fps"].get<int>());
		ctx->timestamp += GST_BUFFER_DURATION(buffer);

		g_signal_emit_by_name(appsrc, "push-buffer", buffer, &ret);
		gst_buffer_unref(buffer);
	} else {
		g_print("[need_data - %lld] No response!", 
			std::chrono::duration_cast<std::chrono::milliseconds>(
				std::chrono::high_resolution_clock::now() - start).count());
	}
}

static void enough_data(GstElement* appsrc, gpointer udata) {
	uint64_t current_level_buffers = 0;
	uint64_t current_level_bytes = 0;
	uint64_t current_level_time = 0;
	bool is_live = false;

	g_object_get(G_OBJECT(appsrc), 
		"current-level-buffers", current_level_buffers, 
		"current-level-bytes", current_level_bytes, 
		"current-level-time", current_level_time, 
		"is-live", is_live, 
		NULL);

	printf("'appsrc' has enough data (CLBuf: %lu, CLByt: %lu, CLT: %lu, Live: %d)!\n", 
		current_level_buffers, current_level_bytes, current_level_time, is_live);
}

static void media_configure(GstRTSPMediaFactory *factory, GstRTSPMedia *media, gpointer user_data) {
	GstElement *element, *appsrc;

	element = gst_rtsp_media_get_element(media);
	appsrc = gst_bin_get_by_name_recurse_up(GST_BIN(element), 
		rtsp_opts["appsrc_key"].get<std::string>().c_str());

	gst_util_set_object_arg(G_OBJECT(appsrc), "format", "time");

	g_object_set(G_OBJECT(appsrc), "caps", 
		gst_caps_new_simple("video/x-raw", 
			"format", G_TYPE_STRING, rtsp_opts["format"].get<std::string>().c_str(), 
			"width", G_TYPE_INT, rtsp_opts["width"].get<int>(), 
			"height", G_TYPE_INT, rtsp_opts["height"].get<int>(), 
			"framerate", GST_TYPE_FRACTION, rtsp_opts["fps"].get<int>(), 1, NULL), 
		NULL);

	ctx = g_new0(AirSimStreamContext, 1);
	ctx->timestamp = 0;
	ctx->channels = rtsp_opts["channels"].get<int>();
	ctx->width = rtsp_opts["width"].get<int>();
	ctx->height = rtsp_opts["height"].get<int>();

	ctx->frame_size = ctx->width * ctx->height * ctx->channels;
	// ctx->frame_size = [](int w, int h, int c, const std::string& fmt){
	// 	if (fmt == "BGR" || fmt == "RGB" || fmt == "Y444") {
	// 		return w * h * c;
	// 	} else if (fmt == "I420" || fmt == "YV12") {
	// 		return (int)(w * h * 1.5);
	// 	} else {
	// 		return w * h * c;
	// 	}
	// }(ctx->width, ctx->height, ctx->channels, std::move(rtsp_opts["format"].get<std::string>()));

	if (rtsp_opts["sim_mode"].get<std::string>() == "Multirotor") {
		ctx->client.reset(
			new msr::airlib::MultirotorRpcLibClient(rtsp_opts["client_addr"].get<std::string>(), 
													rtsp_opts["client_port"].get<uint16_t>(), 2.0));

		ctx->requests.push_back(ImageRequest(rtsp_opts["airsim_cam"].get<std::string>(), 
										 	 ImageType::Scene, false, false));
	} else {
		ctx->client.reset(
			new msr::airlib::RpcLibClientBase(rtsp_opts["client_addr"].get<std::string>(), 
											  rtsp_opts["client_port"].get<uint16_t>(), 2.0));

		ctx->requests.push_back(ImageRequest("0", ImageType::Scene, false, false));
	}

	if (ctx->client == nullptr) {
		printf("Client pointer is NULL!\n");
		exit(EXIT_FAILURE);
	}

	ctx->client->confirmConnection();
	printf("AirSimStreamContext is created.\n");

	g_object_set_data_full(G_OBJECT(media), "my-extra-data", ctx, (GDestroyNotify)g_free);
	g_signal_connect(appsrc, "need-data", (GCallback)need_data, ctx);

	if (rtsp_opts["appsrc_enough_data_debug"].get<bool>()) {
		g_signal_connect(appsrc, "enough-data", (GCallback)enough_data, NULL);
	}

	gst_object_unref(appsrc);
	gst_object_unref(element);
}

int main(int argc, char *argv[]) {
	rtsp_opts = json::parse(std::ifstream(std::string(getenv("HOME")) + "/Documents/AirSim/rtsp_opts.json"));

	GMainLoop *loop;
	GstRTSPServer *server;
	GstRTSPMountPoints *mounts;
	GstRTSPMediaFactory *factory;

	gst_init(&argc, &argv);

	try {
		loop = g_main_loop_new(NULL, FALSE);
		server = gst_rtsp_server_new();
		mounts = gst_rtsp_server_get_mount_points(server);
		factory = gst_rtsp_media_factory_new();

		gst_rtsp_server_set_address(server, rtsp_opts["output_addr"].get<std::string>().c_str());
		gst_rtsp_server_set_service(server, rtsp_opts["output_port"].get<std::string>().c_str());

		gst_rtsp_media_factory_set_launch(factory, rtsp_opts["pipeline"].get<std::string>().c_str());

		g_signal_connect(factory, "media-configure", (GCallback)media_configure, NULL);
		gst_rtsp_mount_points_add_factory(mounts, rtsp_opts["key"].get<std::string>().c_str(), factory);
		g_object_unref(mounts);

		gst_rtsp_server_attach(server, NULL);
		g_print("AirSim RTSP stream is at rtsp://%s:%s/%s\n", 
			gst_rtsp_server_get_address(server), 
			gst_rtsp_server_get_service(server), 
			rtsp_opts["key"].get<std::string>().c_str());

		start = std::chrono::high_resolution_clock::now();
		g_main_loop_run(loop);

	} catch(const std::exception& e) {
		printf("Error: %s", e.what());
	}

	g_main_loop_unref(loop);

	return 0;
}