import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { FolderOpen, Plus, Trash2, Folder } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const FolderManagement = () => {
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newFolderName, setNewFolderName] = useState("");
  const [showDialog, setShowDialog] = useState(false);

  useEffect(() => {
    fetchFolders();
  }, []);

  const fetchFolders = async () => {
    try {
      const response = await axios.get(`${API}/folders`);
      setFolders(response.data);
    } catch (error) {
      toast.error("Failed to load folders");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFolder = async (e) => {
    e.preventDefault();

    if (!newFolderName.trim()) {
      toast.error("Please enter a folder name");
      return;
    }

    try {
      await axios.post(`${API}/folders`, { name: newFolderName });
      toast.success("Folder created successfully");
      setNewFolderName("");
      setShowDialog(false);
      fetchFolders();
    } catch (error) {
      toast.error("Failed to create folder");
    }
  };

  const handleDeleteFolder = async (folderId) => {
    if (!window.confirm("Are you sure you want to delete this folder?")) return;

    try {
      await axios.delete(`${API}/folders/${folderId}`);
      toast.success("Folder deleted successfully");
      fetchFolders();
    } catch (error) {
      toast.error("Failed to delete folder");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-white text-xl">Loading folders...</div>
      </div>
    );
  }

  return (
    <div className="p-8" data-testid="folder-management">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">Folder Management</h2>
          <p className="text-slate-400">Organize your videos into folders</p>
        </div>
        <Dialog open={showDialog} onOpenChange={setShowDialog}>
          <DialogTrigger asChild>
            <Button
              data-testid="create-folder-button"
              className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Folder
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-slate-950/95 border-white/10">
            <DialogHeader>
              <DialogTitle className="text-white">Create New Folder</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateFolder} className="space-y-4">
              <div>
                <Label htmlFor="folder-name" className="text-slate-200">
                  Folder Name
                </Label>
                <Input
                  id="folder-name"
                  data-testid="folder-name-input"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  placeholder="Enter folder name"
                  className="bg-white/5 border-white/10 text-white"
                  autoFocus
                />
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowDialog(false)}
                  className="flex-1 bg-gray-700 hover:bg-gray-600 border-gray-600 text-white"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  data-testid="submit-folder-button"
                  className="flex-1 bg-indigo-500 hover:bg-indigo-600"
                >
                  Create
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {folders.length === 0 ? (
        <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
          <CardContent className="p-12 text-center">
            <FolderOpen className="w-16 h-16 text-slate-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No folders yet</h3>
            <p className="text-slate-400">Create your first folder to organize videos</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {folders.map((folder) => (
            <Card
              key={folder.id}
              className="bg-white/5 border-white/10 backdrop-blur-xl hover:bg-white/10 transition-all duration-200 group"
              data-testid={`folder-card-${folder.id}`}
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="w-12 h-12 bg-indigo-500/20 rounded-lg flex items-center justify-center">
                      <Folder className="w-6 h-6 text-indigo-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-white font-medium truncate">{folder.name}</h3>
                      <p className="text-xs text-slate-400">
                        {new Date(folder.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <Button
                    data-testid={`delete-folder-${folder.id}`}
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDeleteFolder(folder.id)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300 hover:bg-red-500/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default FolderManagement;
