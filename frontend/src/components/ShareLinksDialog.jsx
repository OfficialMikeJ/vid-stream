import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Share2, Copy, Trash2, Plus, Loader2, Lock, Eye } from "lucide-react";

const buildPublicUrl = (token) => {
  if (typeof window === "undefined") return `/watch/${token}`;
  return `${window.location.origin}/watch/${token}`;
};

const ShareLinksDialog = ({ video, open, onOpenChange }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [label, setLabel] = useState("");
  const [password, setPassword] = useState("");
  const [usePassword, setUsePassword] = useState(false);
  const [expiresAt, setExpiresAt] = useState("");
  const [useExpiry, setUseExpiry] = useState(false);

  const load = useCallback(async () => {
    if (!video?.id) return;
    setLoading(true);
    try {
      const r = await axios.get(`${API}/videos/${video.id}/share`);
      setItems(r.data.items || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [video?.id]);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  const reset = () => {
    setLabel("");
    setPassword("");
    setUsePassword(false);
    setExpiresAt("");
    setUseExpiry(false);
    setShowAddForm(false);
  };

  const create = async (e) => {
    e.preventDefault();
    setCreating(true);
    const payload = {};
    if (label.trim()) payload.label = label.trim();
    if (usePassword && password) payload.password = password;
    if (useExpiry && expiresAt) {
      // Convert datetime-local input to ISO string
      payload.expires_at = new Date(expiresAt).toISOString();
    }
    try {
      await axios.post(`${API}/videos/${video.id}/share`, payload);
      toast.success("Share link created");
      reset();
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to create link");
    } finally {
      setCreating(false);
    }
  };

  const copy = async (token) => {
    const url = buildPublicUrl(token);
    try {
      await navigator.clipboard.writeText(url);
      toast.success("Link copied");
    } catch {
      // Fallback
      window.prompt("Copy this link:", url);
    }
  };

  const revoke = async (token) => {
    if (!window.confirm("Revoke this share link? Anyone with the URL will lose access.")) return;
    try {
      await axios.delete(`${API}/share/${token}`);
      toast.success("Link revoked");
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to revoke");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-gray-900 border-gray-800 text-white" data-testid="share-dialog">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Share2 className="w-5 h-5 text-blue-400" />
            Share "{video?.title}"
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            Create public links anyone can use to watch this video — no login required.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {!showAddForm && (
            <Button
              onClick={() => setShowAddForm(true)}
              data-testid="share-create-toggle"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create new link
            </Button>
          )}

          {showAddForm && (
            <form onSubmit={create} className="space-y-3 p-4 bg-gray-800/40 border border-gray-800 rounded-lg" data-testid="share-create-form">
              <div>
                <Label htmlFor="share-label" className="text-gray-300 text-sm">Label (optional)</Label>
                <Input
                  id="share-label"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder="e.g. Client preview"
                  className="bg-gray-800 border-gray-700 text-white text-sm"
                  data-testid="share-label"
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="share-pw-toggle" className="text-gray-300 flex items-center gap-2 text-sm">
                  <Lock className="w-4 h-4" /> Require password
                </Label>
                <Switch id="share-pw-toggle" checked={usePassword} onCheckedChange={setUsePassword} data-testid="share-pw-toggle" />
              </div>
              {usePassword && (
                <Input
                  type="text"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password viewers must enter"
                  className="bg-gray-800 border-gray-700 text-white text-sm"
                  data-testid="share-pw-input"
                  required
                />
              )}
              <div className="flex items-center justify-between">
                <Label htmlFor="share-exp-toggle" className="text-gray-300 text-sm">Set expiration</Label>
                <Switch id="share-exp-toggle" checked={useExpiry} onCheckedChange={setUseExpiry} data-testid="share-exp-toggle" />
              </div>
              {useExpiry && (
                <Input
                  type="datetime-local"
                  value={expiresAt}
                  onChange={(e) => setExpiresAt(e.target.value)}
                  className="bg-gray-800 border-gray-700 text-white text-sm"
                  data-testid="share-exp-input"
                  required
                />
              )}
              <div className="flex gap-2">
                <Button type="button" onClick={reset} className="flex-1 bg-gray-700 hover:bg-gray-600">Cancel</Button>
                <Button type="submit" disabled={creating} className="flex-1 bg-blue-600 hover:bg-blue-700" data-testid="share-create-submit">
                  {creating ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Plus className="w-4 h-4 mr-1" />}
                  Create
                </Button>
              </div>
            </form>
          )}

          <div className="border-t border-gray-800 pt-3">
            <h4 className="text-sm font-medium text-gray-400 mb-2">Active links ({items.length})</h4>
            {loading ? (
              <div className="text-sm text-gray-500 py-2">Loading...</div>
            ) : items.length === 0 ? (
              <div className="text-sm text-gray-500 py-2" data-testid="share-empty">
                No share links yet. Create one above.
              </div>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto" data-testid="share-list">
                {items.map((it) => {
                  const url = buildPublicUrl(it.token);
                  const expired = it.expires_at && new Date(it.expires_at) < new Date();
                  return (
                    <div
                      key={it.id}
                      className="bg-gray-800/50 rounded-lg p-3 border border-gray-800 space-y-2"
                      data-testid={`share-item-${it.id}`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-2 min-w-0">
                          {it.label && <span className="text-sm text-white truncate max-w-xs">{it.label}</span>}
                          {it.has_password && (
                            <Badge className="bg-amber-600/30 text-amber-300"><Lock className="w-3 h-3 mr-1" />Password</Badge>
                          )}
                          {expired ? (
                            <Badge className="bg-red-600/30 text-red-300">Expired</Badge>
                          ) : (
                            it.expires_at && <Badge className="bg-gray-700 text-gray-300">Expires {new Date(it.expires_at).toLocaleString()}</Badge>
                          )}
                          <Badge className="bg-gray-700 text-gray-300"><Eye className="w-3 h-3 mr-1" />{it.view_count || 0}</Badge>
                        </div>
                        <div className="flex gap-1 shrink-0">
                          <Button size="sm" onClick={() => copy(it.token)} className="bg-gray-700 hover:bg-gray-600" data-testid={`share-copy-${it.id}`}>
                            <Copy className="w-3 h-3" />
                          </Button>
                          <Button size="sm" onClick={() => revoke(it.token)} className="bg-red-600 hover:bg-red-700" data-testid={`share-revoke-${it.id}`}>
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                      <code className="block text-xs text-gray-400 bg-gray-900 px-2 py-1 rounded truncate">{url}</code>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ShareLinksDialog;
