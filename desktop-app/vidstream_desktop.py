#!/usr/bin/env python3
"""
VidStream Desktop Application
A modern Python desktop client for VidStream video hosting service
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import threading
from datetime import datetime

# Load environment variables
load_dotenv()

class VidStreamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VidStream Desktop")
        self.root.geometry("1200x800")
        
        # API Configuration
        self.api_url = os.getenv("VIDSTREAM_API_URL", "http://localhost:8001")
        self.token = None
        self.current_user = None
        
        # Apply dark theme
        style = ttk.Style("darkly")
        
        # Initialize UI
        self.create_login_screen()
        
    def create_login_screen(self):
        """Create login interface"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Login Frame
        login_frame = ttk.Frame(self.root)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo/Title
        title = ttk.Label(
            login_frame,
            text="VidStream",
            font=("Helvetica", 32, "bold"),
            bootstyle="primary"
        )
        title.pack(pady=20)
        
        subtitle = ttk.Label(
            login_frame,
            text="Desktop Application",
            font=("Helvetica", 14)
        )
        subtitle.pack(pady=(0, 40))
        
        # Username
        ttk.Label(login_frame, text="Username:", font=("Helvetica", 11)).pack(anchor="w", pady=(10, 5))
        self.username_entry = ttk.Entry(login_frame, width=30, font=("Helvetica", 11))
        self.username_entry.pack(pady=(0, 15))
        
        # Password
        ttk.Label(login_frame, text="Password:", font=("Helvetica", 11)).pack(anchor="w", pady=(10, 5))
        self.password_entry = ttk.Entry(login_frame, width=30, show="•", font=("Helvetica", 11))
        self.password_entry.pack(pady=(0, 25))
        
        # Login Button
        login_btn = ttk.Button(
            login_frame,
            text="Sign In",
            command=self.login,
            bootstyle="primary",
            width=20
        )
        login_btn.pack(pady=10)
        
        # Bind Enter key
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        # Status Label
        self.login_status = ttk.Label(login_frame, text="", font=("Helvetica", 10))
        self.login_status.pack(pady=10)
        
    def login(self):
        """Handle login"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            self.login_status.config(text="Please enter username and password", bootstyle="danger")
            return
        
        self.login_status.config(text="Signing in...", bootstyle="info")
        self.root.update()
        
        try:
            response = requests.post(
                f"{self.api_url}/api/auth/login",
                json={"username": username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.current_user = username
                
                # Check if password change required
                if data.get("must_change_password"):
                    messagebox.showinfo(
                        "Password Change Required",
                        "Please change your password through the web interface first."
                    )
                    return
                
                self.create_main_interface()
            else:
                error_msg = response.json().get("detail", "Login failed")
                self.login_status.config(text=error_msg, bootstyle="danger")
        except requests.exceptions.RequestException as e:
            self.login_status.config(text=f"Connection error: {str(e)}", bootstyle="danger")
    
    def create_main_interface(self):
        """Create main application interface"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        sidebar = ttk.Frame(main_container, width=200, bootstyle="dark")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # Logo in sidebar
        logo = ttk.Label(
            sidebar,
            text="VidStream",
            font=("Helvetica", 18, "bold"),
            bootstyle="inverse-primary"
        )
        logo.pack(pady=20)
        
        # Navigation buttons
        self.nav_buttons = []
        
        nav_items = [
            ("📚 Video Library", self.show_library),
            ("⬆️ Upload Video", self.show_upload),
            ("📁 Folders", self.show_folders),
            ("⚙️ Settings", self.show_settings),
        ]
        
        for text, command in nav_items:
            btn = ttk.Button(
                sidebar,
                text=text,
                command=command,
                bootstyle="secondary",
                width=25
            )
            btn.pack(pady=5, padx=10, fill="x")
            self.nav_buttons.append(btn)
        
        # Logout button
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=20)
        logout_btn = ttk.Button(
            sidebar,
            text="🚪 Logout",
            command=self.logout,
            bootstyle="danger",
            width=25
        )
        logout_btn.pack(pady=5, padx=10, side="bottom")
        
        # Main content area
        self.content_frame = ttk.Frame(main_container)
        self.content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Show library by default
        self.show_library()
    
    def show_library(self):
        """Show video library"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title = ttk.Label(
            self.content_frame,
            text="Video Library",
            font=("Helvetica", 24, "bold")
        )
        title.pack(pady=20, anchor="w")
        
        # Refresh button
        refresh_btn = ttk.Button(
            self.content_frame,
            text="🔄 Refresh",
            command=self.load_videos,
            bootstyle="info"
        )
        refresh_btn.pack(pady=10, anchor="e")
        
        # Videos container with scrollbar
        videos_container = ttk.Frame(self.content_frame)
        videos_container.pack(fill="both", expand=True)
        
        # Create canvas for scrolling
        canvas = tk.Canvas(videos_container, bg="#2b3e50", highlightthickness=0)
        scrollbar = ttk.Scrollbar(videos_container, orient="vertical", command=canvas.yview)
        self.videos_frame = ttk.Frame(canvas)
        
        self.videos_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.videos_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load videos
        self.load_videos()
    
    def load_videos(self):
        """Load videos from API"""
        # Clear current videos
        for widget in self.videos_frame.winfo_children():
            widget.destroy()
        
        # Show loading
        loading = ttk.Label(
            self.videos_frame,
            text="Loading videos...",
            font=("Helvetica", 14)
        )
        loading.pack(pady=50)
        self.root.update()
        
        try:
            response = requests.get(
                f"{self.api_url}/api/videos",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            loading.destroy()
            
            if response.status_code == 200:
                videos = response.json()
                
                if not videos:
                    no_videos = ttk.Label(
                        self.videos_frame,
                        text="No videos yet. Upload your first video!",
                        font=("Helvetica", 14)
                    )
                    no_videos.pack(pady=50)
                else:
                    # Display videos in grid
                    for i, video in enumerate(videos):
                        self.create_video_card(video, i)
            else:
                error = ttk.Label(
                    self.videos_frame,
                    text="Failed to load videos",
                    bootstyle="danger"
                )
                error.pack(pady=50)
        except Exception as e:
            loading.destroy()
            error = ttk.Label(
                self.videos_frame,
                text=f"Error: {str(e)}",
                bootstyle="danger"
            )
            error.pack(pady=50)
    
    def create_video_card(self, video, index):
        """Create video card widget"""
        card = ttk.Frame(self.videos_frame, bootstyle="secondary")
        card.pack(fill="x", padx=10, pady=10)
        
        # Video info
        info_frame = ttk.Frame(card)
        info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        
        # Title
        title = ttk.Label(
            info_frame,
            text=video["title"],
            font=("Helvetica", 14, "bold")
        )
        title.pack(anchor="w")
        
        # Description
        if video.get("description"):
            desc = ttk.Label(
                info_frame,
                text=video["description"][:100] + "..." if len(video.get("description", "")) > 100 else video.get("description", ""),
                font=("Helvetica", 10)
            )
            desc.pack(anchor="w", pady=(5, 10))
        
        # Metadata
        metadata = []
        if video.get("duration"):
            mins = int(video["duration"] // 60)
            secs = int(video["duration"] % 60)
            metadata.append(f"⏱️ {mins}:{secs:02d}")
        
        if video.get("processing_status"):
            status = video["processing_status"]
            status_emoji = "✅" if status == "ready" else "⏳" if status == "processing" else "❌"
            metadata.append(f"{status_emoji} {status.title()}")
        
        if metadata:
            meta_text = ttk.Label(
                info_frame,
                text=" | ".join(metadata),
                font=("Helvetica", 9)
            )
            meta_text.pack(anchor="w")
        
        # Actions
        actions_frame = ttk.Frame(card)
        actions_frame.pack(side="right", padx=15, pady=15)
        
        if video.get("processing_status") == "ready":
            play_btn = ttk.Button(
                actions_frame,
                text="▶️ Play",
                command=lambda v=video: self.play_video(v),
                bootstyle="success"
            )
            play_btn.pack(pady=2)
        
        delete_btn = ttk.Button(
            actions_frame,
            text="🗑️ Delete",
            command=lambda v=video: self.delete_video(v),
            bootstyle="danger"
        )
        delete_btn.pack(pady=2)
    
    def play_video(self, video):
        """Open video player"""
        stream_url = f"{self.api_url}/api/stream/hls/{video['id']}/playlist.m3u8"
        messagebox.showinfo(
            "Video Stream",
            f"Stream URL:\n{stream_url}\n\nOpen this URL in VLC or any HLS-compatible player."
        )
    
    def delete_video(self, video):
        """Delete video"""
        if messagebox.askyesno("Confirm Delete", f"Delete '{video['title']}'?"):
            try:
                response = requests.delete(
                    f"{self.api_url}/api/videos/{video['id']}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Video deleted successfully")
                    self.load_videos()
                else:
                    messagebox.showerror("Error", "Failed to delete video")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def show_upload(self):
        """Show upload interface"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title = ttk.Label(
            self.content_frame,
            text="Upload Video",
            font=("Helvetica", 24, "bold")
        )
        title.pack(pady=20, anchor="w")
        
        # Upload form
        form_frame = ttk.Frame(self.content_frame)
        form_frame.pack(fill="both", expand=True, padx=50, pady=20)
        
        # File selection
        ttk.Label(form_frame, text="Video File:", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(10, 5))
        
        file_frame = ttk.Frame(form_frame)
        file_frame.pack(fill="x", pady=(0, 20))
        
        self.file_path_var = tk.StringVar(value="No file selected")
        file_label = ttk.Label(file_frame, textvariable=self.file_path_var, font=("Helvetica", 10))
        file_label.pack(side="left", fill="x", expand=True)
        
        browse_btn = ttk.Button(
            file_frame,
            text="Browse...",
            command=self.browse_file,
            bootstyle="info"
        )
        browse_btn.pack(side="right", padx=(10, 0))
        
        # Title
        ttk.Label(form_frame, text="Title:", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(10, 5))
        self.title_entry = ttk.Entry(form_frame, font=("Helvetica", 11))
        self.title_entry.pack(fill="x", pady=(0, 20))
        
        # Description
        ttk.Label(form_frame, text="Description:", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(10, 5))
        self.description_text = tk.Text(form_frame, height=4, font=("Helvetica", 11))
        self.description_text.pack(fill="x", pady=(0, 20))
        
        # Upload button
        self.upload_btn = ttk.Button(
            form_frame,
            text="⬆️ Upload Video",
            command=self.upload_video,
            bootstyle="primary",
            width=20
        )
        self.upload_btn.pack(pady=20)
        
        # Progress
        self.upload_progress = ttk.Progressbar(
            form_frame,
            mode="indeterminate",
            bootstyle="success"
        )
        self.upload_status = ttk.Label(form_frame, text="", font=("Helvetica", 10))
    
    def browse_file(self):
        """Browse for video file"""
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv *.mpeg *.mpg"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            self.file_path_var.set(filename)
            # Set title from filename if empty
            if not self.title_entry.get():
                title = Path(filename).stem
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, title)
    
    def upload_video(self):
        """Upload video to server"""
        file_path = self.file_path_var.get()
        title = self.title_entry.get().strip()
        description = self.description_text.get("1.0", tk.END).strip()
        
        if file_path == "No file selected":
            messagebox.showerror("Error", "Please select a video file")
            return
        
        if not title:
            messagebox.showerror("Error", "Please enter a title")
            return
        
        # Check file size (56GB max)
        file_size = os.path.getsize(file_path)
        max_size = 56 * 1024 * 1024 * 1024
        if file_size > max_size:
            messagebox.showerror("Error", "File too large. Maximum size is 56GB.")
            return
        
        # Show progress
        self.upload_btn.config(state="disabled")
        self.upload_progress.pack(fill="x", pady=10)
        self.upload_progress.start()
        self.upload_status.config(text="Uploading...")
        self.upload_status.pack()
        
        # Upload in thread
        thread = threading.Thread(
            target=self._upload_thread,
            args=(file_path, title, description)
        )
        thread.daemon = True
        thread.start()
    
    def _upload_thread(self, file_path, title, description):
        """Upload thread"""
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                data = {
                    "title": title,
                    "description": description
                }
                
                response = requests.post(
                    f"{self.api_url}/api/videos/upload",
                    headers={"Authorization": f"Bearer {self.token}"},
                    files=files,
                    data=data,
                    timeout=3600  # 1 hour for large files
                )
            
            self.root.after(0, self._upload_complete, response)
        except Exception as e:
            self.root.after(0, self._upload_error, str(e))
    
    def _upload_complete(self, response):
        """Handle upload completion"""
        self.upload_progress.stop()
        self.upload_progress.pack_forget()
        self.upload_btn.config(state="normal")
        
        if response.status_code == 200:
            self.upload_status.config(text="✅ Upload successful! Processing started.", bootstyle="success")
            messagebox.showinfo("Success", "Video uploaded successfully! Processing will begin shortly.")
            
            # Clear form
            self.file_path_var.set("No file selected")
            self.title_entry.delete(0, tk.END)
            self.description_text.delete("1.0", tk.END)
        else:
            error_msg = response.json().get("detail", "Upload failed")
            self.upload_status.config(text=f"❌ {error_msg}", bootstyle="danger")
    
    def _upload_error(self, error_msg):
        """Handle upload error"""
        self.upload_progress.stop()
        self.upload_progress.pack_forget()
        self.upload_btn.config(state="normal")
        self.upload_status.config(text=f"❌ Error: {error_msg}", bootstyle="danger")
    
    def show_folders(self):
        """Show folders interface"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        title = ttk.Label(
            self.content_frame,
            text="Folders",
            font=("Helvetica", 24, "bold")
        )
        title.pack(pady=20, anchor="w")
        
        # Coming soon message
        ttk.Label(
            self.content_frame,
            text="Folder management coming soon!",
            font=("Helvetica", 14)
        ).pack(pady=50)
    
    def show_settings(self):
        """Show settings interface"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        title = ttk.Label(
            self.content_frame,
            text="Settings",
            font=("Helvetica", 24, "bold")
        )
        title.pack(pady=20, anchor="w")
        
        # Settings frame
        settings_frame = ttk.Frame(self.content_frame)
        settings_frame.pack(fill="both", expand=True, padx=50, pady=20)
        
        # API URL
        ttk.Label(settings_frame, text="API URL:", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(10, 5))
        api_label = ttk.Label(settings_frame, text=self.api_url, font=("Helvetica", 10))
        api_label.pack(anchor="w", pady=(0, 20))
        
        # User info
        ttk.Label(settings_frame, text="Logged in as:", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(10, 5))
        user_label = ttk.Label(settings_frame, text=self.current_user, font=("Helvetica", 10))
        user_label.pack(anchor="w", pady=(0, 20))
    
    def logout(self):
        """Logout user"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.token = None
            self.current_user = None
            self.create_login_screen()

def main():
    root = ttk.Window(themename="darkly")
    app = VidStreamApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
