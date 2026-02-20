import copy
import tkinter as tk
from PIL import Image, ImageTk
import os
from pyriichi.tiles import create_tile
from pyriichi.hand import Hand, Combination
from pyriichi.yaku import YakuChecker
from pyriichi.game_state import GameState

# Define the path to the assets folder
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets", "images")

class MahjongTileApp:
    def __init__(self, master, tiles_data):
        self.master = master
        self.master.title("Mahjong Tile Display")

        self.tile_width = 60
        self.tile_height = 90
        self.padding = 5
        self.x_offset = 10
        self.y_offset = 10
        self.tile_toggle_row_height = 28

        # Adjust canvas width to accommodate hand tiles (14 tiles)
        self.canvas = tk.Canvas(
            master,
            width=(self.tile_width + self.padding) * 14 + self.x_offset,
            height=self.tile_height + self.tile_toggle_row_height + 2 * self.y_offset,
            bg="lightgray",
        )
        self.canvas.pack()

        # Frame for displaying winning combinations and meld toggles
        self.combinations_frame = tk.Frame(master, bd=2, relief="groove", padx=5, pady=5)
        self.combinations_frame.pack(pady=10)

        self.images = [] # Keep references to PhotoImage objects to prevent garbage collection
        self.displayed_tiles_info = [] # Stores (tile_str, image_id, bbox_coords)
        self.tile_is_red_states = [False] * len(tiles_data)  # False = not selected/open
        self.tile_toggle_buttons = {}
        self.selected_winning_tile_index = -1
        self.highlight_rect_id = None

        # To store the current hand data (sorted as well)
        self.hand_tiles_data = self._load_and_display_tiles(tiles_data)
        self.combination_toggles_data = [] # Stores (Combination object, BooleanVar, Button) tuples

        # For selecting the winning_tile
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # For initializing combination and meld state switch for each combination
        # self._init_comb()
        dummy_winning_tile = self.hand_tiles_data._tiles[0]
        dummy_hand = copy.deepcopy(self.hand_tiles_data)
        dummy_hand._tiles.remove(dummy_winning_tile)
    
        self.init_combination = dummy_hand.get_winning_combinations(winning_tile=dummy_winning_tile) # Arbitraily assign one winning tile and get the dummy combination
        if self.init_combination:
            # For simplicity, display toggles for the first winning combination only
            selected_winning_combination = list(self.init_combination.values())[0]

            tk.Label(self.combinations_frame, text="Combination Melds:").pack(anchor="w")
            combos_row_frame = tk.Frame(self.combinations_frame)
            combos_row_frame.pack(anchor="w", fill="x")

            # Create toggles for each combination in the selected winning combination
            display_col = 0
            for i, combo in enumerate(selected_winning_combination):
                if combo.type.value == "pair":
                    continue
                combo_var = tk.BooleanVar(self.master, value=combo.is_open)
                # Create a descriptive text for the combination
                combo_tiles_str = " ".join([str(t) for t in combo.tiles])
                combo_text = f"{combo.type.value.capitalize()}: {combo_tiles_str}"
                combo_block = tk.Frame(combos_row_frame, padx=8, pady=4, bd=1, relief="solid")
                combo_block.grid(row=0, column=display_col, padx=4, pady=4, sticky="n")
                combo_label = tk.Label(
                    combo_block,
                    text=combo_text,
                )
                combo_label.pack(anchor="center")
                combo_button = tk.Button(
                    combo_block,
                    text=self._get_combo_toggle_text(combo_var.get()),
                )
                combo_button.configure(
                    command=lambda c=combo, v=combo_var, b=combo_button: self._toggle_combo_state(c, v, b)
                )
                combo_button.pack(anchor="center", pady=(6, 0))
                self.combination_toggles_data.append((combo, combo_var, combo_button))
                display_col += 1
            
            # Update the is_open state of the combination objects based on the toggles
            for combo, combo_var, _ in self.combination_toggles_data:
                combo.set_open(combo_var.get())
        
        # Riichi Checkbox
        self.riichi_var = tk.BooleanVar(master, value=False)
        self.riichi_checkbox = tk.Checkbutton(master, text="Riichi", variable=self.riichi_var)
        self.riichi_checkbox.pack()

        # Main Pyriichi logic button
        main_button = tk.Button(root, text="Count Points", command=self._run_pyriichi_logic)
        main_button.pack()

    def _get_combo_toggle_text(self, is_meld):
        return f"State: {'Meld' if is_meld else 'Not Meld'} (Toggle)"

    def _toggle_combo_state(self, combo, combo_var, button):
        new_state = not combo_var.get()
        combo_var.set(new_state)
        combo.set_open(new_state)
        button.configure(text=self._get_combo_toggle_text(new_state))


    def _get_image_filename(self, tile_str):
        # Maps pyriichi tile string to image filename
        return f"{tile_str}.jpg"

    def _load_and_display_tiles(self, tiles_data):
        # Clear previous images and info
        self.canvas.delete("all") # Clear all canvas items
        self.images.clear()
        self.displayed_tiles_info.clear()
        self.tile_toggle_buttons.clear()
        self.selected_winning_tile_index = -1
        self.highlight_rect_id = None

        current_x = self.x_offset
        current_y = self.y_offset + self.tile_toggle_row_height
        
        tiles = [create_tile(tile_str) for tile_str in tiles_data]
        hand = Hand(tiles)
        hand.sort_tile()
        for i, tile in enumerate(hand._tiles):
            tile_str = str(tile)
            filename = self._get_image_filename(tile_str)
            if filename:
                image_path = os.path.join(ASSETS_PATH, filename)
                if os.path.exists(image_path):
                    original_image = Image.open(image_path)
                    resized_image = original_image.resize((self.tile_width, self.tile_height), Image.LANCZOS)
                    photo_image = ImageTk.PhotoImage(resized_image)
                    self.images.append(photo_image) # Store reference

                    # Create image and store its ID and bounding box for click detection
                    image_id = self.canvas.create_image(current_x, current_y, image=photo_image, anchor=tk.NW, tags=("tile", f"tile_{i}"))
                    bbox = (current_x, current_y, current_x + self.tile_width, current_y + self.tile_height)
                    self.displayed_tiles_info.append((tile_str, image_id, bbox))
                    self._create_tile_toggle_button(i, current_x, current_y)

                    current_x += self.tile_width + self.padding
                else:
                    print(f"Image not found for tile: {tile_str} at {image_path}")
            else:
                print(f"Unknown tile string or no mapping: {tile_str}")
        return hand

    def _create_tile_toggle_button(self, tile_index, tile_x, tile_y):
        button = tk.Button(
            self.canvas,
            text=self._get_tile_toggle_icon(self.tile_is_red_states[tile_index]),
            fg="red" if self.tile_is_red_states[tile_index] else "#888888",
            width=2,
            height=1,
            relief=tk.RAISED,
            command=lambda idx=tile_index: self._toggle_tile_state(idx),
        )
        self.tile_toggle_buttons[tile_index] = button
        center_x = tile_x + self.tile_width // 2
        button_y = tile_y - (self.tile_toggle_row_height // 2)
        self.canvas.create_window(center_x, button_y, window=button)

    def _get_tile_toggle_icon(self, is_on):
        return "◆" if is_on else "◇"

    def _toggle_tile_state(self, tile_index):
        self.tile_is_red_states[tile_index] = not self.tile_is_red_states[tile_index]
        button = self.tile_toggle_buttons.get(tile_index)
        if button is None:
            return
        is_on = self.tile_is_red_states[tile_index]
        button.configure(
            text=self._get_tile_toggle_icon(is_on),
            fg="red" if is_on else "#888888",
            relief=tk.SUNKEN if is_on else tk.RAISED,
        )

    def _on_canvas_click(self, event):
        clicked_items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        for item_id in clicked_items:
            # Check if the clicked item is a tile
            if "tile" in self.canvas.gettags(item_id):
                for i, (_, img_id, _) in enumerate(self.displayed_tiles_info):
                    if img_id == item_id:
                        self._select_winning_tile(i)
                        return

    def _select_winning_tile(self, tile_index):
        if self.highlight_rect_id:
            self.canvas.delete(self.highlight_rect_id)
            self.highlight_rect_id = None

        self.selected_winning_tile_index = tile_index
        if 0 <= self.selected_winning_tile_index < len(self.displayed_tiles_info):
            _, image_id, bbox = self.displayed_tiles_info[self.selected_winning_tile_index]
            x1, y1, x2, y2 = bbox
            # Create a red border around the selected tile without padding
            self.highlight_rect_id = self.canvas.create_rectangle(
                x1, y1, x2, y2, outline="red", width=3
            )
            # Bring the highlight rectangle below the tile image to avoid obscuring it
            self.canvas.tag_lower(self.highlight_rect_id, image_id)

    def _run_pyriichi_logic(self):
        if self.selected_winning_tile_index == -1:
            print("No winning tile selected.")
            return

        dummy_hand = copy.deepcopy(self.hand_tiles_data)
        for idx, tile in enumerate(dummy_hand._tiles):
            if self.tile_is_red_states[idx]:
                new_tile = copy.deepcopy(tile)
                setattr(new_tile, "_is_red", True)
                dummy_hand._tiles[idx] = new_tile
        print(f"fuck: {dummy_hand._tiles}")

        winning_tile = self.hand_tiles_data._tiles[self.selected_winning_tile_index]
        dummy_hand._tiles.pop(self.selected_winning_tile_index)
        print(f"Selected winning tile: {str(winning_tile)}")

        for combo, combo_var, _ in self.combination_toggles_data:
            if combo_var.get():
                for t in combo.tiles:
                    dummy_hand._tiles.remove(t)
                dummy_hand._melds.append(combo.comb2meld())

        print(f"Is winning hand: {dummy_hand.is_winning_hand(winning_tile=winning_tile)}")
        winning_comb_all = dummy_hand.get_winning_combinations(winning_tile=winning_tile) # Renamed to avoid confusion

        print(f"Number of winning combinations: {len(winning_comb_all)}")
        selected_winning_combination = list(winning_comb_all.values())[0]

        state = GameState()
        check = YakuChecker()
        dummy_hand._is_riichi = self.riichi_var.get() # Set Riichi based on checkbox
        res = check.check_all(dummy_hand, winning_tile, selected_winning_combination, state)
        print(f"Yaku check result: {res}")

        print("-" * 30)
        # --- End of existing pyriichi logic ---


if __name__ == "__main__":
    tiles_data = ["2C", "3C", "4C", "4D", "5D", "6D", "WW", "WW", "2B", "3B", "4B", "8B", "8B", "8B"]
    # The winning_tile_data is now selected by click, so it's not needed here
    # winning_tile_data = "6D"
    root = tk.Tk()
    app = MahjongTileApp(root, tiles_data)
    root.mainloop()
