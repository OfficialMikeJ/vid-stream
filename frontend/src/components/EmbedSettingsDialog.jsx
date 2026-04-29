import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Copy, X, Plus, Save, Loader2, Code, Monitor } from "lucide-react";

const EmbedSettingsDialog = ({ video, onClose }) => {
  const [settings, setSettings] = useState({
    allowed_domains: [],
    player_color: "#3b82f6",
    show_controls: true,
    autoplay: false,
    loop: false,
    custom_css: "",
  });
  const [newDomain, setNewDomain] = useState("");
  const [saving, setSaving] = useState(false);
  const [embedCode, setEmbedCode] = useState("");
  const [loadingCode, setLoadingCode] = useState(false);
  const [hasExisting, setHasExisting] = useState(false);

  useEffect(() => {
    if (!video) return;
    // Try to load existing embed settings
    axios.get(`${API}/embed-settings/${video.id}`)
      .then(r => {
        setSettings({
          allowed_domains: r.data.allowed_domains || [],
          player_color: r.data.player_color || "#3b82f6",
          show_controls: r.data.show_controls ?? true,
          autoplay: r.data.autoplay ?? false,
          loop: r.data.loop ?? false,
          custom_css: r.data.custom_css || "",
        });
        setHasExisting(true);
      })
      .catch(() => setHasExisting(false));

    // Also pre-load embed code
    loadEmbedCode();
  }, [video]);

  const loadEmbedCode = async () => {
    if (!video) return;
    setLoadingCode(true);
    try {
      const r = await axios.get(`${API}/embed-code/${video.id}`);
      setEmbedCode(r.data.embed_code);
    } catch {
      setEmbedCode("");
    } finally {
      setLoadingCode(false);
    }
  };

  const save = async () => {
    setSaving(true);
    try {
      if (hasExisting) {
        await axios.patch(
          `${API}/embed-settings/${video.id}`,
          null,
          {
            params: {
              player_color: settings.player_color,
              show_controls: settings.show_controls,
              autoplay: settings.autoplay,
              loop: settings.loop,
              custom_css: settings.custom_css || null,
            },
          }
        );
        // Update allowed_domains separately (array param)
        const params = new URLSearchParams();
        settings.allowed_domains.forEach(d => params.append("allowed_domains", d));
        params.append("player_color", settings.player_color);
        params.append("show_controls", settings.show_controls);
        params.append("autoplay", settings.autoplay);
        params.append("loop", settings.loop);
        if (settings.custom_css) params.append("custom_css", settings.custom_css);
        await axios.patch(`${API}/embed-settings/${video.id}?${params.toString()}`);
      } else {
        await axios.post(`${API}/embed-settings`, {
          video_id: video.id,
          ...settings,
        });
        setHasExisting(true);
      }
      toast.success("Embed settings saved");
      await loadEmbedCode();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to save embed settings");
    } finally {
      setSaving(false);
    }
  };

  const copyCode = () => {
    navigator.clipboard.writeText(embedCode);
    toast.success("Embed code copied!");
  };

  const addDomain = () => {
    const d = newDomain.trim().toLowerCase().replace(/^https?:\/\//, "");
    if (!d) return;
    if (settings.allowed_domains.includes(d)) {
      toast.error("Domain already added");
      return;
    }
    setSettings(s => ({ ...s, allowed_domains: [...s.allowed_domains, d] }));
    setNewDomain("");
  };

  const removeDomain = (d) => {
    setSettings(s => ({ ...s, allowed_domains: s.allowed_domains.filter(x => x !== d) }));
  };

  return (
    <Dialog open={!!video} onOpenChange={() => onClose()}>
      <DialogContent className="max-w-2xl bg-gray-900 border-gray-800 text-white max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Code className="w-5 h-5 text-orange-400" />
            Embed — {video?.title}
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="code" className="mt-2">
          <TabsList className="bg-gray-800 border border-gray-700">
            <TabsTrigger value="code" data-testid="embed-tab-code"
              className="data-[state=active]:bg-orange-600 data-[state=active]:text-white text-gray-400">
              <Code className="w-3 h-3 mr-1" /> Embed Code
            </TabsTrigger>
            <TabsTrigger value="settings" data-testid="embed-tab-settings"
              className="data-[state=active]:bg-orange-600 data-[state=active]:text-white text-gray-400">
              <Monitor className="w-3 h-3 mr-1" /> Player Settings
            </TabsTrigger>
          </TabsList>

          {/* ── Embed Code Tab ── */}
          <TabsContent value="code" className="mt-4 space-y-4">
            {loadingCode ? (
              <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 text-orange-400 animate-spin" /></div>
            ) : embedCode ? (
              <>
                <div className="relative group">
                  <pre className="bg-gray-950 border border-gray-800 rounded-lg p-4 text-xs text-green-400 font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed">
                    {embedCode}
                  </pre>
                  <Button size="sm" onClick={copyCode} data-testid="copy-embed-code-btn"
                    className="absolute top-3 right-3 bg-orange-600 hover:bg-orange-700 text-white h-7 px-3 text-xs">
                    <Copy className="w-3 h-3 mr-1" /> Copy
                  </Button>
                </div>
                <p className="text-gray-500 text-xs">
                  Paste this snippet anywhere on your website. Requires HLS.js for non-Safari browsers (included).
                </p>
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p className="mb-3">No embed code available yet.</p>
                {video?.processing_status !== "ready" && video?.processing_status !== "external" && (
                  <Badge className="bg-yellow-600/20 text-yellow-400 border-yellow-600/30">
                    Video is still {video?.processing_status}
                  </Badge>
                )}
              </div>
            )}
          </TabsContent>

          {/* ── Settings Tab ── */}
          <TabsContent value="settings" className="mt-4 space-y-5">
            {/* Colors */}
            <div>
              <Label className="text-gray-300 block mb-2">Player Accent Color</Label>
              <div className="flex gap-2 items-center">
                <input type="color" value={settings.player_color}
                  onChange={e => setSettings(s => ({ ...s, player_color: e.target.value }))}
                  className="w-10 h-9 rounded border border-gray-700 bg-gray-800 cursor-pointer"
                  data-testid="player-color-picker"
                />
                <Input value={settings.player_color}
                  onChange={e => setSettings(s => ({ ...s, player_color: e.target.value }))}
                  className="flex-1 bg-gray-800 border-gray-700 text-white font-mono text-sm"
                />
              </div>
            </div>

            {/* Toggles */}
            <div className="space-y-3">
              {[
                { key: "show_controls", label: "Show player controls" },
                { key: "autoplay", label: "Autoplay" },
                { key: "loop", label: "Loop" },
              ].map(({ key, label }) => (
                <div key={key} className="flex items-center justify-between">
                  <Label className="text-gray-300">{label}</Label>
                  <Switch
                    checked={settings[key]}
                    onCheckedChange={v => setSettings(s => ({ ...s, [key]: v }))}
                    data-testid={`embed-toggle-${key}`}
                  />
                </div>
              ))}
            </div>

            {/* Domain restriction */}
            <div>
              <Label className="text-gray-300 block mb-2">Allowed Domains <span className="text-gray-500 font-normal">(leave empty to allow all)</span></Label>
              <div className="flex gap-2 mb-2">
                <Input
                  data-testid="domain-input"
                  value={newDomain}
                  onChange={e => setNewDomain(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && addDomain()}
                  placeholder="example.com"
                  className="flex-1 bg-gray-800 border-gray-700 text-white text-sm"
                />
                <Button size="sm" onClick={addDomain} className="bg-gray-700 hover:bg-gray-600 text-white shrink-0">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {settings.allowed_domains.map(d => (
                  <Badge key={d} className="bg-gray-800 border border-gray-700 text-gray-300 gap-1 pr-1">
                    {d}
                    <button onClick={() => removeDomain(d)} className="ml-1 hover:text-white">
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            </div>

            <Button onClick={save} disabled={saving} data-testid="save-embed-settings-btn"
              className="w-full bg-orange-600 hover:bg-orange-700 text-white">
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
              Save &amp; Refresh Embed Code
            </Button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

export default EmbedSettingsDialog;
