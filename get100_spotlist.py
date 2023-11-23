#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Get playlist as user input
playlist_id = input()

auth_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager)

def get_all_playlist_tracks(playlist_id):
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    
    while results:
        tracks.extend(results['items'])
        results = sp.next(results)  # Get the next page of tracks

    return tracks

# Retrieve all tracks from the specified playlist
all_tracks = get_all_playlist_tracks(playlist_id)

# Iterate and print track details
for i, track_item in enumerate(all_tracks):
    track = track_item['track']
    print(f"{i + 1}: {track['name']} by {', '.join([artist['name'] for artist in track['artists']])}")
