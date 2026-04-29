import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { API } from "../App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Captions as CaptionsIcon, Trash2, Upload, Loader2, Star } from "lucide-react";

const VideoCaptions = ({ videoId, isAdmin }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [language, setLanguage] = useState("en");
  const [label, setLabel] = useState("");
  const [isDefault, setIsDefault] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/videos/${videoId}/captions`);
      setItems(r.data.items || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [videoId]);

  useEffect(() => {
    load();
  }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    if (!file) {
      toast.error("Choose a .vtt or .srt file first");
      return;
    }
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    fd.append("language", language.trim().toLowerCase());
    if (label.trim()) fd.append("label", label.trim());
    fd.append("is_default", isDefault ? "true" : "false");
    try {
      await axios.post(`${API}/videos/${videoId}/captions`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Caption track added");
      setFile(null);
      setLabel("");
      setIsDefault(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Delete this caption track?")) return;
    try {
      await axios.delete(`${API}/videos/${videoId}/captions/${id}`);
      toast.success("Caption removed");
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to delete");
    }
  };

  return (
    <div className="border-t border-gray-800 pt-4 mt-2" data-testid="captions-section">
      <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
        <CaptionsIcon className="w-4 h-4" />
        Captions
        <Badge className="bg-gray-800 text-gray-400 ml-1">{items.length}</Badge>
      </h3>

      {loading ? (
        <div className="text-sm text-gray-500 py-2">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-sm text-gray-500 py-2" data-testid="captions-empty">
          No caption tracks yet.
        </div>
      ) : (
        <div className="space-y-2 mb-4" data-testid="captions-list">
          {items.map((c) => (
            <div
              key={c.id}
              className="flex items-center justify-between bg-gray-800/50 rounded-lg p-2 border border-gray-800"
              data-testid={`caption-item-${c.id}`}
            >
              <div className="flex items-center gap-3">
                <Badge className="bg-blue-600/30 text-blue-300 uppercase">{c.language}</Badge>
                <span className="text-sm text-white">{c.label}</span>
                {c.is_default && (
                  <span className="flex items-center gap-1 text-xs text-amber-300">
                    <Star className="w-3 h-3 fill-amber-300" /> default
                  </span>
                )}
              </div>
              {isAdmin && (
                <button
                  onClick={() => remove(c.id)}
                  data-testid={`caption-delete-${c.id}`}
                  className="text-gray-500 hover:text-red-400"
                  aria-label="Delete caption"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {isAdmin && (
        <form onSubmit={submit} className="space-y-2 bg-gray-800/30 rounded-lg p-3 border border-gray-800" data-testid="caption-upload-form">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label htmlFor="caption-lang" className="text-xs text-gray-400">Language</Label>
              <Input
                id="caption-lang"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                placeholder="en"
                maxLength={10}
                className="bg-gray-800 border-gray-700 text-white text-sm h-9"
                data-testid="caption-language"
              />
            </div>
            <div>
              <Label htmlFor="caption-label" className="text-xs text-gray-400">Label (optional)</Label>
              <Input
                id="caption-label"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder="English"
                className="bg-gray-800 border-gray-700 text-white text-sm h-9"
                data-testid="caption-label-input"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="caption-file" className="text-xs text-gray-400">File (.vtt or .srt)</Label>
            <input
              id="caption-file"
              ref={fileInputRef}
              type="file"
              accept=".vtt,.srt,text/vtt,application/x-subrip"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-gray-300 file:mr-2 file:py-1.5 file:px-3 file:rounded file:border-0 file:bg-gray-700 file:text-white"
              data-testid="caption-file"
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-gray-300">
              <Switch checked={isDefault} onCheckedChange={setIsDefault} data-testid="caption-default-switch" />
              Make default track
            </label>
            <Button
              type="submit"
              size="sm"
              data-testid="caption-upload-submit"
              disabled={uploading || !file}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {uploading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Upload className="w-4 h-4 mr-1" />}
              Upload
            </Button>
          </div>
        </form>
      )}
    </div>
  );
};

export default VideoCaptions;
