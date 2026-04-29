import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { MessageSquare, Trash2, Send, Loader2 } from "lucide-react";

const formatRelative = (iso) => {
  if (!iso) return "";
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 30 * 86400) return `${Math.floor(diff / 86400)}d ago`;
  return new Date(iso).toLocaleDateString();
};

const VideoComments = ({ videoId, currentUsername, currentUserRole = "viewer" }) => {
  const [comments, setComments] = useState([]);
  const [body, setBody] = useState("");
  const [posting, setPosting] = useState(false);
  const [loading, setLoading] = useState(true);
  const isAdmin = currentUserRole === "admin";

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/videos/${videoId}/comments`);
      setComments(r.data.items || []);
    } catch {
      // 404 means video not found — should not happen if we got here
    } finally {
      setLoading(false);
    }
  }, [videoId]);

  useEffect(() => {
    load();
  }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    const text = body.trim();
    if (!text) return;
    setPosting(true);
    try {
      const r = await axios.post(`${API}/videos/${videoId}/comments`, { body: text });
      setComments((prev) => [r.data, ...prev]);
      setBody("");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to post comment");
    } finally {
      setPosting(false);
    }
  };

  const remove = async (commentId) => {
    if (!window.confirm("Delete this comment?")) return;
    try {
      await axios.delete(`${API}/videos/${videoId}/comments/${commentId}`);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
      toast.success("Comment removed");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to delete");
    }
  };

  return (
    <div className="border-t border-gray-800 pt-4 mt-2" data-testid="comments-section">
      <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
        <MessageSquare className="w-4 h-4" />
        Comments
        <Badge className="bg-gray-800 text-gray-400 ml-1">{comments.length}</Badge>
      </h3>

      <form onSubmit={submit} className="mb-4 space-y-2" data-testid="comment-form">
        <Textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Add a comment..."
          maxLength={2000}
          rows={2}
          className="bg-gray-800 border-gray-700 text-white text-sm resize-none"
          data-testid="comment-input"
          disabled={posting}
        />
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-500">{body.length}/2000</span>
          <Button
            type="submit"
            size="sm"
            data-testid="comment-submit"
            disabled={posting || !body.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            {posting ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Send className="w-4 h-4 mr-1" />}
            Post
          </Button>
        </div>
      </form>

      {loading ? (
        <div className="text-sm text-gray-500 py-4">Loading comments...</div>
      ) : comments.length === 0 ? (
        <div className="text-sm text-gray-500 py-4 text-center" data-testid="comments-empty">
          No comments yet. Be the first to share your thoughts.
        </div>
      ) : (
        <div className="space-y-3 max-h-72 overflow-y-auto pr-2" data-testid="comments-list">
          {comments.map((c) => {
            const canDelete = isAdmin || c.username === currentUsername;
            return (
              <div
                key={c.id}
                className="bg-gray-800/50 rounded-lg p-3 border border-gray-800"
                data-testid={`comment-${c.id}`}
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-blue-300">{c.username}</span>
                    {c.user_role === "admin" && (
                      <Badge className="bg-blue-600/30 text-blue-300 text-xs px-1.5 py-0">Admin</Badge>
                    )}
                    <span className="text-xs text-gray-500">{formatRelative(c.created_at)}</span>
                  </div>
                  {canDelete && (
                    <button
                      onClick={() => remove(c.id)}
                      data-testid={`comment-delete-${c.id}`}
                      className="text-gray-500 hover:text-red-400 transition-colors"
                      aria-label="Delete comment"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
                <p className="text-sm text-gray-200 whitespace-pre-wrap break-words">{c.body}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default VideoComments;
