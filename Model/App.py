import tkinter as tk
import customtkinter as ctk
import random
import cv2
from PIL import Image, ImageTk
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser
import numpy as np
import tensorflow as tf
import csv
import os
import speech_recognition as sr
import requests
import tkinter.messagebox as messagebox
import json  # For saving/loading user data
from collections import Counter
import sqlite3

USER_DATA_FILE = "user_data.json"
DATABASE_FILE = "moodsync_data.db"

class MoodSyncApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MoodSync Music System")
        self.root.geometry("1500x700")
        self.root.configure(bg="#2c003e")
        self.root.resizable(True, True)

        # Load emotion detection model
        try:
            self.model = tf.keras.models.load_model(r'E:\FYP_PROJECT\Complete_project\FER_2013_dataset\FER_DATA.keras')
        except FileNotFoundError:
            messagebox.showerror("Model Error", "Emotion detection model file not found!")
            self.model = None
        except Exception as e:
            messagebox.showerror("Model Error", f"Error loading emotion detection model: {e}")
            self.model = None

        # Spotify credentials
        self.client_id = "206cc88c5d7649f4befdc41e69a16268"
        self.client_secret = "aa4b800f36804c9baf8340ff7f566ec4"  # Replace with your client secret
        self.redirect_uri = "http://127.0.0.1:5000/callback"
        self.scope = "user-read-private user-read-currently-playing user-read-playback-state"

        self.sp = None
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope
            ))
        except Exception as e:
            messagebox.showerror("Spotify Auth Error", f"Could not authenticate with Spotify: {e}")

        self.video_source = 0
        self.capture = cv2.VideoCapture(self.video_source)
        self.is_video_playing = True

        self.emoji_dir = r"E:\FYP_PROJECT\emojis"

        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.language_var = tk.StringVar(value=" ")
        self.search_var = tk.StringVar()

        self.user_data = self.load_user_data()
        self.favorite_songs = self.user_data.get('favorite_songs', [])
        self.search_history = self.user_data.get('search_history', [])
        self.user_preferences = self.analyze_user_preferences()

        self.init_database()
        self.load_favorites_from_db()
        self.load_search_history_from_db()

        self.init_welcome_screen()

    def init_database(self):
        """Initializes the SQLite database and creates necessary tables."""
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                artist TEXT NOT NULL,
                url TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT UNIQUE NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def load_favorites_from_db(self):
        """Loads favorite songs from the database into the in-memory list."""
        self.cursor.execute("SELECT name, artist, url FROM favorites")
        rows = self.cursor.fetchall()
        self.favorite_songs = [{"name": row[0], "artist": row[1], "url": row[2]} for row in rows]

    def save_favorite_to_db(self, track_info):
        """Saves a favorite song to the database."""
        try:
            self.cursor.execute("INSERT INTO favorites (name, artist, url) VALUES (?, ?, ?)",
                                (track_info['name'], track_info['artist'], track_info['url']))
            self.conn.commit()
            self.load_favorites_from_db() # Reload to keep in-memory list updated
        except sqlite3.IntegrityError:
            print(f"'{track_info['name']}' is already in favorites database.")

    def remove_favorite_from_db(self, track_info):
        """Removes a favorite song from the database."""
        self.cursor.execute("DELETE FROM favorites WHERE name = ?", (track_info['name'],))
        self.conn.commit()
        self.load_favorites_from_db() # Reload to keep in-memory list updated

    def load_search_history_from_db(self):
        """Loads search history from the database into the in-memory list."""
        self.cursor.execute("SELECT query FROM search_history ORDER BY timestamp DESC LIMIT 10")
        rows = self.cursor.fetchall()
        self.search_history = [row[0] for row in rows]

    def save_search_query_to_db(self, query):
        """Saves a search query to the database."""
        try:
            self.cursor.execute("INSERT INTO search_history (query) VALUES (?)", (query,))
            self.conn.commit()
            self.load_search_history_from_db() # Reload to keep in-memory list updated
        except sqlite3.IntegrityError:
            print(f"'{query}' is already in search history.")

    def load_user_data(self):
        """Loads user data (other preferences if any) from a JSON file."""
        try:
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def save_user_data(self):
        """Saves user data (other preferences if any) to a JSON file."""
        # Currently not saving favorites/search history to JSON as we are using SQLite
        data = {}
        try:
            with open(USER_DATA_FILE, 'w') as f:
                json.dump(data, f)
        except IOError:
            messagebox.showerror("File Error", "Could not save user data.")

    def analyze_user_preferences(self):
        """Analyzes user's favorite songs and search history to determine preferences."""
        all_terms = []
        for song in self.favorite_songs:
            all_terms.extend(song['name'].lower().split())
            all_terms.extend(song['artist'].lower().split())
        for query in self.search_history:
            all_terms.extend(query.lower().split())

        return Counter(all_terms).most_common(10) # Get top 10 most frequent terms

    def get_content_based_recommendations(self, limit=5):
        """Recommends songs based on user's favorite songs and search history."""
        if not self.user_preferences:
            return []

        query_terms = [term for term, count in self.user_preferences]
        search_query = " ".join(query_terms)

        try:
            results = self.sp.search(q=search_query, type='track', limit=limit * 3) # Search more to filter
            if results and results['tracks']['items']:
                recommendations = []
                seen_tracks = set()
                for track in results['tracks']['items']:
                    track_id = track['id']
                    if track_id not in seen_tracks and track not in self.favorite_songs:
                        track_name = track['name']
                        artist_name = track['artists'][0]['name']
                        track_url = track['external_urls']['spotify']
                        recommendations.append({"name": track_name, "artist": artist_name, "url": track_url})
                        seen_tracks.add(track_id)
                        if len(recommendations) >= limit:
                            break
                return recommendations
            else:
                return []
        except spotipy.exceptions.SpotifyException as e:
            print(f"Spotify error during content-based recommendation: {e}")
            return []
        except requests.exceptions.ConnectionError:
            print("Network error during content-based recommendation.")
            return []
        except Exception as e:
            print(f"Unexpected error during content-based recommendation: {e}")
            return []

    def clear_window(self):
        """Destroys all widgets in the root window."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def init_welcome_screen(self):
        """Initializes and displays the welcome/login screen."""
        self.clear_window()

        frame = tk.Frame(self.root, bg="#2c003e")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="Welcome to", font=("Arial", 22), bg="#2c003e", fg="white").pack(pady=(0, 5))
        tk.Label(frame, text="MoodSync", font=("Arial", 44, "bold"), bg="#2c003e", fg="#1DB954").pack(pady=(0, 5))
        tk.Label(frame, text="Personalized Music System", font=("Arial", 16), bg="#2c003e", fg="white").pack(pady=(0, 20))

        self.add_entry_field(frame, "👤 Username", self.name_var)
        self.add_entry_field(frame, "📧 Email", self.email_var)
        self.add_entry_field(frame, "🔒 Password", self.pass_var, show="*")

        tk.Label(frame, text="🌍 Select Language", font=("Arial", 12), bg="#2c003e", fg="white").pack(pady=(10, 2))
        self.language_dropdown = ctk.CTkComboBox(frame, values=["Urdu", "Sindhi", "Punjabi"], variable=self.language_var, width=250)
        self.language_dropdown.pack(pady=5)

        ctk.CTkButton(frame, text="Proceed 🎶", command=self.show_main_screen,
                      width=220, height=45, corner_radius=12,fg_color="#1DB954", hover_color="#1ed760").pack(pady=20)

    def add_entry_field(self, frame, label_text, var, show=None):
        """Helper to create labeled entry fields."""
        tk.Label(frame, text=label_text, font=("Arial", 12), bg="#2c003e", fg="white").pack(anchor="center", pady=(10, 2))
        entry = ctk.CTkEntry(frame, textvariable=var, width=250, corner_radius=8)
        if show:
            entry.configure(show=show)
        entry.pack(pady=2)

    def show_main_screen(self):
        """Displays the main application screen with webcam, mood detection, and playlist."""
        self.clear_window()

        outer_frame = tk.Frame(self.root, bg="#2c003e", padx=30, pady=30)
        outer_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.95)

        title_bar = tk.Frame(outer_frame, bg="#2c003e")
        title_bar.pack(fill="x", pady=(0, 20))

        tk.Label(title_bar, text="🎵 Mood-Based Music Suggestions 🎵", font=("Arial", 22, "bold"),
                 bg="#2c003e", fg="#1DB954").pack(pady=(0, 20), anchor="center")

        search_suggestion_row = tk.Frame(outer_frame, bg="#2c003e")
        search_suggestion_row.pack(fill="x", pady=(0, 20), padx=20)

        search_bar_frame = tk.Frame(search_suggestion_row, bg="#2c003e")
        search_bar_frame.pack(side="left", padx=(0, 20))
        self.search_entry = ctk.CTkEntry(search_bar_frame, textvariable=self.search_var, placeholder_text="Search", width=300)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        search_button = ctk.CTkButton(search_bar_frame, text="Search", width=60, command=self.manual_search)
        search_button.pack(side="left")
        voice_button = ctk.CTkButton(search_bar_frame, text="🎙️", width=40, command=self.voice_search)
        voice_button.pack(side="left")

        suggestion_button = ctk.CTkButton(search_suggestion_row, text="Suggestion", command=self.show_suggestion_screen,
                                             fg_color="#1DB954", hover_color="#1ed760", width=100)
        suggestion_button.pack(side="right")

        content_frame = tk.Frame(outer_frame, bg="#2c003e")
        content_frame.pack(expand=True, fill="both")

        webcam_frame = tk.Frame(content_frame, bg="#3b0a57", padx=10, pady=10, relief="ridge", bd=2)
        webcam_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        mood_frame = tk.Frame(content_frame, bg="#2c003e")
        mood_frame.grid(row=0, column=1, sticky="nsew", padx=40, pady=10)

        playlist_frame = tk.Frame(content_frame, bg="#3b0a57", padx=20, pady=20, relief="ridge", bd=2)
        playlist_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_columnconfigure(2, weight=2)
        content_frame.grid_rowconfigure(0, weight=1)

        # Webcam view
        self.video_label = tk.Label(webcam_frame, bg="#3b0a57")
        self.video_label.pack(expand=True)
        self.show_webcam()

        # Mood Info
        self.mood_label = tk.Label(mood_frame, text="Mood: Not detected", font=("Arial", 18, "bold"),
                                     bg="#2c003e", fg="#1DB954")
        self.mood_label.pack(pady=(10, 5))

        self.emoji_label = tk.Label(mood_frame, bg="#2c003e")
        self.emoji_label.pack(pady=(0, 20))

        ctk.CTkButton(mood_frame, text="Detect Mood 🎭", command=self.detect_mood,
                      width=200, height=40, corner_radius=10,
                      fg_color="#1DB954", hover_color="#1ed760").pack(pady=20)

        # Playlist on Main Screen
        tk.Label(playlist_frame, text="🎶 Recommended Playlist", font=("Arial", 16, "bold"),
                 bg="#3b0a57", fg="#1DB954").pack(pady=(0, 10))
        self.playlist_canvas = tk.Canvas(playlist_frame, bg="#3b0a57", bd=0, highlightthickness=0)
        self.playlist_scrollbar = tk.Scrollbar(playlist_frame, orient="vertical", command=self.playlist_canvas.yview)
        self.playlist_canvas.configure(yscrollcommand=self.playlist_scrollbar.set)

        self.playlist_scrollbar.pack(side="right", fill="y")
        self.playlist_canvas.pack(side="left", fill="both", expand=True)

        self.playlist_container = tk.Frame(self.playlist_canvas, bg="#3b0a57")
        self.playlist_container_id = self.playlist_canvas.create_window((0, 0), window=self.playlist_container, anchor="nw", width=self.playlist_canvas.winfo_width())
        self.playlist_canvas.bind("<Configure>", lambda event: self.playlist_canvas.itemconfig(self.playlist_container_id, width=event.width))
        self.playlist_container.bind("<Configure>", lambda event: self.playlist_canvas.configure(scrollregion=self.playlist_canvas.bbox("all")))

    def show_suggestion_screen(self):
        """Displays the suggestion screen with options for weather-based, favorites, and content-based playlists."""
        self.clear_window()
        self.suggestion_frame = tk.Frame(self.root, bg="#2c003e")
        self.suggestion_frame.pack(fill="both", expand=True)

        tk.Label(self.suggestion_frame, text="Suggestions & Your Playlists", font=("Arial", 24, "bold"), bg="#2c003e", fg="#1DB954").pack(pady=20)

        # Container for the buttons
        self.suggestion_buttons_frame = tk.Frame(self.suggestion_frame, bg="#2c003e")
        self.suggestion_buttons_frame.pack(pady=(0, 20))

        ctk.CTkButton(self.suggestion_buttons_frame, text="Weather-Based Recommendation", width=280, height=40, corner_radius=10,
                      fg_color="#4a148c", hover_color="#6a1b9a",
                      command=self.trigger_weather_recommendation).pack(side="left", padx=10)

        ctk.CTkButton(self.suggestion_buttons_frame, text="View Favorites ❤️", width=200, height=40, corner_radius=10,
                      fg_color="#ff69b4", hover_color="#ff80c0",
                      command=self.trigger_favorites_playlist).pack(side="left", padx=10)

        ctk.CTkButton(self.suggestion_buttons_frame, text="Content-Based 🧠", width=200, height=40, corner_radius=10,
                      fg_color="#ffa000", hover_color="#ffc107",
                      command=self.trigger_content_based_recommendation).pack(side="left", padx=10)

        # Centered container for the playlist area and info label
        self.centered_playlist_container = tk.Frame(self.suggestion_frame, bg="#2c003e")

        # Label to display specific info (weather, favorites, or content-based title)
        self.info_label = tk.Label(self.centered_playlist_container, text="", font=("Arial", 16), bg="#2c003e", fg="white")
        self.info_label.pack(pady=(0, 10))

        # Playlist area with Canvas and Scrollbar
        self.suggestion_playlist_canvas_frame = tk.Frame(self.centered_playlist_container, bg="#2c003e", width=650, height=400, relief="ridge", bd=2)
        self.suggestion_playlist_canvas_frame.pack(fill="both", expand=False, padx=20, pady=10)

        self.suggestion_playlist_canvas = tk.Canvas(self.suggestion_playlist_canvas_frame, bg="#2c003e", highlightthickness=0)
        self.suggestion_playlist_scrollbar = tk.Scrollbar(self.suggestion_playlist_canvas_frame, orient="vertical", command=self.suggestion_playlist_canvas.yview)
        self.suggestion_playlist_canvas.configure(yscrollcommand=self.suggestion_playlist_scrollbar.set)

        self.suggestion_playlist_scrollbar.pack(side="right", fill="y")
        self.suggestion_playlist_canvas.pack(side="left", fill="both", expand=True)

        self.suggestion_playlist_container = tk.Frame(self.suggestion_playlist_canvas, bg="#2c003e")
        self.suggestion_playlist_container_id = self.suggestion_playlist_canvas.create_window((0, 0), window=self.suggestion_playlist_container, anchor="nw", width=650)
        self.suggestion_playlist_container.bind("<Configure>", lambda e: self.suggestion_playlist_canvas.configure(scrollregion=self.suggestion_playlist_canvas.bbox("all")))
        self.suggestion_playlist_canvas.bind("<Configure>", lambda event: self.suggestion_playlist_canvas.itemconfig(self.suggestion_playlist_container_id, width=event.width))

        # Back to Suggestions button
        self.back_to_suggestions_button = ctk.CTkButton(self.suggestion_frame, text="⬅ Back to Suggestions",
                                                     command=self.reset_suggestion_screen,
                                                     fg_color="#1DB954", hover_color="#1ed760", width=200)

        # Back to Main button
        ctk.CTkButton(self.suggestion_frame, text="⬅ Back to Main", command=self.show_main_screen,
                      fg_color="#1DB954", hover_color="#1ed760", width=200).pack(side="bottom", pady=(10, 20))

    def reset_suggestion_screen(self):
        """Resets the suggestion screen to show buttons and hide playlists."""
        self._clear_container_widgets(self.suggestion_playlist_container)
        self.info_label.config(text="")
        self.centered_playlist_container.pack_forget()
        self.back_to_suggestions_button.pack_forget()
        self.suggestion_buttons_frame.pack(pady=(0, 20))
        for widget in self.suggestion_buttons_frame.winfo_children():
            widget.pack(side="left", padx=10)

    def hide_suggestion_buttons(self):
        """Hides the weather, favorites, and content-based selection buttons."""
        self.suggestion_buttons_frame.pack_forget()

    def show_playlist_area(self):
        """Shows the playlist canvas, info label, and back to suggestions button on the suggestion screen."""
        self.centered_playlist_container.pack(side="top", pady=10, fill="none", expand=False)
        self.back_to_suggestions_button.pack(pady=10)

    def trigger_weather_recommendation(self):
        """Triggers the display of weather-based recommendations."""
        self.hide_suggestion_buttons()
        self.show_playlist_area()
        self.handle_suggestion("Weather Based Recommendation")

    def trigger_favorites_playlist(self):
        """Triggers the display of the user's favorite songs."""
        self.hide_suggestion_buttons()
        self.show_playlist_area()
        self.show_favorites_playlist()

    def trigger_content_based_recommendation(self):
        """Triggers the display of content-based recommendations."""
        self.hide_suggestion_buttons()
        self.show_playlist_area()
        self.info_label.config(text="Based on Your Favorites & Searches")
        self._clear_container_widgets(self.suggestion_playlist_container)
        recommendations = self.get_content_based_recommendations()
        if recommendations:
            for track_info in recommendations:
                self.create_song_card(self.suggestion_playlist_container, track_info, enable_remove=False)
        else:
            tk.Label(self.suggestion_playlist_container, text="No content-based recommendations available yet.",
                     font=("Arial", 12), bg="#2c003e", fg="white").pack(pady=10)

        self.suggestion_playlist_container.update_idletasks()
        self.suggestion_playlist_canvas.config(scrollregion=self.suggestion_playlist_canvas.bbox("all"))

    def manual_search(self):
        """Performs a manual search on Spotify based on user input."""
        query = self.search_var.get()
        if query:
            self.perform_search(query)

    def voice_search(self):
        """Initiates a voice search for music."""
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            try:
                audio = r.listen(source, timeout=5)
                query = r.recognize_google(audio)
                print(f"You said: {query}")
                self.search_var.set(query)
                self.perform_search(query)
            except sr.WaitTimeoutError:
                messagebox.showinfo("Voice Search", "No speech detected.")
            except sr.UnknownValueError:
                messagebox.showerror("Voice Search", "Could not understand audio.")
            except sr.RequestError as e:
                messagebox.showerror("Voice Search", f"Could not request results from Google Speech Recognition service; {e}")

    def perform_search(self, query):
        """Fetches and displays Spotify tracks for a given search query on the main screen."""
        self._clear_container_widgets(self.playlist_container)
        self.save_search_query_to_db(query)
        self.user_preferences = self.analyze_user_preferences() # Update preferences on search
        self.save_user_data() # Save any other user data
        try:
            results = self.sp.search(q=query, type='track', limit=10)
            if results and results['tracks']['items']:
                for track in results['tracks']['items']:
                    track_name = track['name']
                    artist_name = track['artists'][0]['name']
                    track_url = track['external_urls']['spotify']
                    track_info = {"name": track_name, "artist": artist_name, "url": track_url}
                    self.create_song_card(self.playlist_container, track_info, enable_remove=False)
            else:
                tk.Label(self.playlist_container, text="No songs found for your search.",
                         font=("Arial", 12), bg="#3b0a57", fg="white").pack(pady=10)
        except spotipy.exceptions.SpotifyException as e:
            messagebox.showerror("Spotify Error", f"Could not perform search: {e}")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Network Error", "Could not connect to Spotify. Check your internet connection.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during search: {e}")

        self.playlist_container.update_idletasks()
        self.playlist_canvas.config(scrollregion=self.playlist_canvas.bbox("all"))

    def _clear_container_widgets(self, container_frame):
        """Helper function to destroy all widgets within a given frame."""
        for widget in container_frame.winfo_children():
            widget.destroy()

    def handle_suggestion(self, suggestion_type):
        """Fetches and displays a playlist based on the selected suggestion type (e.g., weather)."""
        self._clear_container_widgets(self.suggestion_playlist_container)

        if suggestion_type == "Weather Based Recommendation":
            api_key = "0887f01a6be409675ed1284dc132c2d1"  # Replace with your OpenWeatherMap API key
            city = "Nawabshah"  # Using the current location
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

            try:
                response = requests.get(url)
                data = response.json()

                if response.status_code == 200:
                    weather_main = data.get("weather", [{}])[0].get("main", "").lower()
                    weather_desc = data.get("weather", [{}])[0].get("description", "N/A").capitalize()
                    temp = data.get("main", {}).get("temp", "N/A")
                    self.info_label.config(text=f"🌤 Weather in {city}: {weather_desc} | Temp: {temp}°C")

                    weather_query_map = {
                        "clear": "sunny day songs, uplifting urdu tracks, positive punjabi music",
                        "rain": "rainy day indian music, urdu romantic sad, lo-fi for rain",
                        "drizzle": "mellow urdu music, rain chill urdu songs, mellow sindhi music, mellow punjabi music",
                        "clouds": "cloudy day playlist india, soft mood pakistani, lo-fi punjabi vibes",
                        "thunderstorm": "intense urdu rap, thunderstorm tracks, hardcore urdu beats",
                        "haze": "chill instrumental hindi, lo-fi haze pakistan",
                        "mist": "calm instrumental, soothing Pakistani music",
                        "fog": "ambient soundscapes, chill Pakistani lo-fi",
                        "snow": "winter chill playlist, cozy Urdu songs"
                    }

                    query = weather_query_map.get(weather_main, "top urdu, sindhi, punjabi hits")

                    results = self.sp.search(q=query, type='track', limit=5)
                    if results and results['tracks']['items']:
                        for track in results['tracks']['items']:
                            track_name = track['name']
                            artist_name = track['artists'][0]['name']
                            track_url = track['external_urls']['spotify']
                            track_info = {"name": track_name, "artist": artist_name, "url": track_url}
                            self.create_song_card(self.suggestion_playlist_container, track_info, enable_remove=False)
                    else:
                        tk.Label(self.suggestion_playlist_container, text=f"No Spotify tracks found for {weather_main} weather.",
                                 font=("Arial", 12), bg="#2c003e", fg="white").pack(pady=10)
                else:
                    self.info_label.config(text=f"Error fetching weather: {data.get('message', 'Unknown error')}", fg="red")
                    tk.Label(self.suggestion_playlist_container, text="Could not get weather recommendations.",
                             font=("Arial", 12), bg="#2c003e", fg="red").pack(pady=10)

            except requests.exceptions.ConnectionError:
                self.info_label.config(text="Network Error: Cannot connect to weather service.", fg="red")
                tk.Label(self.suggestion_playlist_container, text="Check your internet connection.",
                         font=("Arial", 12), bg="#2c003e", fg="red").pack(pady=10)
            except Exception as e:
                self.info_label.config(text=f"Error fetching weather or Spotify data: {e}", fg="red")
                tk.Label(self.suggestion_playlist_container, text="An unexpected error occurred.",
                         font=("Arial", 12), bg="#2c003e", fg="red").pack(pady=10)

        self.suggestion_playlist_container.update_idletasks()
        self.suggestion_playlist_canvas.config(scrollregion=self.suggestion_playlist_canvas.bbox("all"))

    def show_favorites_playlist(self):
        """Displays the user's saved favorite songs."""
        self._clear_container_widgets(self.suggestion_playlist_container)
        self.info_label.config(text="❤️ Your Favorite Songs ❤️")

        if self.favorite_songs:
            for track_info in self.favorite_songs:
                self.create_song_card(self.suggestion_playlist_container, track_info, enable_remove=True)
        else:
            tk.Label(self.suggestion_playlist_container, text="No favorite songs added yet.",
                     font=("Arial", 12), bg="#2c003e", fg="white").pack(pady=10)

        self.suggestion_playlist_container.update_idletasks()
        self.suggestion_playlist_canvas.config(scrollregion=self.suggestion_playlist_canvas.bbox("all"))

    def remove_from_favorites(self, track_info_to_remove, card_frame):
        """Removes a song from the favorites list and updates the UI and database."""
        self.remove_favorite_from_db(track_info_to_remove)
        card_frame.destroy()
        self.suggestion_playlist_container.update_idletasks()
        self.suggestion_playlist_canvas.config(scrollregion=self.suggestion_playlist_canvas.bbox("all"))
        messagebox.showinfo("Favorites", f"'{track_info_to_remove['name']}' removed from your favorites.")
        print(f"Removed from favorites: {track_info_to_remove['name']} - {track_info_to_remove['artist']}")

    def show_webcam(self):
        """Continuously updates the webcam feed in the UI."""
        if self.is_video_playing and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                frame = cv2.resize(frame, (300, 300))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image=img)
                self.video_label.configure(image=photo)
                self.video_label.image = photo
            self.video_label.after(10, self.show_webcam)
        elif not self.capture.isOpened():
            print("Webcam capture is not open.")

    def detect_mood(self):
        """Detects mood from the webcam feed and updates the UI and playlist."""
        self.is_video_playing = False # Pause webcam update while processing
        if self.capture.isOpened():
            ret, frame = self.capture.read()
            if not ret:
                self.is_video_playing = True
                self.show_webcam()
                messagebox.showerror("Webcam Error", "Could not capture image from webcam.")
                return

            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                face_img = cv2.resize(gray, (48, 48)) / 255.0
                face_img = np.expand_dims(face_img, axis=0)
                face_img = np.expand_dims(face_img, axis=-1)

                prediction = self.model.predict(face_img)
                mood = self.get_mood_label(prediction)

                self.mood_label.config(text=f"Mood: {mood.upper()}")
                self.show_emoji(mood)
                self.show_playlist(mood) # Update main screen playlist based on mood
            except Exception as e:
                messagebox.showerror("Mood Detection Error", f"An error occurred during mood detection: {e}")
                print(f"Mood detection error: {e}")

            # Resume webcam
            self.is_video_playing = True
            self.show_webcam()
        else:
            print("Webcam capture is not open.")

    def get_mood_label(self, prediction):
        """Converts model prediction to a human-readable mood label."""
        classes = ["angry", "happy", "sad", "neutral"] # Ensure these match your model's output order
        return classes[np.argmax(prediction)]

    def show_emoji(self, mood):
        """Displays an emoji corresponding to the detected mood."""
        emoji_path = os.path.join(self.emoji_dir, f"{mood}.jpeg")
        try:
            img = Image.open(emoji_path)
            img = img.resize((100, 100))
            photo = ImageTk.PhotoImage(img)
            self.emoji_label.configure(image=photo)
            self.emoji_label.image = photo
        except FileNotFoundError:
            self.emoji_label.config(text="😐", font=("Arial", 48))
            print(f"Emoji file not found: {emoji_path}")
        except Exception as e:
            self.emoji_label.config(text="😐", font=("Arial", 48))
            print(f"Error loading emoji {mood}.jpeg: {e}")

    def play_song(self, url):
        """Opens the song in the default web browser (Spotify web player)."""
        webbrowser.open(url)

    def add_to_favorites(self, track_info):
        """Adds a song to the in-memory and database favorites list."""
        if track_info not in self.favorite_songs:
            self.favorite_songs.append(track_info)
            self.save_favorite_to_db(track_info)
            messagebox.showinfo("Favorites", f"'{track_info['name']}' added to your favorites!")
            print(f"Added to favorites: {track_info['name']} - {track_info['artist']}")
        else:
            messagebox.showinfo("Favorites", f"'{track_info['name']}' is already in your favorites!")

    def show_playlist(self, mood):
        """Fetches and displays a mood-based playlist on the main screen."""
        self._clear_container_widgets(self.playlist_container) # Clear existing songs

        query = {
            "happy": "Armaan Malik songs, Diljit Dosanjh songs, Honey Singh songs, punjabi happy hits, sindhi joyful music",
            "sad": "Arijit Singh songs, Rahat Fateh Ali Khan songs, Sahir Ali Bagga songs, urdu pakistani drama sad osts, urdu sad songs, punjabi heartbreak, desi emotional, sindhi mellow songs",
            "angry": "Raftaar songs, Sidhu Moose Wala songs, punjabi gym songs, desi pump up, urdu motivational rap, sindhi energetic songs",
            "neutral": "Atif Aslam songs, Pakistani drama ost, urdu chill songs, punjabi lo-fi, sindhi calm music, desi slow romantic tracks"
        }.get(mood, "top pakistani, indian hits") # Default query

        try:
            results = self.sp.search(q=query, type='track', limit=5)
            if results and results['tracks']['items']:
                for track in results['tracks']['items']:
                    track_name = track['name']
                    artist_name = track['artists'][0]['name']
                    track_url = track['external_urls']['spotify']
                    track_info = {"name": track_name, "artist": artist_name, "url": track_url}
                    # IMPORTANT: This ensures the Add to Favorites button is displayed
                    self.create_song_card(self.playlist_container, track_info, enable_remove=False)
            else:
                tk.Label(self.playlist_container, text=f"No Spotify tracks found for {mood} mood.",
                         font=("Arial", 12), bg="#3b0a57", fg="white").pack(pady=10)
        except spotipy.exceptions.SpotifyException as e:
            messagebox.showerror("Spotify Error", f"Could not fetch playlist: {e}")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Network Error", "Could not connect to Spotify. Check your internet connection.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while fetching playlist: {e}")

        self.playlist_container.update_idletasks()
        self.playlist_canvas.config(scrollregion=self.playlist_canvas.bbox("all"))

    def create_song_card(self, parent, track_info, enable_remove=False):
        """
        Creates a song card widget with play and (add/remove) favorite buttons.
        'parent' is the frame where the card will be placed.
        'track_info' is a dictionary with 'name', 'artist', 'url'.
        'enable_remove' (boolean) determines if a 'Remove' button or 'Add to Favorites' button is shown.
        """
        card_frame = tk.Frame(parent, bg="#4a148c", bd=2, relief="groove", padx=10, pady=10)
        card_frame.pack(fill="x", pady=5) # Fill horizontally, small vertical padding

        # Play Button
        play_button = ctk.CTkButton(card_frame, text="Play", width=60, fg_color="green", hover_color="#00b300",
                                     command=lambda url=track_info['url']: self.play_song(url))
        play_button.pack(side="left", padx=(0, 10))

        # Song Info Label
        song_info_label = tk.Label(card_frame, text=f"{track_info['name']} - {track_info['artist']}",
                                     font=("Arial", 12), bg="#4a148c", fg="white", anchor="w")
        song_info_label.pack(side="left", fill="x", expand=True) # Allow text to expand

        if enable_remove:
            # Remove from Favorites Button (only shown in the "View Favorites" playlist)
            remove_fav_button = ctk.CTkButton(card_frame, text="Remove", width=70, fg_color="#ff4d4d", hover_color="#ff6666",
                                             command=lambda info=track_info, frame=card_frame: self.remove_from_favorites(info, frame))
            remove_fav_button.pack(side="right", padx=(10, 0))
        else:
            # Add to Favorites Button (shown on mood-based, search, and weather suggestion playlists)
            fav_button = ctk.CTkButton(card_frame, text="❤️", width=40, fg_color="#ff69b4", hover_color="#ff80c0",
                                        command=lambda info=track_info: self.add_to_favorites(info))
            fav_button.pack(side="right", padx=(10, 0)) # Pack to the right

if __name__ == "__main__":
    root = tk.Tk()
    app = MoodSyncApp(root)
    root.mainloop()

