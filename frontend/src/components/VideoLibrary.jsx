import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Play, Trash2, Edit2, Copy, Clock, HardDrive, Eye, Code } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import VideoPlayer from "./VideoPlayer";
import EmbedSettingsDialog from "./EmbedSettingsDialog";

const VideoLibrary = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [showPlayer, setShowPlayer] = useState(false);
  const [showEmbedDialog, setShowEmbedDialog] = useState(false);
  const [embedCode, setEmbedCode] = useState("");
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [showEmbedSettings, setShowEmbedSettings] = useState(false);

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const response = await axios.get(`${API}/videos`);
      setVideos(response.data);
    } catch (error) {
      toast.error("Failed to load videos");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (videoId) => {
    if (!window.confirm("Are you sure you want to delete this video?")) return;

    try {
      await axios.delete(`${API}/videos/${videoId}`);
      toast.success("Video deleted successfully");
      fetchVideos();
    } catch (error) {
      toast.error("Failed to delete video");
    }
  };

  const handleGetEmbedCode = async (video) => {
    try {
      const response = await axios.get(`${API}/embed-code/${video.id}`);
      setEmbedCode(response.data.embed_code);
      setSelectedVideo(video);
      setShowEmbedDialog(true);
    } catch (error) {
      toast.error("Failed to get embed code");
    }
  };

  const copyEmbedCode = () => {
    navigator.clipboard.writeText(embedCode);
    toast.success("Embed code copied to clipboard");
  };

  const handleEdit = (video) => {
    setSelectedVideo(video);
    setEditTitle(video.title);
    setEditDescription(video.description || "");
    setShowEditDialog(true);
  };

  const handleSaveEdit = async () => {
    try {
      const formData = new FormData();
      formData.append("title", editTitle);
      formData.append("description", editDescription);

      await axios.patch(`${API}/videos/${selectedVideo.id}?title=${encodeURIComponent(editTitle)}&description=${encodeURIComponent(editDescription)}`);
      toast.success("Video updated successfully");
      setShowEditDialog(false);
      fetchVideos();
    } catch (error) {
      toast.error("Failed to update video");
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return "--:--";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return "0 B";
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-white text-xl">Loading videos...</div>
      </div>
    );
  }

  return (
    <div className="p-8" data-testid="video-library">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Video Library</h2>
        <p className="text-gray-500">Manage and organize your video content</p>
      </div>

      {videos.length === 0 ? (
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-12 text-center">
            <Play className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No videos yet</h3>
            <p className="text-gray-500">Upload your first video to get started</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {videos.map((video) => (
            <Card
              key={video.id}
              className="bg-gray-900 border-gray-800 hover:bg-gray-800 transition-all duration-200 group overflow-hidden"
              data-testid={`video-card-${video.id}`}
            >
              <div className="relative aspect-video bg-black overflow-hidden">
                {video.thumbnail_path ? (
                  <img
                    src={`${API}/stream/thumbnail/${video.id}`}
                    alt={video.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Play className="w-12 h-12 text-gray-700" />
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-end justify-center pb-4">
                  <Button
                    data-testid={`play-video-${video.id}`}
                    size="sm"
                    onClick={() => {
                      setSelectedVideo(video);
                      setShowPlayer(true);
                    }}
                    className="bg-blue-600 hover:bg-blue-700 text-white gap-2"
                    disabled={video.processing_status !== "ready"}
                  >
                    <Play className="w-4 h-4" />
                    Play
                  </Button>
                </div>
                <div className="absolute top-2 right-2">
                  <Badge
                    variant={video.processing_status === "ready" ? "success" : "secondary"}
                    className={`${
                      video.processing_status === "ready"
                        ? "bg-green-600/20 text-green-400 border-green-500/30"
                        : video.processing_status === "processing"
                        ? "bg-orange-500/20 text-orange-400 border-orange-500/30"
                        : "bg-red-500/20 text-red-400 border-red-500/30"
                    }`}
                  >
                    {video.processing_status}
                  </Badge>
                </div>
              </div>
              <CardContent className="p-4">
                <h3 className="text-lg font-semibold text-white mb-2 truncate">{video.title}</h3>
                {video.description && (
                  <p className="text-sm text-gray-500 mb-3 line-clamp-2">{video.description}</p>
                )}
                <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-4">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDuration(video.duration)}
                  </div>
                  <div className="flex items-center gap-1">
                    <HardDrive className="w-3 h-3" />
                    {formatFileSize(video.file_size)}
                  </div>
                  {video.aspect_ratio && (
                    <div className="flex items-center gap-1">
                      <Eye className="w-3 h-3" />
                      {video.aspect_ratio}
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    data-testid={`edit-video-${video.id}`}
                    size="sm"
                    onClick={() => handleEdit(video)}
                    className="flex-1 bg-gray-700 hover:bg-gray-600 text-white"
                  >
                    <Edit2 className="w-3 h-3 mr-1" />
                    Edit
                  </Button>
                  <Button
                    data-testid={`embed-video-${video.id}`}
                    size="sm"
                    onClick={() => {
                      setSelectedVideo(video);
                      setShowEmbedSettings(true);
                    }}
                    className="flex-1 bg-orange-600 hover:bg-orange-700 text-white"
                    disabled={video.processing_status !== "ready"}
                  >
                    <Code className="w-3 h-3 mr-1" />
                    Embed
                  </Button>
                  <Button
                    data-testid={`delete-video-${video.id}`}
                    size="sm"
                    onClick={() => handleDelete(video.id)}
                    className="bg-red-600 hover:bg-red-700 text-white"
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Video Player Dialog */}
      <Dialog open={showPlayer} onOpenChange={setShowPlayer}>
        <DialogContent className="max-w-4xl bg-gray-900 border-gray-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-white">{selectedVideo?.title}</DialogTitle>
            {selectedVideo?.description && (
              <DialogDescription className="text-gray-500">{selectedVideo.description}</DialogDescription>
            )}
          </DialogHeader>
          {selectedVideo && <VideoPlayer video={selectedVideo} />}
        </DialogContent>
      </Dialog>

      {/* Embed Code Dialog */}
      <Dialog open={showEmbedDialog} onOpenChange={setShowEmbedDialog}>
        <DialogContent className="max-w-2xl bg-gray-900 border-gray-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-white">Embed Code</DialogTitle>
            <DialogDescription className="text-gray-500">
              Copy this code to embed the video on your website
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Textarea
              value={embedCode}
              readOnly
              className="font-mono text-sm bg-gray-800 border-gray-700 text-gray-300 min-h-[300px]"
            />
            <Button onClick={copyEmbedCode} className="w-full bg-blue-600 hover:bg-blue-700 text-white">
              <Copy className="w-4 h-4 mr-2" />
              Copy Embed Code
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Video Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-md bg-gray-900 border-gray-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-white">Edit Video</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="edit-title" className="text-gray-300">
                Title
              </Label>
              <Input
                id="edit-title"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="bg-gray-800 border-gray-700 text-white"
              />
            </div>
            <div>
              <Label htmlFor="edit-description" className="text-gray-300">
                Description
              </Label>
              <Textarea
                id="edit-description"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                className="bg-gray-800 border-gray-700 text-white"
                rows={4}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={() => setShowEditDialog(false)} className="flex-1 bg-gray-700 hover:bg-gray-600 text-white">
                Cancel
              </Button>
              <Button onClick={handleSaveEdit} className="flex-1 bg-green-600 hover:bg-green-700 text-white">
                Save Changes
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Embed Settings Dialog */}
      {selectedVideo && (
        <EmbedSettingsDialog
          video={selectedVideo}
          open={showEmbedSettings}
          onOpenChange={setShowEmbedSettings}
          onGetEmbedCode={() => {
            setShowEmbedSettings(false);
            handleGetEmbedCode(selectedVideo);
          }}
        />
      )}
    </div>
  );
};

export default VideoLibrary;
