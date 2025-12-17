import { useState } from "react";
import axios from "axios";
import { API } from "../App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Film, Lock, User } from "lucide-react";
import Footer from "../components/Footer";

const LoginPage = ({ onLogin }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [mustChangePassword, setMustChangePassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, {
        username,
        password,
      });

      if (response.data.must_change_password) {
        setMustChangePassword(true);
        setCurrentPassword(password);
        localStorage.setItem("token", response.data.access_token);
        axios.defaults.headers.common["Authorization"] = `Bearer ${response.data.access_token}`;
        toast.info("Please change your password to continue");
      } else {
        onLogin(response.data.access_token, false);
        toast.success("Login successful!");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    if (newPassword.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }

    setLoading(true);

    try {
      await axios.post(`${API}/auth/change-password`, {
        current_password: currentPassword,
        new_password: newPassword,
      });

      toast.success("Password changed successfully!");
      onLogin(localStorage.getItem("token"), false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Password change failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 p-4 pb-20">
      <Card className="w-full max-w-md bg-gray-900 border-gray-800 shadow-2xl relative z-10" data-testid="login-card">
        <CardHeader className="space-y-3 text-center">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/30">
            <Film className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-3xl font-bold text-white">
            {mustChangePassword ? "Change Password" : "StreamHost Admin"}
          </CardTitle>
          <CardDescription className="text-gray-400">
            {mustChangePassword
              ? "Please set a new password to continue"
              : "Sign in to manage your video hosting service"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!mustChangePassword ? (
            <form onSubmit={handleLogin} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-gray-300 font-medium">
                  Username
                </Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <Input
                    id="username"
                    data-testid="username-input"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="pl-10 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500 focus:border-blue-500 focus:ring-blue-500 h-12"
                    placeholder="Enter username"
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-gray-300 font-medium">
                  Password
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <Input
                    id="password"
                    data-testid="password-input"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500 focus:border-blue-500 focus:ring-blue-500 h-12"
                    placeholder="Enter password"
                    required
                  />
                </div>
              </div>
              <Button
                type="submit"
                data-testid="login-button"
                className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-lg shadow-blue-500/20 transition-all duration-200"
                disabled={loading}
              >
                {loading ? "Signing in..." : "Sign In"}
              </Button>
            </form>
          ) : (
            <form onSubmit={handlePasswordChange} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="new-password" className="text-gray-300 font-medium">
                  New Password
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <Input
                    id="new-password"
                    data-testid="new-password-input"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="pl-10 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500 focus:border-blue-500 focus:ring-blue-500 h-12"
                    placeholder="Enter new password"
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm-password" className="text-gray-300 font-medium">
                  Confirm Password
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <Input
                    id="confirm-password"
                    data-testid="confirm-password-input"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="pl-10 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500 focus:border-blue-500 focus:ring-blue-500 h-12"
                    placeholder="Confirm new password"
                    required
                  />
                </div>
              </div>
              <Button
                type="submit"
                data-testid="change-password-button"
                className="w-full h-12 bg-green-600 hover:bg-green-700 text-white font-semibold shadow-lg shadow-green-500/20 transition-all duration-200"
                disabled={loading}
              >
                {loading ? "Changing Password..." : "Change Password"}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
      <Footer />
    </div>
  );
};

export default LoginPage;
