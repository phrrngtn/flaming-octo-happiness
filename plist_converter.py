
# from https://www.google.com/search?q=xml+schema+for+itunes+playlists&sca_esv=4dee6c104a808b1e&rlz=1C1GCEA_enUS1165US1167&udm=50&fbs=AIIjpHxU7SXXniUZfeShr2fp4giZ1Y6MJ25_tmWITc7uy4KIeoJTKjrFjVxydQWqI2NcOha3O1YqG67F0QIhAOFN_ob1yXos5K_Qo9Tq-0cVPzex8akBC0YDCZ6Kdb3tXvKc6RFFaJZ5G23Reu3aSyxvn2qD41n-47oj-b-f0NcRPP5lz0IcnVzj2DIj_DMpoDz5XbfZAMcEl5-58jjbkgCC_7e4L5AEDQ&aep=1&ntc=1&sa=X&ved=2ahUKEwjm-IK_sraPAxWpGlkFHa9eDDUQ2J8OegQIEhAD&biw=1427&bih=759&dpr=2&mstk=AUtExfBfc1_mifSQYLnBiOj-2STo7vBLjnXfQUMfGiGRbvXfxl5HcJJK1B3Lg8T5vhEfYhQCOELwPAX4cq7dJINipbVdzrbK0VDUXmxTwUJgKPAWFlOZ-OtFamMTT4Vqgi2kjv3lR6mUmr7N8AFslSp2pGidhmL1beilQHvQHhl5yRl5j7PcpPLBnoODtdr-r0N18nPHkLZkQXc1-6u7vp8ElGVysK6yB1jRYUUoVnFJr6dKc2iQlUc9Oar3og&csuir=1

import plistlib
import csv
import sys

def convert_itunes_xml_to_csv(xml_path, csv_path):
    """
    Parses an iTunes library XML file and exports playlists to a CSV file.
    Each row in the CSV represents a song and its associated playlist.
    """
    try:
        with open(xml_path, 'rb') as f:
            library = plistlib.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{xml_path}' was not found. Please ensure your XML file is in the correct directory.")
        return
    except plistlib.InvalidFileException:
        print(f"Error: The file '{xml_path}' is not a valid plist XML.")
        return

    # Extract tracks and playlists
    tracks = library['Tracks']
    playlists = library['Playlists']

    # Set the desired CSV headers.
    # Add or remove headers as needed based on the available track metadata.
    fieldnames = ['Playlist', 'Track ID', 'Artist', 'Album', 'Name', 'Genre', 'Location']

    all_playlist_tracks = []
    for playlist in playlists:
        playlist_name = playlist.get('Name')
        if playlist_name and 'Playlist Items' in playlist:
            for playlist_item in playlist['Playlist Items']:
                track_id = str(playlist_item['Track ID'])
                if track_id in tracks:
                    track_data = tracks[track_id]
                    row_data = {
                        'Playlist': playlist_name,
                        'Track ID': track_id,
                        'Artist': track_data.get('Artist'),
                        'Album': track_data.get('Album'),
                        'Name': track_data.get('Name'),
                        'Genre': track_data.get('Genre'),
                        'Location': track_data.get('Location')
                    }
                    all_playlist_tracks.append(row_data)
    
    # Write the combined data to a CSV file
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_playlist_tracks)
        print(f"Successfully exported {len(all_playlist_tracks)} tracks to '{csv_path}'.")
    except IOError as e:
        print(f"Error writing to CSV file '{csv_path}': {e}")

if __name__ == "__main__":
    xml_filename = "iTunes Music Library.xml"
    csv_filename = "playlists.csv"
    convert_itunes_xml_to_csv(xml_filename, csv_filename)
