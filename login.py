import tkinter as tk
from tkinter import ttk, messagebox
import json
import hashlib
import os
import random
import time
from datetime import datetime
import sqlite3
from PIL import Image, ImageTk

class GameApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Game Center")
        self.root.geometry("800x600")
        
        # Initialize database
        self.init_database()
        
        # Theme settings
        self.theme = {
            'light': {
                'bg': '#ffffff',
                'fg': '#000000',
                'button': '#e0e0e0',
                'highlight': '#4a90e2'
            },
            'dark': {
                'bg': '#2d2d2d',
                'fg': '#ffffff',
                'button': '#404040',
                'highlight': '#5a9ee2'
            }
        }
        self.current_theme = 'light'
        
        self.current_user = None
        self.create_frames()
        self.show_login_frame()
        
    def init_database(self):
        self.conn = sqlite3.connect('gameapp.db')
        self.cursor = self.conn.cursor()
        
        # First, check if the users table exists and its structure
        self.cursor.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name='users'
        ''')
        if self.cursor.fetchone():
            # Table exists, check for new columns
            self.cursor.execute('PRAGMA table_info(users)')
            columns = [col[1] for col in self.cursor.fetchall()]
            
            # Add new columns if they don't exist
            if 'failed_attempts' not in columns:
                self.cursor.execute('ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0')
            if 'last_attempt' not in columns:
                self.cursor.execute('ALTER TABLE users ADD COLUMN last_attempt DATETIME')
        else:
            # Create users table with all columns
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    theme TEXT,
                    created_at DATETIME,
                    failed_attempts INTEGER DEFAULT 0,
                    last_attempt DATETIME
                )
            ''')
        
        # Create profiles table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                username TEXT PRIMARY KEY,
                display_name TEXT,
                avatar TEXT,
                bio TEXT,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Create achievements table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                username TEXT,
                achievement TEXT,
                earned_at DATETIME,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Create scores table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                username TEXT,
                game TEXT,
                score INTEGER,
                date DATETIME,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Create todos table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY,
                username TEXT,
                task TEXT,
                completed BOOLEAN,
                created_at DATETIME,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Create notes table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                username TEXT,
                title TEXT,
                content TEXT,
                updated_at DATETIME,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Create settings table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                username TEXT PRIMARY KEY,
                notification_enabled BOOLEAN DEFAULT 1,
                sound_enabled BOOLEAN DEFAULT 1,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Create game_stats table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_stats (
                username TEXT,
                game TEXT,
                total_time INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                high_score INTEGER DEFAULT 0,
                FOREIGN KEY (username) REFERENCES users(username),
                PRIMARY KEY (username, game)
            )
        ''')
        
        self.conn.commit()
        
    def hash_password(self, password):
        return password
        
    def create_frames(self):
        # Authentication Frames
        self.login_frame = self.create_login_frame()
        self.signup_frame = self.create_signup_frame()
        
        # Main App Frames
        self.dashboard_frame = self.create_dashboard_frame()
        self.settings_frame = self.create_settings_frame()
        self.games_frame = self.create_game_frames()  # Fixed method name
        self.utilities_frame = self.create_utilities_frame()
        self.stats_frame = self.create_stats_frame()


    def create_login_frame(self):
        frame = ttk.Frame(self.root, padding="20")
        
        # Animated welcome banner
        self.login_banner = ttk.Label(frame, text="Welcome to Game Center", 
                                    font=('Arial', 28, 'bold'))
        self.login_banner.pack(pady=20)
        self.animate_login_banner()
        
        # Login container with visual effects
        login_container = ttk.LabelFrame(frame, text="Login", padding="20")
        login_container.pack(pady=10, padx=20, fill='x')
        
        # Username field with icon
        username_frame = ttk.Frame(login_container)
        username_frame.pack(fill='x', pady=5)
        ttk.Label(username_frame, text="👤").pack(side='left', padx=5)
        self.login_username = ttk.Entry(username_frame, width=30)
        self.login_username.pack(side='left', padx=5)
        
        # Password field with icon and show/hide toggle
        password_frame = ttk.Frame(login_container)
        password_frame.pack(fill='x', pady=5)
        ttk.Label(password_frame, text="🔒").pack(side='left', padx=5)
        self.login_password = ttk.Entry(password_frame, show="*", width=30)
        self.login_password.pack(side='left', padx=5)
        
        # Show/Hide password button
        self.show_password_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(password_frame, text="👁", variable=self.show_password_var,
                       command=self.toggle_password_visibility).pack(side='left')
        
        # Enter key bindings
        self.login_username.bind('<Return>', lambda e: self.login_password.focus())
        self.login_password.bind('<Return>', lambda e: self.login())
        
        # Login button with hover effect
        login_btn = ttk.Button(login_container, text="Login", command=self.login)
        login_btn.pack(pady=10, fill='x')
        
        # Create account link
        signup_frame = ttk.Frame(login_container)
        signup_frame.pack(fill='x', pady=5)
        ttk.Label(signup_frame, text="Don't have an account?").pack(side='left', padx=5)
        signup_link = ttk.Button(signup_frame, text="Create Account",
                               command=lambda: self.show_frame(self.signup_frame))
        signup_link.pack(side='left')
        
        # Quick stats display
        stats_frame = ttk.LabelFrame(frame, text="Community Stats", padding=10)
        stats_frame.pack(fill='x', pady=10, padx=20)
        self.stats_label = ttk.Label(stats_frame, text="Loading stats...")
        self.stats_label.pack(pady=5)
        self.update_login_stats()
        
        return frame
        
    def show_users_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("View Users")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Enter Admin Password:").pack(pady=10)
        password_entry = ttk.Entry(dialog, show="*")
        password_entry.pack(pady=5)
        
        def show_users():
            if password_entry.get() == "r6967815":
                users_window = tk.Toplevel(self.root)
                users_window.title("User List")
                users_window.geometry("400x300")
                users_window.transient(self.root)
                users_window.grab_set()
                
                # Create scrolled text widget
                text_widget = tk.Text(users_window, wrap=tk.WORD, height=15, width=40)
                scrollbar = ttk.Scrollbar(users_window, orient="vertical", command=text_widget.yview)
                text_widget.configure(yscrollcommand=scrollbar.set)
                
                text_widget.pack(side="left", fill="both", expand=True, padx=10, pady=10)
                scrollbar.pack(side="right", fill="y")
                
                # Fetch and display users
                self.cursor.execute('SELECT username, password FROM users')
                users = self.cursor.fetchall()
                
                text_widget.insert(tk.END, "Username | Password\n")
                text_widget.insert(tk.END, "-" * 30 + "\n")
                
                for username, password in users:
                    text_widget.insert(tk.END, f"{username} | {password}\n")
                
                text_widget.configure(state='disabled')
                
                def close_windows():
                    users_window.destroy()
                    dialog.destroy()
                
                ttk.Button(users_window, text="Close", command=close_windows).pack(pady=10)
            else:
                messagebox.showerror("Error", "Incorrect password", parent=dialog)
        
        ttk.Button(dialog, text="View", command=show_users).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()        

    def show_random_quote(self):
        quote = random.choice(self.quotes)
        self.quote_label.config(text=quote)
        
    def show_add_quote_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Quote")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Enter Password:").pack(pady=5)
        password_entry = ttk.Entry(dialog, show="*")
        password_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Enter New Quote:").pack(pady=5)
        quote_entry = ttk.Entry(dialog, width=40)
        quote_entry.pack(pady=5)
        
        def add_quote():
            if password_entry.get() == "6967815":
                new_quote = quote_entry.get().strip()
                if new_quote:
                    self.quotes.append(new_quote)
                    messagebox.showinfo("Success", "Quote added successfully!", parent=dialog)
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Please enter a quote", parent=dialog)
            else:
                messagebox.showerror("Error", "Incorrect password", parent=dialog)
        
        ttk.Button(dialog, text="Add", command=add_quote).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()

    def toggle_theme_preview(self):
        self.current_preview = 'dark' if self.current_preview == 'light' else 'light'
        self.draw_theme_preview()
        
    def draw_theme_preview(self):
        theme_colors = self.theme[self.current_preview]
        self.preview_canvas.delete('all')
        self.preview_canvas.configure(bg=theme_colors['bg'])
        self.preview_canvas.create_text(100, 15, text=f"{self.current_preview.title()} Theme",
                                      fill=theme_colors['fg'])
        
    def update_visitor_count(self):
        self.visitor_count += random.randint(1, 5)
        self.visitor_label.config(text=f"Today's Visitors: {self.visitor_count}")
        
    def create_signup_frame(self):
        frame = ttk.Frame(self.root, padding="20")
        
        # Animated title with progress
        self.signup_title = ttk.Label(frame, text="Create Your Account", 
                                    font=('Arial', 24, 'bold'))
        self.signup_title.pack(pady=20)
        
        # Progress indicator
        self.signup_progress = ttk.Progressbar(frame, length=300, mode='determinate')
        self.signup_progress.pack(pady=10)
        
        # Signup container
        signup_container = ttk.LabelFrame(frame, text="Account Details", padding="20")
        signup_container.pack(pady=10, padx=20, fill='x')
        
        # Username field with availability checker
        username_frame = ttk.Frame(signup_container)
        username_frame.pack(fill='x', pady=5)
        ttk.Label(username_frame, text="👤").pack(side='left', padx=5)
        self.signup_username = ttk.Entry(username_frame, width=30)
        self.signup_username.pack(side='left', padx=5)
        self.username_status = ttk.Label(username_frame, text="❓")
        self.username_status.pack(side='left', padx=5)
        
        # Password field with strength indicator
        password_frame = ttk.Frame(signup_container)
        password_frame.pack(fill='x', pady=5)
        ttk.Label(password_frame, text="🔒").pack(side='left', padx=5)
        self.signup_password = ttk.Entry(password_frame, show="*", width=30)
        self.signup_password.pack(side='left', padx=5)
        self.password_strength = ttk.Label(password_frame, text="")
        self.password_strength.pack(side='left', padx=5)
        
        # Confirm password field
        confirm_frame = ttk.Frame(signup_container)
        confirm_frame.pack(fill='x', pady=5)
        ttk.Label(confirm_frame, text="🔒").pack(side='left', padx=5)
        self.signup_confirm = ttk.Entry(confirm_frame, show="*", width=30)
        self.signup_confirm.pack(side='left', padx=5)
        self.confirm_status = ttk.Label(confirm_frame, text="")
        self.confirm_status.pack(side='left', padx=5)
        
        # Create account button
        create_btn = ttk.Button(signup_container, text="Create Account", 
                              command=self.create_account)
        create_btn.pack(pady=10, fill='x')
        
        # Back to login link
        back_frame = ttk.Frame(signup_container)
        back_frame.pack(fill='x', pady=5)
        ttk.Label(back_frame, text="Already have an account?").pack(side='left', padx=5)
        back_btn = ttk.Button(back_frame, text="Login", 
                            command=lambda: self.show_frame(self.login_frame))
        back_btn.pack(side='left')
        
        # Bind events for real-time validation
        self.signup_username.bind('<KeyRelease>', self.check_username_availability)
        self.signup_password.bind('<KeyRelease>', self.check_password_strength)
        self.signup_confirm.bind('<KeyRelease>', self.check_passwords_match)
        
        # Enter key bindings
        self.signup_username.bind('<Return>', lambda e: self.signup_password.focus())
        self.signup_password.bind('<Return>', lambda e: self.signup_confirm.focus())
        self.signup_confirm.bind('<Return>', lambda e: self.create_account())
        
        return frame


    def create_dashboard_frame(self):
        frame = ttk.Frame(self.root, padding="20")
        
        # Welcome section with animated dots
        self.welcome_label = ttk.Label(frame, font=('Arial', 24))
        self.welcome_label.pack(pady=10)
        
        # Quick Stats Panel
        stats_frame = ttk.LabelFrame(frame, text="Your Activity", padding=10)
        stats_frame.pack(fill='x', pady=10)
        
        self.quick_stats_label = ttk.Label(stats_frame, text="Loading stats...", font=('Arial', 10))
        self.quick_stats_label.pack(pady=5)
        
        # Main Navigation with hover effects
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(pady=20)
        
        # Create buttons with icons and descriptions
        game_btn = ttk.Button(buttons_frame, text="🎮 Games", 
                          command=lambda: self.show_frame(self.games_frame))
        game_btn.pack(side='left', padx=10)
        
        utils_btn = ttk.Button(buttons_frame, text="🛠 Utilities", 
                           command=lambda: self.show_frame(self.utilities_frame))
        utils_btn.pack(side='left', padx=10)
        
        stats_btn = ttk.Button(buttons_frame, text="📊 Stats", 
                           command=lambda: self.show_frame(self.stats_frame))
        stats_btn.pack(side='left', padx=10)
        
        settings_btn = ttk.Button(buttons_frame, text="⚙ Settings", 
                              command=lambda: self.show_frame(self.settings_frame))
        settings_btn.pack(side='left', padx=10)
        
        # Recent Activity Feed
        activity_frame = ttk.LabelFrame(frame, text="Recent Activity", padding=10)
        activity_frame.pack(fill='x', pady=10)
        
        self.activity_text = tk.Text(activity_frame, height=4, wrap=tk.WORD)
        self.activity_text.pack(fill='x', pady=5)
        
        # Daily Challenge
        challenge_frame = ttk.LabelFrame(frame, text="Daily Challenge", padding=10)
        challenge_frame.pack(fill='x', pady=10)
        
        self.challenge_label = ttk.Label(challenge_frame, text="Loading challenge...", 
                                       font=('Arial', 10))
        self.challenge_label.pack(pady=5)
        
        # Start the dashboard updates
        self.update_dashboard_elements()
        
        return frame

    def update_dashboard_elements(self):
        if hasattr(self, 'welcome_label'):
            # Update quick stats
            self.cursor.execute('''
                SELECT COUNT(*) from scores WHERE username=?
            ''', (self.current_user,))
            games_played = self.cursor.fetchone()[0]
            
            self.cursor.execute('''
                SELECT MAX(score) from scores WHERE username=? AND game="typing"
            ''', (self.current_user,))
            best_typing = self.cursor.fetchone()[0] or 0
            
            stats_text = f"Games Played: {games_played}\n"
            stats_text += f"Best Typing Score: {best_typing} WPM"
            self.quick_stats_label.config(text=stats_text)
            
            # Update activity feed
            self.cursor.execute('''
                SELECT game, score, date FROM scores 
                WHERE username=? ORDER BY date DESC LIMIT 3
            ''', (self.current_user,))
            activities = self.cursor.fetchall()
            
            activity_text = "Recent Games:\n"
            for game, score, date in activities:
                activity_text += f"• {game.title()}: Score {score}\n"
            
            self.activity_text.delete(1.0, tk.END)
            self.activity_text.insert(tk.END, activity_text)
            
            # Update daily challenge
            challenges = [
                "Complete a typing game with score > 30 WPM",
                "Solve the puzzle in less than 50 moves",
                "Get a perfect score in Memory Game",
                "Play all available games today"
            ]
            self.challenge_label.config(text=random.choice(challenges))
            
            # Schedule next update
            self.root.after(5000, self.update_dashboard_elements)


    def create_settings_frame(self):
        frame = ttk.Frame(self.root, padding="20")
        
        ttk.Label(frame, text="Settings", font=('Arial', 24)).pack(pady=20)
        
        # User Info Section
        info_frame = ttk.LabelFrame(frame, text="Account Information", padding=10)
        info_frame.pack(fill='x', pady=10)
        
        # Username display
        ttk.Label(info_frame, text="Username:").pack(anchor='w')
        username_label = ttk.Label(info_frame, text=self.current_user, font=('Arial', 10, 'bold'))
        username_label.pack(anchor='w', pady=(0, 10))
        
        # Password display with toggle
        ttk.Label(info_frame, text="Password:").pack(anchor='w')
        password_frame = ttk.Frame(info_frame)
        password_frame.pack(fill='x', pady=(0, 10))
        
        self.password_var = tk.StringVar(value='●' * 8)  # Default hidden
        password_label = ttk.Label(password_frame, textvariable=self.password_var, font=('Arial', 10))
        password_label.pack(side='left')
        
        def toggle_password():
            # Get actual password from database
            self.cursor.execute('SELECT password FROM users WHERE username=?', (self.current_user,))
            current_pass = self.cursor.fetchone()[0]
            
            if self.password_var.get().startswith('●'):
                self.password_var.set(current_pass)
                toggle_btn.config(text="Hide")
            else:
                self.password_var.set('●' * 8)
                toggle_btn.config(text="Show")
        
        toggle_btn = ttk.Button(password_frame, text="Show", width=8, command=toggle_password)
        toggle_btn.pack(side='left', padx=10)
        
        # Separator
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=20)
        
        # Rest of the settings
        # Theme toggle
        theme_frame = ttk.Frame(frame)
        theme_frame.pack(fill='x', pady=10)
        ttk.Label(theme_frame, text="Theme:").pack(side='left')
        self.theme_var = tk.StringVar(value='light')
        ttk.Radiobutton(theme_frame, text="Light", variable=self.theme_var, 
                       value='light', command=self.toggle_theme).pack(side='left', padx=10)
        ttk.Radiobutton(theme_frame, text="Dark", variable=self.theme_var, 
                       value='dark', command=self.toggle_theme).pack(side='left')
        
        # Change password
        ttk.Button(frame, text="Change Password", 
                  command=self.show_change_password_dialog).pack(pady=10)
        
        # Reset account
        ttk.Button(frame, text="Reset Account Data", 
                  command=self.reset_account_data).pack(pady=10)
        
        # Delete account
        ttk.Button(frame, text="Delete Account", 
                  command=self.show_delete_account_dialog,
                  style='Danger.TButton').pack(pady=10)
        
        # Back and logout buttons
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(pady=20)
        ttk.Button(buttons_frame, text="Back to Dashboard", 
                  command=lambda: self.show_frame(self.dashboard_frame)).pack(side='left', padx=10)
        ttk.Button(buttons_frame, text="Logout", 
                  command=self.logout).pack(side='left')
        
        return frame

        
    def create_game_frames(self):
        # Create main games frame
        games_frame = ttk.Frame(self.root)
        
        # Create scrollable canvas for games
        canvas = tk.Canvas(games_frame)
        scrollbar = ttk.Scrollbar(games_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(e):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
        def _unbind_mousewheel(e):
            canvas.unbind_all("<MouseWheel>")
            
        canvas.bind('<Enter>', _bind_mousewheel)
        canvas.bind('<Leave>', _unbind_mousewheel)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Add game buttons
        ttk.Label(scrollable_frame, text="Choose a game to play:", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        ttk.Button(scrollable_frame, text="Math Quiz", 
                  command=self.start_math_quiz).pack(pady=10)
        
        ttk.Button(scrollable_frame, text="Memory Cards", 
                  command=self.start_memory_game).pack(pady=10)
        
        ttk.Button(scrollable_frame, text="Snake Game", 
                  command=self.start_snake_game).pack(pady=10)
        
        ttk.Button(scrollable_frame, text="Tic Tac Toe", 
                  command=self.start_tictactoe).pack(pady=10)
        
        ttk.Button(scrollable_frame, text="2048", 
                  command=self.start_2048).pack(pady=10)
        
        ttk.Button(scrollable_frame, text="Word Scramble", 
                  command=self.start_word_scramble).pack(pady=10)
        
        ttk.Button(scrollable_frame, text="Color Match", 
                  command=self.start_color_match).pack(pady=10)
        
        ttk.Button(scrollable_frame, text="Pattern Memory", 
                  command=self.start_pattern_memory).pack(pady=10)
        
        ttk.Button(scrollable_frame, text="Reaction Timer", 
                  command=self.start_reaction_game).pack(pady=10)
        
        ttk.Button(scrollable_frame, text="Hangman", 
                  command=self.start_hangman).pack(pady=10)
        
        ttk.Button(scrollable_frame, text="Sliding Puzzle", 
                  command=self.start_puzzle_game).pack(pady=10)
        
        # Back button
        ttk.Button(games_frame, text="Back to Dashboard", 
                  command=lambda: self.show_frame(self.dashboard_frame)).pack(pady=10)
        
        return games_frame

    def create_utilities_frame(self):
        frame = ttk.Frame(self.root, padding="20")
        
        # Create a canvas with scrollbar
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(e):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
        def _unbind_mousewheel(e):
            canvas.unbind_all("<MouseWheel>")
            
        canvas.bind('<Enter>', _bind_mousewheel)
        canvas.bind('<Leave>', _unbind_mousewheel)
        
        # Title
        ttk.Label(scrollable_frame, text="Utilities", font=('Arial', 24)).pack(pady=20)
        
        # Calculator
        calc_frame = ttk.LabelFrame(scrollable_frame, text="Calculator", padding="10")
        calc_frame.pack(fill='x', pady=10)
        
        self.calc_display = ttk.Entry(calc_frame, justify='right', font=('Arial', 12))
        self.calc_display.pack(fill='x', pady=5)
        
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]
        
        button_frame = ttk.Frame(calc_frame)
        button_frame.pack()
        
        row = 0
        col = 0
        for button in buttons:
            cmd = lambda x=button: self.calculator_click(x)
            ttk.Button(button_frame, text=button, command=cmd, width=5).grid(row=row, column=col, padx=2, pady=2)
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        ttk.Button(calc_frame, text="Clear", command=self.calculator_clear).pack(pady=5)
        
        # Todo List
        todo_frame = ttk.LabelFrame(scrollable_frame, text="Todo List", padding="10")
        todo_frame.pack(fill='x', pady=10)
        
        todo_input_frame = ttk.Frame(todo_frame)
        todo_input_frame.pack(fill='x')
        
        self.todo_entry = ttk.Entry(todo_input_frame)
        self.todo_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        ttk.Button(todo_input_frame, text="Add", command=self.add_todo).pack(side='right')
        
        self.todo_listbox = tk.Listbox(todo_frame, height=5)
        self.todo_listbox.pack(fill='x', pady=5)
        
        # Notes
        notes_frame = ttk.LabelFrame(scrollable_frame, text="Quick Notes", padding="10")
        notes_frame.pack(fill='x', pady=10)
        
        self.notes_text = tk.Text(notes_frame, height=5)
        self.notes_text.pack(fill='x', pady=5)
        
        ttk.Button(notes_frame, text="Save Note", command=self.save_note).pack()
        
        # Pomodoro Timer
        timer_frame = ttk.LabelFrame(scrollable_frame, text="Pomodoro Timer", padding="10")
        timer_frame.pack(fill='x', pady=10)
        
        self.timer_label = ttk.Label(timer_frame, text="25:00", font=('Arial', 20))
        self.timer_label.pack(pady=5)
        
        timer_buttons = ttk.Frame(timer_frame)
        timer_buttons.pack()
        
        ttk.Button(timer_buttons, text="Start", command=self.start_timer).pack(side='left', padx=5)
        ttk.Button(timer_buttons, text="Stop", command=self.stop_timer).pack(side='left', padx=5)
        ttk.Button(timer_buttons, text="Reset", command=self.reset_timer).pack(side='left', padx=5)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Back button in a separate frame
        back_frame = ttk.Frame(frame)
        back_frame.pack(side='bottom', fill='x', pady=10)
        ttk.Button(back_frame, text="Back to Dashboard", 
                  command=lambda: self.show_frame(self.dashboard_frame)).pack()
        
        return frame

        
    def create_stats_frame(self):
        frame = ttk.Frame(self.root, padding="20")
        
        ttk.Label(frame, text="Statistics", font=('Arial', 24)).pack(pady=20)
        
        self.stats_text = tk.Text(frame, height=10, width=40)
        self.stats_text.pack(pady=10)
        
        ttk.Button(frame, text="Back to Dashboard", 
                  command=lambda: self.show_frame(self.dashboard_frame)).pack(pady=20)
        
        return frame
        
    def show_frame(self, frame):
        for f in (self.login_frame, self.signup_frame, self.dashboard_frame,
                 self.settings_frame, self.games_frame, self.utilities_frame,
                 self.stats_frame):
            f.pack_forget()
        frame.pack(fill='both', expand=True)
        
        if frame == self.dashboard_frame:
            self.update_welcome_message()
        elif frame == self.utilities_frame:
            self.update_todo_list()
        elif frame == self.stats_frame:
            self.update_stats()
            
    def show_login_frame(self):
        self.show_frame(self.login_frame)
        self.login_username.delete(0, tk.END)
        self.login_password.delete(0, tk.END)
        
    def login(self):
        username = self.login_username.get()
        password = self.hash_password(self.login_password.get())
        
        # Check for too many failed attempts
        self.cursor.execute('''
            SELECT failed_attempts, last_attempt 
            FROM users WHERE username=?
        ''', (username,))
        result = self.cursor.fetchone()
        
        if result and result[0] >= 3:
            last_attempt = datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S.%f')
            time_diff = datetime.now() - last_attempt
            
            if time_diff.total_seconds() < 300:  # 5 minutes lockout
                messagebox.showerror("Error", "Account temporarily locked. Try again later.")
                return
            else:
                # Reset failed attempts after lockout period
                self.cursor.execute('''
                    UPDATE users SET failed_attempts=0 
                    WHERE username=?
                ''', (username,))
                self.conn.commit()
        
        # Attempt login
        self.cursor.execute('SELECT * FROM users WHERE username=? AND password=?',
                          (username, password))
        user = self.cursor.fetchone()
        
        if user:
            # Reset failed attempts on successful login
            self.cursor.execute('''
                UPDATE users SET failed_attempts=0 
                WHERE username=?
            ''', (username,))
            self.conn.commit()
            
            self.current_user = username
            self.current_theme = user[2]
            self.theme_var.set(self.current_theme)
            self.apply_theme()
            self.show_frame(self.dashboard_frame)
        else:
            # Increment failed attempts
            self.cursor.execute('''
                UPDATE users SET 
                    failed_attempts = COALESCE(failed_attempts, 0) + 1,
                    last_attempt = ?
                WHERE username=?
            ''', (datetime.now(), username))
            self.conn.commit()
            messagebox.showerror("Error", "Invalid credentials")      

    def create_account(self):
        username = self.signup_username.get()
        password = self.signup_password.get()
        confirm = self.signup_confirm.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        if password != confirm:
            messagebox.showerror("Error", "Passwords don't match")
            return
            
        try:
            hashed_password = self.hash_password(password)
            self.cursor.execute('''
                INSERT INTO users (username, password, theme, created_at)
                VALUES (?, ?, ?, ?)
            ''', (username, hashed_password, 'light', datetime.now()))
            self.conn.commit()
            messagebox.showinfo("Success", "Account created successfully!")
            self.show_login_frame()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
            
    def logout(self):
        self.current_user = None
        self.show_login_frame()
        
    def toggle_theme(self):
        self.current_theme = self.theme_var.get()
        self.cursor.execute('UPDATE users SET theme=? WHERE username=?',
                          (self.current_theme, self.current_user))
        self.conn.commit()
        self.apply_theme()
        
    def apply_theme(self):
        theme = self.theme[self.current_theme]
        self.root.configure(bg=theme['bg'])
        style = ttk.Style()
        style.configure('TFrame', background=theme['bg'])
        style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])
        style.configure('TButton', background=theme['button'])
        style.configure('Danger.TButton', background='#ff4444', foreground='white')
        
    def update_welcome_message(self):
        self.welcome_label.config(text=f"Welcome, {self.current_user}!")

    def show_delete_account_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Delete Account")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="⚠️ This action cannot be undone!", 
                 font=('Arial', 10, 'bold')).pack(pady=5)
        ttk.Label(dialog, text="Please enter your password to confirm:").pack(pady=5)
        
        password_entry = ttk.Entry(dialog, show="*")
        password_entry.pack(pady=10)
        
        def confirm_delete():
            password = password_entry.get()
            if not password:
                messagebox.showerror("Error", "Please enter your password", parent=dialog)
                return
                
            # Verify password
            password_hash = self.hash_password(password)
            self.cursor.execute('SELECT password FROM users WHERE username=?', 
                              (self.current_user,))
            stored_hash = self.cursor.fetchone()[0]
            
            if password_hash != stored_hash:
                messagebox.showerror("Error", "Incorrect password", parent=dialog)
                return
                
            if messagebox.askyesno("Final Confirmation", 
                                 "Are you absolutely sure you want to delete your account?\n"
                                 "All your data will be permanently lost!", parent=dialog):
                # Delete all user data
                self.cursor.execute('DELETE FROM todos WHERE username=?', (self.current_user,))
                self.cursor.execute('DELETE FROM notes WHERE username=?', (self.current_user,))
                self.cursor.execute('DELETE FROM scores WHERE username=?', (self.current_user,))
                self.cursor.execute('DELETE FROM users WHERE username=?', (self.current_user,))
                self.conn.commit()
                
                dialog.destroy()
                messagebox.showinfo("Account Deleted", "Your account has been permanently deleted.")
                self.logout()
        
        ttk.Button(dialog, text="Delete Account", command=confirm_delete,
                  style='Danger.TButton').pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()

    def show_change_password_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Change Password")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Current Password:").pack(pady=5)
        current_password = ttk.Entry(dialog, show="*")
        current_password.pack(pady=5)
        
        ttk.Label(dialog, text="New Password:").pack(pady=5)
        new_password = ttk.Entry(dialog, show="*")
        new_password.pack(pady=5)
        
        ttk.Label(dialog, text="Confirm New Password:").pack(pady=5)
        confirm_password = ttk.Entry(dialog, show="*")
        confirm_password.pack(pady=5)
        
        def change_password():
            current = current_password.get()
            new = new_password.get()
            confirm = confirm_password.get()
            
            if not current or not new or not confirm:
                messagebox.showerror("Error", "Please fill all fields", parent=dialog)
                return
                
            if new != confirm:
                messagebox.showerror("Error", "New passwords don't match", parent=dialog)
                return
                
            # Verify current password
            current_hash = self.hash_password(current)
            self.cursor.execute('SELECT password FROM users WHERE username=?', 
                              (self.current_user,))
            stored_hash = self.cursor.fetchone()[0]
            
            if current_hash != stored_hash:
                messagebox.showerror("Error", "Current password is incorrect", parent=dialog)
                return
                
            # Update password
            new_hash = self.hash_password(new)
            self.cursor.execute('UPDATE users SET password=? WHERE username=?',
                              (new_hash, self.current_user))
            self.conn.commit()
            
            messagebox.showinfo("Success", "Password changed successfully!", parent=dialog)
            dialog.destroy()
            
        ttk.Button(dialog, text="Change Password", 
                  command=change_password).pack(pady=10)

    def reset_account_data(self):
        if messagebox.askyesno("Confirm Reset", 
                              "Are you sure you want to reset all your data? This cannot be undone!"):
            self.cursor.execute('DELETE FROM todos WHERE username=?', (self.current_user,))
            self.cursor.execute('DELETE FROM notes WHERE username=?', (self.current_user,))
            self.cursor.execute('DELETE FROM scores WHERE username=?', (self.current_user,))
            self.conn.commit()
            messagebox.showinfo("Success", "Account data has been reset!")

    def animate_login_banner(self):
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        def update_color():
            try:
                current_color = self.login_banner.cget("foreground")
                current_index = colors.index(current_color)
                next_color = colors[(current_index + 1) % len(colors)]
            except ValueError:
                # If color not found in list, start from beginning
                next_color = colors[0]
            
            self.login_banner.configure(foreground=next_color)
            self.root.after(2000, update_color)
            
        self.login_banner.configure(foreground=colors[0])
        update_color()

    def update_login_stats(self):
        try:
            # Get total registered users
            self.cursor.execute('SELECT COUNT(*) FROM users')
            total_users = self.cursor.fetchone()[0]
            
            # Get total games played
            self.cursor.execute('SELECT COUNT(*) FROM scores')
            total_games = self.cursor.fetchone()[0]
            
            # Get most popular game
            self.cursor.execute('''
                SELECT game, COUNT(*) as count 
                FROM scores 
                GROUP BY game 
                ORDER BY count DESC 
                LIMIT 1
            ''')
            result = self.cursor.fetchone()
            most_played = result[0].title() if result else "None"
            
            # Get highest score
            self.cursor.execute('''
                SELECT username, game, score 
                FROM scores 
                ORDER BY score DESC 
                LIMIT 1
            ''')
            high_score = self.cursor.fetchone()
            
            # Format stats text with emojis
            stats_text = f"👥 Total Users: {total_users}\n"
            stats_text += f"🎮 Games Played: {total_games}\n"
            stats_text += f"🏆 Most Popular: {most_played}\n"
            
            if high_score:
                stats_text += f"⭐ Best Score: {high_score[0]} ({high_score[1]}: {high_score[2]})"
            
            self.stats_label.config(text=stats_text)
            
            # Schedule next update (every 30 seconds)
            self.root.after(30000, self.update_login_stats)
            
        except Exception as e:
            self.stats_label.config(text="Statistics Unavailable")
            # Retry after 1 minute if there's an error
            self.root.after(60000, self.update_login_stats)

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.login_password.configure(show="")
        else:
            self.login_password.configure(show="*")

    def check_username_availability(self, event=None):
        username = self.signup_username.get()
        if len(username) < 3:
            self.username_status.configure(text="❓")
            return
        
        self.cursor.execute('SELECT username FROM users WHERE username=?', (username,))
        if self.cursor.fetchone():
            self.username_status.configure(text="❌")
        else:
            self.username_status.configure(text="✅")

    def check_password_strength(self, event=None):
        password = self.signup_password.get()
        strength = ""
        
        if len(password) < 8:
            strength = "❌ Too Short"
        else:
            score = 0
            if any(c.islower() for c in password): score += 1
            if any(c.isupper() for c in password): score += 1
            if any(c.isdigit() for c in password): score += 1
            if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password): score += 1
            
            if score == 0: strength = "❌ Very Weak"
            elif score == 1: strength = "⚠️ Weak"
            elif score == 2: strength = "✅ Medium"
            elif score == 3: strength = "✅ Strong"
            else: strength = "⭐ Very Strong"
        
        self.password_strength.config(text=strength)

    def check_passwords_match(self, event=None):
        password = self.signup_password.get()
        confirm = self.signup_confirm.get()
        
        if not confirm or not password:
            self.password_match.config(text="")
            return
            
        if password == confirm:
            self.password_match.config(text="✅ Passwords Match")
        else:
            self.password_match.config(text="❌ Passwords Don't Match")

    def start_memory_game(self):
        game_window = tk.Toplevel(self.root)
        game_window.title("Memory Game")
        game_window.geometry("400x500")
        
        # Game variables
        self.cards = []
        self.flipped = []
        self.matched = []
        self.can_flip = True
        
        # Create symbols for pairs
        symbols = ['🌟', '🎈', '🎮', '🎲', '🎭', '🎨', '🎪', '🎯'] * 2
        random.shuffle(symbols)
        
        # Create game grid
        for i in range(4):
            for j in range(4):
                card = ttk.Button(game_window, text='?', width=8,
                                command=lambda x=i, y=j: self.flip_card(x, y, symbols, game_window))
                card.grid(row=i, column=j, padx=5, pady=5)
                self.cards.append(card)
        
        # Score label
        self.score_label = ttk.Label(game_window, text="Moves: 0")
        self.score_label.grid(row=4, column=0, columnspan=4, pady=10)
        self.moves = 0
        
    def flip_card(self, x, y, symbols, window):
        if not self.can_flip:
            return
            
        index = x * 4 + y
        card = self.cards[index]
        
        if card in self.flipped or card in self.matched:
            return
            
        # Show symbol
        card.configure(text=symbols[index])
        self.flipped.append(card)
        
        if len(self.flipped) == 2:
            self.moves += 1
            self.score_label.configure(text=f"Moves: {self.moves}")
            self.can_flip = False
            window.after(1000, lambda: self.check_match(symbols, window))
            
    def check_match(self, symbols, window):
        if len(self.flipped) == 2:
            idx1 = self.cards.index(self.flipped[0])
            idx2 = self.cards.index(self.flipped[1])
            
            if symbols[idx1] == symbols[idx2]:
                self.matched.extend(self.flipped)
                if len(self.matched) == len(self.cards):
                    self.game_over(window)
            else:
                for card in self.flipped:
                    card.configure(text='?')
                    
            self.flipped.clear()
            self.can_flip = True
            
    def game_over(self, window):
        # Save score
        self.cursor.execute('''
            INSERT INTO scores (username, game, score, date)
            VALUES (?, ?, ?, ?)
        ''', (self.current_user, 'memory', self.moves, datetime.now()))
        self.conn.commit()
        
        messagebox.showinfo("Congratulations!", 
                          f"You won in {self.moves} moves!", parent=window)
        window.destroy()

    def start_snake_game(self):
        game_window = tk.Toplevel(self.root)
        game_window.title("Snake Game")
        game_window.geometry("400x550")
        game_window.resizable(False, False)
        
        # Calculate maximum possible food (total grid spaces minus minimum snake length)
        max_food = (400 * 400) // (10 * 10) - 3  # Grid spaces minus minimum snake length
        
        # Settings frame
        settings_frame = ttk.LabelFrame(game_window, text="Game Settings", padding=10)
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        # Snake length setting
        ttk.Label(settings_frame, text="Starting Length:").grid(row=0, column=0, padx=5)
        self.snake_length = ttk.Spinbox(settings_frame, from_=3, to=10, width=5)
        self.snake_length.set(3)
        self.snake_length.grid(row=0, column=1, padx=5)
        
        # Food amount setting with dynamic maximum
        ttk.Label(settings_frame, text="Food Amount:").grid(row=0, column=2, padx=5)
        self.food_amount = ttk.Spinbox(settings_frame, from_=1, to=max_food, width=5)
        self.food_amount.set(1)
        self.food_amount.grid(row=0, column=3, padx=5)
        
        # Game speed setting
        ttk.Label(settings_frame, text="Speed:").grid(row=1, column=0, padx=5)
        self.game_speed_setting = ttk.Spinbox(settings_frame, from_=50, to=200, width=5)
        self.game_speed_setting.set(100)
        self.game_speed_setting.grid(row=1, column=1, padx=5)
        
        # Help text for speed
        ttk.Label(settings_frame, text="(Lower = Faster)").grid(row=1, column=2, columnspan=2, padx=5)
        
        # Create Start button
        ttk.Button(settings_frame, text="Start", 
                  command=lambda: self.initialize_snake_game(game_window)).grid(
                      row=2, column=0, columnspan=4, pady=5)
        
        # Game canvas
        self.game_canvas = tk.Canvas(game_window, width=400, height=400, bg='black')
        self.game_canvas.pack(pady=10)
        
        # Score label
        self.snake_score_label = ttk.Label(game_window, text="Score: 0")
        self.snake_score_label.pack(pady=5)
        
    def initialize_snake_game(self, window):
        # Validate settings
        start_length = int(self.snake_length.get())
        food_count = int(self.food_amount.get())
        
        # Check if snake length is too long for the game area
        max_length = (400 * 400) // (10 * 10)  # Total grid spaces
        if start_length > max_length // 2:  # Use half of available space as max
            messagebox.showerror("Invalid Settings", 
                               "Snake length is too large for the game area!")
            return
            
        # Check if there's enough space for food
        available_spaces = max_length - start_length
        if food_count > available_spaces // 2:  # Leave some free space
            messagebox.showerror("Invalid Settings", 
                               "Too many food items for the game area!")
            return
        
        # Hide settings frame
        for widget in window.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                widget.pack_forget()
        
        # Game variables
        self.snake_pos = [(100 - i*10, 100) for i in range(start_length)]
        self.food_positions = []
        self.snake_dir = "Right"
        self.snake_score = 0
        self.game_speed = int(self.game_speed_setting.get())
        self.movement_queue = []
        self.last_update = time.time()
        
        # Clear canvas
        self.game_canvas.delete('all')
        
        # Spawn initial food
        for _ in range(food_count):
            self.spawn_food()
        
        # Controls
        window.bind('<Left>', lambda e: self.change_direction('Left'))
        window.bind('<Right>', lambda e: self.change_direction('Right'))
        window.bind('<Up>', lambda e: self.change_direction('Up'))
        window.bind('<Down>', lambda e: self.change_direction('Down'))
        window.bind('a', lambda e: self.change_direction('Left'))
        window.bind('d', lambda e: self.change_direction('Right'))
        window.bind('w', lambda e: self.change_direction('Up'))
        window.bind('s', lambda e: self.change_direction('Down'))
        
        self.update_snake()

        
    def spawn_food(self):
        while True:
            x = random.randint(1, 39) * 10
            y = random.randint(1, 39) * 10
            new_pos = (x, y)
            if new_pos not in self.food_positions and new_pos not in self.snake_pos:
                self.food_positions.append(new_pos)
                self.game_canvas.create_oval(x, y, x+10, y+10, fill='red', tags='food')
                break
                
    def change_direction(self, new_dir):
        opposites = {'Left': 'Right', 'Right': 'Left', 'Up': 'Down', 'Down': 'Up'}
        
        if len(self.movement_queue) < 2:  # Limit queue size
            if not self.movement_queue:
                current_dir = self.snake_dir
            else:
                current_dir = self.movement_queue[-1]
                
            if opposites[new_dir] != current_dir:
                self.movement_queue.append(new_dir)
                
    def update_snake(self):
        current_time = time.time()
        
        if self.movement_queue and (current_time - self.last_update) >= (self.game_speed / 1000.0):
            self.snake_dir = self.movement_queue.pop(0)
            self.last_update = current_time
            
        head = self.snake_pos[0]
        
        # Calculate new head position
        if self.snake_dir == 'Left':
            new_head = (head[0] - 10, head[1])
        elif self.snake_dir == 'Right':
            new_head = (head[0] + 10, head[1])
        elif self.snake_dir == 'Up':
            new_head = (head[0], head[1] - 10)
        else:  # Down
            new_head = (head[0], head[1] + 10)
            
        # Check for collisions
        if (new_head in self.snake_pos[:-1] or 
            new_head[0] < 0 or new_head[0] >= 400 or 
            new_head[1] < 0 or new_head[1] >= 400):
            self.game_over_snake()
            return
            
        # Update snake position
        self.snake_pos.insert(0, new_head)
        
        # Check if food is eaten
        if new_head in self.food_positions:
            self.food_positions.remove(new_head)
            self.snake_score += 1
            self.snake_score_label.config(text=f"Score: {self.snake_score}")
            self.game_canvas.delete('food')
            # Redraw remaining food
            for fx, fy in self.food_positions:
                self.game_canvas.create_oval(fx, fy, fx+10, fy+10, fill='red', tags='food')
            # Spawn new food
            self.spawn_food()
            if self.game_speed > 50:
                self.game_speed -= 2
        else:
            self.snake_pos.pop()
            
        # Update canvas
        self.game_canvas.delete('snake')
        for x, y in self.snake_pos:
            self.game_canvas.create_rectangle(x, y, x+10, y+10, fill='green', tags='snake')
            
        # Schedule next update
        self.game_canvas.after(self.game_speed, self.update_snake)
        
    def game_over_snake(self):
        # Save score
        self.cursor.execute('''
            INSERT INTO scores (username, game, score, date)
            VALUES (?, ?, ?, ?)
        ''', (self.current_user, 'snake', self.snake_score, datetime.now()))
        self.conn.commit()
        
        messagebox.showinfo("Game Over", 
                          f"Game Over! Your score: {self.snake_score}")
        self.game_canvas.master.destroy()

    def start_typing_game(self):
        game_window = tk.Toplevel(self.root)
        game_window.title("Typing Game")
        game_window.geometry("600x400")
        
        # Word list
        self.typing_words = [
            "python", "programming", "computer", "algorithm", "database",
            "interface", "software", "developer", "keyboard", "function",
            "variable", "network", "security", "application", "framework"
        ]
        
        # Add custom words section
        custom_frame = ttk.Frame(game_window)
        custom_frame.pack(pady=5)
        self.custom_word_entry = ttk.Entry(custom_frame, width=20)
        self.custom_word_entry.pack(side='left', padx=5)
        ttk.Button(custom_frame, text="Add Word", 
                  command=self.add_custom_word).pack(side='left')
        
        self.current_word = ""
        self.typing_score = 0
        self.time_left = 60
        self.typing_game_active = False
        
        # Game widgets
        ttk.Label(game_window, text="Type the words as they appear:", 
                 font=('Arial', 12)).pack(pady=10)
        
        self.word_label = ttk.Label(game_window, text="", font=('Arial', 24))
        self.word_label.pack(pady=20)
        
        self.typing_entry = ttk.Entry(game_window, font=('Arial', 14))
        self.typing_entry.pack(pady=10)
        self.typing_entry.bind('<Return>', lambda e: self.check_word())
        
        self.typing_score_label = ttk.Label(game_window, text="Score: 0", 
                                          font=('Arial', 12))
        self.typing_score_label.pack(pady=5)
        
        self.typing_timer_label = ttk.Label(game_window, text="Time: 60", 
                                          font=('Arial', 12))
        self.typing_timer_label.pack(pady=5)
        
        ttk.Button(game_window, text="Start Game", 
                  command=self.start_typing_round).pack(pady=10)

    def add_custom_word(self):
        word = self.custom_word_entry.get().strip().lower()
        if word and word not in self.typing_words:
            self.typing_words.append(word)
            self.custom_word_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Added word: {word}")

        
    def start_typing_round(self):
        if not self.typing_game_active:
            self.typing_game_active = True
            self.typing_score = 0
            self.time_left = 60
            self.typing_score_label.config(text="Score: 0")
            self.typing_entry.delete(0, tk.END)
            self.typing_entry.focus()
            self.next_word()
            self.update_typing_timer()
            
    def next_word(self):
        if self.typing_game_active:
            self.current_word = random.choice(self.typing_words)
            self.word_label.config(text=self.current_word)
            
    def check_word(self):
        if self.typing_game_active:
            typed_word = self.typing_entry.get().strip().lower()
            if typed_word == self.current_word:
                self.typing_score += 1
                self.typing_score_label.config(text=f"Score: {self.typing_score}")
            self.typing_entry.delete(0, tk.END)
            self.next_word()
            
    def update_typing_timer(self):
        if self.typing_game_active:
            self.typing_timer_label.config(text=f"Time: {self.time_left}")
            if self.time_left > 0:
                self.time_left -= 1
                self.word_label.after(1000, self.update_typing_timer)
            else:
                self.typing_game_active = False
                self.word_label.config(text="Game Over!")
                
                # Save score
                self.cursor.execute('''
                    INSERT INTO scores (username, game, score, date)
                    VALUES (?, ?, ?, ?)
                ''', (self.current_user, 'typing', self.typing_score, datetime.now()))
                self.conn.commit()
                
                messagebox.showinfo("Game Over", 
                                  f"Time's up! Your final score: {self.typing_score} words",
                                  parent=self.word_label.winfo_toplevel())

    def start_puzzle_game(self):
        game_window = tk.Toplevel(self.root)
        game_window.title("Puzzle Game")
        game_window.geometry("400x600")
        
        # Add custom styles
        style = ttk.Style()
        style.configure('Moving.TButton', background='lightblue')
        style.configure('Invalid.TButton', background='pink')
        style.configure('Winner.TButton', background='lightgreen')
        style.configure('Paused.TButton', background='gray')
        
        # Game variables
        self.puzzle_moves = 0
        self.puzzle_tiles = []
        self.puzzle_numbers = list(range(1, 16)) + [None]
        self.game_paused = False
        self.game_time = 0
        self.current_theme = 'default'
        
        # Control frame
        control_frame = ttk.Frame(game_window)
        control_frame.pack(pady=5, fill='x')
        
        # Difficulty selector
        ttk.Label(control_frame, text="Size:").pack(side='left', padx=5)
        self.grid_size = ttk.Combobox(control_frame, values=['3x3', '4x4', '5x5'], width=5)
        self.grid_size.set('4x4')
        self.grid_size.pack(side='left', padx=5)
        
        # Theme selector
        ttk.Label(control_frame, text="Theme:").pack(side='left', padx=5)
        self.theme_choice = ttk.Combobox(control_frame, values=['Default', 'Blue', 'Green'], width=8)
        self.theme_choice.set('Default')
        self.theme_choice.pack(side='left', padx=5)
        self.theme_choice.bind('<<ComboboxSelected>>', self.change_theme)
        
        # Help button
        help_button = ttk.Button(control_frame, text="❓ Help", 
                               command=self.show_tutorial)
        help_button.pack(side='right', padx=5)
        
        # Pause button
        self.pause_button = ttk.Button(control_frame, text="⏸️ Pause", 
                                     command=self.toggle_pause)
        self.pause_button.pack(side='right', padx=5)
        
        # Game frame
        self.puzzle_frame = ttk.Frame(game_window)
        self.puzzle_frame.pack(pady=20)
        
        # Stats frame
        stats_frame = ttk.Frame(game_window)
        stats_frame.pack(fill='x', padx=10)
        
        # Move counter and timer
        self.puzzle_moves_label = ttk.Label(stats_frame, text="Moves: 0", font=('Arial', 12))
        self.puzzle_moves_label.pack(side='left', padx=10)
        
        self.timer_label = ttk.Label(stats_frame, text="Time: 0:00", font=('Arial', 12))
        self.timer_label.pack(side='right', padx=10)
        
        # Best score display
        self.best_score_label = ttk.Label(stats_frame, text="Best: --", font=('Arial', 12))
        self.best_score_label.pack(side='left', padx=10)
        
        # New game and reset buttons
        button_frame = ttk.Frame(game_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="New Game", 
                  command=self.reset_puzzle).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Reset Current", 
                  command=self.reset_current_puzzle).pack(side='left', padx=5)
        
        # Add keyboard controls
        game_window.bind('<Left>', lambda e: self.handle_keyboard('Left'))
        game_window.bind('<Right>', lambda e: self.handle_keyboard('Right'))
        game_window.bind('<Up>', lambda e: self.handle_keyboard('Up'))
        game_window.bind('<Down>', lambda e: self.handle_keyboard('Down'))
        game_window.bind('<space>', lambda e: self.toggle_pause())
        
        # Initialize game
        self.initialize_puzzle()
        self.update_timer()
        self.update_best_score()
        
    def show_tutorial(self):
        messagebox.showinfo("How to Play",
            "🎮 Puzzle Game Instructions:\n\n"
            "1. Move tiles by clicking them\n"
            "2. Use arrow keys for movement\n"
            "3. Arrange numbers in order\n"
            "4. Empty space helps you move tiles\n\n"
            "💡 Tips:\n"
            "- Plan your moves ahead\n"
            "- Use the empty tile strategically\n"
            "- Try to solve row by row")

    def handle_keyboard(self, direction):
        if self.game_paused:
            return
            
        empty_pos = self.puzzle_numbers.index(None)
        size = int(self.grid_size.get()[0])
        
        if direction == 'Left' and empty_pos % size < size - 1:
            self.move_tile(empty_pos + 1)
        elif direction == 'Right' and empty_pos % size > 0:
            self.move_tile(empty_pos - 1)
        elif direction == 'Up' and empty_pos < len(self.puzzle_numbers) - size:
            self.move_tile(empty_pos + size)
        elif direction == 'Down' and empty_pos >= size:
            self.move_tile(empty_pos - size)

    def update_best_score(self):
        # Get best score from database
        self.cursor.execute('''
            SELECT MIN(score) FROM scores 
            WHERE username = ? AND game = 'puzzle'
        ''', (self.current_user,))
        best_score = self.cursor.fetchone()[0]
        if best_score:
            self.best_score_label.config(text=f"Best: {best_score}")

    def initialize_puzzle(self):
        # Clear existing tiles
        for widget in self.puzzle_frame.winfo_children():
            widget.destroy()
        self.puzzle_tiles.clear()
        
        # Reset game state
        self.puzzle_moves = 0
        self.game_time = 0
        self.game_paused = False
        size = int(self.grid_size.get()[0])
        self.puzzle_numbers = list(range(1, size*size)) + [None]
        random.shuffle(self.puzzle_numbers)
        
        # Create grid of tiles
        for i in range(size*size):
            row, col = i // size, i % size
            btn = ttk.Button(self.puzzle_frame, width=5)
            if self.puzzle_numbers[i]:
                btn.configure(text=str(self.puzzle_numbers[i]))
            else:
                btn.configure(text="")
            btn.position = i
            btn.configure(command=lambda b=btn: self.move_tile(b.position))
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.puzzle_tiles.append(btn)
            
    def toggle_pause(self):
        self.game_paused = not self.game_paused
        if self.game_paused:
            self.pause_button.configure(text="▶️ Resume")
            for tile in self.puzzle_tiles:
                tile.configure(state='disabled', style='Paused.TButton')
        else:
            self.pause_button.configure(text="⏸️ Pause")
            for tile in self.puzzle_tiles:
                tile.configure(state='normal', style='TButton')
                
    def change_theme(self, event=None):
        theme = self.theme_choice.get().lower()
        style = ttk.Style()
        
        if theme == 'blue':
            style.configure('TButton', background='lightblue')
            style.configure('Moving.TButton', background='blue')
        elif theme == 'green':
            style.configure('TButton', background='lightgreen')
            style.configure('Moving.TButton', background='green')
        else:
            style.configure('TButton', background='white')
            style.configure('Moving.TButton', background='lightblue')
            
    def update_timer(self):
        if not self.game_paused:
            mins, secs = divmod(self.game_time, 60)
            self.timer_label.configure(text=f"Time: {mins}:{secs:02d}")
            self.game_time += 1
        self.timer_label.after(1000, self.update_timer)
        
    def reset_puzzle(self):
        self.initialize_puzzle()
        
    def reset_current_puzzle(self):
        size = int(self.grid_size.get()[0])
        self.puzzle_numbers = list(range(1, size*size)) + [None]
        random.shuffle(self.puzzle_numbers)
        for i, btn in enumerate(self.puzzle_tiles):
            if self.puzzle_numbers[i]:
                btn.configure(text=str(self.puzzle_numbers[i]))
            else:
                btn.configure(text="")

        
    def move_tile(self, position):
        empty_pos = self.puzzle_numbers.index(None)
        row, col = position // 4, position % 4
        empty_row, empty_col = empty_pos // 4, empty_pos % 4
        
        # Check if move is valid (adjacent to empty tile)
        if (abs(row - empty_row) == 1 and col == empty_col) or \
           (abs(col - empty_col) == 1 and row == empty_row):
            
            # Visual feedback for valid move
            self.puzzle_tiles[position].config(style='Moving.TButton')
            self.puzzle_tiles[position].after(100, lambda: self.puzzle_tiles[position].config(style='TButton'))
            
            # Swap tiles
            self.puzzle_numbers[position], self.puzzle_numbers[empty_pos] = \
                self.puzzle_numbers[empty_pos], self.puzzle_numbers[position]
            
            # Update buttons with animation
            def update_tiles():
                if self.puzzle_numbers[empty_pos] is not None:
                    self.puzzle_tiles[empty_pos].config(text=str(self.puzzle_numbers[empty_pos]))
                else:
                    self.puzzle_tiles[empty_pos].config(text="")
                if self.puzzle_numbers[position] is not None:
                    self.puzzle_tiles[position].config(text=str(self.puzzle_numbers[position]))
                else:
                    self.puzzle_tiles[position].config(text="")
            
            self.puzzle_tiles[position].after(50, update_tiles)
            
            self.puzzle_moves += 1
            self.puzzle_moves_label.config(text=f"Moves: {self.puzzle_moves}")
            
            # Check for win with visual feedback
            if self.check_puzzle_win():
                for tile in self.puzzle_tiles:
                    tile.config(style='Winner.TButton')
                self.puzzle_tiles[0].after(500, lambda: self.puzzle_game_over())
        else:
            # Visual feedback for invalid move
            self.puzzle_tiles[position].config(style='Invalid.TButton')
            self.puzzle_tiles[position].after(100, lambda: self.puzzle_tiles[position].config(style='TButton'))

    def check_puzzle_win(self):
        return self.puzzle_numbers[:-1] == list(range(1, 16))
        
    def puzzle_game_over(self):
        # Save score
        self.cursor.execute('''
            INSERT INTO scores (username, game, score, date)
            VALUES (?, ?, ?, ?)
        ''', (self.current_user, 'puzzle', self.puzzle_moves, datetime.now()))
        self.conn.commit()
        
        messagebox.showinfo("Congratulations!", 
                          f"You solved the puzzle in {self.puzzle_moves} moves!")
                    
    def start_word_scramble(self):
        game_window = tk.Toplevel(self.root)
        game_window.title("Word Scramble")
        game_window.geometry("400x500")
        
        self.scramble_score = 0
        self.scramble_time = 60
        self.game_active = False
        
        # Word bank with hints
        self.word_bank = {
            "python": "A popular programming language named after a snake",
            "programming": "Writing instructions for computers",
            "computer": "An electronic device that processes data",
            "algorithm": "A step-by-step procedure to solve a problem",
            "database": "A structured collection of data",
            "interface": "A point where two systems meet and interact",
            "software": "Programs and other operating information",
            "developer": "Someone who creates computer programs",
            "keyboard": "Device used to input text",
            "function": "A reusable block of code",
            "variable": "A container for storing data values",
            "network": "Interconnected computers sharing resources",
            "security": "Protection against cyber threats",
            "application": "A program designed for end users",
            "framework": "A platform for developing software applications"
        }
        
        # Game widgets
        ttk.Label(game_window, text="Unscramble the word:", 
                 font=('Arial', 12)).pack(pady=10)
        
        self.scrambled_label = ttk.Label(game_window, text="", font=('Arial', 24))
        self.scrambled_label.pack(pady=20)
        
        # Add hint label
        self.hint_label = ttk.Label(game_window, text="", font=('Arial', 12))
        self.hint_label.pack(pady=5)
        
        self.scramble_entry = ttk.Entry(game_window, font=('Arial', 14))
        self.scramble_entry.pack(pady=10)
        self.scramble_entry.bind('<Return>', lambda e: self.check_scrambled_word())
        
        # Add hint button
        ttk.Button(game_window, text="Get Hint", 
                  command=self.show_hint).pack(pady=5)
        
        self.scramble_score_label = ttk.Label(game_window, text="Score: 0", 
                                            font=('Arial', 12))
        self.scramble_score_label.pack(pady=5)
        
        self.scramble_timer_label = ttk.Label(game_window, text="Time: 60", 
                                            font=('Arial', 12))
        self.scramble_timer_label.pack(pady=5)
        
        ttk.Button(game_window, text="Start Game", 
                  command=self.start_scramble_round).pack(pady=10)

    def scramble_word(self, word):
        chars = list(word)
        while ''.join(chars) == word:  # Ensure word is actually scrambled
            random.shuffle(chars)
        return ''.join(chars)

    def start_scramble_round(self):
        if not self.game_active:
            self.game_active = True
            self.scramble_score = 0
            self.scramble_time = 60
            self.scramble_score_label.config(text="Score: 0")
            self.scramble_entry.delete(0, tk.END)
            self.scramble_entry.focus()
            self.next_scrambled_word()
            self.update_scramble_timer()

    def show_hint(self):
        if self.game_active:
            # Show hint for current word
            hint = self.word_bank[self.current_word]
            self.hint_label.config(text=f"Hint: {hint}")
            # Deduct half a point for using hint
            self.scramble_score -= 0.5
            self.scramble_score_label.config(text=f"Score: {self.scramble_score}")

    def next_scrambled_word(self):
        if self.game_active:
            self.current_word = random.choice(list(self.word_bank.keys()))
            scrambled = self.scramble_word(self.current_word)
            self.scrambled_label.config(text=scrambled)
            self.hint_label.config(text="")  # Clear previous hint

    def check_scrambled_word(self):
        if self.game_active:
            answer = self.scramble_entry.get().strip().lower()
            if answer == self.current_word:
                self.scramble_score += 1
                self.scramble_score_label.config(text=f"Score: {self.scramble_score}")
            self.scramble_entry.delete(0, tk.END)
            self.next_scrambled_word()

    def update_scramble_timer(self):
        if self.game_active:
            self.scramble_timer_label.config(text=f"Time: {self.scramble_time}")
            if self.scramble_time > 0:
                self.scramble_time -= 1
                self.scrambled_label.after(1000, self.update_scramble_timer)
            else:
                self.game_active = False
                self.scrambled_label.config(text="Game Over!")
                
                # Save score
                self.cursor.execute('''
                    INSERT INTO scores (username, game, score, date)
                    VALUES (?, ?, ?, ?)
                ''', (self.current_user, 'scramble', self.scramble_score, datetime.now()))
                self.conn.commit()
                
                messagebox.showinfo("Game Over", 
                                  f"Time's up! Your final score: {self.scramble_score} words",
                                  parent=self.scrambled_label.winfo_toplevel())

    def start_color_match(self):
        game_window = tk.Toplevel(self.root)
        game_window.title("Color Match")
        game_window.geometry("400x500")
        
        self.color_score = 0
        self.color_time = 60
        self.color_active = False
        
        # Color bank (name: hex_color)
        self.colors = {
            'Red': '#FF0000', 'Blue': '#0000FF', 'Green': '#00FF00',
            'Yellow': '#FFFF00', 'Purple': '#800080', 'Orange': '#FFA500',
            'Pink': '#FFC0CB', 'Brown': '#A52A2A'
        }
        
        # Game widgets
        ttk.Label(game_window, text="Match the color with the word!", 
                 font=('Arial', 12)).pack(pady=10)
        
        self.color_word = ttk.Label(game_window, text="", font=('Arial', 24))
        self.color_word.pack(pady=20)
        
        # Create color buttons frame
        button_frame = ttk.Frame(game_window)
        button_frame.pack(pady=10)
        
        # Create grid of color buttons
        row = 0
        col = 0
        for color_name, color_hex in self.colors.items():
            btn = tk.Button(button_frame, text="", width=8, height=2,
                          bg=color_hex, command=lambda c=color_name: self.check_color(c))
            btn.grid(row=row, column=col, padx=5, pady=5)
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        self.color_score_label = ttk.Label(game_window, text="Score: 0", 
                                         font=('Arial', 12))
        self.color_score_label.pack(pady=5)
        
        self.color_timer_label = ttk.Label(game_window, text="Time: 60", 
                                         font=('Arial', 12))
        self.color_timer_label.pack(pady=5)
        
        ttk.Button(game_window, text="Start Game", 
                  command=self.start_color_round).pack(pady=10)

    def start_color_round(self):
        if not self.color_active:
            self.color_active = True
            self.color_score = 0
            self.color_time = 60
            self.color_score_label.config(text="Score: 0")
            self.next_color()
            self.update_color_timer()

    def next_color(self):
        if self.color_active:
            # Select random color name and display color
            color_name = random.choice(list(self.colors.keys()))
            display_color = random.choice(list(self.colors.values()))
            self.current_color = color_name
            self.color_word.config(text=color_name, foreground=display_color)

    def check_color(self, selected_color):
        if self.color_active:
            if selected_color == self.current_color:
                self.color_score += 1
                self.color_score_label.config(text=f"Score: {self.color_score}")
            self.next_color()

    def update_color_timer(self):
        if self.color_active:
            self.color_timer_label.config(text=f"Time: {self.color_time}")
            if self.color_time > 0:
                self.color_time -= 1
                self.color_word.after(1000, self.update_color_timer)
            else:
                self.color_active = False
                self.color_word.config(text="Game Over!")
                
                # Save score
                self.cursor.execute('''
                    INSERT INTO scores (username, game, score, date)
                    VALUES (?, ?, ?, ?)
                ''', (self.current_user, 'color_match', self.color_score, datetime.now()))
                self.conn.commit()
                
                messagebox.showinfo("Game Over", 
                                  f"Time's up! Your final score: {self.color_score}",
                                  parent=self.color_word.winfo_toplevel())

    def start_pattern_memory(self):
        game_window = tk.Toplevel(self.root)
        game_window.title("Pattern Memory")
        game_window.geometry("400x500")
        
        self.pattern_score = 0
        self.current_pattern = []
        self.player_pattern = []
        self.pattern_active = False
        
        # Create game grid
        self.pattern_buttons = []
        colors = ['red', 'blue', 'green', 'yellow']
        button_frame = ttk.Frame(game_window)
        button_frame.pack(pady=20)
        
        for i in range(2):
            for j in range(2):
                idx = i * 2 + j
                btn = tk.Button(button_frame, width=10, height=5, bg='gray',
                              command=lambda x=idx: self.check_pattern(x))
                btn.grid(row=i, column=j, padx=5, pady=5)
                self.pattern_buttons.append((btn, colors[idx]))
        
        self.pattern_score_label = ttk.Label(game_window, text="Score: 0", 
                                           font=('Arial', 12))
        self.pattern_score_label.pack(pady=10)
        
        self.pattern_status = ttk.Label(game_window, text="Press Start to begin", 
                                      font=('Arial', 12))
        self.pattern_status.pack(pady=10)
        
        ttk.Button(game_window, text="Start Game", 
                  command=self.start_pattern_round).pack(pady=10)

    def start_pattern_round(self):
        if not self.pattern_active:
            self.pattern_active = True
            self.pattern_score = 0
            self.current_pattern = []
            self.pattern_score_label.config(text="Score: 0")
            self.add_to_pattern()

    def add_to_pattern(self):
        self.current_pattern.append(random.randint(0, 3))
        self.pattern_status.config(text="Watch the pattern...")
        self.player_pattern = []
        self.show_pattern(0)

    def show_pattern(self, index):
        if index < len(self.current_pattern):
            btn_idx = self.current_pattern[index]
            btn, color = self.pattern_buttons[btn_idx]
            btn.config(bg=color)
            self.pattern_status.after(500, lambda: self.reset_button(btn_idx, index))
        else:
            self.pattern_status.config(text="Your turn! Repeat the pattern")

    def reset_button(self, btn_idx, index):
        btn, _ = self.pattern_buttons[btn_idx]
        btn.config(bg='gray')
        self.pattern_status.after(200, lambda: self.show_pattern(index + 1))

    def check_pattern(self, button_idx):
        if not self.pattern_active or len(self.current_pattern) == 0:
            return
            
        self.player_pattern.append(button_idx)
        btn, color = self.pattern_buttons[button_idx]
        
        # Flash button
        btn.config(bg=color)
        self.pattern_status.after(200, lambda: btn.config(bg='gray'))
        
        # Check if pattern is correct so far
        for i in range(len(self.player_pattern)):
            if self.player_pattern[i] != self.current_pattern[i]:
                self.pattern_game_over()
                return
        
        # If completed pattern correctly
        if len(self.player_pattern) == len(self.current_pattern):
            self.pattern_score += 1
            self.pattern_score_label.config(text=f"Score: {self.pattern_score}")
            self.pattern_status.after(1000, self.add_to_pattern)

    def pattern_game_over(self):
        self.pattern_active = False
        self.pattern_status.config(text="Game Over!")
        
        # Save score
        self.cursor.execute('''
            INSERT INTO scores (username, game, score, date)
            VALUES (?, ?, ?, ?)
        ''', (self.current_user, 'pattern', self.pattern_score, datetime.now()))
        self.conn.commit()
        
        messagebox.showinfo("Game Over", 
                          f"Game Over! Your score: {self.pattern_score} patterns",
                          parent=self.pattern_status.winfo_toplevel())

    def start_reaction_game(self):
        game_window = tk.Toplevel(self.root)
        game_window.title("Reaction Timer")
        game_window.geometry("400x500")
        
        self.reaction_active = False
        self.waiting_for_click = False
        self.start_time = 0
        self.reaction_scores = []
        
        # Game widgets
        ttk.Label(game_window, text="Click when the screen turns green!", 
                 font=('Arial', 12)).pack(pady=10)
        
        self.reaction_area = tk.Canvas(game_window, width=300, height=300, bg='gray')
        self.reaction_area.pack(pady=20)
        
        self.reaction_status = ttk.Label(game_window, text="Press Start to begin", 
                                       font=('Arial', 12))
        self.reaction_status.pack(pady=10)
        
        self.reaction_scores_label = ttk.Label(game_window, text="", font=('Arial', 12))
        self.reaction_scores_label.pack(pady=5)
        
        ttk.Button(game_window, text="Start Game", 
                  command=self.start_reaction_round).pack(pady=10)
        
        # Bind click event
        self.reaction_area.bind('<Button-1>', self.handle_reaction_click)

    def start_reaction_round(self):
        if not self.reaction_active:
            self.reaction_active = True
            self.reaction_scores = []
            self.reaction_area.config(bg='red')
            self.reaction_status.config(text="Wait for green...")
            self.schedule_color_change()

    def schedule_color_change(self):
        if self.reaction_active:
            # Random delay between 1 and 5 seconds
            delay = random.randint(1000, 5000)
            self.reaction_area.after(delay, self.show_green)

    def show_green(self):
        if self.reaction_active:
            self.reaction_area.config(bg='green')
            self.waiting_for_click = True
            self.start_time = time.time()

    def handle_reaction_click(self, event):
        if not self.reaction_active:
            return
            
        if not self.waiting_for_click:
            # Clicked too early
            self.reaction_status.config(text="Too early! Wait for green.")
            self.reaction_area.config(bg='red')
            self.reaction_area.after(1000, self.schedule_color_change)
            return
            
        # Calculate reaction time
        reaction_time = round((time.time() - self.start_time) * 1000)  # Convert to milliseconds
        self.reaction_scores.append(reaction_time)
        
        # Update display
        self.reaction_area.config(bg='red')
        self.reaction_status.config(text=f"Reaction time: {reaction_time}ms")
        self.waiting_for_click = False
        
        # Update scores display
        avg_score = sum(self.reaction_scores) / len(self.reaction_scores)
        best_score = min(self.reaction_scores)
        self.reaction_scores_label.config(
            text=f"Best: {best_score}ms | Average: {round(avg_score)}ms\n"
                 f"Attempts: {len(self.reaction_scores)}/5"
        )
        
        # Check if game is complete
        if len(self.reaction_scores) >= 5:
            self.reaction_game_over()
        else:
            self.reaction_area.after(1000, self.schedule_color_change)

    def reaction_game_over(self):
        self.reaction_active = False
        avg_score = sum(self.reaction_scores) / len(self.reaction_scores)
        
        # Save score (using average reaction time)
        self.cursor.execute('''
            INSERT INTO scores (username, game, score, date)
            VALUES (?, ?, ?, ?)
        ''', (self.current_user, 'reaction', round(avg_score), datetime.now()))
        self.conn.commit()
        
        messagebox.showinfo("Game Over", 
                          f"Game Over!\nAverage reaction time: {round(avg_score)}ms\n"
                          f"Best time: {min(self.reaction_scores)}ms",
                          parent=self.reaction_area.winfo_toplevel())

    def start_hangman(self):
        game_window = tk.Toplevel(self.root)
        game_window.title("Hangman")
        game_window.geometry("400x600")
        
        self.word_list = [
            "python", "programming", "computer", "algorithm", "database",
            "interface", "software", "developer", "keyboard", "function",
            "variable", "network", "security", "application", "framework"
        ]
        
        self.hangman_tries = 6
        self.current_hangman_word = ""
        self.guessed_letters = set()
        
        # Game widgets
        self.hangman_canvas = tk.Canvas(game_window, width=200, height=250)
        self.hangman_canvas.pack(pady=20)
        
        self.word_display = ttk.Label(game_window, text="", font=('Arial', 24))
        self.word_display.pack(pady=20)
        
        self.tries_label = ttk.Label(game_window, text="Tries left: 6", font=('Arial', 12))
        self.tries_label.pack(pady=10)
        
        # Letter buttons frame
        letters_frame = ttk.Frame(game_window)
        letters_frame.pack(pady=10)
        
        # Create letter buttons
        row = 0
        col = 0
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            btn = ttk.Button(letters_frame, text=letter.upper(),
                           command=lambda l=letter: self.guess_letter(l))
            btn.grid(row=row, column=col, padx=2, pady=2)
            col += 1
            if col > 6:
                col = 0
                row += 1
        
        ttk.Button(game_window, text="New Game", 
                  command=self.start_hangman_round).pack(pady=10)
        
        self.start_hangman_round()

    def draw_hangman(self):
        self.hangman_canvas.delete("all")
        # Base
        self.hangman_canvas.create_line(40, 230, 160, 230)
        if self.hangman_tries < 6:  # Pole
            self.hangman_canvas.create_line(100, 230, 100, 50)
        if self.hangman_tries < 5:  # Top
            self.hangman_canvas.create_line(100, 50, 140, 50)
        if self.hangman_tries < 4:  # Rope
            self.hangman_canvas.create_line(140, 50, 140, 70)
        if self.hangman_tries < 3:  # Head
            self.hangman_canvas.create_oval(130, 70, 150, 90)
        if self.hangman_tries < 2:  # Body
            self.hangman_canvas.create_line(140, 90, 140, 150)
            self.hangman_canvas.create_line(140, 110, 120, 130)  # Arms
            self.hangman_canvas.create_line(140, 110, 160, 130)
        if self.hangman_tries < 1:  # Legs
            self.hangman_canvas.create_line(140, 150, 120, 180)
            self.hangman_canvas.create_line(140, 150, 160, 180)

    def start_hangman_round(self):
        self.current_hangman_word = random.choice(self.word_list)
        self.guessed_letters = set()
        self.hangman_tries = 6
        self.update_word_display()
        self.draw_hangman()
        
        # Reset letter buttons
        for widget in self.word_display.master.winfo_children():
            if isinstance(widget, ttk.Frame):
                for button in widget.winfo_children():
                    button.configure(state='normal')

    def update_word_display(self):
        display = ""
        for letter in self.current_hangman_word:
            if letter in self.guessed_letters:
                display += letter.upper() + " "
            else:
                display += "_ "
        self.word_display.config(text=display.strip())

    def guess_letter(self, letter):
        if letter not in self.guessed_letters:
            self.guessed_letters.add(letter)
            
            # Disable the button
            for widget in self.word_display.master.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for button in widget.winfo_children():
                        if button['text'].lower() == letter:
                            button.configure(state='disabled')
            
            if letter not in self.current_hangman_word:
                self.hangman_tries -= 1
                self.tries_label.config(text=f"Tries left: {self.hangman_tries}")
                self.draw_hangman()
                
                if self.hangman_tries == 0:
                    self.hangman_game_over(False)
            
            self.update_word_display()
            
            # Check for win
            if all(letter in self.guessed_letters for letter in self.current_hangman_word):
                self.hangman_game_over(True)

    def hangman_game_over(self, won):
        score = len(self.guessed_letters) if won else 0
        
        # Save score
        self.cursor.execute('''
            INSERT INTO scores (username, game, score, date)
            VALUES (?, ?, ?, ?)
        ''', (self.current_user, 'hangman', score, datetime.now()))
        self.conn.commit()
        
        message = "Congratulations! You won!" if won else f"Game Over! The word was: {self.current_hangman_word}"
        messagebox.showinfo("Game Over", message,
                          parent=self.word_display.winfo_toplevel())

    def start_math_quiz(self):
        game_window = tk.Toplevel(self.root)
        game_window.title("Math Quiz")
        game_window.geometry("400x500")
        
        self.math_score = 0
        self.math_time = 60
        self.math_active = False
        self.total_questions = 0
        
        # Game widgets
        ttk.Label(game_window, text="Solve the math problems!", 
                 font=('Arial', 12)).pack(pady=10)
        
        self.question_label = ttk.Label(game_window, text="", font=('Arial', 24))
        self.question_label.pack(pady=20)
        
        self.math_entry = ttk.Entry(game_window, font=('Arial', 14))
        self.math_entry.pack(pady=10)
        self.math_entry.bind('<Return>', lambda e: self.check_answer())
        
        self.math_score_label = ttk.Label(game_window, text="Score: 0/0", 
                                        font=('Arial', 12))
        self.math_score_label.pack(pady=5)
        
        self.math_timer_label = ttk.Label(game_window, text="Time: 60", 
                                        font=('Arial', 12))
        self.math_timer_label.pack(pady=5)
        
        ttk.Button(game_window, text="Start Game", 
                  command=self.start_math_round).pack(pady=10)

    def start_math_round(self):
        if not self.math_active:
            self.math_active = True
            self.math_score = 0
            self.total_questions = 0
            self.math_time = 60
            self.math_score_label.config(text="Score: 0/0")
            self.math_entry.delete(0, tk.END)
            self.math_entry.focus()
            self.next_question()
            self.update_math_timer()

    def next_question(self):
        if self.math_active:
            # Generate random numbers and operator
            num1 = random.randint(1, 20)
            num2 = random.randint(1, 20)
            operator = random.choice(['+', '-', '*'])
            
            # Store correct answer
            if operator == '+':
                self.current_answer = num1 + num2
            elif operator == '-':
                self.current_answer = num1 - num2
            else:
                self.current_answer = num1 * num2
            
            # Display question
            self.question_label.config(text=f"{num1} {operator} {num2} = ?")

    def check_answer(self):
        if self.math_active:
            try:
                answer = int(self.math_entry.get().strip())
                self.total_questions += 1
                
                if answer == self.current_answer:
                    self.math_score += 1
                    
                self.math_score_label.config(
                    text=f"Score: {self.math_score}/{self.total_questions}")
                self.math_entry.delete(0, tk.END)
                self.next_question()
                
            except ValueError:
                messagebox.showwarning("Invalid Input", 
                                     "Please enter a valid number",
                                     parent=self.question_label.winfo_toplevel())
                self.math_entry.delete(0, tk.END)

    def update_math_timer(self):
        if self.math_active:
            self.math_timer_label.config(text=f"Time: {self.math_time}")
            if self.math_time > 0:
                self.math_time -= 1
                self.question_label.after(1000, self.update_math_timer)
            else:
                self.math_active = False
                self.question_label.config(text="Game Over!")
                
                # Calculate accuracy percentage
                accuracy = (self.math_score / self.total_questions * 100) if self.total_questions > 0 else 0
                
                # Save score
                self.cursor.execute('''
                    INSERT INTO scores (username, game, score, date)
                    VALUES (?, ?, ?, ?)
                ''', (self.current_user, 'math_quiz', self.math_score, datetime.now()))
                self.conn.commit()
                
                messagebox.showinfo("Game Over", 
                                  f"Time's up!\nFinal Score: {self.math_score}/{self.total_questions}\n"
                                  f"Accuracy: {accuracy:.1f}%",
                                  parent=self.question_label.winfo_toplevel())

    def start_tictactoe(self):
        game_window = tk.Toplevel(self.root)
        game_window.title("Tic Tac Toe")
        game_window.geometry("400x500")
        
        self.current_player = 'X'
        self.board = [''] * 9
        self.game_over = False
        self.moves_made = 0
        
        # Game widgets
        ttk.Label(game_window, text="Tic Tac Toe", 
                 font=('Arial', 16, 'bold')).pack(pady=10)
        
        self.status_label = ttk.Label(game_window, 
                                    text="Player X's turn", 
                                    font=('Arial', 12))
        self.status_label.pack(pady=5)
        
        # Create game board
        board_frame = ttk.Frame(game_window)
        board_frame.pack(pady=20)
        
        self.buttons = []
        for i in range(3):
            for j in range(3):
                btn = tk.Button(board_frame, text="", width=8, height=4,
                              font=('Arial', 14, 'bold'),
                              command=lambda x=i*3+j: self.make_move(x))
                btn.grid(row=i, column=j, padx=2, pady=2)
                self.buttons.append(btn)
        
        ttk.Button(game_window, text="New Game", 
                  command=self.reset_board).pack(pady=10)

    def make_move(self, position):
        if not self.game_over and self.board[position] == '':
            self.board[position] = self.current_player
            self.buttons[position].config(text=self.current_player)
            self.moves_made += 1
            
            if self.check_winner():
                self.game_over = True
                self.status_label.config(text=f"Player {self.current_player} wins!")
                self.save_tictactoe_score(True)
            elif self.moves_made == 9:
                self.game_over = True
                self.status_label.config(text="It's a draw!")
                self.save_tictactoe_score(False)
            else:
                self.current_player = 'O' if self.current_player == 'X' else 'X'
                self.status_label.config(text=f"Player {self.current_player}'s turn")

    def check_winner(self):
        # Check rows, columns and diagonals
        win_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]  # Diagonals
        ]
        
        for combo in win_combinations:
            if (self.board[combo[0]] == self.board[combo[1]] == 
                self.board[combo[2]] == self.current_player):
                # Highlight winning combination
                for pos in combo:
                    self.buttons[pos].config(bg='lightgreen')
                return True
        return False

    def reset_board(self):
        self.current_player = 'X'
        self.board = [''] * 9
        self.game_over = False
        self.moves_made = 0
        self.status_label.config(text="Player X's turn")
        
        for button in self.buttons:
            button.config(text="", bg='SystemButtonFace')

    def save_tictactoe_score(self, won):
        score = 1 if won else 0
        self.cursor.execute('''
            INSERT INTO scores (username, game, score, date)
            VALUES (?, ?, ?, ?)
        ''', (self.current_user, 'tictactoe', score, datetime.now()))
        self.conn.commit()

    def start_2048(self):
        game_window = tk.Toplevel(self.root)
        game_window.title("2048")
        game_window.geometry("400x500")
        
        self.score_2048 = 0
        self.board_2048 = [[0] * 4 for _ in range(4)]
        self.game_2048_over = False
        
        # Game widgets
        ttk.Label(game_window, text="2048", font=('Arial', 24, 'bold')).pack(pady=10)
        
        self.score_label_2048 = ttk.Label(game_window, text="Score: 0", 
                                        font=('Arial', 14))
        self.score_label_2048.pack(pady=5)
        
        # Create game board
        self.board_frame_2048 = ttk.Frame(game_window)
        self.board_frame_2048.pack(pady=20)
        
        self.cells_2048 = []
        for i in range(4):
            row = []
            for j in range(4):
                cell = tk.Label(self.board_frame_2048, text="",
                              width=6, height=3, relief="solid",
                              font=('Arial', 16, 'bold'))
                cell.grid(row=i, column=j, padx=2, pady=2)
                row.append(cell)
            self.cells_2048.append(row)
        
        # Bind arrow keys
        game_window.bind('<Left>', lambda e: self.move_2048('left'))
        game_window.bind('<Right>', lambda e: self.move_2048('right'))
        game_window.bind('<Up>', lambda e: self.move_2048('up'))
        game_window.bind('<Down>', lambda e: self.move_2048('down'))
        
        ttk.Button(game_window, text="New Game", 
                  command=self.new_game_2048).pack(pady=10)
        
        self.new_game_2048()
        
    def new_game_2048(self):
        self.score_2048 = 0
        self.game_2048_over = False
        self.board_2048 = [[0] * 4 for _ in range(4)]
        self.score_label_2048.config(text="Score: 0")
        self.add_new_tile()
        self.add_new_tile()
        self.update_board_2048()
        
    def add_new_tile(self):
        empty_cells = [(i, j) for i in range(4) for j in range(4) 
                      if self.board_2048[i][j] == 0]
        if empty_cells:
            i, j = random.choice(empty_cells)
            self.board_2048[i][j] = 2 if random.random() < 0.9 else 4
            
    def update_board_2048(self):
        colors = {
            0: ('#CCC0B3', '#776E65'),
            2: ('#EEE4DA', '#776E65'),
            4: ('#EDE0C8', '#776E65'),
            8: ('#F2B179', '#F9F6F2'),
            16: ('#F59563', '#F9F6F2'),
            32: ('#F67C5F', '#F9F6F2'),
            64: ('#F65E3B', '#F9F6F2'),
            128: ('#EDCF72', '#F9F6F2'),
            256: ('#EDCC61', '#F9F6F2'),
            512: ('#EDC850', '#F9F6F2'),
            1024: ('#EDC53F', '#F9F6F2'),
            2048: ('#EDC22E', '#F9F6F2')
        }
        
        for i in range(4):
            for j in range(4):
                value = self.board_2048[i][j]
                bg_color = colors.get(value, colors[0])[0]
                fg_color = colors.get(value, colors[0])[1]
                self.cells_2048[i][j].config(
                    text=str(value) if value != 0 else "",
                    bg=bg_color,
                    fg=fg_color
                )
                
    def move_2048(self, direction):
        if self.game_2048_over:
            return
            
        # Store the current board state
        old_board = [row[:] for row in self.board_2048]
        
        # Merge tiles
        if direction == 'left':
            self.merge_left()
        elif direction == 'right':
            self.reverse_board()
            self.merge_left()
            self.reverse_board()
        elif direction == 'up':
            self.transpose_board()
            self.merge_left()
            self.transpose_board()
        else:  # down
            self.transpose_board()
            self.reverse_board()
            self.merge_left()
            self.reverse_board()
            self.transpose_board()
            
        # Check if board changed
        if any(old_board[i][j] != self.board_2048[i][j] 
               for i in range(4) for j in range(4)):
            self.add_new_tile()
            
        self.update_board_2048()
        
        # Check for game over
        if self.is_game_over():
            self.game_2048_over = True
            self.save_2048_score()
            messagebox.showinfo("Game Over", 
                              f"Game Over! Final Score: {self.score_2048}",
                              parent=self.board_frame_2048.winfo_toplevel())
            
    def merge_left(self):
        for i in range(4):
            # Merge same numbers
            line = [n for n in self.board_2048[i] if n != 0]
            for j in range(len(line) - 1):
                if line[j] == line[j + 1]:
                    line[j] *= 2
                    self.score_2048 += line[j]
                    line[j + 1] = 0
            line = [n for n in line if n != 0]
            # Fill with zeros
            line.extend([0] * (4 - len(line)))
            self.board_2048[i] = line
            self.score_label_2048.config(text=f"Score: {self.score_2048}")
            
    def reverse_board(self):
        for i in range(4):
            self.board_2048[i].reverse()
            
    def transpose_board(self):
        self.board_2048 = list(map(list, zip(*self.board_2048)))
        
    def is_game_over(self):
        # Check for empty cells
        if any(0 in row for row in self.board_2048):
            return False
            
        # Check for possible merges
        for i in range(4):
            for j in range(3):
                if (self.board_2048[i][j] == self.board_2048[i][j + 1] or
                    self.board_2048[j][i] == self.board_2048[j + 1][i]):
                    return False
        return True
        
    def save_2048_score(self):
        self.cursor.execute('''
            INSERT INTO scores (username, game, score, date)
            VALUES (?, ?, ?, ?)
        ''', (self.current_user, '2048', self.score_2048, datetime.now()))
        self.conn.commit()

    def update_welcome_message(self):
        self.welcome_label.config(text=f"Welcome, {self.current_user}!")

    # Add these utility methods
    def add_todo(self):
        task = self.todo_entry.get()
        if task:
            self.cursor.execute('''
                INSERT INTO todos (username, task, completed, created_at)
                VALUES (?, ?, ?, ?)
            ''', (self.current_user, task, False, datetime.now()))
            self.conn.commit()
            self.todo_entry.delete(0, tk.END)
            self.update_todo_list()

    def update_todo_list(self):
        self.todo_listbox.delete(0, tk.END)
        self.cursor.execute('SELECT task FROM todos WHERE username=? AND completed=0',
                          (self.current_user,))
        for task in self.cursor.fetchall():
            self.todo_listbox.insert(tk.END, task[0])

    def save_note(self):
        content = self.notes_text.get("1.0", tk.END).strip()
        if content:
            self.cursor.execute('''
                INSERT OR REPLACE INTO notes (username, content, updated_at)
                VALUES (?, ?, ?)
            ''', (self.current_user, content, datetime.now()))
            self.conn.commit()
            messagebox.showinfo("Success", "Note saved successfully!")

    def start_timer(self):
        if not hasattr(self, 'timer_running'):
            self.timer_running = True
            self.remaining_time = 25 * 60  # 25 minutes in seconds
            self.update_timer()

    def stop_timer(self):
        if hasattr(self, 'timer_running'):
            self.timer_running = False

    def reset_timer(self):
        self.timer_running = False
        self.remaining_time = 25 * 60
        self.timer_label.config(text="25:00")

    def update_timer(self):
        if hasattr(self, 'timer_running') and self.timer_running:
            minutes = self.remaining_time // 60
            seconds = self.remaining_time % 60
            self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            
            if self.remaining_time > 0:
                self.remaining_time -= 1
                self.root.after(1000, self.update_timer)
            else:
                self.timer_running = False
                messagebox.showinfo("Time's Up!", "Pomodoro session completed!")
                self.timer_label.config(text="25:00")

    def update_stats(self):
        self.stats_text.delete("1.0", tk.END)
        
        # Get game scores
        self.cursor.execute('''
            SELECT game, COUNT(*) as games_played, MIN(score) as best_score
            FROM scores WHERE username=?
            GROUP BY game
        ''', (self.current_user,))
        
        stats = "Game Statistics:\n\n"
        for game, played, best in self.cursor.fetchall():
            stats += f"{game.title()}:\n"
            stats += f"Games Played: {played}\n"
            stats += f"Best Score: {best}\n\n"
            
        self.stats_text.insert("1.0", stats)

    def calculator_click(self, value):
        current = self.calc_display.get()
        
        if value == '=':
            try:
                result = eval(current)
                self.calc_display.delete(0, tk.END)
                self.calc_display.insert(tk.END, str(result))
            except:
                self.calc_display.delete(0, tk.END)
                self.calc_display.insert(tk.END, "Error")
        else:
            self.calc_display.insert(tk.END, value)
            
    def calculator_clear(self):
        self.calc_display.delete(0, tk.END)

    def run(self):
        self.root.mainloop()
        self.conn.close()

if __name__ == "__main__":
    app = GameApp()
    app.run()
