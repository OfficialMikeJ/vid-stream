import { useState, useEffect } from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import { Film, FolderOpen, Upload, Settings, LogOut, Video } from "lucide-react";
import { Button } from "@/components/ui/button";
import VideoLibrary from "../components/VideoLibrary";
import UploadVideo from "../components/UploadVideo";
import VideoSettings from "../components/VideoSettings";
import FolderManagement from "../components/FolderManagement";

const Dashboard = ({ onLogout }) => {
  const location = useLocation();
  const [activeTab, setActiveTab] = useState("library");

  useEffect(() => {
    const path = location.pathname.split("/")[1] || "library";
    setActiveTab(path);
  }, [location]);

  const navItems = [
    { id: "library", label: "Video Library", icon: Video, path: "/" },
    { id: "upload", label: "Upload", icon: Upload, path: "/upload" },
    { id: "folders", label: "Folders", icon: FolderOpen, path: "/folders" },
    { id: "settings", label: "Settings", icon: Settings, path: "/settings" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-950">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-20"></div>

      <div className="relative z-10 flex h-screen">
        {/* Sidebar */}
        <aside className="w-64 bg-black/20 backdrop-blur-xl border-r border-white/10 flex flex-col">
          <div className="p-6 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/50">
                <Film className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">StreamHost</h1>
                <p className="text-xs text-slate-400">Admin Panel</p>
              </div>
            </div>
          </div>

          <nav className="flex-1 p-4 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <Link key={item.id} to={item.path}>
                  <Button
                    data-testid={`nav-${item.id}`}
                    variant={isActive ? "default" : "ghost"}
                    className={`w-full justify-start gap-3 h-12 transition-all duration-200 ${
                      isActive
                        ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/30"
                        : "text-slate-300 hover:text-white hover:bg-white/5"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {item.label}
                  </Button>
                </Link>
              );
            })}
          </nav>

          <div className="p-4 border-t border-white/10">
            <Button
              data-testid="logout-button"
              onClick={onLogout}
              variant="ghost"
              className="w-full justify-start gap-3 h-12 text-red-400 hover:text-red-300 hover:bg-red-500/10"
            >
              <LogOut className="w-5 h-5" />
              Logout
            </Button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<VideoLibrary />} />
            <Route path="/upload" element={<UploadVideo />} />
            <Route path="/folders" element={<FolderManagement />} />
            <Route path="/settings" element={<VideoSettings />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
