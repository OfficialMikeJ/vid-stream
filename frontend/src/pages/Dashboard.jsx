import { useState, useEffect } from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import { Film, FolderOpen, Upload, Settings, LogOut, Video } from "lucide-react";
import { Button } from "@/components/ui/button";
import VideoLibrary from "../components/VideoLibrary";
import UploadVideo from "../components/UploadVideo";
import VideoSettings from "../components/VideoSettings";
import FolderManagement from "../components/FolderManagement";
import Footer from "../components/Footer";

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
    <div className="min-h-screen bg-gray-950">
      <div className="flex h-screen">
        {/* Sidebar */}
        <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
          <div className="p-6 border-b border-gray-800">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                <Film className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">StreamHost</h1>
                <p className="text-xs text-gray-500">Admin Panel</p>
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
                        ? "bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20"
                        : "text-gray-400 hover:text-white hover:bg-gray-800"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {item.label}
                  </Button>
                </Link>
              );
            })}
          </nav>

          <div className="p-4 border-t border-gray-800">
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
        <main className="flex-1 overflow-auto bg-gray-950 pb-16">
          <Routes>
            <Route path="/" element={<VideoLibrary />} />
            <Route path="/upload" element={<UploadVideo />} />
            <Route path="/folders" element={<FolderManagement />} />
            <Route path="/settings" element={<VideoSettings />} />
          </Routes>
        </main>
      </div>
      <Footer />
    </div>
  );
};

export default Dashboard;
