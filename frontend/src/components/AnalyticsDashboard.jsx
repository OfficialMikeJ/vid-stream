import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import {
  BarChart3,
  Eye,
  Users,
  Clock,
  HardDrive,
  Video as VideoIcon,
  Activity,
  TrendingUp,
} from "lucide-react";

const formatBytes = (n) => {
  if (!n) return "0 B";
  const u = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  while (n >= 1024 && i < u.length - 1) {
    n /= 1024;
    i++;
  }
  return `${n.toFixed(1)} ${u[i]}`;
};

const formatDuration = (s) => {
  if (!s) return "0m";
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
};

const formatRelative = (iso) => {
  if (!iso) return "—";
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
};

const StatCard = ({ icon: Icon, label, value, accent = "blue", testid }) => {
  const colors = {
    blue: "text-blue-400 bg-blue-500/10",
    green: "text-green-400 bg-green-500/10",
    orange: "text-orange-400 bg-orange-500/10",
    purple: "text-purple-400 bg-purple-500/10",
    red: "text-red-400 bg-red-500/10",
    cyan: "text-cyan-400 bg-cyan-500/10",
  };
  return (
    <Card className="bg-gray-900 border-gray-800" data-testid={testid}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
            <p className="text-2xl font-bold text-white mt-2">{value}</p>
          </div>
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors[accent]}`}>
            <Icon className="w-5 h-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const TimelineChart = ({ series }) => {
  if (!series || series.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
        No view data yet — share a video to start collecting stats.
      </div>
    );
  }
  const max = Math.max(1, ...series.map((d) => d.views));
  return (
    <div className="space-y-2" data-testid="timeline-chart">
      <div className="flex items-end gap-1 h-48">
        {series.map((d) => {
          const h = (d.views / max) * 100;
          return (
            <div
              key={d.date}
              className="flex-1 flex flex-col items-center justify-end group relative"
              title={`${d.date}: ${d.views} views`}
            >
              <div
                className="w-full bg-gradient-to-t from-blue-600 to-blue-400 rounded-t transition-all hover:from-blue-500 hover:to-blue-300"
                style={{ height: `${Math.max(h, d.views > 0 ? 4 : 1)}%`, minHeight: d.views > 0 ? "4px" : "1px" }}
              />
              <div className="absolute -top-7 hidden group-hover:block bg-gray-800 text-white text-xs px-2 py-1 rounded shadow-lg z-10">
                {d.views}
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex justify-between text-xs text-gray-500">
        <span>{series[0].date}</span>
        <span>{series[series.length - 1].date}</span>
      </div>
    </div>
  );
};

const AnalyticsDashboard = () => {
  const [overview, setOverview] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [topVideos, setTopVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState("30");
  const [sort, setSort] = useState("views");

  const load = async () => {
    setLoading(true);
    try {
      const [ov, tl, vids] = await Promise.all([
        axios.get(`${API}/analytics/overview`),
        axios.get(`${API}/analytics/timeline?days=${days}`),
        axios.get(`${API}/analytics/videos?sort=${sort}&limit=20`),
      ]);
      setOverview(ov.data);
      setTimeline(tl.data);
      setTopVideos(vids.data.items || []);
    } catch (e) {
      toast.error("Failed to load analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [days, sort]); // eslint-disable-line

  return (
    <div className="p-8 max-w-7xl mx-auto" data-testid="analytics-page">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-blue-400" />
            Analytics
          </h1>
          <p className="text-gray-400 mt-1">Track views, viewers, and storage across your library.</p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={Eye}
          label="Total Views"
          value={overview ? overview.total_views.toLocaleString() : "—"}
          accent="blue"
          testid="stat-total-views"
        />
        <StatCard
          icon={Users}
          label="Unique Viewers"
          value={overview ? overview.unique_viewers.toLocaleString() : "—"}
          accent="green"
          testid="stat-unique-viewers"
        />
        <StatCard
          icon={Activity}
          label="Views (24h)"
          value={overview ? overview.views_24h.toLocaleString() : "—"}
          accent="orange"
          testid="stat-views-24h"
        />
        <StatCard
          icon={VideoIcon}
          label="Videos"
          value={overview ? `${overview.ready_videos} / ${overview.total_videos}` : "—"}
          accent="purple"
          testid="stat-videos"
        />
        <StatCard
          icon={HardDrive}
          label="Storage Used"
          value={overview ? formatBytes(overview.storage_bytes) : "—"}
          accent="cyan"
          testid="stat-storage"
        />
        <StatCard
          icon={Clock}
          label="Total Duration"
          value={overview ? formatDuration(overview.total_duration_seconds) : "—"}
          accent="red"
          testid="stat-duration"
        />
      </div>

      {/* Timeline chart */}
      <Card className="bg-gray-900 border-gray-800 mb-8">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-400" />
                Views Over Time
              </h2>
              <p className="text-sm text-gray-500 mt-1">Daily view counts across all videos.</p>
            </div>
            <Select value={days} onValueChange={setDays}>
              <SelectTrigger className="w-32 bg-gray-800 border-gray-700 text-white" data-testid="timeline-range">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="7">Last 7 days</SelectItem>
                <SelectItem value="30">Last 30 days</SelectItem>
                <SelectItem value="90">Last 90 days</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {loading && !timeline ? (
            <div className="h-48 flex items-center justify-center text-gray-500">Loading...</div>
          ) : (
            <TimelineChart series={timeline?.series || []} />
          )}
        </CardContent>
      </Card>

      {/* Top videos table */}
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white">Top Videos</h2>
              <p className="text-sm text-gray-500 mt-1">Your most-watched content.</p>
            </div>
            <Select value={sort} onValueChange={setSort}>
              <SelectTrigger className="w-40 bg-gray-800 border-gray-700 text-white" data-testid="topvideos-sort">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="views">Most viewed</SelectItem>
                <SelectItem value="unique">Most unique viewers</SelectItem>
                <SelectItem value="recent">Recently watched</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {topVideos.length === 0 ? (
            <div className="text-center py-12 text-gray-500" data-testid="topvideos-empty">
              <VideoIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No views recorded yet.</p>
              <p className="text-xs mt-1">Stats appear once viewers start watching.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full" data-testid="topvideos-table">
                <thead>
                  <tr className="border-b border-gray-800 text-left text-xs uppercase text-gray-500">
                    <th className="pb-3 pr-4">#</th>
                    <th className="pb-3 pr-4">Title</th>
                    <th className="pb-3 pr-4 text-right">Views</th>
                    <th className="pb-3 pr-4 text-right">Unique</th>
                    <th className="pb-3 text-right">Last viewed</th>
                  </tr>
                </thead>
                <tbody className="text-sm">
                  {topVideos.map((v, i) => (
                    <tr
                      key={v.video_id}
                      className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
                      data-testid={`topvideo-row-${i}`}
                    >
                      <td className="py-3 pr-4 text-gray-500">{i + 1}</td>
                      <td className="py-3 pr-4 text-white truncate max-w-md">{v.title}</td>
                      <td className="py-3 pr-4 text-right text-blue-300 font-mono">{v.views}</td>
                      <td className="py-3 pr-4 text-right text-green-300 font-mono">{v.unique_viewers}</td>
                      <td className="py-3 text-right text-gray-400">{formatRelative(v.last_viewed)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsDashboard;
