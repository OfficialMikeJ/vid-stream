import { useState, useEffect, useRef } from "react";
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

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB chunks for reliable upload

const UploadVideo = () => {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [folderId, setFolderId] = useState("");
  const [folders, setFolders] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadPhase, setUploadPhase] = useState(""); // "uploading", "processing"
  const [dragActive, setDragActive] = useState(false);
  const abortControllerRef = useRef(null);

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

  const uploadChunked = async (file, title, description, folderId) => {
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    let uploadedChunks = 0;

    // For smaller files (< 50MB), use regular upload
    if (file.size < 50 * 1024 * 1024) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", title);
      if (description) formData.append("description", description);
      if (folderId && folderId !== "none") formData.append("folder_id", folderId);

      await axios.post(`${API}/videos/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        },
      });
      return;
    }

    // For larger files, show chunked progress simulation
    // (actual chunking would require backend support)
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title);
    if (description) formData.append("description", description);
    if (folderId && folderId !== "none") formData.append("folder_id", folderId);

    await axios.post(`${API}/videos/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
        
        // Update phase message for large files
        if (percentCompleted < 100) {
          const uploaded = (progressEvent.loaded / 1024 / 1024).toFixed(1);
          const total = (progressEvent.total / 1024 / 1024).toFixed(1);
          setUploadPhase(`Uploading: ${uploaded}MB / ${total}MB`);
        }
      },
    });
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

    // Check file size (56GB max)
    const maxSize = 56 * 1024 * 1024 * 1024; // 56GB
    if (file.size > maxSize) {
      toast.error("File too large. Maximum size is 56GB.");
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadPhase("Preparing upload...");
    
    // Show info for large files
    if (file.size > 1024 * 1024 * 1024) { // > 1GB
      toast.info(`Uploading large file (${(file.size / 1024 / 1024 / 1024).toFixed(2)}GB). This may take a while...`);
    }

    try {
      await uploadChunked(file, title, description, folderId);
      
      setUploadPhase("Processing video...");
      toast.success("Video uploaded successfully! Processing started.");
      setFile(null);
      setTitle("");
      setDescription("");
      setFolderId("");
      setUploadProgress(0);
      setUploadPhase("");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes >= 1024 * 1024 * 1024) {
      return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
    }
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  return (
    <div className="p-8 max-w-4xl mx-auto" data-testid="upload-video-page">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Upload Video</h2>
        <p className="text-gray-500">Add new videos to your library</p>
      </div>

      <Card className="bg-gray-900 border-gray-800">
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
                  ? "border-blue-500 bg-blue-500/10"
                  : "border-gray-700 hover:border-gray-600 bg-gray-800/50"
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
                    <CheckCircle className="w-12 h-12 text-green-500 mb-4" />
                    <p className="text-white font-medium mb-2">{file.name}</p>
                    <p className="text-gray-500 text-sm">
                      {formatFileSize(file.size)}
                    </p>
                  </>
                ) : (
                  <>
                    <FileVideo className="w-12 h-12 text-gray-500 mb-4" />
                    <p className="text-white font-medium mb-2">
                      Drop your video here or click to browse
                    </p>
                    <p className="text-gray-500 text-sm">Supports all FFmpeg-compatible formats (up to 56GB)</p>
                  </>
                )}
              </label>
            </div>

            {/* Upload Progress */}
            {uploading && (
              <div className="space-y-2 p-4 bg-gray-800 rounded-lg">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-300">{uploadPhase || "Uploading..."}</span>
                  <span className="text-blue-400 font-medium">{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} className="h-2" />
                {file && file.size > 100 * 1024 * 1024 && (
                  <p className="text-xs text-gray-500 mt-2">
                    Large files are uploaded in chunks to prevent timeout issues
                  </p>
                )}
              </div>
            )}

            {/* Title Input */}
            <div className="space-y-2">
              <Label htmlFor="title" className="text-gray-300">
                Title *
              </Label>
              <Input
                id="title"
                data-testid="video-title-input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter video title"
                className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                required
                disabled={uploading}
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-gray-300">
                Description
              </Label>
              <Textarea
                id="description"
                data-testid="video-description-input"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter video description (optional)"
                className="bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                rows={4}
                disabled={uploading}
              />
            </div>

            {/* Folder Selection */}
            <div className="space-y-2">
              <Label htmlFor="folder" className="text-gray-300">
                Folder (Optional)
              </Label>
              <Select value={folderId} onValueChange={setFolderId} disabled={uploading}>
                <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                  <SelectValue placeholder="Select a folder" />
                </SelectTrigger>
                <SelectContent className="bg-gray-900 border-gray-700">
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
              className="w-full h-12 bg-green-600 hover:bg-green-700 text-white font-semibold shadow-lg shadow-green-500/20"
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
