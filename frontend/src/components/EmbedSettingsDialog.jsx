import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { Code, Plus, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";

const EmbedSettingsDialog = ({ video, open, onOpenChange, onGetEmbedCode }) => {
  const [loading, setLoading] = useState(false);
  const [allowedDomains, setAllowedDomains] = useState([]);
  const [newDomain, setNewDomain] = useState("");
  const [playerColor, setPlayerColor] = useState("#3b82f6");
  const [showControls, setShowControls] = useState(true);
  const [autoplay, setAutoplay] = useState(false);
  const [loop, setLoop] = useState(false);
  const [hasSettings, setHasSettings] = useState(false);

  useEffect(() => {
    if (open && video) {
      fetchSettings();
    }
  }, [open, video]);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/embed-settings/${video.id}`);
      const settings = response.data;
      setAllowedDomains(settings.allowed_domains || []);
      setPlayerColor(settings.player_color || "#3b82f6");
      setShowControls(settings.show_controls !== false);
      setAutoplay(settings.autoplay || false);
      setLoop(settings.loop || false);
      setHasSettings(true);
    } catch (error) {
      if (error.response?.status === 404) {
        setHasSettings(false);
        setAllowedDomains([]);
        setPlayerColor("#3b82f6");
        setShowControls(true);
        setAutoplay(false);
        setLoop(false);
      }
    }
  };

  const handleAddDomain = () => {
    if (newDomain.trim() && !allowedDomains.includes(newDomain.trim())) {
      setAllowedDomains([...allowedDomains, newDomain.trim()]);
      setNewDomain("");
    }
  };

  const handleRemoveDomain = (domain) => {
    setAllowedDomains(allowedDomains.filter((d) => d !== domain));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const data = {
        video_id: video.id,
        allowed_domains: allowedDomains,
        player_color: playerColor,
        show_controls: showControls,
        autoplay: autoplay,
        loop: loop,
      };

      if (hasSettings) {
        await axios.patch(
          `${API}/embed-settings/${video.id}`,
          null,
          {
            params: {
              allowed_domains: allowedDomains.join(","),
              player_color: playerColor,
              show_controls: showControls,
              autoplay: autoplay,
              loop: loop,
            },
          }
        );
      } else {
        await axios.post(`${API}/embed-settings`, data);
        setHasSettings(true);
      }

      toast.success("Embed settings saved");
      onGetEmbedCode();
    } catch (error) {
      toast.error("Failed to save embed settings");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-slate-950/95 border-white/10 text-white">
        <DialogHeader>
          <DialogTitle className="text-white">Embed Settings</DialogTitle>
          <DialogDescription className="text-slate-400">
            Configure embed options for {video?.title}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Domain Restrictions */}
          <div className="space-y-3">
            <Label className="text-slate-200">Allowed Domains</Label>
            <p className="text-sm text-slate-400">Leave empty to allow all domains</p>
            <div className="flex gap-2">
              <Input
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                placeholder="example.com"
                className="bg-white/5 border-white/10 text-white"
                onKeyPress={(e) => e.key === "Enter" && handleAddDomain()}
              />
              <Button
                onClick={handleAddDomain}
                size="sm"
                className="bg-indigo-500 hover:bg-indigo-600"
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            {allowedDomains.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {allowedDomains.map((domain) => (
                  <Badge
                    key={domain}
                    variant="secondary"
                    className="bg-indigo-500/20 text-indigo-300 border-indigo-500/30 gap-2"
                  >
                    {domain}
                    <button
                      onClick={() => handleRemoveDomain(domain)}
                      className="hover:text-indigo-100"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Player Color */}
          <div className="space-y-3">
            <Label htmlFor="player-color" className="text-slate-200">
              Player Color
            </Label>
            <div className="flex gap-3 items-center">
              <Input
                id="player-color"
                type="color"
                value={playerColor}
                onChange={(e) => setPlayerColor(e.target.value)}
                className="w-20 h-12 bg-white/5 border-white/10"
              />
              <Input
                value={playerColor}
                onChange={(e) => setPlayerColor(e.target.value)}
                className="flex-1 bg-white/5 border-white/10 text-white"
              />
            </div>
          </div>

          {/* Player Options */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-slate-200">Show Controls</Label>
                <p className="text-sm text-slate-400">Display video player controls</p>
              </div>
              <Switch checked={showControls} onCheckedChange={setShowControls} />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-slate-200">Autoplay</Label>
                <p className="text-sm text-slate-400">Start playing automatically</p>
              </div>
              <Switch checked={autoplay} onCheckedChange={setAutoplay} />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-slate-200">Loop</Label>
                <p className="text-sm text-slate-400">Replay video continuously</p>
              </div>
              <Switch checked={loop} onCheckedChange={setLoop} />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-4">
            <Button
              onClick={() => onOpenChange(false)}
              variant="outline"
              className="flex-1 border-white/10"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              className="flex-1 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 gap-2"
              disabled={loading}
            >
              <Code className="w-4 h-4" />
              {loading ? "Saving..." : "Save & Get Embed Code"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default EmbedSettingsDialog;
