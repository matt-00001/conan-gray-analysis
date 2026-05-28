import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "pylast"])
import pylast
import glob
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import date
import os

from dotenv import load_dotenv
load_dotenv()
API_KEY = os.environ["LASTFM_KEY"]
API_SECRET = os.environ["LASTFM_SECRET"]
network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)

artist = network.get_artist("Conan Gray")
top_albums = artist.get_top_albums(limit=10)

full_data = []
print("Downloading discography...")

for album_item in top_albums:
    album = album_item.item
    album_name = album.get_name()
    try:
        tracks = album.get_tracks()
        for track in tracks:
            full_data.append({
                'song': track.get_name(),
                'album': album_name,
                'listeners': track.get_listener_count()
            })
    except:
        print(f"Skipping album {album_name} due to an error.")
        continue

df_discography = pd.DataFrame(full_data)
print(f"Done! We have data for {len(df_discography)} songs.")

official_albums = ["Kid Krow", "Superache", "Found Heaven", "Wishbone", "Wishbone Deluxe"]
album_stats = []
print("Fetching official album data...")

for album_name in official_albums:
    album = network.get_album("Conan Gray", album_name)
    try:
        listeners = album.get_listener_count()
        if listeners:
            album_stats.append({
                'album': album_name,
                'listeners': int(listeners),
                'playcount': int(album.get_playcount())
            })
        else:
            print(f"Note: {album_name} has no data on Last.fm yet.")
    except:
        print(f"Could not find data for: {album_name}")
        continue

df_albums = pd.DataFrame(album_stats).sort_values(by='listeners', ascending=False)
print(df_albums)

plt.figure(figsize=(12, 8))
sns.set_style("whitegrid")
plot = sns.barplot(data=df_albums, x='listeners', y='album', palette='mako')
plt.title('Total Listeners per Album: Conan Gray', fontsize=15)
plt.xlabel('Total Unique Listeners', fontsize=12)
plt.ylabel('Album Title', fontsize=12)
for i, v in enumerate(df_albums['listeners']):
    plot.text(v + 3, i, f' {v:,}', color='black', va='center')
plt.tight_layout()
plt.show()

deluxe_tracks = {
    "Original": [
        "Actor", "This Song", "Vodka Cranberry", "Romeo", "My World",
        "Class Clown", "Nauseous", "Caramel", "Connell", "Sunset Tower",
        "Eleven Eleven", "Care"
    ],
    "New": ["Do I Dare", "House That Always Rains", "Door", "Moths", "The Best"]
}

data = []
print("Analyzing Wishbone Deluxe tracks...")

for category, tracks in deluxe_tracks.items():
    for track_name in tracks:
        try:
            track = network.get_track("Conan Gray", track_name)
            listeners = int(track.get_listener_count())
            playcount = int(track.get_playcount())
            intensity = playcount / listeners if listeners > 0 else 0
            data.append({
                'Track': track_name,
                'Listeners': listeners,
                'Playcount': playcount,
                'Intensity': intensity,
                'Type': category
            })
        except:
            print(f"Skipping {track_name} (data not found)")
            continue

df_wishbone = pd.DataFrame(data).sort_values(by='Listeners', ascending=False)
print(df_wishbone[['Track', 'Listeners', 'Type']])

plt.figure(figsize=(12, 7))
sns.set_style("dark")
plot = sns.barplot(data=df_wishbone, x='Listeners', y='Track', hue='Type', dodge=False, palette='magma')
plt.title('Wishbone Deluxe: Track Popularity (April 2026)', fontsize=15, pad=20)
plt.xlabel('Total Listeners on Last.fm')
plt.ylabel('')
plt.legend(title="Track Status")
for i, v in enumerate(df_wishbone['Listeners']):
    plot.text(v + 50, i, f' {v:,}', va='center', fontsize=10)
plt.tight_layout()
plt.show()

# --- Gráfico tracks nuevos: volumen vs intensidad ---
df_new = df_wishbone[df_wishbone['Type'] == 'New'].reset_index(drop=True)

fig, ax1 = plt.subplots(figsize=(14, 7))
sns.set_style("dark")
sns.barplot(data=df_new, x='Track', y='Listeners', color='blue', alpha=0.6, ax=ax1)
ax1.set_ylabel('Total Listeners', fontsize=12)
ax1.tick_params(axis='x', rotation=45)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x/1000)}k' if x >= 1000 else str(int(x))))

ax2 = ax1.twinx()
ax2.plot(df_new['Track'].tolist(), df_new['Intensity'].tolist(), color='black', marker='o', linewidth=2, label='Intensity')
ax2.set_ylabel('Intensity (plays/listener)', fontsize=12, color='black')
ax2.tick_params(axis='y', labelcolor='black')
plt.title('Wishbone Deluxe: New Tracks — Volume vs Intensity', fontsize=15)
fig.tight_layout()
plt.show()

today = date.today()
filename = f"wishbone_snapshot_{today}.csv"
df_wishbone.to_csv(filename, index=False)
print(f"Snapshot saved as: {filename}")

dfs = []
for f in sorted(glob.glob("wishbone_snapshot_*.csv")):
    df = pd.read_csv(f)
    df['date'] = f.replace("wishbone_snapshot_", "").replace(".csv", "")
    dfs.append(df)

if len(dfs) > 1:
    df_history = pd.concat(dfs)
    df_history['date'] = pd.to_datetime(df_history['date'])

    plt.figure(figsize=(14, 7))
    sns.set_style("darkgrid")

    for track in df_history['Track'].unique():
        df_track = df_history[df_history['Track'] == track]
        plt.plot(df_track['date'], df_track['Listeners'], marker='o', label=track)

    plt.title('Wishbone Deluxe: Listener Growth Over Time', fontsize=15)
    plt.xlabel('Date')
    plt.ylabel('Listeners')
    plt.xticks(rotation=45)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    plt.tight_layout()
    plt.show()
else:
    print("Need at least 2 snapshots to show growth chart.")

dfs = []
for f in sorted(glob.glob("wishbone_snapshot_*.csv")):
    df = pd.read_csv(f)
    df['date'] = f.replace("wishbone_snapshot_", "").replace(".csv", "")
    dfs.append(df)

if len(dfs) > 1:
    df_history = pd.concat(dfs)
    df_pivot = df_history.pivot_table(index='Track', columns='date', values='Listeners')
    dates = sorted(df_pivot.columns)
    df_pivot['crecimiento'] = df_pivot[dates[-1]] - df_pivot[dates[0]]
    df_pivot['crecimiento'].sort_values().plot(kind='barh', color='steelblue', figsize=(10, 6))
    plt.title(f'{dates[0]} → {dates[-1]}')
    plt.tight_layout()
    plt.show()
else:
    print("Need at least 2 snapshots to show growth chart.")