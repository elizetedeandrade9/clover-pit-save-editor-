#!/usr/bin/env python3
# Clover Pit Save Editor
# Created by: Crux4000
# GitHub: github.com/Crux4000

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import shutil
from pathlib import Path
import hashlib

# Author verification
_AUTHOR = "Crux4000"
_AUTHOR_HASH = hashlib.sha256(_AUTHOR.encode()).hexdigest()

class SaveFileEditor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Clover Pit Save Editor - by {_AUTHOR}")
        self.root.geometry("1200x800")
        
        # Watermark canvas
        self._init_watermark()
        
        # XOR key from your scripts
        self.key = [0x48, 0x06, 0x5c, 0x11, 0x06, 0x43, 0x01, 0x60, 
                   0x18, 0x55, 0x42, 0x18, 0x19, 0x1a, 0x00, 0x4a, 
                   0x5a, 0x1a, 0x00, 0x51, 0x56, 0x46, 0x4e, 0x47, 
                   0x0c, 0x1b, 0x01]
        
        self.current_file = None
        self.save_data = None
        self.backup_created = False
        
        self.setup_ui()
        
    def _init_watermark(self):
        """Initialize background watermark"""
        # Create watermark label
        self.watermark = tk.Label(
            self.root,
            text=f"Created by {_AUTHOR}",
            font=("Arial", 60, "bold"),
            fg="#f0f0f0",
            bg="#e0e0e0"
        )
        self.watermark.place(relx=0.5, rely=0.5, anchor="center")
        self.watermark.lower()
        
    def _verify_attribution(self):
        """Verify author attribution - called periodically"""
        title = self.root.title()
        if _AUTHOR not in title or hashlib.sha256(_AUTHOR.encode()).hexdigest() != _AUTHOR_HASH:
            return False
        return True
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # File selection
        ttk.Label(main_frame, text="Save File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.file_var, state="readonly", width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="Load & Decrypt", command=self.load_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save & Encrypt", command=self.save_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Create Backup", command=self.create_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Restore Backup", command=self.restore_backup).pack(side=tk.LEFT, padx=5)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Quick Edit tab
        self.quick_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.quick_frame, text="Quick Edit")
        self.setup_quick_edit()
        
        # Game Values tab
        self.game_values_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.game_values_frame, text="Game Values")
        self.setup_game_values()
        
        # JSON Editor tab
        self.json_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.json_frame, text="JSON Editor")
        self.setup_json_editor()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set(f"Ready - Select a save file to begin | Created by {_AUTHOR}")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
    def setup_quick_edit(self):
        # Scrollable frame for quick edit fields
        canvas = tk.Canvas(self.quick_frame)
        scrollbar = ttk.Scrollbar(self.quick_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        self.bind_mousewheel(canvas)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.quick_edit_vars = {}
        
    def bind_mousewheel(self, widget):
        """Bind mouse wheel to widget for scrolling"""
        def _on_mousewheel(event):
            widget.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_enter(event):
            widget.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _on_leave(event):
            widget.unbind_all("<MouseWheel>")
        
        widget.bind('<Enter>', _on_enter)
        widget.bind('<Leave>', _on_leave)
        
    def setup_game_values(self):
        # Create main scrollable area
        main_canvas = tk.Canvas(self.game_values_frame)
        v_scrollbar = ttk.Scrollbar(self.game_values_frame, orient="vertical", command=main_canvas.yview)
        h_scrollbar = ttk.Scrollbar(self.game_values_frame, orient="horizontal", command=main_canvas.xview)
        scrollable_main = ttk.Frame(main_canvas)
        
        scrollable_main.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_main, anchor="nw")
        main_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Enable mouse wheel scrolling
        self.bind_mousewheel(main_canvas)
        
        main_canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.game_values_frame.grid_rowconfigure(0, weight=1)
        self.game_values_frame.grid_columnconfigure(0, weight=1)
        
        # Create sections
        row = 0
        
        # Currency section
        currency_frame = ttk.LabelFrame(scrollable_main, text="Currency & Money", padding="10")
        currency_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        
        self.coins_var = tk.StringVar()
        self.deposited_coins_var = tk.StringVar()
        self.clover_tickets_var = tk.StringVar()
        self.interest_rate_var = tk.StringVar()
        
        ttk.Label(currency_frame, text="Coins:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(currency_frame, textvariable=self.coins_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(currency_frame, text="Deposited Coins:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Entry(currency_frame, textvariable=self.deposited_coins_var, width=15).grid(row=0, column=3, padx=5)
        
        ttk.Label(currency_frame, text="Clover Tickets:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Entry(currency_frame, textvariable=self.clover_tickets_var, width=15).grid(row=1, column=1, padx=5)
        
        ttk.Label(currency_frame, text="Interest Rate %:").grid(row=1, column=2, sticky="w", padx=5)
        ttk.Entry(currency_frame, textvariable=self.interest_rate_var, width=15).grid(row=1, column=3, padx=5)
        
        # Spins section
        spins_frame = ttk.LabelFrame(scrollable_main, text="Spins & Rounds", padding="10")
        spins_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        
        self.spins_left_var = tk.StringVar()
        self.max_spins_var = tk.StringVar()
        self.extra_spins_var = tk.StringVar()
        self.round_deadline_var = tk.StringVar()
        
        ttk.Label(spins_frame, text="Spins Left:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(spins_frame, textvariable=self.spins_left_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(spins_frame, text="Max Spins:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Entry(spins_frame, textvariable=self.max_spins_var, width=15).grid(row=0, column=3, padx=5)
        
        ttk.Label(spins_frame, text="Extra Spins:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Entry(spins_frame, textvariable=self.extra_spins_var, width=15).grid(row=1, column=1, padx=5)
        
        ttk.Label(spins_frame, text="Round Deadline:").grid(row=1, column=2, sticky="w", padx=5)
        ttk.Entry(spins_frame, textvariable=self.round_deadline_var, width=15).grid(row=1, column=3, padx=5)
        
        # Symbols section
        symbols_frame = ttk.LabelFrame(scrollable_main, text="Symbols", padding="10")
        symbols_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Symbols multiplier
        self.all_symbols_mult_var = tk.StringVar()
        ttk.Label(symbols_frame, text="All Symbols Multiplier:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(symbols_frame, textvariable=self.all_symbols_mult_var, width=15).grid(row=0, column=1, padx=5)
        
        # Individual symbol controls
        symbol_headers = ["Symbol", "Extra Value", "Spawn Chance", "Golden %", "Instant Reward %", "Clover Ticket %"]
        for i, header in enumerate(symbol_headers):
            ttk.Label(symbols_frame, text=header).grid(row=1, column=i, padx=5, pady=5)
        
        self.symbol_vars = {}
        symbols = ["lemon", "cherry", "clover", "bell", "diamond", "coins", "seven"]
        
        for idx, symbol in enumerate(symbols):
            row_idx = idx + 2
            ttk.Label(symbols_frame, text=symbol.title()).grid(row=row_idx, column=0, sticky="w", padx=5)
            
            self.symbol_vars[symbol] = {
                'extraValue': tk.StringVar(),
                'spawnChance': tk.StringVar(),
                'golden': tk.StringVar(),
                'instantReward': tk.StringVar(),
                'cloverTicket': tk.StringVar()
            }
            
            ttk.Entry(symbols_frame, textvariable=self.symbol_vars[symbol]['extraValue'], width=10).grid(row=row_idx, column=1, padx=2)
            ttk.Entry(symbols_frame, textvariable=self.symbol_vars[symbol]['spawnChance'], width=10).grid(row=row_idx, column=2, padx=2)
            ttk.Entry(symbols_frame, textvariable=self.symbol_vars[symbol]['golden'], width=10).grid(row=row_idx, column=3, padx=2)
            ttk.Entry(symbols_frame, textvariable=self.symbol_vars[symbol]['instantReward'], width=10).grid(row=row_idx, column=4, padx=2)
            ttk.Entry(symbols_frame, textvariable=self.symbol_vars[symbol]['cloverTicket'], width=10).grid(row=row_idx, column=5, padx=2)
        
        row += 1
        
        # Patterns section
        patterns_frame = ttk.LabelFrame(scrollable_main, text="Patterns", padding="10")
        patterns_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Pattern multiplier
        self.all_patterns_mult_var = tk.StringVar()
        ttk.Label(patterns_frame, text="All Patterns Multiplier:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(patterns_frame, textvariable=self.all_patterns_mult_var, width=15).grid(row=0, column=1, padx=5)
        
        # Pattern availability toggles
        ttk.Label(patterns_frame, text="Available Patterns (check to enable):").grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=(10,5))
        
        pattern_toggle_frame = ttk.Frame(patterns_frame)
        pattern_toggle_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=5)
        
        all_patterns = ["jackpot", "horizontal2", "horizontal3", "horizontal4", "horizontal5", 
                       "vertical2", "vertical3", "diagonal2", "diagonal3", "pyramid", 
                       "pyramidInverted", "triangle", "triangleInverted", "snakeUpDown", 
                       "snakeDownUp", "eye"]
        
        self.pattern_enabled_vars = {}
        for idx, pattern in enumerate(all_patterns):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(pattern_toggle_frame, text=pattern, variable=var)
            cb.grid(row=idx // 3, column=idx % 3, sticky="w", padx=10, pady=2)
            self.pattern_enabled_vars[pattern] = var
        
        # Individual pattern value controls
        ttk.Label(patterns_frame, text="Pattern Values:").grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=(10,5))
        ttk.Label(patterns_frame, text="Pattern").grid(row=4, column=0, padx=5, pady=5)
        ttk.Label(patterns_frame, text="Extra Value").grid(row=4, column=1, padx=5, pady=5)
        
        self.pattern_vars = {}
        
        for idx, pattern in enumerate(all_patterns):
            row_idx = idx + 5
            ttk.Label(patterns_frame, text=pattern.replace("_", " ").title()).grid(row=row_idx, column=0, sticky="w", padx=5)
            
            self.pattern_vars[pattern] = tk.StringVar()
            ttk.Entry(patterns_frame, textvariable=self.pattern_vars[pattern], width=15).grid(row=row_idx, column=1, padx=5)
        
        row += 1
        
        # Powerups section
        powerups_frame = ttk.LabelFrame(scrollable_main, text="Powerups & Equipment", padding="10")
        powerups_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Equipped powerups - FIXED WIDTH
        ttk.Label(powerups_frame, text="Equipped Powerups (30 slots):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        equipped_frame = ttk.Frame(powerups_frame)
        equipped_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5)
        
        self.equipped_vars = []
        self.equipped_combos = []
        for i in range(30):
            if i % 6 == 0:  # 6 items per row for better visibility
                current_row = i // 6
            var = tk.StringVar()
            combo = ttk.Combobox(equipped_frame, textvariable=var, width=28, state="normal")
            combo.grid(row=current_row, column=i % 6, padx=2, pady=2)
            self.equipped_vars.append(var)
            self.equipped_combos.append(combo)
        
        # Store powerups - FIXED WIDTH
        ttk.Label(powerups_frame, text="Store Powerups (4 slots):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        store_frame = ttk.Frame(powerups_frame)
        store_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5)
        
        self.store_vars = []
        self.store_combos = []
        for i in range(4):
            var = tk.StringVar()
            combo = ttk.Combobox(store_frame, textvariable=var, width=35, state="normal")
            combo.grid(row=0, column=i, padx=5, pady=2)
            self.store_vars.append(var)
            self.store_combos.append(combo)
        
        # Drawer powerups - FIXED WIDTH
        ttk.Label(powerups_frame, text="Drawer Powerups (4 slots):").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        drawer_frame = ttk.Frame(powerups_frame)
        drawer_frame.grid(row=6, column=0, columnspan=3, sticky="ew", padx=5)
        
        self.drawer_vars = []
        self.drawer_combos = []
        for i in range(4):
            var = tk.StringVar()
            combo = ttk.Combobox(drawer_frame, textvariable=var, width=35, state="normal")
            combo.grid(row=0, column=i, padx=5, pady=2)
            self.drawer_vars.append(var)
            self.drawer_combos.append(combo)
        
        # Skeleton powerups - FIXED WIDTH
        ttk.Label(powerups_frame, text="Skeleton Powerups (5 slots):").grid(row=7, column=0, sticky="w", padx=5, pady=5)
        skeleton_frame = ttk.Frame(powerups_frame)
        skeleton_frame.grid(row=8, column=0, columnspan=3, sticky="ew", padx=5)
        
        self.skeleton_vars = []
        self.skeleton_combos = []
        for i in range(5):
            var = tk.StringVar()
            combo = ttk.Combobox(skeleton_frame, textvariable=var, width=28, state="normal")
            combo.grid(row=0, column=i, padx=5, pady=2)
            self.skeleton_vars.append(var)
            self.skeleton_combos.append(combo)
        
        # Powerup management buttons
        buttons_frame = ttk.Frame(powerups_frame)
        buttons_frame.grid(row=9, column=0, columnspan=3, pady=5)
        
        ttk.Button(buttons_frame, text="Clear All Equipped", command=self.clear_equipped).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Clear Store", command=self.clear_store).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Clear Drawers", command=self.clear_drawers).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Max Luck Values", command=self.max_luck).pack(side=tk.LEFT, padx=5)
        
        # Max equippable powerups and red button multiplier
        equipment_settings_frame = ttk.Frame(powerups_frame)
        equipment_settings_frame.grid(row=10, column=0, columnspan=3, pady=5)
        
        ttk.Label(equipment_settings_frame, text="Max Equippable Powerups:").pack(side=tk.LEFT, padx=5)
        self.max_equippable_var = tk.StringVar()
        max_equippable_combo = ttk.Combobox(equipment_settings_frame, textvariable=self.max_equippable_var, 
                                           values=list(range(1, 31)), width=5, state="readonly")
        max_equippable_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(equipment_settings_frame, text="Red Button Multiplier:").pack(side=tk.LEFT, padx=10)
        self.red_button_mult_var = tk.StringVar()
        ttk.Entry(equipment_settings_frame, textvariable=self.red_button_mult_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Unlock buttons section
        row += 1
        unlock_frame = ttk.LabelFrame(scrollable_main, text="Unlock Features", padding="10")
        unlock_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        unlock_buttons_frame = ttk.Frame(unlock_frame)
        unlock_buttons_frame.grid(row=0, column=0, columnspan=2, pady=5)
        
        ttk.Button(unlock_buttons_frame, text="Unlock All Drawers", command=self.unlock_all_drawers).pack(side=tk.LEFT, padx=5)
        ttk.Button(unlock_buttons_frame, text="Unlock All Powerups", command=self.unlock_all_powerups).pack(side=tk.LEFT, padx=5)
        ttk.Button(unlock_buttons_frame, text="Transform Phone to Holy (999)", command=self.transform_phone_holy).pack(side=tk.LEFT, padx=5)
        
        # Luck modifiers
        row += 1
        luck_frame = ttk.LabelFrame(scrollable_main, text="Luck Modifiers", padding="10")
        luck_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.powerup_luck_var = tk.StringVar()
        self.activation_luck_var = tk.StringVar()
        self.store_luck_var = tk.StringVar()
        
        ttk.Label(luck_frame, text="Powerup Luck:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(luck_frame, textvariable=self.powerup_luck_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(luck_frame, text="Activation Luck:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Entry(luck_frame, textvariable=self.activation_luck_var, width=15).grid(row=0, column=3, padx=5)
        
        ttk.Label(luck_frame, text="Store Luck:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Entry(luck_frame, textvariable=self.store_luck_var, width=15).grid(row=1, column=1, padx=5)
        
        # 666 Section
        row += 1
        evil_frame = ttk.LabelFrame(scrollable_main, text="666 Events", padding="10")
        evil_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.evil_chance_var = tk.StringVar()
        self.evil_chance_max_var = tk.StringVar()
        self.evil_suppressed_var = tk.StringVar()
        
        ttk.Label(evil_frame, text="666 Chance:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(evil_frame, textvariable=self.evil_chance_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(evil_frame, text="666 Max Chance:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Entry(evil_frame, textvariable=self.evil_chance_max_var, width=15).grid(row=0, column=3, padx=5)
        
        ttk.Label(evil_frame, text="Suppressed Spins:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Entry(evil_frame, textvariable=self.evil_suppressed_var, width=15).grid(row=1, column=1, padx=5)
        
        # Run Modifiers section - FIXED HEIGHT AND SCROLLING
        row += 1
        modifiers_frame = ttk.LabelFrame(scrollable_main, text="Run Modifiers", padding="10")
        modifiers_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Button to add all modifiers
        mod_button_frame = ttk.Frame(modifiers_frame)
        mod_button_frame.grid(row=0, column=0, columnspan=6, pady=5, sticky="ew")
        
        ttk.Button(mod_button_frame, text="Add All Run Modifiers", command=self.add_all_run_modifiers).pack(side=tk.LEFT, padx=5)
        ttk.Label(mod_button_frame, text="(Creates entries for all available run modifiers)").pack(side=tk.LEFT, padx=10)
        
        # Fixed header frame (non-scrolling)
        header_frame = ttk.Frame(modifiers_frame)
        header_frame.grid(row=1, column=0, columnspan=6, sticky="ew", padx=5)
        
        # Headers for modifier controls - FIXED AT TOP
        ttk.Label(header_frame, text="Modifier Name", font=("TkDefaultFont", 8, "bold"), width=40, anchor="w").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(header_frame, text="Owned", font=("TkDefaultFont", 8, "bold"), width=10).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(header_frame, text="Unlocked", font=("TkDefaultFont", 8, "bold"), width=10).grid(row=0, column=2, padx=5, pady=2)
        ttk.Label(header_frame, text="Played", font=("TkDefaultFont", 8, "bold"), width=10).grid(row=0, column=3, padx=5, pady=2)
        ttk.Label(header_frame, text="Won", font=("TkDefaultFont", 8, "bold"), width=10).grid(row=0, column=4, padx=5, pady=2)
        ttk.Label(header_frame, text="Foil Level", font=("TkDefaultFont", 8, "bold"), width=10).grid(row=0, column=5, padx=5, pady=2)
        
        # Scrollable frame for modifiers - FIXED HEIGHT WITH HORIZONTAL SCROLL
        mod_canvas = tk.Canvas(modifiers_frame, height=300, width=900)
        mod_v_scrollbar = ttk.Scrollbar(modifiers_frame, orient="vertical", command=mod_canvas.yview)
        mod_h_scrollbar = ttk.Scrollbar(modifiers_frame, orient="horizontal", command=mod_canvas.xview)
        self.modifiers_scroll_frame = ttk.Frame(mod_canvas)
        
        self.modifiers_scroll_frame.bind(
            "<Configure>",
            lambda e: mod_canvas.configure(scrollregion=mod_canvas.bbox("all"))
        )
        
        mod_canvas.create_window((0, 0), window=self.modifiers_scroll_frame, anchor="nw")
        mod_canvas.configure(yscrollcommand=mod_v_scrollbar.set, xscrollcommand=mod_h_scrollbar.set)
        
        # Enable mouse wheel scrolling for modifiers
        self.bind_mousewheel(mod_canvas)
        
        mod_canvas.grid(row=2, column=0, columnspan=6, sticky="nsew", padx=5)
        mod_v_scrollbar.grid(row=2, column=6, sticky="ns")
        mod_h_scrollbar.grid(row=3, column=0, columnspan=6, sticky="ew", padx=5)
        
        self.modifier_vars = {}
        
        # Button to apply game values changes
        apply_button = ttk.Button(scrollable_main, text="Apply Game Values Changes", command=self.apply_game_values)
        apply_button.grid(row=row+1, column=0, columnspan=2, pady=10)
        
    def setup_json_editor(self):
        # JSON text editor
        self.json_text = scrolledtext.ScrolledText(self.json_frame, wrap=tk.WORD, width=80, height=25)
        self.json_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # JSON control buttons
        json_button_frame = ttk.Frame(self.json_frame)
        json_button_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(json_button_frame, text="Format JSON", command=self.format_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(json_button_frame, text="Validate JSON", command=self.validate_json).pack(side=tk.LEFT, padx=5)
        
    def xor_data(self, data):
        """XOR encrypt/decrypt data with the key"""
        result = bytearray()
        for i, byte in enumerate(data):
            key_byte = self.key[i % len(self.key)]
            result.append(byte ^ key_byte)
        return bytes(result)
        
    def browse_file(self):
        """Browse for save file"""
        filename = filedialog.askopenfilename(
            title="Select Save File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.file_var.set(filename)
            self.current_file = filename
            
    def create_backup(self):
        """Create a backup of the current save file"""
        if not self.current_file or not os.path.exists(self.current_file):
            messagebox.showerror("Error", "No save file selected or file doesn't exist")
            return
            
        backup_path = self.current_file + ".backup"
        try:
            shutil.copy2(self.current_file, backup_path)
            self.backup_created = True
            self.status_var.set(f"Backup created: {backup_path}")
            messagebox.showinfo("Success", f"Backup created successfully:\n{backup_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup:\n{str(e)}")
            
    def restore_backup(self):
        """Restore from backup"""
        if not self.current_file:
            messagebox.showerror("Error", "No save file selected")
            return
            
        backup_path = self.current_file + ".backup"
        if not os.path.exists(backup_path):
            messagebox.showerror("Error", "No backup file found")
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to restore from backup? This will overwrite the current save file."):
            try:
                shutil.copy2(backup_path, self.current_file)
                self.status_var.set("Backup restored successfully")
                messagebox.showinfo("Success", "Backup restored successfully")
                # Reload the file
                self.load_file()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore backup:\n{str(e)}")
                
    def load_file(self):
        """Load and decrypt the save file"""
        if not self.current_file or not os.path.exists(self.current_file):
            messagebox.showerror("Error", "Please select a valid save file first")
            return
            
        try:
            # Read encrypted file
            with open(self.current_file, 'rb') as f:
                encrypted_data = f.read()
                
            # Decrypt
            decrypted_data = self.xor_data(encrypted_data)
            
            # Parse JSON
            json_str = decrypted_data.decode('utf-8')
            self.save_data = json.loads(json_str)
            
            # Update UI
            self.populate_quick_edit()
            self.populate_game_values()
            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(1.0, json.dumps(self.save_data, indent=2))
            
            self.status_var.set(f"Loaded: {os.path.basename(self.current_file)}")
            
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Failed to parse JSON:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
            
    def populate_quick_edit(self):
        """Populate quick edit fields with common game values"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.quick_edit_vars.clear()
        
        if not self.save_data:
            return
            
        row = 0
        
        # Find common game save fields and create edit widgets
        def add_field(key, value, parent_path=""):
            nonlocal row
            full_path = f"{parent_path}.{key}" if parent_path else key
            
            if isinstance(value, (int, float)):
                ttk.Label(self.scrollable_frame, text=f"{full_path}:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                var = tk.StringVar(value=str(value))
                entry = ttk.Entry(self.scrollable_frame, textvariable=var, width=20)
                entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                self.quick_edit_vars[full_path] = (var, type(value))
                row += 1
                
            elif isinstance(value, str) and len(value) < 100:  # Short strings only
                ttk.Label(self.scrollable_frame, text=f"{full_path}:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                var = tk.StringVar(value=value)
                entry = ttk.Entry(self.scrollable_frame, textvariable=var, width=30)
                entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                self.quick_edit_vars[full_path] = (var, str)
                row += 1
                
            elif isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                check = ttk.Checkbutton(self.scrollable_frame, text=full_path, variable=var)
                check.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
                self.quick_edit_vars[full_path] = (var, bool)
                row += 1
                
            elif isinstance(value, dict) and len(str(value)) < 1000:  # Small dicts only
                for sub_key, sub_value in value.items():
                    add_field(sub_key, sub_value, full_path)
                    
        # Process the save data
        for key, value in self.save_data.items():
            add_field(key, value)
            
    def populate_game_values(self):
        """Populate game values tab with data from save file"""
        if not self.save_data or 'gameplayData' not in self.save_data:
            return
            
        gd = self.save_data['gameplayData']
        
        # Get available powerups list
        self.populate_powerup_dropdowns()
        self.populate_run_modifiers()
        
        # Currency values
        self.coins_var.set(str(self.decode_byte_array(gd.get('coins_ByteArray', [0]))))
        self.deposited_coins_var.set(str(self.decode_byte_array(gd.get('depositedCoins_ByteArray', [0]))))
        self.clover_tickets_var.set(str(gd.get('cloverTickets', 0)))
        self.interest_rate_var.set(str(gd.get('interestRate', 0)))
        
        # Spins values  
        self.spins_left_var.set(str(gd.get('spinsLeft', 0)))
        self.max_spins_var.set(str(gd.get('maxSpins', 0)))
        self.extra_spins_var.set(str(gd.get('extraSpins', 0)))
        self.round_deadline_var.set(str(gd.get('roundOfDeadline', 0)))
        
        # Symbol multiplier
        self.all_symbols_mult_var.set(str(self.decode_byte_array(gd.get('allSymbolsMultiplier_ByteArray', [1]))))
        
        # Individual symbols
        symbols_data = gd.get('symbolsData', [])
        for symbol_data in symbols_data:
            symbol_name = symbol_data.get('symbolKindAsString', '')
            if symbol_name in self.symbol_vars:
                self.symbol_vars[symbol_name]['extraValue'].set(str(self.decode_byte_array(symbol_data.get('extraValue_ByteArray', [0]))))
                self.symbol_vars[symbol_name]['spawnChance'].set(str(symbol_data.get('spawnChance', 0)))
                self.symbol_vars[symbol_name]['golden'].set(str(symbol_data.get('modifierChance01_Golden', 0)))
                self.symbol_vars[symbol_name]['instantReward'].set(str(symbol_data.get('modifierChance01_InstantReward', 0)))
                self.symbol_vars[symbol_name]['cloverTicket'].set(str(symbol_data.get('modifierChance01_CloverTicket', 0)))
        
        # Pattern multiplier
        self.all_patterns_mult_var.set(str(self.decode_byte_array(gd.get('allPatternsMultiplier_ByteArray', [1]))))
        
        # Available patterns (toggles)
        available_patterns = gd.get('patternsAvailable_AsString', [])
        for pattern_name in self.pattern_enabled_vars.keys():
            # Check if this pattern is in the available list
            is_available = pattern_name in available_patterns
            self.pattern_enabled_vars[pattern_name].set(is_available)
        
        # Individual pattern values
        patterns_data = gd.get('patternsData', [])
        for pattern_data in patterns_data:
            pattern_name = pattern_data.get('patternKindAsString', '')
            if pattern_name in self.pattern_vars:
                self.pattern_vars[pattern_name].set(str(pattern_data.get('extraValue', 0)))
        
        # Equipped powerups
        equipped = gd.get('equippedPowerups', [])
        for i in range(min(len(equipped), 30)):
            self.equipped_vars[i].set(equipped[i] if equipped[i] != "undefined" else "")
        for i in range(len(equipped), 30):
            self.equipped_vars[i].set("")
            
        # Store powerups
        store = gd.get('storePowerups', [])
        for i in range(min(len(store), 4)):
            self.store_vars[i].set(store[i] if store[i] != "undefined" else "")
        for i in range(len(store), 4):
            self.store_vars[i].set("")
            
        # Drawer powerups
        drawer = gd.get('drawerPowerups', [])
        for i in range(min(len(drawer), 4)):
            self.drawer_vars[i].set(drawer[i] if drawer[i] != "undefined" else "")
        for i in range(len(drawer), 4):
            self.drawer_vars[i].set("")
            
        # Skeleton powerups
        skeleton = gd.get('equippedPowerups_Skeleton', [])
        for i in range(min(len(skeleton), 5)):
            self.skeleton_vars[i].set(skeleton[i] if skeleton[i] != "undefined" else "")
        for i in range(len(skeleton), 5):
            self.skeleton_vars[i].set("")
        
        # Luck values
        self.powerup_luck_var.set(str(gd.get('powerupLuck', 1.0)))
        self.activation_luck_var.set(str(gd.get('activationLuck', 1.0)))
        self.store_luck_var.set(str(gd.get('storeLuck', 1.0)))
        
        # 666 values
        self.evil_chance_var.set(str(gd.get('_666Chance', 0)))
        self.evil_chance_max_var.set(str(gd.get('_666ChanceMaxAbsolute', 0)))
        self.evil_suppressed_var.set(str(gd.get('_666SuppressedSpinsLeft', 0)))
        
        # Equipment settings
        self.max_equippable_var.set(str(gd.get('maxEquippablePowerups', 8)))
        self.red_button_mult_var.set(str(gd.get('_redButtonActivationsMultiplier', 1)))
    
    def apply_quick_edits(self):
        """Apply quick edit changes to save_data"""
        if not self.save_data:
            return
            
        for path, (var, data_type) in self.quick_edit_vars.items():
            try:
                # Convert the value back to original type
                if data_type == bool:
                    new_value = var.get()
                elif data_type == int:
                    new_value = int(var.get())
                elif data_type == float:
                    new_value = float(var.get())
                else:
                    new_value = var.get()
                    
                # Navigate to the correct location in save_data and update
                keys = path.split('.')
                current = self.save_data
                for key in keys[:-1]:
                    current = current[key]
                current[keys[-1]] = new_value
                
            except (ValueError, KeyError) as e:
                messagebox.showerror("Error", f"Failed to update {path}: {str(e)}")
                return
                
    def apply_game_values(self):
        """Apply changes from game values tab to save data"""
        if not self.save_data or 'gameplayData' not in self.save_data:
            messagebox.showerror("Error", "No game data loaded")
            return
            
        try:
            gd = self.save_data['gameplayData']
            
            # Currency values
            gd['coins_ByteArray'] = self.encode_byte_array(int(self.coins_var.get() or 0))
            gd['depositedCoins_ByteArray'] = self.encode_byte_array(int(self.deposited_coins_var.get() or 0))
            gd['cloverTickets'] = int(self.clover_tickets_var.get() or 0)
            gd['interestRate'] = float(self.interest_rate_var.get() or 0)
            
            # Spins values
            gd['spinsLeft'] = int(self.spins_left_var.get() or 0)
            gd['maxSpins'] = int(self.max_spins_var.get() or 0)
            gd['extraSpins'] = int(self.extra_spins_var.get() or 0)
            gd['roundOfDeadline'] = int(self.round_deadline_var.get() or 0)
            
            # Symbol multiplier
            gd['allSymbolsMultiplier_ByteArray'] = self.encode_byte_array(int(self.all_symbols_mult_var.get() or 1))
            
            # Individual symbols
            for symbol_data in gd.get('symbolsData', []):
                symbol_name = symbol_data.get('symbolKindAsString', '')
                if symbol_name in self.symbol_vars:
                    symbol_data['extraValue_ByteArray'] = self.encode_byte_array(int(self.symbol_vars[symbol_name]['extraValue'].get() or 0))
                    symbol_data['spawnChance'] = float(self.symbol_vars[symbol_name]['spawnChance'].get() or 0)
                    symbol_data['modifierChance01_Golden'] = float(self.symbol_vars[symbol_name]['golden'].get() or 0)
                    symbol_data['modifierChance01_InstantReward'] = float(self.symbol_vars[symbol_name]['instantReward'].get() or 0)
                    symbol_data['modifierChance01_CloverTicket'] = float(self.symbol_vars[symbol_name]['cloverTicket'].get() or 0)
            
            # Pattern multiplier
            gd['allPatternsMultiplier_ByteArray'] = self.encode_byte_array(int(self.all_patterns_mult_var.get() or 1))
            
            # Available patterns (from toggles)
            available_patterns = []
            for pattern_name, var in self.pattern_enabled_vars.items():
                if var.get():  # If checkbox is checked
                    available_patterns.append(pattern_name)
            gd['patternsAvailable_AsString'] = available_patterns
            
            # Individual pattern values
            for pattern_data in gd.get('patternsData', []):
                pattern_name = pattern_data.get('patternKindAsString', '')
                if pattern_name in self.pattern_vars:
                    pattern_data['extraValue'] = float(self.pattern_vars[pattern_name].get() or 0)
            
            # Equipped powerups
            equipped = []
            for var in self.equipped_vars:
                value = var.get().strip()
                equipped.append(value if value else "undefined")
            gd['equippedPowerups'] = equipped
            
            # Store powerups
            store = []
            for var in self.store_vars:
                value = var.get().strip()
                store.append(value if value else "undefined")
            gd['storePowerups'] = store
            
            # Drawer powerups
            drawer = []
            for var in self.drawer_vars:
                value = var.get().strip()
                drawer.append(value if value else "undefined")
            gd['drawerPowerups'] = drawer
            
            # Skeleton powerups
            skeleton = []
            for var in self.skeleton_vars:
                value = var.get().strip()
                skeleton.append(value if value else "undefined")
            gd['equippedPowerups_Skeleton'] = skeleton
            
            # Luck values
            gd['powerupLuck'] = float(self.powerup_luck_var.get() or 1.0)
            gd['activationLuck'] = float(self.activation_luck_var.get() or 1.0)
            gd['storeLuck'] = float(self.store_luck_var.get() or 1.0)
            
            # 666 values
            gd['_666Chance'] = float(self.evil_chance_var.get() or 0)
            gd['_666ChanceMaxAbsolute'] = float(self.evil_chance_max_var.get() or 0)
            gd['_666SuppressedSpinsLeft'] = int(self.evil_suppressed_var.get() or 0)
            
            # Equipment settings
            gd['maxEquippablePowerups'] = int(self.max_equippable_var.get() or 8)
            gd['_redButtonActivationsMultiplier'] = int(self.red_button_mult_var.get() or 1)
            
            # Apply run modifiers changes
            self.apply_run_modifiers_changes()
            
            # Update JSON editor
            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(1.0, json.dumps(self.save_data, indent=2))
            
            messagebox.showinfo("Success", "Game values applied successfully!")
            
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Failed to apply game values:\n{str(e)}")
    
    def decode_byte_array(self, byte_array):
        """Convert byte array to integer"""
        if not byte_array:
            return 0
        result = 0
        for i, byte in enumerate(byte_array):
            result += byte * (256 ** i)
        return result
    
    def encode_byte_array(self, value):
        """Convert integer to byte array"""
        if value == 0:
            return [0]
        
        bytes_list = []
        while value > 0:
            bytes_list.append(value % 256)
            value //= 256
        return bytes_list
    
    def populate_powerup_dropdowns(self):
        """Populate all powerup dropdown lists with available powerups"""
        if not self.save_data or 'gameplayData' not in self.save_data:
            return
            
        # Extract all powerup names from the powerupsData
        powerups_data = self.save_data['gameplayData'].get('powerupsData', [])
        powerup_names = []
        
        for powerup in powerups_data:
            name = powerup.get('powerupIdentifierAsString', '')
            if name and name != 'undefined':
                powerup_names.append(name)
        
        # Sort alphabetically for easier browsing
        powerup_names.sort()
        
        # Add empty option and "undefined" option
        dropdown_options = ['', 'undefined'] + powerup_names
        
        # Update all combo boxes
        for combo in self.equipped_combos:
            combo['values'] = dropdown_options
            
        for combo in self.store_combos:
            combo['values'] = dropdown_options
            
        for combo in self.drawer_combos:
            combo['values'] = dropdown_options
            
        for combo in self.skeleton_combos:
            combo['values'] = dropdown_options
    
    def clear_equipped(self):
        """Clear all equipped powerup slots"""
        for var in self.equipped_vars:
            var.set("")
    
    def clear_store(self):
        """Clear all store powerup slots"""
        for var in self.store_vars:
            var.set("")
    
    def clear_drawers(self):
        """Clear all drawer powerup slots"""
        for var in self.drawer_vars:
            var.set("")
    
    def max_luck(self):
        """Set all luck values to maximum"""
        self.powerup_luck_var.set("10.0")
        self.activation_luck_var.set("10.0")
        self.store_luck_var.set("10.0")
    
    def unlock_all_drawers(self):
        """Unlock all drawers"""
        if not self.save_data:
            messagebox.showerror("Error", "No save data loaded")
            return
        
        self.save_data["drawersUnlocked"] = [True, True, True, True]
        messagebox.showinfo("Success", "All drawers unlocked!")
    
    def unlock_all_powerups(self):
        """Unlock all powerups by adding them to the unlocked string"""
        if not self.save_data or 'gameplayData' not in self.save_data:
            messagebox.showerror("Error", "No save data loaded")
            return
        
        # Get all powerup names from powerupsData
        powerups_data = self.save_data['gameplayData'].get('powerupsData', [])
        powerup_names = []
        
        for powerup in powerups_data:
            name = powerup.get('powerupIdentifierAsString', '')
            if name and name != 'undefined':
                powerup_names.append(name)
        
        # Create unlocked powerups string
        unlocked_string = "undefined," + ",".join(powerup_names)
        self.save_data["_unlockedPowerupsString"] = unlocked_string
        
        messagebox.showinfo("Success", f"Unlocked {len(powerup_names)} powerups!")
    
    def transform_phone_holy(self):
        """Transform the phone from possessed (666) to holy (999)"""
        if not self.save_data or 'gameplayData' not in self.save_data:
            messagebox.showerror("Error", "No save data loaded")
            return
        
        gd = self.save_data['gameplayData']
        
        # Check if skeleton is complete
        skeleton = gd.get('equippedPowerups_Skeleton', [])
        skeleton_parts = ['Skeleton_Head', 'Skeleton_Arm1', 'Skeleton_Arm2', 'Skeleton_Leg1', 'Skeleton_Leg2']
        has_full_skeleton = all(part in skeleton for part in skeleton_parts)
        
        if not has_full_skeleton:
            response = messagebox.askyesno(
                "Missing Skeleton", 
                "The phone transformation normally requires all 5 skeleton pieces equipped.\n"
                "Do you want to proceed anyway?"
            )
            if not response:
                return
        
        # Set the transformation flags
        gd['_phoneAlreadyTransformed'] = True
        gd['_phone_bookSpecialCall'] = True
        gd['_phone_EvilCallsIgnored_Counter'] = 3
        gd['phoneEasyCounter_SkippedCalls_Evil'] = 3
        gd['_phone_SpecialCalls_Counter'] = max(gd.get('_phone_SpecialCalls_Counter', 0), 1)
        
        # Update phone abilities to holy ones
        gd['_phone_AbilitiesToPick_String'] = "holyGeneric_SpawnSacredCharm,holyPatternsValue_3LessElements,holyGeneric_MultiplierSymbols_1,holyGeneric_ReduceChargesNeeded_ForRedButtonCharms"
        gd['_phone_lastAbilityCategory'] = 2
        
        messagebox.showinfo(
            "Success", 
            "Phone transformed to Holy (999) mode!\n\n"
            "The phone will now offer holy abilities instead of evil ones.\n"
            "666 events will be replaced with 999 events."
        )
    
    def populate_run_modifiers(self):
        """Populate run modifiers from save data"""
        if not self.save_data or '_runModSavingList' not in self.save_data:
            return
        
        # Clear existing modifier widgets
        for widget in self.modifiers_scroll_frame.winfo_children():
            widget.destroy()
        
        self.modifier_vars = {}
        
        # Populate existing modifiers
        modifiers = self.save_data.get('_runModSavingList', [])
        
        for idx, modifier in enumerate(modifiers):
            mod_name = modifier.get('runModifierIdentifierAsString', '')
            
            # Store variables for this modifier
            self.modifier_vars[mod_name] = {
                'owned': tk.StringVar(value=str(modifier.get('ownedCount', 0))),
                'unlocked': tk.StringVar(value=str(modifier.get('unlockedTimes', 0))),
                'played': tk.StringVar(value=str(modifier.get('playedTimes', 0))),
                'won': tk.StringVar(value=str(modifier.get('wonTimes', 0))),
                'foil': tk.StringVar(value=str(modifier.get('foilLevel', 0)))
            }
            
            # Create UI elements - data starts at row 0 now (headers are outside)
            ttk.Label(self.modifiers_scroll_frame, text=mod_name, width=40, anchor="w").grid(row=idx, column=0, padx=5, pady=2, sticky="w")
            ttk.Entry(self.modifiers_scroll_frame, textvariable=self.modifier_vars[mod_name]['owned'], width=10).grid(row=idx, column=1, padx=5, pady=2)
            ttk.Entry(self.modifiers_scroll_frame, textvariable=self.modifier_vars[mod_name]['unlocked'], width=10).grid(row=idx, column=2, padx=5, pady=2)
            ttk.Entry(self.modifiers_scroll_frame, textvariable=self.modifier_vars[mod_name]['played'], width=10).grid(row=idx, column=3, padx=5, pady=2)
            ttk.Entry(self.modifiers_scroll_frame, textvariable=self.modifier_vars[mod_name]['won'], width=10).grid(row=idx, column=4, padx=5, pady=2)
            ttk.Entry(self.modifiers_scroll_frame, textvariable=self.modifier_vars[mod_name]['foil'], width=10).grid(row=idx, column=5, padx=5, pady=2)
    
    def add_all_run_modifiers(self):
        """Add all standard run modifiers to the save data"""
        if not self.save_data:
            messagebox.showerror("Error", "No save data loaded")
            return
        
        # Standard run modifiers from the game
        standard_modifiers = [
            "defaultModifier",
            "phoneEnhancer", 
            "redButtonOverload",
            "smallerStore",
            "smallItemPool",
            "interestsGrow",
            "lessSpaceMoreDiscount",
            "smallRoundsMoreRounds",
            "oneRoundPerDeadline",
            "headStart",
            "extraPacks",
            "_666BigBetDouble_SmallBetNoone",
            "_666DoubleChances_JackpotRecovers",
            "_666LastRoundGuaranteed",
            "drawerTableModifications",
            "drawerModGamble",
            "halven2SymbolsChances",
            "charmsRecycling",
            "allCharmsStoreModded",
            "bigDebt"
        ]
        
        # Get existing modifiers
        existing_modifiers = self.save_data.get('_runModSavingList', [])
        existing_names = {mod.get('runModifierIdentifierAsString', '') for mod in existing_modifiers}
        
        # Add missing modifiers
        for mod_name in standard_modifiers:
            if mod_name not in existing_names:
                new_modifier = {
                    "runModifierIdentifierAsString": mod_name,
                    "ownedCount": 0,
                    "unlockedTimes": 0,
                    "playedTimes": 0,
                    "wonTimes": 0,
                    "foilLevel": 0
                }
                existing_modifiers.append(new_modifier)
        
        # Update save data
        self.save_data['_runModSavingList'] = existing_modifiers
        
        # Refresh the UI
        self.populate_run_modifiers()
        
        messagebox.showinfo("Success", f"Added {len(standard_modifiers)} run modifiers!")
    
    def apply_run_modifiers_changes(self):
        """Apply changes from run modifiers UI to save data"""
        if not self.save_data or '_runModSavingList' not in self.save_data:
            return
        
        # Update modifier values from UI
        for modifier in self.save_data['_runModSavingList']:
            mod_name = modifier.get('runModifierIdentifierAsString', '')
            if mod_name in self.modifier_vars:
                modifier['ownedCount'] = int(self.modifier_vars[mod_name]['owned'].get() or 0)
                modifier['unlockedTimes'] = int(self.modifier_vars[mod_name]['unlocked'].get() or 0)
                modifier['playedTimes'] = int(self.modifier_vars[mod_name]['played'].get() or 0)
                modifier['wonTimes'] = int(self.modifier_vars[mod_name]['won'].get() or 0)
                modifier['foilLevel'] = int(self.modifier_vars[mod_name]['foil'].get() or 0)
                
    def save_file(self):
        """Save and encrypt the file"""
        if not self.save_data or not self.current_file:
            messagebox.showerror("Error", "No data to save")
            return
            
        try:
            # Apply quick edits first
            self.apply_quick_edits()
            
            # Apply game values changes
            self.apply_game_values()
            
            # Also update from JSON editor
            json_content = self.json_text.get(1.0, tk.END).strip()
            if json_content:
                self.save_data = json.loads(json_content)
                
            # Convert to JSON string
            json_str = json.dumps(self.save_data, separators=(',', ':'))
            
            # Encrypt
            encrypted_data = self.xor_data(json_str.encode('utf-8'))
            
            # Save
            with open(self.current_file, 'wb') as f:
                f.write(encrypted_data)
                
            self.status_var.set(f"Saved: {os.path.basename(self.current_file)}")
            messagebox.showinfo("Success", "Save file updated successfully!")
            
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")
            
    def format_json(self):
        """Format the JSON in the editor"""
        try:
            content = self.json_text.get(1.0, tk.END).strip()
            if content:
                parsed = json.loads(content)
                formatted = json.dumps(parsed, indent=2)
                self.json_text.delete(1.0, tk.END)
                self.json_text.insert(1.0, formatted)
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON:\n{str(e)}")
            
    def validate_json(self):
        """Validate the JSON in the editor"""
        try:
            content = self.json_text.get(1.0, tk.END).strip()
            if content:
                json.loads(content)
                messagebox.showinfo("Valid", "JSON is valid!")
            else:
                messagebox.showwarning("Warning", "No JSON content to validate")
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON:\n{str(e)}")

def main():
    root = tk.Tk()
    app = SaveFileEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()