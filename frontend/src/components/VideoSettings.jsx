import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Settings, Info } from "lucide-react";

const VideoSettings = () => {
  return (
    <div className="p-8" data-testid="video-settings">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Video Settings</h2>
        <p className="text-slate-400">Configure your video hosting service</p>
      </div>

      <div className="grid gap-6 max-w-4xl">
        <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-500/20 rounded-lg flex items-center justify-center">
                <Settings className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <CardTitle className="text-white">Processing Settings</CardTitle>
                <CardDescription className="text-slate-400">
                  Video processing is handled automatically by FFmpeg
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-white/5 rounded-lg p-4 space-y-2">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-indigo-400 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="text-white font-medium mb-1">Automatic Processing</h4>
                  <p className="text-sm text-slate-400">
                    When you upload a video, it automatically:
                  </p>
                  <ul className="text-sm text-slate-400 mt-2 space-y-1 list-disc list-inside">
                    <li>Extracts video metadata (duration, resolution, aspect ratio)</li>
                    <li>Generates a thumbnail from the video</li>
                    <li>Creates HLS streaming segments for adaptive playback</li>
                    <li>Supports all FFmpeg-compatible formats</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="bg-white/5 rounded-lg p-4 space-y-2">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="text-white font-medium mb-1">Streaming Technology</h4>
                  <p className="text-sm text-slate-400">
                    Videos are transcoded to HLS format for optimal streaming across all devices.
                    The player automatically adapts to the viewer's device and connection speed.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white/5 rounded-lg p-4 space-y-2">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="text-white font-medium mb-1">Embed Options</h4>
                  <p className="text-sm text-slate-400">
                    For each video, you can configure:
                  </p>
                  <ul className="text-sm text-slate-400 mt-2 space-y-1 list-disc list-inside">
                    <li>Domain restrictions (whitelist specific domains)</li>
                    <li>Custom player colors</li>
                    <li>Autoplay and loop settings</li>
                    <li>Control visibility</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-white">Supported Formats</CardTitle>
            <CardDescription className="text-slate-400">
              All FFmpeg-compatible video formats
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {[
                "MP4", "MOV", "AVI", "MKV", "WebM", "FLV",
                "WMV", "MPEG", "3GP", "OGV", "M4V", "TS"
              ].map((format) => (
                <div
                  key={format}
                  className="bg-white/5 rounded-lg px-4 py-2 text-center text-sm text-slate-300 font-medium"
                >
                  {format}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default VideoSettings;
