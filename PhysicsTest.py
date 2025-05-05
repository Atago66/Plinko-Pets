import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageFilter
import random
import math
import pygame
import os
import sys

class EnhancedPet:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Desktop Pet")
        self.root.geometry("550x650")
        self.root.configure(bg="#f0f0f0")
        
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
        self.warp_enabled = tk.BooleanVar(value=True)
        self.multi_monitor = tk.BooleanVar(value=False)
        self.collision_enabled = tk.BooleanVar(value=True)
        
        # Create UI
        self.create_ui()
    
    def create_default_sounds(self):
        """Create default bounce sounds using pygame"""
        # Create a few different bounce sounds with different pitches
        frequencies = [220, 330, 440, 550]
        duration = 100  # milliseconds
        
        for i, freq in enumerate(frequencies):
            sound_file = f"bounce_sound_{i}.wav"
            
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
        title = tk.Label(main_frame, text="Enhanced Desktop Pet", font=("Arial", 16, "bold"), bg="#f0f0f0")
        title.pack(pady=10)
        
        # Preview frame
        self.preview_frame = tk.Frame(main_frame, width=200, height=200, bg="white", relief=tk.SUNKEN, bd=1)
        self.preview_frame.pack(pady=10)
        self.preview_frame.pack_propagate(False)
        
        self.preview_label = tk.Label(self.preview_frame, text="Image Preview", bg="white")
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # Upload button
        upload_btn = tk.Button(main_frame, text="Upload Image", command=self.upload_image, 
                              bg="#4CAF50", fg="white", font=("Arial", 12), padx=10, pady=5)
        upload_btn.pack(pady=10)
        
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
        
        # Warp effect
        warp_check = tk.Checkbutton(visual_frame, text="Impact warp effect", variable=self.warp_enabled, 
                                   bg="#f0f0f0", font=("Arial", 10))
        warp_check.pack(anchor=tk.W, padx=15, pady=5)
        
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
        
        # Collision
        collision_check = tk.Checkbutton(other_frame, text="Enable collisions between pets", 
                                        variable=self.collision_enabled, bg="#f0f0f0", font=("Arial", 10))
        collision_check.pack(anchor=tk.W, padx=15, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status.pack(side=tk.BOTTOM, fill=tk.X)
    
    def upload_image(self):
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
                
                # Save and display preview
                self.active_image = image  # Store original image first
                
                # Create a PhotoImage for display and explicitly store it as an instance variable
                self.preview_image = ImageTk.PhotoImage(image)
                self.preview_label.config(image=self.preview_image, text="")
                
                # Reference in multiple places to avoid garbage collection issues
                self.preview_label.image = self.preview_image  # Keep a reference
                
                self.status_var.set(f"Image loaded: {file_path.split('/')[-1]}")
                
                print(f"Image loaded successfully: {image.width}x{image.height}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def launch_pet(self):
        if not hasattr(self, 'active_image'):
            messagebox.showwarning("Warning", "Please upload an image first!")
            return
        
        # Create a copy of the image for this pet instance
        pet_image = self.active_image.copy()
        
        # Apply size scaling if needed
        if self.size_scale.get() != 1.0:
            new_width = int(pet_image.width * self.size_scale.get())
            new_height = int(pet_image.height * self.size_scale.get())
            pet_image = pet_image.resize((new_width, new_height), Image.LANCZOS)
        
        # Store original image for warping effects
        original_image = pet_image.copy()
        
        # Add to pet images list
        self.pet_images.append({
            'image': pet_image,
            'original': original_image,
            'is_warped': False,
            'warp_counter': 0
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
        
        # Display pet image - ensure we keep a strong reference
        # Create the PhotoImage and store it explicitly
        pet_tk_image = ImageTk.PhotoImage(pet_image)
        
        # Create the image on canvas
        pet_sprite = canvas.create_image(
            width // 2,
            height // 2,
            image=pet_tk_image
        )
        
        # Store image reference on window to prevent garbage collection
        pet_window.pet_tk_image = pet_tk_image
        
        # Store pet-specific data
        window_index = len(self.pet_windows)
        
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
    
    def remove_all_pets(self):
        """Remove all active pets"""
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
    
    def on_click(self, event, window_index):
        """Handle mouse click on a pet"""
        self.pet_is_dragging[window_index] = True
        self.pet_offset[window_index] = (event.x, event.y)
        self.pet_velocities[window_index] = [0, 0]  # Reset velocity when clicked
    
    def on_drag(self, event, window_index):
        """Handle dragging a pet"""
        if self.pet_is_dragging[window_index]:
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
    
    def on_release(self, event, window_index):
        """Handle mouse release on a pet"""
        if self.pet_is_dragging[window_index]:
            self.pet_is_dragging[window_index] = False
            
            # Amplify velocity on release for throwing effect
            self.pet_velocities[window_index][0] *= 5
            self.pet_velocities[window_index][1] *= 5
    
    def on_double_click(self, event, window_index):
        """Handle double click - make the pet jump"""
        self.pet_velocities[window_index][1] = -20  # Big upward jump
    
    def on_right_click(self, event, window_index):
        """Display context menu"""
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
        if window_index < len(self.pet_windows) and self.pet_windows[window_index].winfo_exists():
            self.pet_windows[window_index].destroy()
            self.status_var.set(f"Pet {window_index + 1} removed")
            
            # Mark as removed (will clean up later in animate())
            self.pet_velocities[window_index] = None
    
    def throw_pet(self, window_index):
        """Apply random velocity to throw the pet"""
        self.pet_velocities[window_index][0] = random.randint(-30, 30)
        self.pet_velocities[window_index][1] = random.randint(-35, -15)
    
    def play_bounce_sound(self):
        """Play a random bounce sound if sounds are enabled"""
        if not self.sound_enabled.get() or not self.bounce_sounds or not self.sound_init_success:
            return
            
        # Choose a random sound and play it
        sound = random.choice(self.bounce_sounds)
        try:
            sound.play()
        except Exception as e:
            print(f"Error playing sound: {e}")
            # Disable sound on error to prevent further errors
            self.sound_enabled.set(False)
    
    def warp_image(self, window_index):
        """Apply a temporary warping effect to the image"""
        if not self.warp_enabled.get():
            return
            
        if self.pet_images[window_index]['is_warped']:
            # Already warped, skip
            return
            
        try:
            # Get original image
            orig_img = self.pet_images[window_index]['original']
            
            # Create warped version - use a more compatible filter if BULGE is not available
            try:
                warped = orig_img.filter(ImageFilter.BULGE)
            except AttributeError:
                # Fall back to a different filter if BULGE is not available in this Pillow version
                warped = orig_img.filter(ImageFilter.CONTOUR)
                if hasattr(ImageFilter, "EMBOSS"):
                    warped = warped.filter(ImageFilter.EMBOSS)
            
            # Update the display
            self.pet_images[window_index]['image'] = warped
            self.pet_images[window_index]['is_warped'] = True
            self.pet_images[window_index]['warp_counter'] = 5  # Frames to keep warped
            
            # Update the image in the canvas with strong references
            pet_tk_image = ImageTk.PhotoImage(warped)
            
            # Update references to prevent garbage collection
            self.pet_sprites[window_index]['tk_image'] = pet_tk_image
            self.pet_windows[window_index].pet_tk_image = pet_tk_image  # Store on window too
            
            # Update the image in canvas
            self.pet_sprites[window_index]['canvas'].itemconfig(
                self.pet_sprites[window_index]['sprite'], 
                image=pet_tk_image
            )
        except Exception as e:
            print(f"Error warping image: {e}")
    
    def restore_image_after_warp(self, window_index):
        """Restore image to original after warping effect"""
        if not self.pet_images[window_index]['is_warped']:
            return
            
        # Decrease counter
        self.pet_images[window_index]['warp_counter'] -= 1
        
        if self.pet_images[window_index]['warp_counter'] <= 0:
            # Restore original image
            orig_img = self.pet_images[window_index]['original']
            self.pet_images[window_index]['image'] = orig_img
            self.pet_images[window_index]['is_warped'] = False
            
            # Update the image in the canvas with strong references
            pet_tk_image = ImageTk.PhotoImage(orig_img)
            
            # Update references to prevent garbage collection
            self.pet_sprites[window_index]['tk_image'] = pet_tk_image
            self.pet_windows[window_index].pet_tk_image = pet_tk_image  # Store on window too
            
            # Update the image in canvas
            self.pet_sprites[window_index]['canvas'].itemconfig(
                self.pet_sprites[window_index]['sprite'], 
                image=pet_tk_image
            )
    
    def check_pet_collision(self, i, j):
        """Check if two pets are colliding and handle the collision"""
        if i == j or not self.collision_enabled.get():
            return False
            
        # Get pet positions and dimensions
        w1 = self.pet_windows[i]
        w2 = self.pet_windows[j]
        
        if not w1.winfo_exists() or not w2.winfo_exists():
            return False
            
        x1, y1 = w1.winfo_x(), w1.winfo_y()
        x2, y2 = w2.winfo_x(), w2.winfo_y()
        
        width1, height1 = w1.winfo_width(), w1.winfo_height()
        width2, height2 = w2.winfo_width(), w2.winfo_height()
        
        # Calculate centers
        cx1 = x1 + width1/2
        cy1 = y1 + height1/2
        cx2 = x2 + width2/2
        cy2 = y2 + height2/2
        
        # Calculate collision radii (average of width and height)
        r1 = (width1 + height1) / 4
        r2 = (width2 + height2) / 4
        
        # Calculate distance between centers
        distance = math.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
        
        # If distance is less than sum of radii, collision occurred
        if distance < (r1 + r2) * 0.8:  # 0.8 factor for better visual collision
            # Calculate collision normal vector
            if distance > 0:  # Avoid division by zero
                nx = (cx2 - cx1) / distance
                ny = (cy2 - cy1) / distance
            else:
                nx, ny = 0, -1  # Default if centers are exactly the same
                
            # Calculate relative velocity
            rvx = self.pet_velocities[j][0] - self.pet_velocities[i][0]
            rvy = self.pet_velocities[j][1] - self.pet_velocities[i][1]
            
            # Calculate velocity component along normal
            vel_along_normal = rvx * nx + rvy * ny
            
            # If objects are moving away from each other, no collision response
            if vel_along_normal > 0:
                return False
                
            # Calculate bounce coefficient (average of bounce strength)
            bounce = self.bounce_strength.get() if self.bounce_enabled.get() else 0.2
                
            # Calculate impulse scalar
            impulse = -(1 + bounce) * vel_along_normal
            impulse /= 2  # Split impulse between both objects
            
            # Apply impulse to velocities
            self.pet_velocities[i][0] -= impulse * nx
            self.pet_velocities[i][1] -= impulse * ny
            self.pet_velocities[j][0] += impulse * nx
            self.pet_velocities[j][1] += impulse * ny
            
            # Move pets slightly apart to prevent sticking
            overlap = (r1 + r2) - distance
            if overlap > 0:
                self.pet_windows[i].geometry(f"+{int(x1 - nx * overlap/2)}+{int(y1 - ny * overlap/2)}")
                self.pet_windows[j].geometry(f"+{int(x2 + nx * overlap/2)}+{int(y2 + ny * overlap/2)}")
                
            # Play bounce sound
            self.play_bounce_sound()
            
            # Apply warping to both pets
            self.warp_image(i)
            self.warp_image(j)
                
            return True
            
        return False
    
    def animate(self):
        """Animation loop for all pets"""
        # Check if we have any pets left
        active_windows = []
        for i, window in enumerate(self.pet_windows):
            if window.winfo_exists() and self.pet_velocities[i] is not None:
                active_windows.append(i)
        
        # If no active windows, stop animation
        if not active_windows:
            return
        
        # Process each active pet
        for i in active_windows:
            if self.pet_is_dragging[i]:
                continue  # Skip if being dragged
                
            # Get current position
            window = self.pet_windows[i]
            x = window.winfo_x()
            y = window.winfo_y()
            width = window.winfo_width()
            height = window.winfo_height()
            
            # Apply gravity if enabled
            if self.gravity_enabled.get():
                self.pet_velocities[i][1] += self.gravity_strength.get()
            
            # Apply velocity
            x += int(self.pet_velocities[i][0])
            y += int(self.pet_velocities[i][1])
            
            # Apply friction if enabled
            if self.friction_enabled.get():
                self.pet_velocities[i][0] *= self.friction_strength.get()
                self.pet_velocities[i][1] *= self.friction_strength.get()
            
            # Handle screen boundaries
            screen_boundaries_hit = False
            
            # Define screen boundaries based on multi-monitor setting
            if self.multi_monitor.get():
                # Use full virtual screen space
                max_x = self.root.winfo_screenwidth()
                max_y = self.root.winfo_screenheight()
                min_x = 0
                min_y = 0
            else:
                # Use only primary monitor
                max_x = self.root.winfo_screenwidth()
                max_y = self.root.winfo_screenheight()
                min_x = 0
                min_y = 0
            
            # Bottom boundary
            if y + height > max_y:
                y = max_y - height
                if self.bounce_enabled.get():
                    self.pet_velocities[i][1] = -self.pet_velocities[i][1] * self.bounce_strength.get()
                else:
                    self.pet_velocities[i][1] = 0
                
                screen_boundaries_hit = True
                
                # Stop if velocity is very small
                if abs(self.pet_velocities[i][1]) < 0.5:
                    self.pet_velocities[i][1] = 0
            
            # Top boundary
            if y < min_y:
                y = min_y
                if self.bounce_enabled.get():
                    self.pet_velocities[i][1] = -self.pet_velocities[i][1] * self.bounce_strength.get()
                else:
                    self.pet_velocities[i][1] = 0
                    
                screen_boundaries_hit = True
            
            # Right boundary
            if x + width > max_x:
                x = max_x - width
                if self.bounce_enabled.get():
                    self.pet_velocities[i][0] = -self.pet_velocities[i][0] * self.bounce_strength.get()
                else:
                    self.pet_velocities[i][0] = 0
                    
                screen_boundaries_hit = True
            
            # Left boundary
            if x < min_x:
                x = min_x
                if self.bounce_enabled.get():
                    self.pet_velocities[i][0] = -self.pet_velocities[i][0] * self.bounce_strength.get()
                else:
                    self.pet_velocities[i][0] = 0
                    
                screen_boundaries_hit = True
            
            # Play bounce sound and apply warp effect if hit boundary
            if screen_boundaries_hit:
                self.play_bounce_sound()
                self.warp_image(i)
            
            # Update position
            window.geometry(f"+{x}+{y}")
            self.last_positions[i] = (x, y)
            
            # Process warping recovery if necessary
            if self.pet_images[i]['is_warped']:
                self.restore_image_after_warp(i)
        
        # Process pet collisions
        for i in range(len(active_windows)):
            for j in range(i+1, len(active_windows)):
                idx1 = active_windows[i]
                idx2 = active_windows[j]
                self.check_pet_collision(idx1, idx2)
        
        # Clean up deleted pets
        for i in reversed(range(len(self.pet_windows))):
            window = self.pet_windows[i]
            if not window.winfo_exists() or self.pet_velocities[i] is None:
                # Remove from lists
                self.pet_windows.pop(i)
                self.pet_sprites.pop(i)
                self.pet_velocities.pop(i)
                self.pet_is_dragging.pop(i)
                self.pet_offset.pop(i)
                self.last_positions.pop(i)
                self.pet_images.pop(i)
                
                # Update listbox
                self.pets_listbox.delete(i)
                
                # Renumber remaining pets in listbox
                for j in range(i, self.pets_listbox.size()):
                    old_text = self.pets_listbox.get(j)
                    # Extract dimensions
                    dimensions = old_text.split(": ")[1] if ": " in old_text else ""
                    new_text = f"Pet {j + 1}: {dimensions}"
                    self.pets_listbox.delete(j)
                    self.pets_listbox.insert(j, new_text)
        
        # Schedule next animation frame
        self.root.after(16, self.animate)  # ~60 FPS


if __name__ == "__main__":
    root = tk.Tk()
    
    # Try to set a nicer theme if available
    try:
        from ttkthemes import ThemedTk
        root = ThemedTk(theme="arc")
    except ImportError:
        # Continue with regular tk
        pass
        
    app = EnhancedPet(root)
    root.mainloop()