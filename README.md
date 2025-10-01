Clover Pit Save Editor
A comprehensive save file editor for the game Clover Pit

Features

User-friendly GUI - No command line knowledge required
Complete save editing including:

Currency (coins, deposited coins, clover tickets)
Spins and rounds
Symbol values and modifiers
Pattern availability and values
Powerup management (equipped, store, drawer, skeleton slots)
Luck modifiers
Run modifiers
666/999 event settings


Automatic encryption/decryption 
Backup system - Create and restore backups before editing
JSON editor - Advanced users can edit raw JSON data

Requirements

Python 3.7+
tkinter (usually included with Python)

Editing Your Save

Create a Backup First!

Click "Browse" to select your save file
Click "Create Backup" - this creates a .backup file
You can restore this backup anytime with "Restore Backup"


Load the Save File

Click "Load & Decrypt" to load and decrypt the save file
The editor will populate all tabs with your current save data


Edit Values

Quick Edit Tab: Simple fields for basic editing
Game Values Tab: Comprehensive editing of all game systems

Currency & Money
Spins & Rounds
Symbols (spawn chances, golden %, instant reward %, etc.)
Patterns (enable/disable, extra values)
Powerups & Equipment (30 equipped slots, store, drawers, skeleton)
Luck Modifiers
Run Modifiers
666 Event settings


JSON Editor Tab: Raw JSON editing for advanced users


Apply and Save

Click "Apply Game Values Changes" to apply your edits
Click "Save & Encrypt" to save and re-encrypt the file
The game will now load your modified save

Special Features
Unlock All Drawers

Instantly unlock all 4 drawer slots

Unlock All Powerups

Adds all powerups to your unlocked collection

Transform Phone to Holy (999)

Converts the possessed phone (666) to holy mode (999)
Normally requires all 5 skeleton pieces equipped

Max Luck Values

Sets all luck modifiers to 10.0 (maximum)

Add All Run Modifiers

Creates entries for all available run modifiers

Clear Functions

Quickly clear equipped powerups, store, or drawers

Byte Arrays
Some values (coins, multipliers) are stored as byte arrays representing large integers. The editor automatically converts between human-readable numbers and byte arrays.

Disclaimer
This is an unofficial tool created by fans for educational purposes. Use at your own risk. The author is not responsible for corrupted saves or game issues resulting from save editing.

Always backup your saves before editing!

Created by Crux4000

If you find this tool useful, consider starring the repository!

