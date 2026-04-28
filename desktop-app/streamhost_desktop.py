#!/usr/bin/env python3
"""
StreamHost Desktop Application
A modern Python desktop client for StreamHost video hosting service
Version: 2025.12.17
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

APP_VERSION = "2025.12.17"
APP_NAME = "StreamHost"

class StreamHostApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} Desktop")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # API Configuration
        self.api_url = os.getenv("STREAMHOST_API_URL", "http://localhost:8001")
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
            
        # Main container with footer
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)
        
        # Login Frame
        login_frame = ttk.Frame(main_frame)
        login_frame.place(relx=0.5, rely=0.45, anchor="center")
        
        # Logo/Title
        title = ttk.Label(
            login_frame,
            text=APP_NAME,
            font=("Helvetica", 36, "bold"),
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
        self.username_entry = ttk.Entry(login_frame, width=35, font=("Helvetica", 11))
        self.username_entry.pack(pady=(0, 15))
        
        # Password
        ttk.Label(login_frame, text="Password:", font=("Helvetica", 11)).pack(anchor="w", pady=(10, 5))
        self.password_entry = ttk.Entry(login_frame, width=35, show="•", font=("Helvetica", 11))
        self.password_entry.pack(pady=(0, 25))
        
        # Login Button
        login_btn = ttk.Button(
            login_frame,
            text="Sign In",
            command=self.login,
            bootstyle="primary",
            width=25
        )
        login_btn.pack(pady=10)
        
        # Bind Enter key
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        # Status Label
        self.login_status = ttk.Label(login_frame, text="", font=("Helvetica", 10))
        self.login_status.pack(pady=10)
        
        # Footer
        self.create_footer(main_frame)
        
    def create_footer(self, parent):
        """Create footer with copyright and version"""
        footer_frame = ttk.Frame(parent)
        footer_frame.pack(side="bottom", fill="x", pady=10)
        
        footer_text = ttk.Label(
            footer_frame,
            text=f"Copyright 2026 {APP_NAME}  |  {APP_NAME} Ver: {APP_VERSION}",
            font=("Helvetica", 9),
            bootstyle="secondary"
        )
        footer_text.pack()
        
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
                    self.create_password_change_screen(password)
                else:
                    self.create_main_interface()
            else:
                error_msg = response.json().get("detail", "Login failed")
                self.login_status.config(text=error_msg, bootstyle="danger")
        except requests.exceptions.RequestException as e:
            self.login_status.config(text=f"Connection error: {str(e)}", bootstyle="danger")
    
    def create_password_change_screen(self, current_password):
        """Create password change interface"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container with footer
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)
        
        # Password change frame
        change_frame = ttk.Frame(main_frame)
        change_frame.place(relx=0.5, rely=0.45, anchor="center")
        
        # Title
        title = ttk.Label(
            change_frame,
            text="Change Password",
            font=("Helvetica", 28, "bold"),
            bootstyle="warning"
        )
        title.pack(pady=20)
        
        subtitle = ttk.Label(
            change_frame,
            text="Please set a new password to continue",
            font=("Helvetica", 12)
        )
        subtitle.pack(pady=(0, 30))
        
        # New Password
        ttk.Label(change_frame, text="New Password:", font=("Helvetica", 11)).pack(anchor="w", pady=(10, 5))
        self.new_password_entry = ttk.Entry(change_frame, width=35, show="•", font=("Helvetica", 11))
        self.new_password_entry.pack(pady=(0, 15))
        
        # Confirm Password
        ttk.Label(change_frame, text="Confirm Password:", font=("Helvetica", 11)).pack(anchor="w", pady=(10, 5))
        self.confirm_password_entry = ttk.Entry(change_frame, width=35, show="•", font=("Helvetica", 11))
        self.confirm_password_entry.pack(pady=(0, 25))
        
        # Change Password Button
        change_btn = ttk.Button(
            change_frame,
            text="Change Password",
            command=lambda: self.change_password(current_password),
            bootstyle="success",
            width=25
        )
        change_btn.pack(pady=10)
        
        # Bind Enter key
        self.confirm_password_entry.bind("<Return>", lambda e: self.change_password(current_password))
        
        # Status Label
        self.change_status = ttk.Label(change_frame, text="", font=("Helvetica", 10))
        self.change_status.pack(pady=10)
        
        # Footer
        self.create_footer(main_frame)
    
    def change_password(self, current_password):
        """Handle password change"""
        new_password = self.new_password_entry.get().strip()
        confirm_password = self.confirm_password_entry.get().strip()
        
        if not new_password or not confirm_password:
            self.change_status.config(text="Please fill in all fields", bootstyle="danger")
            return
        
        if new_password != confirm_password:
            self.change_status.config(text="Passwords do not match", bootstyle="danger")
            return
        
        if len(new_password) < 6:
            self.change_status.config(text="Password must be at least 6 characters", bootstyle="danger")
            return
        
        self.change_status.config(text="Changing password...", bootstyle="info")
        self.root.update()
        
        try:
            response = requests.post(
                f"{self.api_url}/api/auth/change-password",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "current_password": current_password,
                    "new_password": new_password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                messagebox.showinfo("Success", "Password changed successfully!")
                self.create_main_interface()
            else:
                error_msg = response.json().get("detail", "Password change failed")
                self.change_status.config(text=error_msg, bootstyle="danger")
        except requests.exceptions.RequestException as e:
            self.change_status.config(text=f"Connection error: {str(e)}", bootstyle="danger")
    
    def create_main_interface(self):
        """Create main application interface"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True)
        
        # Sidebar
        sidebar = ttk.Frame(main_container, width=220, bootstyle="dark")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # Logo in sidebar
        logo_frame = ttk.Frame(sidebar)
        logo_frame.pack(fill="x", pady=20, padx=15)
        
        logo = ttk.Label(
            logo_frame,
            text=f"🎬 {APP_NAME}",
            font=("Helvetica", 18, "bold"),
            bootstyle="inverse-primary"
        )
        logo.pack()
        
        admin_label = ttk.Label(
            logo_frame,
            text="Admin Panel",
            font=("Helvetica", 9),
            bootstyle="secondary"
        )
        admin_label.pack()
        
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=15, pady=10)
        
        # Navigation buttons
        self.nav_buttons = []
        
        nav_items = [
            ("📚 Video Library", self.show_library, "info"),
            ("⬆️ Upload Video", self.show_upload, "success"),
            ("📁 Folders", self.show_folders, "primary"),
            ("⚙️ Settings", self.show_settings, "secondary"),
        ]
        
        for text, command, style in nav_items:
            btn = ttk.Button(
                sidebar,
                text=text,
                command=command,
                bootstyle=style,
                width=25
            )
            btn.pack(pady=5, padx=10, fill="x")
            self.nav_buttons.append(btn)
        
        # Spacer
        spacer = ttk.Frame(sidebar)
        spacer.pack(fill="both", expand=True)
        
        # User info
        user_frame = ttk.Frame(sidebar)
        user_frame.pack(fill="x", padx=15, pady=10)
        
        user_label = ttk.Label(
            user_frame,
            text=f"👤 {self.current_user}",
            font=("Helvetica", 10),
            bootstyle="secondary"
        )
        user_label.pack(anchor="w")
        
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=15, pady=10)
        
        # Logout button
        logout_btn = ttk.Button(
            sidebar,
            text="🚪 Logout",
            command=self.logout,
            bootstyle="danger",
            width=25
        )
        logout_btn.pack(pady=10, padx=10)
        
        # Version in sidebar
        version_label = ttk.Label(
            sidebar,
            text=f"Ver: {APP_VERSION}",
            font=("Helvetica", 8),
            bootstyle="secondary"
        )
        version_label.pack(pady=(5, 15))
        
        # Main content area
        content_wrapper = ttk.Frame(main_container)
        content_wrapper.pack(side="right", fill="both", expand=True)
        
        self.content_frame = ttk.Frame(content_wrapper)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Footer in content area
        footer = ttk.Label(
            content_wrapper,
            text=f"Copyright 2026 {APP_NAME}  |  {APP_NAME} Ver: {APP_VERSION}",
            font=("Helvetica", 9),
            bootstyle="secondary"
        )
        footer.pack(side="bottom", pady=10)
        
        # Show library by default
        self.show_library()
    
    def show_library(self):
        """Show video library"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Header
        header_frame = ttk.Frame(self.content_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title = ttk.Label(
            header_frame,
            text="Video Library",
            font=("Helvetica", 24, "bold")
        )
        title.pack(side="left")
        
        # Refresh button
        refresh_btn = ttk.Button(
            header_frame,
            text="🔄 Refresh",
            command=self.load_videos,
            bootstyle="info"
        )
        refresh_btn.pack(side="right")
        
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
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
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
                    # Display videos
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
        card = ttk.Frame(self.videos_frame, bootstyle="dark")
        card.pack(fill="x", padx=10, pady=8)
        
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
            desc_text = video["description"][:100] + "..." if len(video.get("description", "")) > 100 else video.get("description", "")
            desc = ttk.Label(
                info_frame,
                text=desc_text,
                font=("Helvetica", 10),
                bootstyle="secondary"
            )
            desc.pack(anchor="w", pady=(5, 10))
        
        # Metadata
        metadata = []
        if video.get("duration"):
            mins = int(video["duration"] // 60)
            secs = int(video["duration"] % 60)
            metadata.append(f"⏱️ {mins}:{secs:02d}")
        
        if video.get("file_size"):
            size_mb = video["file_size"] / (1024 * 1024)
            if size_mb >= 1024:
                metadata.append(f"💾 {size_mb/1024:.1f} GB")
            else:
                metadata.append(f"💾 {size_mb:.1f} MB")
        
        if video.get("processing_status"):
            status = video["processing_status"]
            if status == "ready":
                metadata.append("✅ Ready")
            elif status == "processing":
                metadata.append("⏳ Processing")
            else:
                metadata.append(f"❌ {status.title()}")
        
        if metadata:
            meta_text = ttk.Label(
                info_frame,
                text="  |  ".join(metadata),
                font=("Helvetica", 9),
                bootstyle="secondary"
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
                bootstyle="success",
                width=10
            )
            play_btn.pack(pady=3)
            
            embed_btn = ttk.Button(
                actions_frame,
                text="📋 Embed",
                command=lambda v=video: self.show_embed_code(v),
                bootstyle="warning",
                width=10
            )
            embed_btn.pack(pady=3)
        
        delete_btn = ttk.Button(
            actions_frame,
            text="🗑️ Delete",
            command=lambda v=video: self.delete_video(v),
            bootstyle="danger",
            width=10
        )
        delete_btn.pack(pady=3)
    
    def play_video(self, video):
        """Open video player info"""
        stream_url = f"{self.api_url}/api/stream/hls/{video['id']}/playlist.m3u8"
        
        # Create info dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Play: {video['title']}")
        dialog.geometry("500x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(
            dialog,
            text="Stream URL:",
            font=("Helvetica", 12, "bold")
        ).pack(pady=(20, 5))
        
        url_entry = ttk.Entry(dialog, width=60, font=("Helvetica", 10))
        url_entry.insert(0, stream_url)
        url_entry.pack(pady=5, padx=20)
        
        ttk.Label(
            dialog,
            text="Open this URL in VLC or any HLS-compatible player.",
            font=("Helvetica", 10)
        ).pack(pady=10)
        
        def copy_url():
            dialog.clipboard_clear()
            dialog.clipboard_append(stream_url)
            messagebox.showinfo("Copied", "URL copied to clipboard!")
        
        ttk.Button(
            dialog,
            text="📋 Copy URL",
            command=copy_url,
            bootstyle="primary"
        ).pack(pady=10)
    
    def show_embed_code(self, video):
        """Show embed code for video"""
        try:
            response = requests.get(
                f"{self.api_url}/api/embed-code/{video['id']}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                embed_code = response.json().get("embed_code", "")
                
                # Create dialog
                dialog = tk.Toplevel(self.root)
                dialog.title(f"Embed Code: {video['title']}")
                dialog.geometry("600x400")
                dialog.transient(self.root)
                dialog.grab_set()
                
                ttk.Label(
                    dialog,
                    text="Embed Code:",
                    font=("Helvetica", 12, "bold")
                ).pack(pady=(20, 5))
                
                text_widget = tk.Text(dialog, height=15, width=70, font=("Courier", 9))
                text_widget.insert("1.0", embed_code)
                text_widget.config(state="disabled")
                text_widget.pack(pady=10, padx=20)
                
                def copy_code():
                    dialog.clipboard_clear()
                    dialog.clipboard_append(embed_code)
                    messagebox.showinfo("Copied", "Embed code copied to clipboard!")
                
                ttk.Button(
                    dialog,
                    text="📋 Copy Code",
                    command=copy_code,
                    bootstyle="primary"
                ).pack(pady=10)
            else:
                messagebox.showerror("Error", "Failed to get embed code")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
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
        title.pack(pady=(0, 20), anchor="w")
        
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
            text="📁 Browse...",
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
        self.description_text = tk.Text(form_frame, height=4, font=("Helvetica", 11), bg="#2b3e50", fg="white")
        self.description_text.pack(fill="x", pady=(0, 20))
        
        # Folder selection
        ttk.Label(form_frame, text="Folder (Optional):", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(10, 5))
        self.folder_var = tk.StringVar(value="")
        self.folder_combo = ttk.Combobox(form_frame, textvariable=self.folder_var, font=("Helvetica", 11), state="readonly")
        self.folder_combo.pack(fill="x", pady=(0, 20))
        self.load_folders_for_upload()
        
        # Upload button
        self.upload_btn = ttk.Button(
            form_frame,
            text="⬆️ Upload Video",
            command=self.upload_video,
            bootstyle="success",
            width=25
        )
        self.upload_btn.pack(pady=20)
        
        # Progress
        self.upload_progress = ttk.Progressbar(
            form_frame,
            mode="determinate",
            maximum=100,
            bootstyle="success-striped"
        )
        self.upload_progress_label = ttk.Label(form_frame, text="", font=("Helvetica", 10), bootstyle="info")
        self.upload_status = ttk.Label(form_frame, text="", font=("Helvetica", 10))
    
    def load_folders_for_upload(self):
        """Load folders for upload dropdown"""
        try:
            response = requests.get(
                f"{self.api_url}/api/folders",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                folders = response.json()
                folder_names = ["No Folder"] + [f["name"] for f in folders]
                self.folder_combo["values"] = folder_names
                self.folder_combo.current(0)
                self.folders_data = folders
        except:
            self.folder_combo["values"] = ["No Folder"]
            self.folder_combo.current(0)
            self.folders_data = []
    
    def browse_file(self):
        """Browse for video file"""
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv *.mpeg *.mpg *.m4v *.ts"),
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
        """Upload video to server using chunked upload"""
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

        # Get folder ID
        folder_id = None
        folder_selection = self.folder_var.get()
        if folder_selection and folder_selection != "No Folder":
            for f in self.folders_data:
                if f["name"] == folder_selection:
                    folder_id = f["id"]
                    break

        # Show progress UI
        self.upload_btn.config(state="disabled")
        self.upload_progress["value"] = 0
        self.upload_progress.pack(fill="x", pady=5)
        self.upload_progress_label.config(text="Initializing upload...")
        self.upload_progress_label.pack()
        self.upload_status.config(text="")
        self.upload_status.pack()

        # Upload in background thread
        thread = threading.Thread(
            target=self._upload_thread,
            args=(file_path, title, description, folder_id, file_size)
        )
        thread.daemon = True
        thread.start()

    def _upload_thread(self, file_path, title, description, folder_id, file_size):
        """Chunked upload thread — splits file into 5 MB chunks"""
        CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB
        filename = Path(file_path).name
        total_chunks = max(1, -(-file_size // CHUNK_SIZE))  # ceiling division
        total_mb = file_size / (1024 * 1024)

        try:
            # --- Step 1: Initialize upload ---
            self.root.after(0, lambda: self.upload_progress_label.config(text="Initializing upload..."))

            init_data = {
                "filename": filename,
                "title": title,
                "total_size": file_size,
            }
            if description:
                init_data["description"] = description
            if folder_id:
                init_data["folder_id"] = folder_id

            resp = requests.post(
                f"{self.api_url}/api/upload/init",
                headers={"Authorization": f"Bearer {self.token}"},
                data=init_data,
                timeout=30
            )
            resp.raise_for_status()
            upload_id = resp.json()["upload_id"]

            # --- Step 2: Upload chunks ---
            with open(file_path, "rb") as f:
                for i in range(total_chunks):
                    chunk_data = f.read(CHUNK_SIZE)
                    if not chunk_data:
                        break

                    files = {"chunk": (f"chunk_{i}", chunk_data, "application/octet-stream")}
                    data = {
                        "upload_id": upload_id,
                        "chunk_index": i,
                        "total_chunks": total_chunks,
                    }

                    chunk_resp = requests.post(
                        f"{self.api_url}/api/upload/chunk",
                        headers={"Authorization": f"Bearer {self.token}"},
                        data=data,
                        files=files,
                        timeout=120
                    )
                    chunk_resp.raise_for_status()

                    progress = int(((i + 1) / total_chunks) * 100)
                    uploaded_mb = min((i + 1) * CHUNK_SIZE / (1024 * 1024), total_mb)
                    label_text = f"Uploading: {uploaded_mb:.1f} MB / {total_mb:.1f} MB  ({i+1}/{total_chunks} chunks)"

                    # Update UI on main thread
                    self.root.after(0, lambda p=progress, t=label_text: self._update_progress(p, t))

                    result = chunk_resp.json()
                    if result.get("status") == "complete":
                        break

            self.root.after(0, self._upload_complete)

        except Exception as e:
            self.root.after(0, lambda err=str(e): self._upload_error(err))

    def _update_progress(self, value, label_text):
        """Update progress bar and label from main thread"""
        self.upload_progress["value"] = value
        self.upload_progress_label.config(text=label_text)

    def _upload_complete(self):
        """Handle upload completion"""
        self.upload_progress["value"] = 100
        self.upload_progress_label.config(text="Upload complete!")
        self.upload_btn.config(state="normal")
        self.upload_status.config(text="✅ Upload successful! Processing started.", bootstyle="success")
        messagebox.showinfo("Success", "Video uploaded successfully! Processing will begin shortly.")

        # Clear form
        self.file_path_var.set("No file selected")
        self.title_entry.delete(0, tk.END)
        self.description_text.delete("1.0", tk.END)
        self.upload_progress.pack_forget()
        self.upload_progress_label.pack_forget()

    def _upload_error(self, error_msg):
        """Handle upload error"""
        self.upload_progress.pack_forget()
        self.upload_progress_label.pack_forget()
        self.upload_btn.config(state="normal")
        self.upload_status.config(text=f"❌ Error: {error_msg}", bootstyle="danger")
    
    def show_folders(self):
        """Show folders interface"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Header
        header_frame = ttk.Frame(self.content_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title = ttk.Label(
            header_frame,
            text="Folders",
            font=("Helvetica", 24, "bold")
        )
        title.pack(side="left")
        
        # Create folder button
        create_btn = ttk.Button(
            header_frame,
            text="➕ Create Folder",
            command=self.create_folder_dialog,
            bootstyle="success"
        )
        create_btn.pack(side="right")
        
        # Folders container
        self.folders_frame = ttk.Frame(self.content_frame)
        self.folders_frame.pack(fill="both", expand=True)
        
        self.load_folders()
    
    def load_folders(self):
        """Load folders from API"""
        # Clear current folders
        for widget in self.folders_frame.winfo_children():
            widget.destroy()
        
        # Show loading
        loading = ttk.Label(
            self.folders_frame,
            text="Loading folders...",
            font=("Helvetica", 14)
        )
        loading.pack(pady=50)
        self.root.update()
        
        try:
            response = requests.get(
                f"{self.api_url}/api/folders",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            loading.destroy()
            
            if response.status_code == 200:
                folders = response.json()
                
                if not folders:
                    no_folders = ttk.Label(
                        self.folders_frame,
                        text="No folders yet. Create your first folder!",
                        font=("Helvetica", 14)
                    )
                    no_folders.pack(pady=50)
                else:
                    # Display folders in grid
                    for i, folder in enumerate(folders):
                        self.create_folder_card(folder)
            else:
                error = ttk.Label(
                    self.folders_frame,
                    text="Failed to load folders",
                    bootstyle="danger"
                )
                error.pack(pady=50)
        except Exception as e:
            loading.destroy()
            error = ttk.Label(
                self.folders_frame,
                text=f"Error: {str(e)}",
                bootstyle="danger"
            )
            error.pack(pady=50)
    
    def create_folder_card(self, folder):
        """Create folder card widget"""
        card = ttk.Frame(self.folders_frame, bootstyle="dark")
        card.pack(fill="x", padx=10, pady=5)
        
        info_frame = ttk.Frame(card)
        info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        
        # Folder icon and name
        name_label = ttk.Label(
            info_frame,
            text=f"📁 {folder['name']}",
            font=("Helvetica", 14, "bold")
        )
        name_label.pack(anchor="w")
        
        # Created date
        if folder.get("created_at"):
            try:
                created = datetime.fromisoformat(folder["created_at"].replace("Z", "+00:00"))
                date_str = created.strftime("%Y-%m-%d")
            except:
                date_str = "Unknown"
            
            date_label = ttk.Label(
                info_frame,
                text=f"Created: {date_str}",
                font=("Helvetica", 9),
                bootstyle="secondary"
            )
            date_label.pack(anchor="w")
        
        # Delete button
        delete_btn = ttk.Button(
            card,
            text="🗑️",
            command=lambda f=folder: self.delete_folder(f),
            bootstyle="danger",
            width=5
        )
        delete_btn.pack(side="right", padx=15, pady=15)
    
    def create_folder_dialog(self):
        """Show create folder dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Folder")
        dialog.geometry("400x180")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(
            dialog,
            text="Folder Name:",
            font=("Helvetica", 12, "bold")
        ).pack(pady=(20, 5))
        
        name_entry = ttk.Entry(dialog, width=40, font=("Helvetica", 11))
        name_entry.pack(pady=10)
        name_entry.focus()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def create():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a folder name")
                return
            
            try:
                response = requests.post(
                    f"{self.api_url}/api/folders",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={"name": name},
                    timeout=10
                )
                
                if response.status_code == 200:
                    dialog.destroy()
                    messagebox.showinfo("Success", "Folder created successfully")
                    self.load_folders()
                else:
                    messagebox.showerror("Error", "Failed to create folder")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            bootstyle="secondary",
            width=12
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text="Create",
            command=create,
            bootstyle="success",
            width=12
        ).pack(side="left", padx=5)
        
        name_entry.bind("<Return>", lambda e: create())
    
    def delete_folder(self, folder):
        """Delete folder"""
        if messagebox.askyesno("Confirm Delete", f"Delete folder '{folder['name']}'?"):
            try:
                response = requests.delete(
                    f"{self.api_url}/api/folders/{folder['id']}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Folder deleted successfully")
                    self.load_folders()
                else:
                    messagebox.showerror("Error", "Failed to delete folder")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
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
        title.pack(pady=(0, 20), anchor="w")
        
        # Settings frame
        settings_frame = ttk.Frame(self.content_frame)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Connection info
        conn_card = ttk.Frame(settings_frame, bootstyle="dark")
        conn_card.pack(fill="x", pady=10)
        
        ttk.Label(
            conn_card,
            text="🔗 Connection",
            font=("Helvetica", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        ttk.Label(
            conn_card,
            text=f"API URL: {self.api_url}",
            font=("Helvetica", 11)
        ).pack(anchor="w", padx=15, pady=5)
        
        ttk.Label(
            conn_card,
            text=f"Status: Connected ✅",
            font=("Helvetica", 11),
            bootstyle="success"
        ).pack(anchor="w", padx=15, pady=(5, 15))
        
        # User info
        user_card = ttk.Frame(settings_frame, bootstyle="dark")
        user_card.pack(fill="x", pady=10)
        
        ttk.Label(
            user_card,
            text="👤 User",
            font=("Helvetica", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        ttk.Label(
            user_card,
            text=f"Logged in as: {self.current_user}",
            font=("Helvetica", 11)
        ).pack(anchor="w", padx=15, pady=(5, 15))
        
        # App info
        app_card = ttk.Frame(settings_frame, bootstyle="dark")
        app_card.pack(fill="x", pady=10)
        
        ttk.Label(
            app_card,
            text="ℹ️ About",
            font=("Helvetica", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        ttk.Label(
            app_card,
            text=f"{APP_NAME} Desktop Application",
            font=("Helvetica", 11)
        ).pack(anchor="w", padx=15, pady=5)
        
        ttk.Label(
            app_card,
            text=f"Version: {APP_VERSION}",
            font=("Helvetica", 11)
        ).pack(anchor="w", padx=15, pady=5)
        
        ttk.Label(
            app_card,
            text="Copyright 2026 StreamHost",
            font=("Helvetica", 11),
            bootstyle="secondary"
        ).pack(anchor="w", padx=15, pady=(5, 15))
    
    def logout(self):
        """Logout user"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.token = None
            self.current_user = None
            self.create_login_screen()


def main():
    root = ttk.Window(themename="darkly")
    app = StreamHostApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
