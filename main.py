import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageFilter
import random
import math
import pygame
import os
import sys
import atexit

class EnhancedPet:
    def __init__(self, root):
        self.root = root
        self.root.title("Plinko Pets - Atago66 on GitHub")
        self.root.geometry("550x650")
        self.root.configure(bg="#f0f0f0")
        
        # Register cleanup function to handle window closing properly
        self.root.protocol("WM_DELETE_WINDOW", self.on_root_close)
        atexit.register(self.cleanup)
        
        # Flag to track if application is running or shutting down
        self.is_running = True
        
        # Store image references to prevent garbage collection
        self.image_references = {}
        
        # Initialize pygame for sound
        try:
            pygame.mixer.init()
            self.sound_init_success = True
        except Exception as e:
            print(f"Sound initialization error: {e}")
            self.sound_init_success = False
        
        # Load or create default sounds
        self.bounce_sounds = []
        try:
            # Default bounce sound - create a temporary file if running as executable
            if getattr(sys, 'frozen', False):
                # We're running in a bundle
                bundle_dir = sys._MEIPASS
            else:
                # We're running in a normal Python environment
                bundle_dir = os.path.dirname(os.path.abspath(__file__))
                
            # Create sound directory if it doesn't exist
            sound_dir = os.path.join(bundle_dir, "sounds")
            if not os.path.exists(sound_dir):
                os.makedirs(sound_dir)
                
            # Try to load built-in sounds or use fallback tones
            self.create_default_sounds()
        except Exception as e:
            print(f"Sound initialization error: {e}")
            # We'll create simple sounds later if needed
        
        # Pet variables
        self.pet_images = []  # List of loaded pet images
        self.pet_windows = []  # List of active pet windows
        self.pet_sprites = []  # List to store canvas image references
        self.pet_velocities = []  # List to store velocities for each pet
        self.pet_is_dragging = []  # List to track dragging state
        self.pet_offset = []  # List to store drag offsets
        self.last_positions = []  # Store last positions for velocity calculation
        
        # Physics settings (with defaults)
        self.gravity_enabled = tk.BooleanVar(value=True)
        self.gravity_strength = tk.DoubleVar(value=0.7)
        self.friction_enabled = tk.BooleanVar(value=True)
        self.friction_strength = tk.DoubleVar(value=0.95)
        self.bounce_enabled = tk.BooleanVar(value=True)
        self.bounce_strength = tk.DoubleVar(value=0.6)
        self.size_scale = tk.DoubleVar(value=1.0)
        self.sound_enabled = tk.BooleanVar(value=True)
        self.multi_monitor = tk.BooleanVar(value=False)
        self.collision_enabled = tk.BooleanVar(value=True)
        self.vertical_boundary_enabled = tk.BooleanVar(value=True)
        
        # Flag to indicate if any pet has been loaded yet
        self.has_active_image = False
        
        # Create UI
        self.create_ui()
    
    def on_root_close(self):
        """Handle root window closing properly"""
        self.is_running = False
        self.remove_all_pets()
        self.root.destroy()
    
    def cleanup(self):
        """Clean up resources on exit"""
        try:
            # Clean up pygame resources
            if hasattr(self, 'sound_init_success') and self.sound_init_success:
                pygame.mixer.quit()
        except:
            pass
    
    def create_default_sounds(self):
        """Create default bounce sounds using pygame"""
        # Create a few different bounce sounds with different pitches
        frequencies = [220, 330, 440, 550]
        duration = 100  # milliseconds
        
        for i, freq in enumerate(frequencies):
            sound_file = f"sounds/bounce_sound_{i}.wav"
            
            if not os.path.exists(sound_file):
                # Create a simple sine wave sound
                pygame.mixer.Sound.fadeout = duration
                sample_rate = 44100
                samples = int(duration * sample_rate / 1000.0)
                
                # Generate a simple sine wave
                buf = bytearray(samples * 2)  # 16-bit samples
                for s in range(samples):
                    t = float(s) / sample_rate
                    val = int(32767.0 * math.sin(2.0 * math.pi * freq * t) * (1.0 - t / (duration / 1000.0)))
                    buf[s*2] = val & 0xff
                    buf[s*2+1] = (val >> 8) & 0xff
                
                try:
                    # Save it as a temporary file
                    with open(sound_file, 'wb') as f:
                        f.write(buf)
                    sound = pygame.mixer.Sound(sound_file)
                    self.bounce_sounds.append(sound)
                except Exception as e:
                    print(f"Error creating sound: {e}")
            else:
                # Load existing sound file
                sound = pygame.mixer.Sound(sound_file)
                self.bounce_sounds.append(sound)
    
    def load_custom_sounds(self):
        """Load custom sound files for bounce effects"""
        if not self.sound_init_success:
            messagebox.showerror("Error", "Sound system not initialized")
            return
            
        file_paths = filedialog.askopenfilenames(
            title="Select Sound Files",
            filetypes=[("Sound files", "*.wav *.mp3 *.ogg")]
        )
        
        if file_paths:
            # Clear existing sounds
            self.bounce_sounds = []
            
            # Load new sounds
            for path in file_paths:
                try:
                    sound = pygame.mixer.Sound(path)
                    self.bounce_sounds.append(sound)
                    self.status_var.set(f"Loaded sound: {os.path.basename(path)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load sound {os.path.basename(path)}: {str(e)}")
            
            if self.bounce_sounds:
                messagebox.showinfo("Success", f"Loaded {len(self.bounce_sounds)} sound files")
            else:
                # If all sound loading failed, recreate default sounds
                self.create_default_sounds()
                messagebox.showinfo("Info", "Using default sounds")
    
    def create_ui(self):
        # Create a notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create two tabs - Main and Settings
        main_tab = ttk.Frame(notebook)
        settings_tab = ttk.Frame(notebook)
        
        notebook.add(main_tab, text='Main')
        notebook.add(settings_tab, text='Settings')
        
        # ===== MAIN TAB =====
        main_frame = tk.Frame(main_tab, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(main_frame, text="Plinko Pets", font=("Arial", 16, "bold"), bg="#f0f0f0")
        title.pack(pady=10)
        
        # Preview frame
        self.preview_frame = tk.Frame(main_frame, width=200, height=200, bg="white", relief=tk.SUNKEN, bd=1)
        self.preview_frame.pack(pady=10)
        self.preview_frame.pack_propagate(False)
        
        self.preview_label = tk.Label(self.preview_frame, text="Image Preview", bg="white")
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # Upload buttons frame
        upload_frame = tk.Frame(main_frame, bg="#f0f0f0")
        upload_frame.pack(pady=10, fill=tk.X)
        
        # Upload image button
        upload_btn = tk.Button(upload_frame, text="Upload Image", command=self.upload_image, 
                              bg="#4CAF50", fg="white", font=("Arial", 12), padx=10, pady=5)
        upload_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Upload sounds button
        sounds_btn = tk.Button(upload_frame, text="Upload Sounds", command=self.load_custom_sounds, 
                              bg="#9C27B0", fg="white", font=("Arial", 12), padx=10, pady=5)
        sounds_btn.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)
        
        # Launch and remove buttons in a frame
        btn_frame = tk.Frame(main_frame, bg="#f0f0f0")
        btn_frame.pack(pady=10, fill=tk.X)
        
        launch_btn = tk.Button(btn_frame, text="Add Pet", command=self.launch_pet,
                              bg="#2196F3", fg="white", font=("Arial", 12, "bold"), padx=20, pady=10)
        launch_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        remove_btn = tk.Button(btn_frame, text="Remove All", command=self.remove_all_pets,
                              bg="#F44336", fg="white", font=("Arial", 12), padx=20, pady=10)
        remove_btn.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)
        
        # Current pets list
        pets_frame = tk.LabelFrame(main_frame, text="Active Pets", bg="#f0f0f0", font=("Arial", 10))
        pets_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.pets_listbox = tk.Listbox(pets_frame, height=5, bd=1, relief=tk.SUNKEN)
        self.pets_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ===== SETTINGS TAB =====
        settings_frame = tk.Frame(settings_tab, bg="#f0f0f0", padx=20, pady=20)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Physics settings
        physics_frame = tk.LabelFrame(settings_frame, text="Physics Settings", bg="#f0f0f0", font=("Arial", 12))
        physics_frame.pack(pady=10, fill=tk.X)
        
        # Gravity settings
        gravity_frame = tk.Frame(physics_frame, bg="#f0f0f0")
        gravity_frame.pack(fill=tk.X, padx=10, pady=5)
        
        gravity_check = tk.Checkbutton(gravity_frame, text="Gravity", variable=self.gravity_enabled, 
                                      bg="#f0f0f0", font=("Arial", 10))
        gravity_check.pack(side=tk.LEFT, padx=5)
        
        gravity_slider = tk.Scale(gravity_frame, from_=0.1, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
                                 variable=self.gravity_strength, bg="#f0f0f0", length=200)
        gravity_slider.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
        
        # Friction settings
        friction_frame = tk.Frame(physics_frame, bg="#f0f0f0")
        friction_frame.pack(fill=tk.X, padx=10, pady=5)
        
        friction_check = tk.Checkbutton(friction_frame, text="Friction", variable=self.friction_enabled, 
                                       bg="#f0f0f0", font=("Arial", 10))
        friction_check.pack(side=tk.LEFT, padx=5)
        
        friction_slider = tk.Scale(friction_frame, from_=0.5, to=1.0, resolution=0.01, orient=tk.HORIZONTAL,
                                  variable=self.friction_strength, bg="#f0f0f0", length=200)
        friction_slider.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
        
        # Bounce settings
        bounce_frame = tk.Frame(physics_frame, bg="#f0f0f0")
        bounce_frame.pack(fill=tk.X, padx=10, pady=5)
        
        bounce_check = tk.Checkbutton(bounce_frame, text="Bounce", variable=self.bounce_enabled, 
                                     bg="#f0f0f0", font=("Arial", 10))
        bounce_check.pack(side=tk.LEFT, padx=5)
        
        bounce_slider = tk.Scale(bounce_frame, from_=0.1, to=0.95, resolution=0.05, orient=tk.HORIZONTAL,
                                variable=self.bounce_strength, bg="#f0f0f0", length=200)
        bounce_slider.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
        
        # Visual settings
        visual_frame = tk.LabelFrame(settings_frame, text="Visual Settings", bg="#f0f0f0", font=("Arial", 12))
        visual_frame.pack(pady=10, fill=tk.X)
        
        # Size settings
        size_frame = tk.Frame(visual_frame, bg="#f0f0f0")
        size_frame.pack(fill=tk.X, padx=10, pady=5)
        
        size_label = tk.Label(size_frame, text="Size:", bg="#f0f0f0", font=("Arial", 10))
        size_label.pack(side=tk.LEFT, padx=5)
        
        size_slider = tk.Scale(size_frame, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
                              variable=self.size_scale, bg="#f0f0f0", length=220)
        size_slider.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
        
        
        # Sound settings
        sound_check = tk.Checkbutton(visual_frame, text="Bounce sounds", variable=self.sound_enabled, 
                                    bg="#f0f0f0", font=("Arial", 10))
        sound_check.pack(anchor=tk.W, padx=15, pady=5)
        
        # Other settings
        other_frame = tk.LabelFrame(settings_frame, text="Other Settings", bg="#f0f0f0", font=("Arial", 12))
        other_frame.pack(pady=10, fill=tk.X)
        
        # Multi-monitor
        multimon_check = tk.Checkbutton(other_frame, text="Enable multi-monitor support", 
                                       variable=self.multi_monitor, bg="#f0f0f0", font=("Arial", 10))
        multimon_check.pack(anchor=tk.W, padx=15, pady=5)
        
        # Vertical boundary toggle 
        vertical_check = tk.Checkbutton(other_frame, text="Enable vertical boundary (floor)",
                                       variable=self.vertical_boundary_enabled, bg="#f0f0f0", font=("Arial", 10))
        vertical_check.pack(anchor=tk.W, padx=15, pady=5)
        
        # Collision
        collision_check = tk.Checkbutton(other_frame, text="Enable collisions between pets", 
                                        variable=self.collision_enabled, bg="#f0f0f0", font=("Arial", 10))
        collision_check.pack(anchor=tk.W, padx=15, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status.pack(side=tk.BOTTOM, fill=tk.X)
    
    def upload_image(self):
        if not self.is_running:
            return
            
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        
        if file_path:
            try:
                image = Image.open(file_path)
                
                # Resize if too large
                max_size = 200
                if image.width > max_size or image.height > max_size:
                    ratio = min(max_size / image.width, max_size / image.height)
                    new_size = (int(image.width * ratio), int(image.height * ratio))
                    image = image.resize(new_size, Image.LANCZOS)
                
                # Store original image
                self.active_image = image.copy()
                self.has_active_image = True
                
                # Create a PhotoImage for display
                self.preview_image = ImageTk.PhotoImage(image)
                
                # Update the preview label
                self.preview_label.config(image=self.preview_image, text="")
                
                # Store multiple references to avoid garbage collection
                self.preview_label.image = self.preview_image
                self.image_references['preview'] = self.preview_image
                
                self.status_var.set(f"Image loaded: {os.path.basename(file_path)}")
                print(f"Image loaded successfully: {image.width}x{image.height}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def launch_pet(self):
        if not self.is_running:
            return
            
        if not self.has_active_image:
            messagebox.showwarning("Warning", "Please upload an image first!")
            return
        
        try:
            # Create a copy of the image for this pet instance
            pet_image = self.active_image.copy()
            
            # Apply size scaling if needed
            if self.size_scale.get() != 1.0:
                new_width = int(pet_image.width * self.size_scale.get())
                new_height = int(pet_image.height * self.size_scale.get())
                pet_image = pet_image.resize((new_width, new_height), Image.LANCZOS)
            
            original_image = pet_image.copy()
            
            # Add to pet images list
            self.pet_images.append({
                'image': pet_image,
                'original': original_image,
            })
            
            # Create pet window
            pet_window = tk.Toplevel(self.root)
            pet_window.overrideredirect(True)  # No window decorations
            pet_window.attributes('-topmost', True)  # Stay on top
            
            # Configure transparency
            pet_window.configure(bg='black')
            pet_window.attributes('-transparentcolor', 'black')
            
            # Set window size based on image
            width = pet_image.width + 20
            height = pet_image.height + 20
            
            # Position randomly on screen
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = random.randint(0, screen_width - width)
            y = random.randint(0, screen_height - height)
            
            pet_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Create canvas
            canvas = tk.Canvas(
                pet_window,
                width=width,
                height=height,
                bg='black',
                highlightthickness=0
            )
            canvas.pack()
            
            # Create PhotoImage and store with unique name
            window_index = len(self.pet_windows)
            pet_tk_image = ImageTk.PhotoImage(pet_image)
            
            # Store image reference in multiple places
            unique_key = f"pet_{window_index}"
            self.image_references[unique_key] = pet_tk_image
            
            # Create image on canvas
            pet_sprite = canvas.create_image(
                width // 2,
                height // 2,
                image=pet_tk_image
            )
            
            # Store reference on window as well
            pet_window.pet_tk_image = pet_tk_image
            
            # Initialize velocity
            velocity = [random.uniform(-3, 3), random.uniform(-4, 0)]  # Random initial movement
            
            # Add to lists
            self.pet_windows.append(pet_window)
            self.pet_sprites.append({'canvas': canvas, 'sprite': pet_sprite, 'tk_image': pet_tk_image})
            self.pet_velocities.append(velocity)
            self.pet_is_dragging.append(False)
            self.pet_offset.append((0, 0))
            self.last_positions.append((x, y))
            
            # Update listbox
            self.pets_listbox.insert(tk.END, f"Pet {window_index + 1}: {width}x{height}")
            
            # Bind events (with the window index)
            canvas.bind("<Button-1>", lambda e, idx=window_index: self.on_click(e, idx))
            canvas.bind("<B1-Motion>", lambda e, idx=window_index: self.on_drag(e, idx))
            canvas.bind("<ButtonRelease-1>", lambda e, idx=window_index: self.on_release(e, idx))
            canvas.bind("<Double-Button-1>", lambda e, idx=window_index: self.on_double_click(e, idx))
            canvas.bind("<Button-3>", lambda e, idx=window_index: self.on_right_click(e, idx))
            
            # If this is the first pet, start animation
            if len(self.pet_windows) == 1:
                self.animate()
            
            self.status_var.set(f"Pet {window_index + 1} launched!")
            print(f"Pet window {window_index + 1} created successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create pet: {str(e)}")
    
    def remove_all_pets(self):
        """Remove all active pets"""
        if not self.is_running:
            return
            
        try:
            for pet_window in self.pet_windows:
                if pet_window.winfo_exists():
                    pet_window.destroy()
            
            # Clear all lists
            self.pet_windows = []
            self.pet_sprites = []
            self.pet_velocities = []
            self.pet_is_dragging = []
            self.pet_offset = []
            self.last_positions = []
            self.pet_images = []
            
            # Clear listbox
            self.pets_listbox.delete(0, tk.END)
            self.status_var.set("All pets removed")
        except Exception as e:
            print(f"Error removing pets: {e}")
    
    def on_click(self, event, window_index):
        """Handle mouse click on a pet"""
        if not self.is_running or window_index >= len(self.pet_is_dragging):
            return
            
        self.pet_is_dragging[window_index] = True
        self.pet_offset[window_index] = (event.x, event.y)
        self.pet_velocities[window_index] = [0, 0]  # Reset velocity when clicked
    
    def on_drag(self, event, window_index):
        """Handle dragging a pet"""
        if not self.is_running or not self.pet_is_dragging[window_index]:
            return
            
        try:
            # Get current window position
            x = self.pet_windows[window_index].winfo_x()
            y = self.pet_windows[window_index].winfo_y()
            
            # Calculate new position
            offset_x, offset_y = self.pet_offset[window_index]
            new_x = x + event.x - offset_x
            new_y = y + event.y - offset_y
            
            # Update window position
            self.pet_windows[window_index].geometry(f"+{new_x}+{new_y}")
            
            # Store positions for velocity calculation
            last_x, last_y = self.last_positions[window_index]
            
            # Calculate velocity
            self.pet_velocities[window_index][0] = new_x - last_x
            self.pet_velocities[window_index][1] = new_y - last_y
            
            # Update last position
            self.last_positions[window_index] = (new_x, new_y)
        except Exception as e:
            print(f"Error during drag: {e}")
    
    def on_release(self, event, window_index):
        """Handle mouse release on a pet"""
        if not self.is_running or window_index >= len(self.pet_is_dragging):
            return
            
        if self.pet_is_dragging[window_index]:
            self.pet_is_dragging[window_index] = False
            
            # Amplify velocity on release for throwing effect
            self.pet_velocities[window_index][0] *= 5
            self.pet_velocities[window_index][1] *= 5
    
    def on_double_click(self, event, window_index):
        """Handle double click - make the pet jump"""
        if not self.is_running or window_index >= len(self.pet_velocities):
            return
            
        self.pet_velocities[window_index][1] = -20  # Big upward jump
    
    def on_right_click(self, event, window_index):
        """Display context menu"""
        if not self.is_running:
            return
            
        menu = tk.Menu(self.root, tearoff=0)
        
        # Add menu items
        menu.add_command(label="Remove This Pet", 
                         command=lambda: self.remove_pet(window_index))
        menu.add_command(label="Throw Around", 
                         command=lambda: self.throw_pet(window_index))
        menu.add_separator()
        menu.add_command(label="Adjust Settings", command=self.root.lift)
        
        # Display menu at mouse position
        menu.post(event.x_root, event.y_root)
    
    def remove_pet(self, window_index):
        """Remove a specific pet"""
        if not self.is_running:
            return
            
        if window_index < len(self.pet_windows) and self.pet_windows[window_index].winfo_exists():
            self.pet_windows[window_index].destroy()
            self.status_var.set(f"Pet {window_index + 1} removed")
            
            # Mark as removed (will clean up later in animate())
            self.pet_velocities[window_index] = None
    
    def throw_pet(self, window_index):
        """Apply random velocity to throw the pet"""
        if not self.is_running or window_index >= len(self.pet_velocities):
            return
            
        self.pet_velocities[window_index][0] = random.randint(-30, 30)
        self.pet_velocities[window_index][1] = random.randint(-35, -15)
    
    def play_bounce_sound(self):
        """Play a random bounce sound if sounds are enabled"""
        if not self.is_running or not self.sound_enabled.get() or not self.bounce_sounds or not self.sound_init_success:
            return
            
        # Choose a random sound and play it
        sound = random.choice(self.bounce_sounds)
        try:
            sound.play()
        except Exception as e:
            print(f"Error playing sound: {e}")
            # Disable sound on error to prevent further errors
            self.sound_enabled.set(False)
    
    def check_pet_collision(self, i, j):
        """Check if two pets are colliding and handle the collision"""
        if not self.is_running:
            return False
            
        if i == j or not self.collision_enabled.get():
            return False
            
        # Get pet positions and dimensions
        try:
            w1 = self.pet_windows[i]
            w2 = self.pet_windows[j]
            
            # Get positions
            x1, y1 = w1.winfo_x(), w1.winfo_y()
            x2, y2 = w2.winfo_x(), w2.winfo_y()
            
            # Get dimensions
            width1, height1 = w1.winfo_width(), w1.winfo_height()
            width2, height2 = w2.winfo_width(), w2.winfo_height()
            
            # Calculate centers
            c1x, c1y = x1 + width1 // 2, y1 + height1 // 2
            c2x, c2y = x2 + width2 // 2, y2 + height2 // 2
            
            # Calculate distance between centers
            distance = math.sqrt((c1x - c2x) ** 2 + (c1y - c2y) ** 2)
            
            # Calculate minimum distance for collision
            min_distance = (width1 + width2) // 4  # Adjust for more natural collisions
            
            if distance < min_distance:
                # Collision detected!
                # Calculate angle of collision
                angle = math.atan2(c2y - c1y, c2x - c1x)
                
                # Exchange momentum (simplified physics)
                v1x, v1y = self.pet_velocities[i]
                v2x, v2y = self.pet_velocities[j]
                
                # Calculate new velocities (simplified elastic collision)
                temp_v1x = v2x * 0.8
                temp_v1y = v2y * 0.8
                temp_v2x = v1x * 0.8
                temp_v2y = v1y * 0.8
                
                self.pet_velocities[i][0] = temp_v1x
                self.pet_velocities[i][1] = temp_v1y
                self.pet_velocities[j][0] = temp_v2x
                self.pet_velocities[j][1] = temp_v2y
                
                # Add a little push to separate them
                push_x = math.cos(angle) * 30
                push_y = math.sin(angle) * 30
                
                self.pet_velocities[i][0] -= push_x
                self.pet_velocities[i][1] -= push_y
                self.pet_velocities[j][0] += push_x
                self.pet_velocities[j][1] += push_y
                
                # Play sound
                if self.sound_enabled.get():
                    self.play_bounce_sound()
                
                return True
            
            return False
        except Exception as e:
            # Skip collision detection if windows no longer exist
            return False
    
    def animate(self):
        """Main animation loop"""
        if not self.is_running:
            return
            
        # Process each pet
        active_pets = False
        
        for i in range(len(self.pet_windows)):
            # Skip if this pet has been removed
            if self.pet_velocities[i] is None:
                continue
                
            # Skip if window no longer exists
            if not self.pet_windows[i].winfo_exists():
                self.pet_velocities[i] = None
                continue
                
            active_pets = True
            
            # Skip if being dragged
            if self.pet_is_dragging[i]:
                continue
            
            try:
                # Get current position
                x = self.pet_windows[i].winfo_x()
                y = self.pet_windows[i].winfo_y()
                width = self.pet_windows[i].winfo_width()
                height = self.pet_windows[i].winfo_height()
                
                # Apply physics if enabled
                if self.gravity_enabled.get():
                    # Apply gravity
                    self.pet_velocities[i][1] += self.gravity_strength.get()
                
                if self.friction_enabled.get():
                    # Apply friction/air resistance
                    self.pet_velocities[i][0] *= self.friction_strength.get()
                    self.pet_velocities[i][1] *= self.friction_strength.get()
                
                # Store velocity before bounce for sound threshold check
                vel_before_bounce = self.pet_velocities[i].copy()
                
                # Update position
                new_x = x + self.pet_velocities[i][0]
                new_y = y + self.pet_velocities[i][1]
                
                # Check screen boundaries
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                
                # Flag to track if a significant bounce occurred
                significant_bounce = False
                
                # Handle horizontal boundaries
                if new_x < 0:
                    new_x = 0
                    self.pet_velocities[i][0] *= -self.bounce_strength.get()
                    # Check if horizontal velocity is significant
                    if abs(vel_before_bounce[0]) > 2.0:
                        significant_bounce = True
                elif new_x > screen_width - width and not self.multi_monitor.get():
                    new_x = screen_width - width
                    self.pet_velocities[i][0] *= -self.bounce_strength.get()
                    # Check if horizontal velocity is significant
                    if abs(vel_before_bounce[0]) > 2.0:
                        significant_bounce = True
                
            
                # Handle vertical boundaries
                if new_y < 0:
                    new_y = 0
                    self.pet_velocities[i][1] *= -self.bounce_strength.get()
                    # Check if vertical velocity is significant
                    if abs(vel_before_bounce[1]) > 2.0:
                        significant_bounce = True
                elif new_y > screen_height - height:
                    new_y = screen_height - height
                    self.pet_velocities[i][1] *= -self.bounce_strength.get()
                    # Check if vertical velocity is significant
                    if abs(vel_before_bounce[1]) > 2.0:
                        significant_bounce = True
                
                # Only play sound if bounce is significant and bounce sound is enabled
                if significant_bounce and self.bounce_enabled.get():
                    self.play_bounce_sound()
                
                # Update window position
                self.pet_windows[i].geometry(f"+{int(new_x)}+{int(new_y)}")
                
                # Update last position
                self.last_positions[i] = (new_x, new_y)
                
                # Check collisions with other pets
                for j in range(len(self.pet_windows)):
                    if self.pet_velocities[j] is not None:
                        self.check_pet_collision(i, j)
            except Exception as e:
                print(f"Error during animation: {e}")
        
        # Clean up removed pet windows
        if len(self.pet_windows) > 0:
            # Remove references to destroyed windows
            new_windows = []
            new_sprites = []
            new_velocities = []
            new_dragging = []
            new_offset = []
            new_positions = []
            new_images = []
            
            for i in range(len(self.pet_windows)):
                if self.pet_velocities[i] is not None:
                    new_windows.append(self.pet_windows[i])
                    new_sprites.append(self.pet_sprites[i])
                    new_velocities.append(self.pet_velocities[i])
                    new_dragging.append(self.pet_is_dragging[i])
                    new_offset.append(self.pet_offset[i])
                    new_positions.append(self.last_positions[i])
                    new_images.append(self.pet_images[i])
            
            # Update lists
            self.pet_windows = new_windows
            self.pet_sprites = new_sprites
            self.pet_velocities = new_velocities
            self.pet_is_dragging = new_dragging
            self.pet_offset = new_offset
            self.last_positions = new_positions
            self.pet_images = new_images
            
            # Update listbox
            self.pets_listbox.delete(0, tk.END)
            for i in range(len(self.pet_windows)):
                width = self.pet_windows[i].winfo_width()
                height = self.pet_windows[i].winfo_height()
                self.pets_listbox.insert(tk.END, f"Pet {i + 1}: {width}x{height}")
        
        # Continue animation if there are active pets and the application is running
        if active_pets and self.is_running:
            # Schedule the next animation frame (reduced to 15ms for smoother animation, physics depends on this)
            self.root.after(15, self.animate)
        else:
            # No active pets, stop animation loop
            print("Animation stopped - no active pets")

def safe_start():
    try:
        root = tk.Tk()
        root.title("Starting Plinko Pet...")
        
        # Set a minimum size for the root window to avoid scaling issues
        root.minsize(550, 650)
        
        # Create the application instance
        app = EnhancedPet(root)
        
        # Start the Tkinter event loop
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        # Try to clean up resources
        try:
            pygame.mixer.quit()
        except:
            pass

if __name__ == "__main__":
    safe_start()
