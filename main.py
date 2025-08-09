import os
import shutil
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
from PIL import Image, ImageTk
import json
from datetime import datetime
import subprocess
import platform

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FileRenamerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("File Renamer")
        self.geometry("1200x700")
        self.minsize(1000, 600)
        
        # Variables
        self.current_folder = None
        self.selected_files = []
        self.undo_history = []
        self.file_list = []
        self.file_data = {}  # Store file info including dates
        self.preview_cache = {}
        self.sort_by = "name"  # default sort
        self.sort_reverse = False
        
        # Build UI
        self.setup_ui()
        
    def setup_ui(self):
        # Main container with PanedWindow for resizable panels
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create main frame
        main_container = ctk.CTkFrame(self)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)
        
        # Top toolbar
        self.create_toolbar(main_container)
        
        # Create PanedWindow for resizable panels
        self.paned_window = tk.PanedWindow(
            main_container, 
            orient=tk.HORIZONTAL,
            bg="#212121",
            sashwidth=8,
            sashrelief=tk.RAISED
        )
        self.paned_window.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Left panel - File list (in PanedWindow)
        left_frame = ctk.CTkFrame(self.paned_window)
        self.create_file_panel(left_frame)
        self.paned_window.add(left_frame, minsize=300, stretch="always")
        
        # Right panel - Preview and controls (in PanedWindow)
        right_frame = ctk.CTkFrame(self.paned_window)
        self.create_preview_panel(right_frame)
        self.paned_window.add(right_frame, minsize=400, stretch="always")
        
        # Set initial sash position
        self.after(100, lambda: self.paned_window.sash_place(0, 450, 0))
        
        # Bottom status bar
        self.create_status_bar()

    def create_toolbar(self, parent):
        toolbar = ctk.CTkFrame(parent, height=50)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        toolbar.grid_columnconfigure(3, weight=1)
        
        # Folder picker button
        self.folder_btn = ctk.CTkButton(
            toolbar, 
            text="📁 Choose Folder",
            command=self.choose_folder,
            width=150
        )
        self.folder_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # Filter dropdown
        self.filter_var = ctk.StringVar(value="All Files (*.*)")
        self.filter_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["All Files (*.*)", "Images (*.jpg, *.png)", "Documents (*.txt, *.pdf)", 
                   "Videos (*.mp4, *.avi)"],  # Removed "Custom..."
            variable=self.filter_var,
            command=self.apply_filter,
            width=180
        )
        self.filter_menu.grid(row=0, column=1, padx=5, pady=5)
        
        # Undo button
        self.undo_btn = ctk.CTkButton(
            toolbar,
            text="↶ Undo",
            command=self.undo_rename,
            width=100,
            state="disabled"
        )
        self.undo_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Current folder label
        self.folder_label = ctk.CTkLabel(toolbar, text="No folder selected", anchor="w")
        self.folder_label.grid(row=0, column=3, sticky="ew", padx=10)

    def create_file_panel(self, parent):
        # Configure parent
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Panel header
        header_frame = ctk.CTkFrame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header_frame, text="Files", font=("Arial", 16, "bold")).grid(
            row=0, column=0, sticky="w", padx=5
        )
        
        # Select all checkbox
        self.select_all_var = ctk.BooleanVar()
        self.select_all_cb = ctk.CTkCheckBox(
            header_frame,
            text="Select All",
            variable=self.select_all_var,
            command=self.toggle_select_all
        )
        self.select_all_cb.grid(row=0, column=1, padx=5)
        
        # Sort controls frame
        sort_frame = ctk.CTkFrame(parent)
        sort_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        sort_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(sort_frame, text="Sort by:").grid(row=0, column=0, padx=5)
        
        # Sort dropdown
        self.sort_var = ctk.StringVar(value="Name")
        self.sort_menu = ctk.CTkOptionMenu(
            sort_frame,
            values=["Name", "Date Modified", "Size", "Type"],
            variable=self.sort_var,
            command=self.change_sort,
            width=140
        )
        self.sort_menu.grid(row=0, column=1, padx=5, sticky="w")
        
        # Sort direction button
        self.sort_dir_btn = ctk.CTkButton(
            sort_frame,
            text="↓",
            width=30,
            command=self.toggle_sort_direction
        )
        self.sort_dir_btn.grid(row=0, column=2, padx=5)
        
        # File list frame with Treeview for better data display
        list_frame = ctk.CTkFrame(parent)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Create Treeview for file list
        self.file_tree = tk.ttk.Treeview(
            list_frame,
            columns=("size", "modified"),
            show="tree headings",
            selectmode="extended"
        )
        
        # Configure columns
        self.file_tree.heading("#0", text="Name", anchor="w")
        self.file_tree.heading("size", text="Size", anchor="e")
        self.file_tree.heading("modified", text="Modified", anchor="w")
        
        self.file_tree.column("#0", width=200, minwidth=150)
        self.file_tree.column("size", width=80, minwidth=60)
        self.file_tree.column("modified", width=150, minwidth=100)
        
        # Style the treeview
        style = tk.ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            borderwidth=0
        )
        style.configure("Treeview.Heading", background="#1f1f1f", foreground="white")
        style.map("Treeview", background=[("selected", "#1f6aa5")])
        
        self.file_tree.grid(row=0, column=0, sticky="nsew")
        
        # Bind events
        self.file_tree.bind('<<TreeviewSelect>>', self.on_file_select)
        self.file_tree.bind('<Button-3>', self.show_context_menu)  # Right-click menu
        self.file_tree.bind('<Double-Button-1>', self.on_double_click)  # Double-click to open
        self.file_tree.bind('<Return>', self.on_enter_key)  # Enter key to open
        
        # Scrollbars
        v_scrollbar = ctk.CTkScrollbar(list_frame, command=self.file_tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ctk.CTkScrollbar(list_frame, orientation="horizontal", command=self.file_tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.file_tree.configure(xscrollcommand=h_scrollbar.set)
        
        # File count label
        self.file_count_label = ctk.CTkLabel(
            parent, 
            text="0 files | 0 selected | Double-click to open",
            font=("Arial", 10)
        )
        self.file_count_label.grid(row=3, column=0, pady=5)
        
        # Context menu
        self.create_context_menu()

    def create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white")
        self.context_menu.add_command(label="Open File", command=self.open_selected_file)
        self.context_menu.add_command(label="Open in Explorer", command=self.open_file_location)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=self.select_all_files)
        self.context_menu.add_command(label="Deselect All", command=self.deselect_all_files)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Refresh", command=self.load_files)

    def show_context_menu(self, event):
        # Select item if right-clicked on a non-selected item
        item = self.file_tree.identify('item', event.x, event.y)
        if item and item not in self.file_tree.selection():
            self.file_tree.selection_set(item)
            self.on_file_select(None)
        
        self.context_menu.post(event.x_root, event.y_root)

    def on_double_click(self, event):
        """Handle double-click on file item"""
        # Get the clicked item
        item = self.file_tree.identify('item', event.x, event.y)
        if item:
            # Open the file
            file_name = self.file_tree.item(item)["text"]
            if file_name and self.current_folder:
                file_path = os.path.join(self.current_folder, file_name)
                self.open_file(file_path)

    def on_enter_key(self, event):
        """Handle Enter key press to open selected file"""
        if self.selected_files:
            self.open_selected_file()

    def open_file(self, file_path):
        """Open a file with the default system application"""
        try:
            if os.path.exists(file_path):
                if platform.system() == 'Darwin':       # macOS
                    subprocess.call(['open', file_path])
                elif platform.system() == 'Windows':    # Windows
                    # Use os.startfile for Windows
                    os.startfile(os.path.normpath(file_path))
                else:                                   # Linux
                    subprocess.call(['xdg-open', file_path])
                
                self.update_status(f"Opened: {os.path.basename(file_path)}")
            else:
                messagebox.showerror("Error", "File not found")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{str(e)}")

    def open_selected_file(self):
        if self.selected_files and self.current_folder:
            file_path = os.path.join(self.current_folder, self.selected_files[0])
            self.open_file(file_path)

    def open_file_location(self):
        if self.selected_files and self.current_folder:
            file_path = os.path.join(self.current_folder, self.selected_files[0])
            
            try:
                if platform.system() == 'Darwin':       # macOS
                    subprocess.call(['open', '-R', file_path])
                elif platform.system() == 'Windows':    # Windows
                    # For Windows, we need to properly escape the path
                    if os.path.exists(file_path):
                        subprocess.run(['explorer', '/select,', os.path.normpath(file_path)])
                    else:
                        # If file doesn't exist, open the folder
                        subprocess.run(['explorer', os.path.normpath(self.current_folder)])
                else:                                   # Linux
                    # For Linux, open the containing folder
                    subprocess.call(['xdg-open', self.current_folder])
                
                self.update_status("Opened file location")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file location:\n{str(e)}")

    def change_sort(self, choice):
        sort_map = {
            "Name": "name",
            "Date Modified": "modified",
            "Size": "size",
            "Type": "type"
        }
        self.sort_by = sort_map.get(choice, "name")
        self.load_files()

    def toggle_sort_direction(self):
        self.sort_reverse = not self.sort_reverse
        self.sort_dir_btn.configure(text="↑" if self.sort_reverse else "↓")
        self.load_files()

    def create_preview_panel(self, parent):
        # Configure parent
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Preview section with notebook for different preview types
        preview_header = ctk.CTkFrame(parent)
        preview_header.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        preview_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            preview_header, 
            text="Preview", 
            font=("Arial", 16, "bold")
        ).grid(row=0, column=0, sticky="w")
        
        # Add open file button
        self.open_file_btn = ctk.CTkButton(
            preview_header,
            text="🔗 Open File",
            width=100,
            command=self.open_selected_file
        )
        self.open_file_btn.grid(row=0, column=1, padx=5)
        
        # Preview frame with scrollable content
        self.preview_frame = ctk.CTkFrame(parent)
        self.preview_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.preview_frame.grid_rowconfigure(0, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        
        # Create scrollable preview area
        self.preview_scroll = ctk.CTkScrollableFrame(self.preview_frame)
        self.preview_scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Preview label for images
        self.preview_image_label = ctk.CTkLabel(
            self.preview_scroll,
            text=""
        )
        self.preview_image_label.pack(expand=True, fill="both")
        
        # Preview text widget for text files
        self.preview_text = ctk.CTkTextbox(
            self.preview_scroll,
            height=200,
            font=("Courier New", 10)
        )
        
        # File info frame
        self.file_info_frame = ctk.CTkFrame(self.preview_scroll)
        
        # Initially show default message
        self.show_default_preview()
        
        # Rename controls section
        controls_frame = ctk.CTkFrame(parent)
        controls_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        controls_frame.grid_columnconfigure(1, weight=1)
        
        # Base name input
        ctk.CTkLabel(controls_frame, text="Base Name:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        
        self.base_name_entry = ctk.CTkEntry(
            controls_frame,
            placeholder_text="Enter base name (e.g., Image_)"
        )
        self.base_name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.base_name_entry.bind('<KeyRelease>', self.update_preview_names)
        
        # Starting number
        ctk.CTkLabel(controls_frame, text="Start Number:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        
        self.start_number_entry = ctk.CTkEntry(
            controls_frame,
            placeholder_text="1"
        )
        self.start_number_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.start_number_entry.insert(0, "1")
        self.start_number_entry.bind('<KeyRelease>', self.update_preview_names)
        
        # Preview names section
        preview_names_frame = ctk.CTkFrame(parent)
        preview_names_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        preview_names_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            preview_names_frame, 
            text="Preview New Names:", 
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Preview names text
        self.preview_names_text = ctk.CTkTextbox(
            preview_names_frame,
            height=100,
            font=("Courier", 10)
        )
        self.preview_names_text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Rename button
        self.rename_btn = ctk.CTkButton(
            parent,
            text="🔄 Rename Selected Files",
            command=self.rename_files,
            height=40,
            font=("Arial", 14, "bold"),
            state="disabled"
        )
        self.rename_btn.grid(row=4, column=0, sticky="ew", padx=10, pady=10)

    def show_default_preview(self):
        """Show default preview message"""
        self.preview_image_label.pack(expand=True, fill="both")
        self.preview_text.pack_forget()
        self.file_info_frame.pack_forget()
        self.preview_image_label.configure(
            text="Select a file to preview\n\nDouble-click any file to open it",
            image=""
        )

    def create_status_bar(self):
        self.status_bar = ctk.CTkLabel(
            self,
            text="Ready",
            height=30,
            anchor="w"
        )
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.current_folder = folder
            self.folder_label.configure(text=f"📁 {folder}")
            self.load_files()
            self.update_status("Folder loaded successfully")
    
    def load_files(self):
        if not self.current_folder:
            return
        
        # Clear tree
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        self.file_list = []
        self.file_data = {}
        self.preview_cache.clear()
        
        # Get filter
        filter_type = self.filter_var.get()
        extensions = self.get_extensions_for_filter(filter_type)
        
        # Load files with metadata
        for file in os.listdir(self.current_folder):
            file_path = os.path.join(self.current_folder, file)
            if os.path.isfile(file_path):
                if extensions == ["*"] or any(file.lower().endswith(ext) for ext in extensions):
                    # Get file stats
                    stat = os.stat(file_path)
                    size = stat.st_size
                    modified = datetime.fromtimestamp(stat.st_mtime)
                    
                    self.file_data[file] = {
                        "path": file_path,
                        "size": size,
                        "modified": modified,
                        "type": Path(file).suffix.lower()
                    }
                    self.file_list.append(file)
        
        # Sort files
        self.sort_files()
        
        # Add files to tree
        for file in self.file_list:
            data = self.file_data[file]
            size_str = self.format_size(data["size"])
            date_str = data["modified"].strftime("%Y-%m-%d %H:%M")
            
            self.file_tree.insert("", "end", text=file, values=(size_str, date_str))
        
        self.update_file_count()
        self.select_all_var.set(False)

    def sort_files(self):
        if self.sort_by == "name":
            self.file_list.sort(key=str.lower, reverse=self.sort_reverse)
        elif self.sort_by == "modified":
            self.file_list.sort(
                key=lambda x: self.file_data[x]["modified"], 
                reverse=self.sort_reverse
            )
        elif self.sort_by == "size":
            self.file_list.sort(
                key=lambda x: self.file_data[x]["size"], 
                reverse=self.sort_reverse
            )
        elif self.sort_by == "type":
            self.file_list.sort(
                key=lambda x: (self.file_data[x]["type"], x.lower()), 
                reverse=self.sort_reverse
            )

    def format_size(self, size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_extensions_for_filter(self, filter_type):
        filters = {
            "All Files (*.*)": ["*"],
            "Images (*.jpg, *.png)": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".webp"],
            "Documents (*.txt, *.pdf)": [".txt", ".pdf", ".doc", ".docx", ".rtf", ".odt"],
            "Videos (*.mp4, *.avi)": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"]
        }
        return filters.get(filter_type, ["*"])
    
    def apply_filter(self, choice):
        self.load_files()
    
    def toggle_select_all(self):
        if self.select_all_var.get():
            self.select_all_files()
        else:
            self.deselect_all_files()

    def select_all_files(self):
        for item in self.file_tree.get_children():
            self.file_tree.selection_add(item)
        self.select_all_var.set(True)
        self.on_file_select(None)

    def deselect_all_files(self):
        self.file_tree.selection_remove(*self.file_tree.get_children())
        self.select_all_var.set(False)
        self.on_file_select(None)
    
    def on_file_select(self, event):
        selected_items = self.file_tree.selection()
        self.selected_files = [
            self.file_tree.item(item)["text"] for item in selected_items
        ]
        self.update_file_count()
        self.update_preview()
        self.update_preview_names()
        
        # Enable/disable buttons
        if self.selected_files:
            self.rename_btn.configure(state="normal")
            self.open_file_btn.configure(state="normal")
        else:
            self.rename_btn.configure(state="disabled")
            self.open_file_btn.configure(state="disabled")

    def update_preview(self):
        if not self.selected_files or not self.current_folder:
            self.show_default_preview()
            return
        
        # Preview first selected file
        file_name = self.selected_files[0]
        file_path = os.path.join(self.current_folder, file_name)
        
        # Check if cached
        if file_path in self.preview_cache:
            preview_type, content = self.preview_cache[file_path]
            self.display_preview(preview_type, content)
            return
        
        # Generate preview based on file type
        try:
            ext = file_name.lower()
            
            # Image files
            if any(ext.endswith(img_ext) for img_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp']):
                self.preview_image(file_path)
            
            # Text-based files
            elif any(ext.endswith(text_ext) for text_ext in ['.txt', '.log', '.md', '.py', '.json', '.xml', '.html', '.css', '.js', '.csv', '.ini', '.cfg', '.conf', '.yaml', '.yml']):
                self.preview_text_file(file_path)
            
            # PDF files (show info only)
            elif ext.endswith('.pdf'):
                self.preview_document(file_path, "PDF Document")
            
            # Office documents
            elif any(ext.endswith(doc_ext) for doc_ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']):
                self.preview_document(file_path, "Office Document")
            
            # Video files
            elif any(ext.endswith(vid_ext) for vid_ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']):
                self.preview_video(file_path)
            
            # Audio files
            elif any(ext.endswith(aud_ext) for aud_ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.wma']):
                self.preview_audio(file_path)
            
            # Default: show file info
            else:
                self.preview_file_info(file_name)
                
        except Exception as e:
            self.show_error_preview(f"Cannot preview file:\n{str(e)}")
    
    def display_preview(self, preview_type, content):
        """Display cached preview content"""
        if preview_type == "image":
            self.preview_text.pack_forget()
            self.file_info_frame.pack_forget()
            self.preview_image_label.pack(expand=True, fill="both")
            self.preview_image_label.configure(text="", image=content)
        elif preview_type == "text":
            self.preview_image_label.pack_forget()
            self.file_info_frame.pack_forget()
            self.preview_text.pack(expand=True, fill="both", padx=5, pady=5)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", content)
        elif preview_type == "info":
            self.preview_image_label.pack_forget()
            self.preview_text.pack_forget()
            self.file_info_frame.pack(expand=True, fill="both", padx=10, pady=10)
    
    def preview_image(self, file_path):
        """Preview image files"""
        try:
            # Open and resize image
            img = Image.open(file_path)
            
            # Get original size
            original_size = img.size
            
            # Calculate thumbnail size maintaining aspect ratio
            max_size = (400, 300)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Display
            self.preview_text.pack_forget()
            self.file_info_frame.pack_forget()
            self.preview_image_label.pack(expand=True, fill="both")
            self.preview_image_label.configure(text="", image=photo)
            self.preview_image_label.image = photo  # Keep reference
            
            # Add image info to status
            self.update_status(f"Image: {original_size[0]}x{original_size[1]} pixels")
            
            # Cache
            self.preview_cache[file_path] = ("image", photo)
            
        except Exception as e:
            self.show_error_preview(f"Cannot preview image:\n{str(e)}")
    
    def preview_text_file(self, file_path):
        """Preview text-based files"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        # Read first 50KB
                        content = f.read(50000)
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise Exception("Unable to decode file with available encodings")
            
            # Check if content was truncated
            if len(content) == 50000:
                content += "\n\n... (file truncated for preview)"
            
            # Display
            self.preview_image_label.pack_forget()
            self.file_info_frame.pack_forget()
            self.preview_text.pack(expand=True, fill="both", padx=5, pady=5)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", content)
            
            # Cache
            self.preview_cache[file_path] = ("text", content)
            
        except Exception as e:
            self.show_error_preview(f"Cannot preview text file:\n{str(e)}")
    
    def preview_document(self, file_path, doc_type):
        """Preview document files with file info"""
        self.preview_file_info(os.path.basename(file_path), doc_type)
    
    def preview_video(self, file_path):
        """Preview video files with info"""
        file_name = os.path.basename(file_path)
        data = self.file_data[file_name]
        
        # Create detailed info
        info_lines = [
            ("🎬 Video File", ""),
            ("", ""),
            ("File:", file_name),
            ("Type:", data['type'].upper()[1:] + " Video"),
            ("Size:", self.format_size(data['size'])),
            ("Modified:", data['modified'].strftime('%Y-%m-%d %H:%M:%S')),
            ("", ""),
            ("💡 Tip:", "Double-click to play"),
            ("", ""),
            ("Path:", file_path)
        ]
        
        self.show_file_info(info_lines)
        self.preview_cache[file_path] = ("info", info_lines)
    
    def preview_audio(self, file_path):
        """Preview audio files with info"""
        file_name = os.path.basename(file_path)
        data = self.file_data[file_name]
        
        # Create detailed info
        info_lines = [
            ("🎵 Audio File", ""),
            ("", ""),
            ("File:", file_name),
            ("Type:", data['type'].upper()[1:] + " Audio"),
            ("Size:", self.format_size(data['size'])),
            ("Modified:", data['modified'].strftime('%Y-%m-%d %H:%M:%S')),
            ("", ""),
            ("💡 Tip:", "Double-click to play"),
            ("", ""),
            ("Path:", file_path)
        ]
        
        self.show_file_info(info_lines)
        self.preview_cache[file_path] = ("info", info_lines)
    
    def preview_file_info(self, file_name, file_type=None):
        """Show generic file information"""
        data = self.file_data[file_name]
        
        if not file_type:
            file_type = data['type'].upper()[1:] if data['type'] else "Unknown"
            file_type += " File"
        
        # Create info lines
        info_lines = [
            (f"📄 {file_type}", ""),
            ("", ""),
            ("File:", file_name),
            ("Size:", self.format_size(data['size'])),
            ("Type:", data['type'] or "Unknown"),
            ("Modified:", data['modified'].strftime('%Y-%m-%d %H:%M:%S')),
            ("", ""),
            ("💡 Tip:", "Double-click to open"),
            ("", ""),
            ("Path:", data['path'])
        ]
        
        self.show_file_info(info_lines)
        self.preview_cache[data['path']] = ("info", info_lines)
    
    def show_file_info(self, info_lines):
        """Display file information in a formatted way"""
        # Hide other preview widgets
        self.preview_image_label.pack_forget()
        self.preview_text.pack_forget()
        
        # Clear previous info
        for widget in self.file_info_frame.winfo_children():
            widget.destroy()
        
        # Show info frame
        self.file_info_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Create info labels
        for i, (label, value) in enumerate(info_lines):
            if label == "" and value == "":  # Empty line
                ctk.CTkLabel(self.file_info_frame, text="", height=10).grid(
                    row=i, column=0, columnspan=2
                )
            elif value == "":  # Header
                ctk.CTkLabel(
                    self.file_info_frame,
                    text=label,
                    font=("Arial", 14, "bold")
                ).grid(row=i, column=0, columnspan=2, sticky="w", pady=5)
            else:  # Label-value pair
                ctk.CTkLabel(
                    self.file_info_frame,
                    text=label,
                    font=("Arial", 11),
                    anchor="e"
                ).grid(row=i, column=0, sticky="e", padx=(0, 10), pady=2)
                
                ctk.CTkLabel(
                    self.file_info_frame,
                    text=value,
                    font=("Arial", 11),
                    anchor="w"
                ).grid(row=i, column=1, sticky="w", pady=2)
        
        # Configure grid weights
        self.file_info_frame.grid_columnconfigure(1, weight=1)
    
    def show_error_preview(self, error_message):
        """Show error in preview"""
        self.preview_text.pack_forget()
        self.file_info_frame.pack_forget()
        self.preview_image_label.pack(expand=True, fill="both")
        self.preview_image_label.configure(
            text=error_message,
            image=""
        )

    def update_preview_names(self, event=None):
        if not self.selected_files:
            self.preview_names_text.delete("1.0", tk.END)
            return
        
        base_name = self.base_name_entry.get() or "File_"
        try:
            start_num = int(self.start_number_entry.get() or 1)
        except ValueError:
            start_num = 1
        
        preview_text = ""
        for i, file in enumerate(self.selected_files[:10]):  # Show first 10
            ext = Path(file).suffix
            new_name = f"{base_name}{start_num + i}{ext}"
            preview_text += f"{file} → {new_name}\n"
        
        if len(self.selected_files) > 10:
            preview_text += f"\n... and {len(self.selected_files) - 10} more files"
        
        self.preview_names_text.delete("1.0", tk.END)
        self.preview_names_text.insert("1.0", preview_text)
    
    def rename_files(self):
        if not self.selected_files:
            return
        
        base_name = self.base_name_entry.get() or "File_"
        try:
            start_num = int(self.start_number_entry.get() or 1)
        except ValueError:
            start_num = 1
        
        # Confirm action
        result = messagebox.askyesno(
            "Confirm Rename",
            f"Rename {len(self.selected_files)} file(s)?\n\nThis action can be undone."
        )
        
        if not result:
            return
        
        # Prepare undo data
        undo_data = {
            "timestamp": datetime.now().isoformat(),
            "folder": self.current_folder,
            "renames": []
        }
        
        # Perform rename
        success_count = 0
        errors = []
        
        for i, file in enumerate(self.selected_files):
            old_path = os.path.join(self.current_folder, file)
            ext = Path(file).suffix
            new_name = f"{base_name}{start_num + i}{ext}"
            new_path = os.path.join(self.current_folder, new_name)
            
            # Handle duplicate names
            counter = 1
            temp_path = new_path
            while os.path.exists(temp_path) and temp_path != old_path:
                new_name = f"{base_name}{start_num + i}_{counter}{ext}"
                temp_path = os.path.join(self.current_folder, new_name)
                counter += 1
            new_path = temp_path
            
            try:
                os.rename(old_path, new_path)
                undo_data["renames"].append({
                    "old": file,
                    "new": os.path.basename(new_path)
                })
                success_count += 1
            except Exception as e:
                errors.append(f"{file}: {str(e)}")
        
        # Save undo data
        if undo_data["renames"]:
            self.undo_history.append(undo_data)
            self.undo_btn.configure(state="normal")
            
            # Save to file
            self.save_undo_history()
        
        # Reload files
        self.load_files()
        
        # Show result
        if errors:
            error_msg = "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n... and {len(errors) - 5} more errors"
            messagebox.showwarning(
                "Rename Completed with Errors",
                f"Successfully renamed {success_count} files.\n\nErrors:\n{error_msg}"
            )
        else:
            self.update_status(f"Successfully renamed {success_count} files")

    def undo_rename(self):
        if not self.undo_history:
            return
        
        last_action = self.undo_history[-1]
        folder = last_action["folder"]
        
        if folder != self.current_folder:
            messagebox.showwarning(
                "Different Folder",
                "The last rename operation was in a different folder.\n"
                f"Please navigate to: {folder}"
            )
            return
        
        # Confirm undo
        result = messagebox.askyesno(
            "Confirm Undo",
            f"Undo last rename operation?\n{len(last_action['renames'])} file(s) will be reverted."
        )
        
        if not result:
            return
        
        # Perform undo
        success_count = 0
        errors = []
        
        for rename in reversed(last_action["renames"]):
            old_path = os.path.join(folder, rename["new"])
            new_path = os.path.join(folder, rename["old"])
            
            try:
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                    success_count += 1
            except Exception as e:
                errors.append(f"{rename['new']}: {str(e)}")
        
        # Remove from history
        self.undo_history.pop()
        
        if not self.undo_history:
            self.undo_btn.configure(state="disabled")
        
        self.save_undo_history()
        self.load_files()
        
        # Show result
        if errors:
            messagebox.showwarning(
                "Undo Completed with Errors",
                f"Successfully reverted {success_count} files.\n\nErrors:\n{', '.join(errors)}"
            )
        else:
            self.update_status(f"Successfully reverted {success_count} files")
    
    def save_undo_history(self):
        # Save last 10 undo operations
        history_file = os.path.join(os.path.expanduser("~"), ".file_renamer_history.json")
        try:
            with open(history_file, 'w') as f:
                json.dump(self.undo_history[-10:], f)
        except:
            pass
    
    def load_undo_history(self):
        history_file = os.path.join(os.path.expanduser("~"), ".file_renamer_history.json")
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.undo_history = json.load(f)
                    if self.undo_history:
                        self.undo_btn.configure(state="normal")
        except:
            pass

    def update_file_count(self):
        total = len(self.file_list)
        selected = len(self.selected_files)
        self.file_count_label.configure(text=f"{total} files | {selected} selected | Double-click to open")
    
    def update_status(self, message):
        self.status_bar.configure(text=message)
        # Auto-clear status after 3 seconds
        self.after(3000, lambda: self.status_bar.configure(text="Ready"))


if __name__ == "__main__":
    app = FileRenamerApp()
    app.load_undo_history()
    app.mainloop()