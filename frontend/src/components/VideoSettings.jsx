import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import {
  Palette, Users, Plus, Trash2, RefreshCw, Loader2,
  UserCheck, UserX, Shield, Eye, Save
} from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

// ── Player Theme ─────────────────────────────────────────────────────────────

const PlayerThemeTab = () => {
  const [settings, setSettings] = useState({
    primary_color: "#3b82f6",
    background_color: "#000000",
    show_controls: true,
    autoplay: false,
    loop: false,
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    axios.get(`${API}/settings/player`).then(r => setSettings(r.data)).catch(() => {});
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await axios.patch(`${API}/settings/player`, settings);
      toast.success("Player settings saved");
    } catch {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <p className="text-gray-400 text-sm">
        These defaults are applied to all new embed codes. Existing embed settings override per-video.
      </p>

      {/* Live Preview */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white text-sm">Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className="rounded-lg w-full flex items-center justify-center"
            style={{
              backgroundColor: settings.background_color,
              aspectRatio: "16/9",
              border: `2px solid ${settings.primary_color}`,
            }}
          >
            <div className="flex flex-col items-center gap-3">
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center"
                style={{ backgroundColor: settings.primary_color }}
              >
                <svg viewBox="0 0 24 24" fill="white" className="w-8 h-8">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
              {settings.show_controls && (
                <div className="flex gap-3 items-center mt-2">
                  <div className="w-16 h-1 rounded" style={{ backgroundColor: settings.primary_color }} />
                  <div className="w-24 h-1 rounded bg-gray-700" />
                  <div className="w-8 h-1 rounded bg-gray-700" />
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Colors */}
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-6 space-y-5">
          <div className="grid grid-cols-2 gap-5">
            <div>
              <Label className="text-gray-300 mb-2 block">Primary / Accent Color</Label>
              <div className="flex gap-2 items-center">
                <input
                  type="color"
                  value={settings.primary_color}
                  onChange={e => setSettings(s => ({ ...s, primary_color: e.target.value }))}
                  className="w-12 h-10 rounded border border-gray-700 bg-gray-800 cursor-pointer"
                  data-testid="primary-color-picker"
                />
                <Input
                  value={settings.primary_color}
                  onChange={e => setSettings(s => ({ ...s, primary_color: e.target.value }))}
                  className="flex-1 bg-gray-800 border-gray-700 text-white font-mono text-sm"
                  placeholder="#3b82f6"
                />
              </div>
            </div>
            <div>
              <Label className="text-gray-300 mb-2 block">Player Background</Label>
              <div className="flex gap-2 items-center">
                <input
                  type="color"
                  value={settings.background_color}
                  onChange={e => setSettings(s => ({ ...s, background_color: e.target.value }))}
                  className="w-12 h-10 rounded border border-gray-700 bg-gray-800 cursor-pointer"
                  data-testid="bg-color-picker"
                />
                <Input
                  value={settings.background_color}
                  onChange={e => setSettings(s => ({ ...s, background_color: e.target.value }))}
                  className="flex-1 bg-gray-800 border-gray-700 text-white font-mono text-sm"
                  placeholder="#000000"
                />
              </div>
            </div>
          </div>

          {/* Toggles */}
          <div className="space-y-4 pt-2">
            {[
              { key: "show_controls", label: "Show player controls", testid: "toggle-controls" },
              { key: "autoplay", label: "Autoplay videos", testid: "toggle-autoplay" },
              { key: "loop", label: "Loop videos", testid: "toggle-loop" },
            ].map(({ key, label, testid }) => (
              <div key={key} className="flex items-center justify-between">
                <Label className="text-gray-300">{label}</Label>
                <Switch
                  data-testid={testid}
                  checked={settings[key]}
                  onCheckedChange={v => setSettings(s => ({ ...s, [key]: v }))}
                />
              </div>
            ))}
          </div>

          <Button
            data-testid="save-player-settings-btn"
            onClick={save}
            disabled={saving}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white mt-2"
          >
            {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
            Save Player Settings
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};


// ── User Management ──────────────────────────────────────────────────────────

const UsersTab = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ username: "", password: "", role: "viewer", must_change_password: true });
  const [deletingId, setDeletingId] = useState(null);
  const [togglingId, setTogglingId] = useState(null);

  useEffect(() => { fetchUsers(); }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/users`);
      setUsers(r.data);
    } catch {
      toast.error("Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  const createUser = async (e) => {
    e.preventDefault();
    if (!form.username || !form.password) {
      toast.error("Username and password are required");
      return;
    }
    setCreating(true);
    try {
      await axios.post(`${API}/users`, form);
      toast.success(`User "${form.username}" created`);
      setForm({ username: "", password: "", role: "viewer", must_change_password: true });
      setShowCreate(false);
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create user");
    } finally {
      setCreating(false);
    }
  };

  const toggleActive = async (user) => {
    setTogglingId(user.id);
    try {
      await axios.patch(`${API}/users/${user.id}?is_active=${!user.is_active}`);
      toast.success(`User ${!user.is_active ? "activated" : "deactivated"}`);
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to update user");
    } finally {
      setTogglingId(null);
    }
  };

  const changeRole = async (user, newRole) => {
    try {
      await axios.patch(`${API}/users/${user.id}?role=${newRole}`);
      toast.success(`Role changed to ${newRole}`);
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to change role");
    }
  };

  const deleteUser = async (user) => {
    if (!window.confirm(`Delete user "${user.username}"? This cannot be undone.`)) return;
    setDeletingId(user.id);
    try {
      await axios.delete(`${API}/users/${user.id}`);
      toast.success(`User "${user.username}" deleted`);
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to delete user");
    } finally {
      setDeletingId(null);
    }
  };

  const currentUsername = localStorage.getItem("username") || "";

  return (
    <div className="space-y-4 max-w-3xl">
      <div className="flex items-center justify-between">
        <p className="text-gray-400 text-sm">
          Manage who can access StreamHost. <span className="text-gray-500">Admins have full access. Viewers can watch videos and get embed codes.</span>
        </p>
        <Button
          data-testid="create-user-btn"
          onClick={() => setShowCreate(true)}
          className="bg-green-600 hover:bg-green-700 text-white shrink-0"
        >
          <Plus className="w-4 h-4 mr-2" />
          New User
        </Button>
      </div>

      {/* Create user dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="bg-gray-900 border-gray-800 text-white max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">Create New User</DialogTitle>
          </DialogHeader>
          <form onSubmit={createUser} className="space-y-4">
            <div>
              <Label className="text-gray-300">Username</Label>
              <Input
                data-testid="new-username-input"
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                placeholder="Enter username"
                className="bg-gray-800 border-gray-700 text-white mt-1"
              />
            </div>
            <div>
              <Label className="text-gray-300">Password</Label>
              <Input
                data-testid="new-password-input"
                type="password"
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                placeholder="Set initial password"
                className="bg-gray-800 border-gray-700 text-white mt-1"
              />
            </div>
            <div>
              <Label className="text-gray-300">Role</Label>
              <Select value={form.role} onValueChange={v => setForm(f => ({ ...f, role: v }))}>
                <SelectTrigger className="bg-gray-800 border-gray-700 text-white mt-1" data-testid="new-user-role-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-900 border-gray-700">
                  <SelectItem value="viewer" className="text-white hover:bg-gray-800">Viewer — Watch &amp; embed</SelectItem>
                  <SelectItem value="admin" className="text-white hover:bg-gray-800">Admin — Full access</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-between">
              <Label className="text-gray-300">Force password change on first login</Label>
              <Switch
                checked={form.must_change_password}
                onCheckedChange={v => setForm(f => ({ ...f, must_change_password: v }))}
              />
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={creating} data-testid="submit-create-user-btn"
                className="flex-1 bg-green-600 hover:bg-green-700 text-white">
                {creating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Create User
              </Button>
              <Button type="button" variant="outline" onClick={() => setShowCreate(false)}
                className="border-gray-700 text-gray-300 hover:bg-gray-800">Cancel</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Users list */}
      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 text-blue-400 animate-spin" /></div>
      ) : (
        <div className="space-y-3">
          {users.map((user) => {
            const isSelf = user.username === currentUsername;
            return (
              <Card key={user.id} data-testid={`user-card-${user.username}`}
                className={`bg-gray-900 ${user.is_active ? "border-gray-800" : "border-red-900/50 opacity-60"}`}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-full flex items-center justify-center ${user.role === "admin" ? "bg-blue-600/20" : "bg-gray-700"}`}>
                        {user.role === "admin"
                          ? <Shield className="w-4 h-4 text-blue-400" />
                          : <Eye className="w-4 h-4 text-gray-400" />
                        }
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">{user.username}</span>
                          {isSelf && <Badge className="bg-green-600/20 text-green-400 text-xs border-0">You</Badge>}
                          {!user.is_active && <Badge className="bg-red-600/20 text-red-400 text-xs border-0">Inactive</Badge>}
                          {user.must_change_password && <Badge className="bg-yellow-600/20 text-yellow-400 text-xs border-0">Temp password</Badge>}
                        </div>
                        <p className="text-gray-500 text-xs">
                          {user.role === "admin" ? "Admin — Full access" : "Viewer — Watch & embed"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {!isSelf && (
                        <>
                          <Select value={user.role} onValueChange={v => changeRole(user, v)}>
                            <SelectTrigger className="w-28 h-8 bg-gray-800 border-gray-700 text-white text-xs"
                              data-testid={`role-select-${user.username}`}>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-gray-900 border-gray-700">
                              <SelectItem value="viewer" className="text-white hover:bg-gray-800 text-xs">Viewer</SelectItem>
                              <SelectItem value="admin" className="text-white hover:bg-gray-800 text-xs">Admin</SelectItem>
                            </SelectContent>
                          </Select>
                          <Button size="sm" variant="outline" onClick={() => toggleActive(user)}
                            disabled={togglingId === user.id}
                            className={`h-8 px-2 ${user.is_active ? "border-yellow-700 text-yellow-400 hover:bg-yellow-900/20" : "border-green-700 text-green-400 hover:bg-green-900/20"}`}
                            data-testid={`toggle-active-${user.username}`}>
                            {togglingId === user.id
                              ? <Loader2 className="w-3 h-3 animate-spin" />
                              : user.is_active ? <UserX className="w-3 h-3" /> : <UserCheck className="w-3 h-3" />
                            }
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => deleteUser(user)}
                            disabled={deletingId === user.id}
                            className="h-8 px-2 border-red-800 text-red-400 hover:bg-red-900/20"
                            data-testid={`delete-user-${user.username}`}>
                            {deletingId === user.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};


// ── Main Settings Page ───────────────────────────────────────────────────────

const VideoSettings = () => {
  return (
    <div className="p-8" data-testid="settings-page">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Settings</h2>
        <p className="text-gray-500">Configure StreamHost to your preferences</p>
      </div>

      <Tabs defaultValue="player" className="w-full">
        <TabsList className="bg-gray-900 border border-gray-800 mb-6">
          <TabsTrigger value="player" data-testid="tab-player"
            className="data-[state=active]:bg-blue-600 data-[state=active]:text-white text-gray-400">
            <Palette className="w-4 h-4 mr-2" />
            Player Theme
          </TabsTrigger>
          <TabsTrigger value="users" data-testid="tab-users"
            className="data-[state=active]:bg-blue-600 data-[state=active]:text-white text-gray-400">
            <Users className="w-4 h-4 mr-2" />
            Users
          </TabsTrigger>
        </TabsList>

        <TabsContent value="player">
          <PlayerThemeTab />
        </TabsContent>
        <TabsContent value="users">
          <UsersTab />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VideoSettings;
