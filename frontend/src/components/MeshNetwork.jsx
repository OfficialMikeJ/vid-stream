import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Server, Plus, RefreshCw, Trash2, HardDrive, Database, Wifi, WifiOff, Loader2 } from "lucide-react";

const StatusBadge = ({ status }) => {
  if (status === "online") return <Badge className="bg-green-600 text-white text-xs">Online</Badge>;
  if (status === "offline") return <Badge className="bg-red-600 text-white text-xs">Offline</Badge>;
  return <Badge className="bg-gray-600 text-white text-xs">Unknown</Badge>;
};

const StorageBar = ({ used, total }) => {
  if (!total) return <span className="text-gray-500 text-xs">N/A</span>;
  const pct = Math.min(100, Math.round((used / total) * 100));
  const color = pct > 85 ? "bg-red-500" : pct > 60 ? "bg-yellow-500" : "bg-green-500";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-gray-400">
        <span>{used?.toFixed(1)} GB used</span>
        <span>{total?.toFixed(1)} GB total</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <p className="text-xs text-gray-500">{pct}% used</p>
    </div>
  );
};

const MeshNetwork = () => {
  const [meshData, setMeshData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pingingId, setPingingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ name: "", url: "", api_key: "" });

  useEffect(() => { fetchMesh(); }, []);

  const fetchMesh = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/mesh/nodes`);
      setMeshData(r.data);
    } catch {
      toast.error("Failed to load mesh data");
    } finally {
      setLoading(false);
    }
  };

  const addNode = async (e) => {
    e.preventDefault();
    if (!form.name || !form.url || !form.api_key) {
      toast.error("All fields are required");
      return;
    }
    setAdding(true);
    try {
      await axios.post(`${API}/mesh/nodes`, form);
      toast.success("Node added to mesh pool");
      setForm({ name: "", url: "", api_key: "" });
      setShowAdd(false);
      fetchMesh();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to add node");
    } finally {
      setAdding(false);
    }
  };

  const pingNode = async (nodeId) => {
    setPingingId(nodeId);
    try {
      await axios.post(`${API}/mesh/nodes/${nodeId}/ping`);
      toast.success("Node refreshed");
      fetchMesh();
    } catch {
      toast.error("Ping failed");
    } finally {
      setPingingId(null);
    }
  };

  const removeNode = async (nodeId, name) => {
    if (!window.confirm(`Remove "${name}" from mesh pool?`)) return;
    setDeletingId(nodeId);
    try {
      await axios.delete(`${API}/mesh/nodes/${nodeId}`);
      toast.success("Node removed");
      fetchMesh();
    } catch {
      toast.error("Failed to remove node");
    } finally {
      setDeletingId(null);
    }
  };

  // Compute total pool storage
  const totalPoolGB = meshData
    ? (meshData.local_node.storage_total_gb || 0) +
      meshData.remote_nodes.reduce((s, n) => s + (n.storage_total_gb || 0), 0)
    : 0;
  const usedPoolGB = meshData
    ? (meshData.local_node.storage_used_gb || 0) +
      meshData.remote_nodes.reduce((s, n) => s + (n.storage_used_gb || 0), 0)
    : 0;

  return (
    <div className="p-8 max-w-5xl mx-auto" data-testid="mesh-network-page">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">Storage Mesh</h2>
          <p className="text-gray-500">
            Pool storage across multiple StreamHost servers. Add remote nodes to expand your total storage capacity.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            data-testid="refresh-mesh-btn"
            variant="outline"
            onClick={fetchMesh}
            disabled={loading}
            className="border-gray-700 text-gray-300 hover:bg-gray-800"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            data-testid="add-node-btn"
            onClick={() => setShowAdd(!showAdd)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Node
          </Button>
        </div>
      </div>

      {/* Pool Summary */}
      {meshData && (
        <Card className="bg-gray-900 border-gray-800 mb-6">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Database className="w-5 h-5 text-blue-400" />
              Total Storage Pool
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-6 mb-4">
              <div>
                <p className="text-xs text-gray-500 mb-1">Total Capacity</p>
                <p className="text-2xl font-bold text-white">{totalPoolGB.toFixed(1)} GB</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">Used</p>
                <p className="text-2xl font-bold text-yellow-400">{usedPoolGB.toFixed(1)} GB</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">Free</p>
                <p className="text-2xl font-bold text-green-400">{(totalPoolGB - usedPoolGB).toFixed(1)} GB</p>
              </div>
            </div>
            <StorageBar used={usedPoolGB} total={totalPoolGB} />
            <p className="text-xs text-gray-500 mt-3">
              {1 + (meshData.remote_nodes?.length || 0)} node{(meshData.remote_nodes?.length || 0) > 0 ? "s" : ""} in pool
            </p>
          </CardContent>
        </Card>
      )}

      {/* Add Node Form */}
      {showAdd && (
        <Card className="bg-gray-900 border-blue-700 mb-6">
          <CardHeader>
            <CardTitle className="text-white">Register Remote Node</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={addNode} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label className="text-gray-300">Node Name</Label>
                  <Input
                    data-testid="node-name-input"
                    value={form.name}
                    onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                    placeholder="e.g., Storage Node 2"
                    className="bg-gray-800 border-gray-700 text-white mt-1"
                  />
                </div>
                <div>
                  <Label className="text-gray-300">Node URL</Label>
                  <Input
                    data-testid="node-url-input"
                    value={form.url}
                    onChange={e => setForm(f => ({ ...f, url: e.target.value }))}
                    placeholder="https://node2.example.com"
                    className="bg-gray-800 border-gray-700 text-white mt-1"
                  />
                </div>
                <div>
                  <Label className="text-gray-300">API Key (JWT Token)</Label>
                  <Input
                    data-testid="node-apikey-input"
                    value={form.api_key}
                    onChange={e => setForm(f => ({ ...f, api_key: e.target.value }))}
                    placeholder="Bearer token from remote node"
                    className="bg-gray-800 border-gray-700 text-white mt-1"
                  />
                </div>
              </div>
              <p className="text-xs text-gray-500">
                The API key is a valid JWT bearer token from the remote StreamHost instance. Log into the remote node, copy the token from your browser's local storage, and paste it here.
              </p>
              <div className="flex gap-3">
                <Button
                  type="submit"
                  data-testid="submit-add-node-btn"
                  disabled={adding}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  {adding ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Adding...</> : "Add Node"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowAdd(false)}
                  className="border-gray-700 text-gray-300 hover:bg-gray-800"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
        </div>
      ) : (
        <div className="space-y-4">
          {/* Local Node */}
          {meshData && (
            <Card className="bg-gray-900 border-green-700" data-testid="local-node-card">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-600/20 rounded-lg flex items-center justify-center">
                      <Server className="w-5 h-5 text-green-400" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-white font-semibold">{meshData.local_node.name}</p>
                        <Badge className="bg-green-600 text-white text-xs">Primary</Badge>
                        <StatusBadge status={meshData.local_node.status} />
                      </div>
                      <p className="text-gray-500 text-sm">This server</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-gray-400 text-sm">{meshData.local_node.video_count} videos</p>
                  </div>
                </div>
                <div className="mt-4">
                  <StorageBar
                    used={meshData.local_node.storage_used_gb}
                    total={meshData.local_node.storage_total_gb}
                  />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Remote Nodes */}
          {meshData?.remote_nodes?.length === 0 && (
            <Card className="bg-gray-900 border-gray-800">
              <CardContent className="p-12 flex flex-col items-center justify-center text-center">
                <HardDrive className="w-12 h-12 text-gray-600 mb-4" />
                <p className="text-gray-400 font-medium mb-1">No remote nodes registered</p>
                <p className="text-gray-600 text-sm">Add a StreamHost node to expand your storage pool</p>
              </CardContent>
            </Card>
          )}

          {meshData?.remote_nodes?.map((node) => (
            <Card
              key={node.node_id}
              data-testid={`mesh-node-${node.node_id}`}
              className={`bg-gray-900 ${node.status === "online" ? "border-gray-700" : "border-red-900"}`}
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      node.status === "online" ? "bg-blue-600/20" : "bg-red-600/20"
                    }`}>
                      {node.status === "online"
                        ? <Wifi className="w-5 h-5 text-blue-400" />
                        : <WifiOff className="w-5 h-5 text-red-400" />
                      }
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-white font-semibold">{node.name}</p>
                        <StatusBadge status={node.status} />
                      </div>
                      <p className="text-gray-500 text-sm font-mono text-xs">{node.url}</p>
                      {node.last_seen && (
                        <p className="text-gray-600 text-xs">
                          Last seen: {new Date(node.last_seen).toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {node.video_count !== null && node.video_count !== undefined && (
                      <span className="text-gray-400 text-sm mr-2">{node.video_count} videos</span>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => pingNode(node.node_id)}
                      disabled={pingingId === node.node_id}
                      className="border-gray-700 text-gray-300 hover:bg-gray-800"
                      data-testid={`ping-node-${node.node_id}`}
                    >
                      {pingingId === node.node_id
                        ? <Loader2 className="w-4 h-4 animate-spin" />
                        : <RefreshCw className="w-4 h-4" />
                      }
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => removeNode(node.node_id, node.name)}
                      disabled={deletingId === node.node_id}
                      className="border-red-800 text-red-400 hover:bg-red-900/20"
                      data-testid={`remove-node-${node.node_id}`}
                    >
                      {deletingId === node.node_id
                        ? <Loader2 className="w-4 h-4 animate-spin" />
                        : <Trash2 className="w-4 h-4" />
                      }
                    </Button>
                  </div>
                </div>
                {(node.storage_total_gb || node.storage_used_gb) && (
                  <div className="mt-4">
                    <StorageBar used={node.storage_used_gb} total={node.storage_total_gb} />
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default MeshNetwork;
