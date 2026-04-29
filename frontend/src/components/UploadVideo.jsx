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

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB chunks — supports resume on network failure

const UploadVideo = () => {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [folderId, setFolderId] = useState("");
  const [folders, setFolders] = useState([]);
  const [presets, setPresets] = useState([]);
  const [defaultPreset, setDefaultPreset] = useState("source");
  const [transcodingPreset, setTranscodingPreset] = useState("default");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadPhase, setUploadPhase] = useState(""); // "uploading", "processing"
  const [dragActive, setDragActive] = useState(false);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    fetchFolders();
    fetchPresets();
  }, []);

  const fetchFolders = async () => {
    try {
      const response = await axios.get(`${API}/folders`);
      setFolders(response.data);
    } catch (error) {
      console.error("Failed to load folders");
    }
  };

  const fetchPresets = async () => {
    try {
      const r = await axios.get(`${API}/settings/transcoding`);
      setPresets(r.data.presets || []);
      setDefaultPreset(r.data.default_preset || "source");
    } catch {
      // If admin hasn't visited settings yet, fall back gracefully
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
    const totalMB = (file.size / 1024 / 1024).toFixed(1);
    const resumeKey = `streamhost_upload_${file.name}_${file.size}`;

    // ── Step 1: Check for a resumable session ──────────────────────────────
    let upload_id = null;
    let chunksAlreadyDone = [];
    const savedId = localStorage.getItem(resumeKey);

    if (savedId) {
      try {
        setUploadPhase("Checking for resumable upload...");
        const statusResp = await axios.get(`${API}/upload/status/${savedId}`);
        if (statusResp.data.status === "in_progress") {
          upload_id = savedId;
          chunksAlreadyDone = statusResp.data.chunks_received || [];
          if (chunksAlreadyDone.length > 0) {
            setUploadPhase(`Resuming upload (${chunksAlreadyDone.length}/${totalChunks} chunks already uploaded)...`);
            const resumeProgress = Math.round((chunksAlreadyDone.length / totalChunks) * 100);
            setUploadProgress(resumeProgress);
            await new Promise((r) => setTimeout(r, 800)); // Brief pause so user sees it
          }
        }
      } catch {
        // Session expired or not found — start fresh
        localStorage.removeItem(resumeKey);
      }
    }

    // ── Step 2: Init new session if needed ────────────────────────────────
    if (!upload_id) {
      setUploadPhase("Initializing upload...");
      const initForm = new FormData();
      initForm.append("filename", file.name);
      initForm.append("title", title);
      initForm.append("total_size", file.size);
      if (description) initForm.append("description", description);
      if (folderId && folderId !== "none") initForm.append("folder_id", folderId);
      if (transcodingPreset && transcodingPreset !== "default") {
        initForm.append("transcoding_preset", transcodingPreset);
      }

      const initResp = await axios.post(`${API}/upload/init`, initForm, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      upload_id = initResp.data.upload_id;
      localStorage.setItem(resumeKey, upload_id);
    }

    // ── Step 3: Upload chunks (skip already done, retry on error) ─────────
    const sendChunk = async (i) => {
      const start = i * CHUNK_SIZE;
      const end = Math.min(start + CHUNK_SIZE, file.size);
      const chunkBlob = file.slice(start, end);
      const form = new FormData();
      form.append("upload_id", upload_id);
      form.append("chunk_index", i);
      form.append("total_chunks", totalChunks);
      form.append("chunk", chunkBlob, `chunk_${i}`);
      return axios.post(`${API}/upload/chunk`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    };

    for (let i = 0; i < totalChunks; i++) {
      if (abortControllerRef.current?.signal?.aborted) {
        throw new Error("Upload cancelled");
      }

      // Skip chunks already on the server
      if (chunksAlreadyDone.includes(i)) {
        const progress = Math.round(((i + 1) / totalChunks) * 100);
        setUploadProgress(progress);
        continue;
      }

      // Send with up to 3 retries (exponential backoff: 1s, 2s, 4s)
      let lastErr;
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          await sendChunk(i);
          lastErr = null;
          break;
        } catch (err) {
          lastErr = err;
          if (attempt < 2) {
            const wait = 1000 * Math.pow(2, attempt);
            setUploadPhase(`Network error — retrying chunk ${i + 1} in ${wait / 1000}s...`);
            await new Promise((r) => setTimeout(r, wait));
          }
        }
      }
      if (lastErr) throw lastErr;

      const progress = Math.round(((i + 1) / totalChunks) * 100);
      const uploadedMB = Math.min(((i + 1) * CHUNK_SIZE) / 1024 / 1024, file.size / 1024 / 1024).toFixed(1);
      setUploadProgress(progress);
      setUploadPhase(`Uploading: ${uploadedMB}MB / ${totalMB}MB (chunk ${i + 1}/${totalChunks})`);
    }

    // Clean up resume key on success
    localStorage.removeItem(resumeKey);
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
        <div className="flex items-center gap-2 mt-2">
          <span className="inline-flex items-center gap-1.5 bg-blue-900/30 border border-blue-800/50 text-blue-300 text-xs px-2.5 py-1 rounded-full">
            Chunked upload — auto-resumes on network failure &middot; up to 56 GB
          </span>
        </div>
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

            {/* Transcoding Preset */}
            <div className="space-y-2">
              <Label htmlFor="preset" className="text-gray-300">
                Transcoding Quality
              </Label>
              <Select value={transcodingPreset} onValueChange={setTranscodingPreset} disabled={uploading}>
                <SelectTrigger className="bg-gray-800 border-gray-700 text-white" data-testid="upload-preset-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-900 border-gray-700">
                  <SelectItem value="default" className="text-white" data-testid="preset-default">
                    Use library default ({presets.find((p) => p.key === defaultPreset)?.label || defaultPreset})
                  </SelectItem>
                  {presets.map((p) => (
                    <SelectItem key={p.key} value={p.key} className="text-white" data-testid={`preset-${p.key}`}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500">
                {transcodingPreset === "default"
                  ? presets.find((p) => p.key === defaultPreset)?.description
                  : presets.find((p) => p.key === transcodingPreset)?.description}
              </p>
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
