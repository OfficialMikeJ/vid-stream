import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Upload, FileVideo, Loader2, CheckCircle } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const UploadVideo = () => {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [folderId, setFolderId] = useState("");
  const [folders, setFolders] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    fetchFolders();
  }, []);

  const fetchFolders = async () => {
    try {
      const response = await axios.get(`${API}/folders`);
      setFolders(response.data);
    } catch (error) {
      console.error("Failed to load folders");
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      if (!title) {
        setTitle(selectedFile.name.replace(/\.[^/.]+$/, ""));
      }
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      if (!title) {
        setTitle(droppedFile.name.replace(/\.[^/.]+$/, ""));
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();

    if (!file) {
      toast.error("Please select a video file");
      return;
    }

    if (!title) {
      toast.error("Please enter a title");
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title);
    if (description) formData.append("description", description);
    if (folderId) formData.append("folder_id", folderId);

    try {
      await axios.post(`${API}/videos/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percentCompleted);
        },
      });

      toast.success("Video uploaded successfully! Processing started.");
      setFile(null);
      setTitle("");
      setDescription("");
      setFolderId("");
      setUploadProgress(0);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto" data-testid="upload-video-page">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Upload Video</h2>
        <p className="text-slate-400">Add new videos to your library</p>
      </div>

      <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-white">Video Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleUpload} className="space-y-6">
            {/* File Upload Area */}
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-lg p-8 transition-all duration-200 ${
                dragActive
                  ? "border-indigo-500 bg-indigo-500/10"
                  : "border-white/20 hover:border-white/40 bg-white/5"
              }`}
            >
              <input
                type="file"
                id="video-file"
                data-testid="video-file-input"
                onChange={handleFileChange}
                accept="video/*"
                className="hidden"
                disabled={uploading}
              />
              <label
                htmlFor="video-file"
                className="flex flex-col items-center justify-center cursor-pointer"
              >
                {file ? (
                  <>
                    <CheckCircle className="w-12 h-12 text-emerald-400 mb-4" />
                    <p className="text-white font-medium mb-2">{file.name}</p>
                    <p className="text-slate-400 text-sm">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </>
                ) : (
                  <>
                    <FileVideo className="w-12 h-12 text-slate-400 mb-4" />
                    <p className="text-white font-medium mb-2">
                      Drop your video here or click to browse
                    </p>
                    <p className="text-slate-400 text-sm">Supports all FFmpeg-compatible formats</p>
                  </>
                )}
              </label>
            </div>

            {/* Upload Progress */}
            {uploading && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-300">Uploading...</span>
                  <span className="text-indigo-400 font-medium">{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} className="h-2" />
              </div>
            )}

            {/* Title Input */}
            <div className="space-y-2">
              <Label htmlFor="title" className="text-slate-200">
                Title *
              </Label>
              <Input
                id="title"
                data-testid="video-title-input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter video title"
                className="bg-white/5 border-white/10 text-white placeholder:text-slate-500"
                required
                disabled={uploading}
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-slate-200">
                Description
              </Label>
              <Textarea
                id="description"
                data-testid="video-description-input"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter video description (optional)"
                className="bg-white/5 border-white/10 text-white placeholder:text-slate-500"
                rows={4}
                disabled={uploading}
              />
            </div>

            {/* Folder Selection */}
            <div className="space-y-2">
              <Label htmlFor="folder" className="text-slate-200">
                Folder (Optional)
              </Label>
              <Select value={folderId} onValueChange={setFolderId} disabled={uploading}>
                <SelectTrigger className="bg-white/5 border-white/10 text-white">
                  <SelectValue placeholder="Select a folder" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-white/10">
                  <SelectItem value="none" className="text-white">No Folder</SelectItem>
                  {folders.map((folder) => (
                    <SelectItem key={folder.id} value={folder.id} className="text-white">
                      {folder.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              data-testid="upload-button"
              className="w-full h-12 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold shadow-lg shadow-indigo-500/30"
              disabled={uploading || !file}
            >
              {uploading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5 mr-2" />
                  Upload Video
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default UploadVideo;
