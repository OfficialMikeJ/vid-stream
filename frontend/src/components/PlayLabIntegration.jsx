import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Key, Copy, RefreshCw, ExternalLink, CheckCircle, Loader2, Play, List } from "lucide-react";

const CodeBlock = ({ code }) => {
  const copy = () => {
    navigator.clipboard.writeText(code);
    toast.success("Copied to clipboard");
  };
  return (
    <div className="relative group">
      <pre className="bg-gray-950 border border-gray-800 rounded-lg p-4 text-sm text-green-400 font-mono overflow-x-auto">
        {code}
      </pre>
      <Button
        size="sm"
        variant="ghost"
        onClick={copy}
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-white h-7 px-2"
      >
        <Copy className="w-3 h-3" />
      </Button>
    </div>
  );
};

const PlayLabIntegration = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [togglingEnabled, setTogglingEnabled] = useState(false);
  const [videos, setVideos] = useState(null);
  const [loadingVideos, setLoadingVideos] = useState(false);

  useEffect(() => { fetchSettings(); }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/playlab/settings`);
      setSettings(r.data);
    } catch {
      toast.error("Failed to load PlayLab settings");
    } finally {
      setLoading(false);
    }
  };

  const regenerateKey = async () => {
    if (!window.confirm("This will invalidate the current API key. All existing PlayLab integrations must be updated. Continue?")) return;
    setRegenerating(true);
    try {
      const r = await axios.post(`${API}/playlab/regenerate-key`);
      setSettings(prev => ({ ...prev, api_key: r.data.api_key }));
      toast.success("API key regenerated. Update your PlayLab configuration.");
    } catch {
      toast.error("Failed to regenerate key");
    } finally {
      setRegenerating(false);
    }
  };

  const toggleEnabled = async (val) => {
    setTogglingEnabled(true);
    try {
      await axios.patch(`${API}/playlab/settings?enabled=${val}`);
      setSettings(prev => ({ ...prev, enabled: val }));
      toast.success(`PlayLab integration ${val ? "enabled" : "disabled"}`);
    } catch {
      toast.error("Failed to update setting");
    } finally {
      setTogglingEnabled(false);
    }
  };

  const loadVideos = async () => {
    if (!settings?.api_key) return;
    setLoadingVideos(true);
    try {
      const r = await axios.get(`${API}/playlab/videos`, {
        headers: { "X-PlayLab-Key": settings.api_key },
      });
      setVideos(r.data);
    } catch {
      toast.error("Failed to load videos from PlayLab API");
    } finally {
      setLoadingVideos(false);
    }
  };

  const copyKey = () => {
    if (settings?.api_key) {
      navigator.clipboard.writeText(settings.api_key);
      toast.success("API key copied to clipboard");
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex justify-center py-20">
        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    );
  }

  const videosEndpoint = settings?.videos_endpoint || `${API}/playlab/videos`;
  const videoDetailEndpoint = settings?.video_detail_endpoint || `${API}/playlab/video/{video_id}`;

  return (
    <div className="p-8 max-w-4xl mx-auto" data-testid="playlab-integration-page">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-orange-500/20 rounded-xl flex items-center justify-center">
            <Play className="w-5 h-5 text-orange-400" />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-white">PlayLab Integration</h2>
          </div>
        </div>
        <p className="text-gray-500 ml-13">
          Connect StreamHost as a video source for your PlayLab streaming service. PlayLab will use StreamHost's HLS streams for video playback.
        </p>
      </div>

      {/* Status + API Key */}
      <Card className="bg-gray-900 border-gray-800 mb-6">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <Key className="w-5 h-5 text-orange-400" />
            API Configuration
          </CardTitle>
          <div className="flex items-center gap-3">
            <Label className="text-gray-400 text-sm">Integration Active</Label>
            <Switch
              data-testid="playlab-enabled-switch"
              checked={settings?.enabled ?? true}
              onCheckedChange={toggleEnabled}
              disabled={togglingEnabled}
            />
            {settings?.enabled
              ? <Badge className="bg-green-600 text-white">Enabled</Badge>
              : <Badge className="bg-gray-600 text-white">Disabled</Badge>
            }
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-gray-400 text-sm">API Key</Label>
            <div className="flex gap-2 mt-2">
              <div className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 font-mono text-sm text-green-400 overflow-hidden">
                <span data-testid="playlab-api-key">{settings?.api_key}</span>
              </div>
              <Button
                size="icon"
                variant="outline"
                onClick={copyKey}
                data-testid="copy-api-key-btn"
                className="border-gray-700 text-gray-300 hover:bg-gray-800 h-12 w-12"
                title="Copy API Key"
              >
                <Copy className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                onClick={regenerateKey}
                disabled={regenerating}
                data-testid="regenerate-key-btn"
                className="border-orange-700 text-orange-400 hover:bg-orange-900/20"
              >
                {regenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
                Regenerate
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Include this key as the <code className="text-gray-300">X-PlayLab-Key</code> header in your PlayLab API requests.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Integration Instructions */}
      <Card className="bg-gray-900 border-gray-800 mb-6">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <ExternalLink className="w-5 h-5 text-blue-400" />
            PlayLab Setup Instructions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <p className="text-gray-300 font-medium mb-2">Step 1 — List videos from StreamHost</p>
            <p className="text-gray-500 text-sm mb-2">In PlayLab, call this endpoint to discover all available videos:</p>
            <CodeBlock code={`GET ${videosEndpoint}\nHeaders: X-PlayLab-Key: ${settings?.api_key || "<your-api-key>"}`} />
          </div>

          <div>
            <p className="text-gray-300 font-medium mb-2">Step 2 — Get a single video's stream URL</p>
            <CodeBlock code={`GET ${videoDetailEndpoint}\nHeaders: X-PlayLab-Key: ${settings?.api_key || "<your-api-key>"}`} />
          </div>

          <div>
            <p className="text-gray-300 font-medium mb-2">Step 3 — Add to PlayLab video entry</p>
            <p className="text-gray-500 text-sm mb-2">
              When adding a video in PlayLab Admin, select <strong className="text-gray-300">"Link"</strong> as the video type and paste the <code className="text-gray-300">hls_url</code> from the response. Set <code className="text-gray-300">server = 2</code> (external link).
            </p>
            <CodeBlock code={`// Example JSON from GET /api/playlab/video/{id}
{
  "playlab": {
    "server_type": 2,
    "seven_twenty_video": "https://your-streamhost/api/stream/hls/{id}/playlist.m3u8",
    "server_seven_twenty": 2,
    // ... same URL for all resolution slots
  }
}`} />
          </div>

          <div>
            <p className="text-gray-300 font-medium mb-2">Step 4 — Use as query parameter (alternative)</p>
            <CodeBlock code={`GET ${videosEndpoint}?api_key=${settings?.api_key || "<your-api-key>"}`} />
          </div>
        </CardContent>
      </Card>

      {/* Test API */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <List className="w-5 h-5 text-green-400" />
            Live API Test
          </CardTitle>
          <Button
            onClick={loadVideos}
            disabled={loadingVideos}
            data-testid="test-playlab-api-btn"
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            {loadingVideos
              ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Loading...</>
              : "Test API — Fetch Videos"
            }
          </Button>
        </CardHeader>
        {videos && (
          <CardContent>
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <p className="text-green-400 text-sm font-medium">
                API working — {videos.count} video{videos.count !== 1 ? "s" : ""} available
              </p>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {videos.videos.map((v) => (
                <div
                  key={v.id}
                  className="flex items-center justify-between bg-gray-800 rounded-lg px-4 py-3"
                  data-testid={`playlab-video-${v.id}`}
                >
                  <div>
                    <p className="text-white text-sm font-medium">{v.title}</p>
                    <p className="text-gray-500 text-xs font-mono">{v.hls_url}</p>
                  </div>
                  <Badge className="bg-blue-600 text-white text-xs ml-3">
                    {v.aspect_ratio || "Video"}
                  </Badge>
                </div>
              ))}
              {videos.count === 0 && (
                <p className="text-gray-500 text-sm text-center py-4">
                  No ready videos yet. Upload and process a video to see it here.
                </p>
              )}
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
};

export default PlayLabIntegration;
