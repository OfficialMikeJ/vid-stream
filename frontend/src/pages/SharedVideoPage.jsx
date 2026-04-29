import { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import Hls from "hls.js";
import { API } from "../App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Film, Lock, AlertTriangle, Loader2, Play } from "lucide-react";

const SharedVideoPage = () => {
  const { token } = useParams();
  const videoRef = useRef(null);
  const hlsRef = useRef(null);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [requiresPassword, setRequiresPassword] = useState(false);
  const [password, setPassword] = useState("");
  const [unlocking, setUnlocking] = useState(false);
  const [label, setLabel] = useState(null);

  const fetchShare = useCallback(
    async (pw = null) => {
      // Use a bare axios instance — public endpoint, no auth header
      try {
        const url = `${API}/share/${token}` + (pw ? `?password=${encodeURIComponent(pw)}` : "");
        const r = await axios.get(url, {
          transformRequest: [(d, headers) => {
            delete headers.Authorization;
            return d;
          }],
        });
        if (r.data.requires_password) {
          setRequiresPassword(true);
          setLabel(r.data.label || null);
          setLoading(false);
          return false;
        }
        setData(r.data);
        setRequiresPassword(false);
        setLoading(false);
        return true;
      } catch (err) {
        const status = err?.response?.status;
        if (status === 410) setError("This share link has expired.");
        else if (status === 404) setError("Share link not found.");
        else if (status === 401) setError("Incorrect password.");
        else setError(err?.response?.data?.detail || "Unable to load share.");
        setLoading(false);
        return false;
      }
    },
    [token]
  );

  useEffect(() => {
    fetchShare();
  }, [fetchShare]);

  const submitPassword = async (e) => {
    e.preventDefault();
    if (!password.trim()) return;
    setUnlocking(true);
    setError("");
    const ok = await fetchShare(password);
    setUnlocking(false);
    if (!ok && error === "") {
      // already handled
    }
  };

  // Attach HLS once data is loaded
  useEffect(() => {
    if (!data || !videoRef.current) return;
    const videoElement = videoRef.current;
    // Build absolute URL since data.hls_url is relative
    const backend = API.replace(/\/api$/, "");
    const videoSrc = backend + data.hls_url;

    if (Hls.isSupported()) {
      const hls = new Hls({ enableWorker: true });
      hls.loadSource(videoSrc);
      hls.attachMedia(videoElement);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        videoElement.play().catch(() => {});
      });
      hlsRef.current = hls;
      return () => hls.destroy();
    } else if (videoElement.canPlayType("application/vnd.apple.mpegurl")) {
      videoElement.src = videoSrc;
    }
  }, [data]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
        <Card className="max-w-md w-full bg-gray-900 border-gray-800" data-testid="share-error">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">Link unavailable</h2>
            <p className="text-gray-400">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (requiresPassword) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
        <Card className="max-w-md w-full bg-gray-900 border-gray-800" data-testid="share-password-prompt">
          <CardContent className="p-8">
            <div className="text-center mb-6">
              <Lock className="w-12 h-12 text-amber-400 mx-auto mb-3" />
              <h2 className="text-xl font-semibold text-white">Password required</h2>
              {label && <p className="text-sm text-gray-400 mt-1">"{label}"</p>}
            </div>
            <form onSubmit={submitPassword} className="space-y-4">
              <div>
                <Label htmlFor="share-pw" className="text-gray-300">Password</Label>
                <Input
                  id="share-pw"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-gray-800 border-gray-700 text-white"
                  data-testid="share-password-input"
                  autoFocus
                />
              </div>
              <Button
                type="submit"
                disabled={unlocking || !password.trim()}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                data-testid="share-password-submit"
              >
                {unlocking ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
                Unlock
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950" data-testid="shared-video-page">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center gap-3">
        <Film className="w-6 h-6 text-blue-400" />
        <span className="text-white font-semibold">StreamHost</span>
        {data?.label && <span className="text-gray-500 text-sm ml-2">· {data.label}</span>}
      </header>
      <main className="max-w-5xl mx-auto p-6">
        <div className="aspect-video bg-black rounded-lg overflow-hidden mb-4">
          <video
            ref={videoRef}
            controls
            crossOrigin="anonymous"
            className="w-full h-full"
            data-testid="shared-video-player"
          >
            {(data?.captions || []).map((c) => (
              <track
                key={c.id}
                kind="subtitles"
                src={`${API}/captions/${c.id}`}
                srcLang={c.language}
                label={c.label || c.language?.toUpperCase()}
                default={c.is_default}
              />
            ))}
          </video>
        </div>
        <h1 className="text-2xl font-bold text-white mb-2" data-testid="shared-video-title">
          {data?.video?.title}
        </h1>
        {data?.video?.description && (
          <p className="text-gray-400 whitespace-pre-wrap">{data.video.description}</p>
        )}
      </main>
    </div>
  );
};

export default SharedVideoPage;
