import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { Settings, Info, Palette, Save, RefreshCw } from "lucide-react";

const VideoSettings = () => {
  const [playerSettings, setPlayerSettings] = useState({
    primaryColor: "#3b82f6",
    backgroundColor: "#000000",
    showControls: true,
    autoplay: false,
    loop: false,
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      // Store settings in localStorage for now (could be extended to backend)
      localStorage.setItem("streamhost_player_settings", JSON.stringify(playerSettings));
      toast.success("Player settings saved successfully");
    } catch (error) {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setPlayerSettings({
      primaryColor: "#3b82f6",
      backgroundColor: "#000000",
      showControls: true,
      autoplay: false,
      loop: false,
    });
    localStorage.removeItem("streamhost_player_settings");
    toast.success("Settings reset to defaults");
  };

  useEffect(() => {
    const saved = localStorage.getItem("streamhost_player_settings");
    if (saved) {
      setPlayerSettings(JSON.parse(saved));
    }
  }, []);

  return (
    <div className="p-8" data-testid="video-settings">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Settings</h2>
        <p className="text-gray-500">Configure your video hosting service</p>
      </div>

      <div className="grid gap-6 max-w-4xl">
        {/* Player Customization */}
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center">
                <Palette className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <CardTitle className="text-white">Player Customization</CardTitle>
                <CardDescription className="text-gray-500">
                  Customize the default video player appearance
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label className="text-gray-300">Primary Color</Label>
                <div className="flex gap-2">
                  <Input
                    type="color"
                    value={playerSettings.primaryColor}
                    onChange={(e) => setPlayerSettings({...playerSettings, primaryColor: e.target.value})}
                    className="w-12 h-10 p-1 bg-gray-800 border-gray-700 rounded cursor-pointer"
                  />
                  <Input
                    type="text"
                    value={playerSettings.primaryColor}
                    onChange={(e) => setPlayerSettings({...playerSettings, primaryColor: e.target.value})}
                    className="flex-1 bg-gray-800 border-gray-700 text-white font-mono"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-gray-300">Background Color</Label>
                <div className="flex gap-2">
                  <Input
                    type="color"
                    value={playerSettings.backgroundColor}
                    onChange={(e) => setPlayerSettings({...playerSettings, backgroundColor: e.target.value})}
                    className="w-12 h-10 p-1 bg-gray-800 border-gray-700 rounded cursor-pointer"
                  />
                  <Input
                    type="text"
                    value={playerSettings.backgroundColor}
                    onChange={(e) => setPlayerSettings({...playerSettings, backgroundColor: e.target.value})}
                    className="flex-1 bg-gray-800 border-gray-700 text-white font-mono"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-gray-300">Show Controls</Label>
                  <p className="text-sm text-gray-500">Display player controls by default</p>
                </div>
                <Switch
                  checked={playerSettings.showControls}
                  onCheckedChange={(checked) => setPlayerSettings({...playerSettings, showControls: checked})}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-gray-300">Autoplay</Label>
                  <p className="text-sm text-gray-500">Automatically play videos when loaded</p>
                </div>
                <Switch
                  checked={playerSettings.autoplay}
                  onCheckedChange={(checked) => setPlayerSettings({...playerSettings, autoplay: checked})}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-gray-300">Loop</Label>
                  <p className="text-sm text-gray-500">Repeat videos when they end</p>
                </div>
                <Switch
                  checked={playerSettings.loop}
                  onCheckedChange={(checked) => setPlayerSettings({...playerSettings, loop: checked})}
                />
              </div>
            </div>

            {/* Preview */}
            <div className="space-y-2">
              <Label className="text-gray-300">Preview</Label>
              <div 
                className="aspect-video rounded-lg flex items-center justify-center relative overflow-hidden"
                style={{ backgroundColor: playerSettings.backgroundColor }}
              >
                <div 
                  className="absolute bottom-0 left-0 right-0 h-12 flex items-center px-4"
                  style={{ backgroundColor: `${playerSettings.primaryColor}20` }}
                >
                  <div 
                    className="w-3 h-3 rounded-full mr-3"
                    style={{ backgroundColor: playerSettings.primaryColor }}
                  />
                  <div 
                    className="flex-1 h-1 rounded-full bg-gray-700"
                  >
                    <div 
                      className="w-1/3 h-full rounded-full"
                      style={{ backgroundColor: playerSettings.primaryColor }}
                    />
                  </div>
                </div>
                <span className="text-gray-400 text-sm">Player Preview</span>
              </div>
            </div>

            <div className="flex gap-3">
              <Button onClick={handleReset} variant="outline" className="bg-gray-700 hover:bg-gray-600 border-gray-600 text-white">
                <RefreshCw className="w-4 h-4 mr-2" />
                Reset to Defaults
              </Button>
              <Button onClick={handleSave} disabled={saving} className="bg-green-600 hover:bg-green-700 text-white">
                <Save className="w-4 h-4 mr-2" />
                {saving ? "Saving..." : "Save Settings"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Processing Info */}
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-600/20 rounded-lg flex items-center justify-center">
                <Settings className="w-5 h-5 text-orange-400" />
              </div>
              <div>
                <CardTitle className="text-white">Processing Settings</CardTitle>
                <CardDescription className="text-gray-500">
                  Video processing is handled automatically by FFmpeg
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-gray-800 rounded-lg p-4 space-y-2">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="text-white font-medium mb-1">Automatic Processing</h4>
                  <p className="text-sm text-gray-500">
                    When you upload a video, it automatically:
                  </p>
                  <ul className="text-sm text-gray-500 mt-2 space-y-1 list-disc list-inside">
                    <li>Extracts video metadata (duration, resolution, aspect ratio)</li>
                    <li>Generates a thumbnail from the video</li>
                    <li>Creates HLS streaming segments for adaptive playback</li>
                    <li>Supports all FFmpeg-compatible formats</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 space-y-2">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="text-white font-medium mb-1">Streaming Technology</h4>
                  <p className="text-sm text-gray-500">
                    Videos are transcoded to HLS format for optimal streaming across all devices.
                    The player automatically adapts to the viewer's device and connection speed.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Supported Formats */}
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white">Supported Formats</CardTitle>
            <CardDescription className="text-gray-500">
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
                  className="bg-gray-800 rounded-lg px-4 py-2 text-center text-sm text-gray-300 font-medium"
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
