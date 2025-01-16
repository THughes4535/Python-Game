import arcade
import arcade.color
import arcade.color
import arcade.color
import arcade.gui
from pyglet.math import Vec2
import actor
import arcade.key
from collections import deque
import random
import transitionView
from typing import Union
from enum import Enum, auto
import copy
import baseCharacters
from baseMoves import *
import json

"""Y Variables"""
DEFAULT_SCREEN_WIDTH = 800
DEFAULT_SCREEN_HEIGHT = 600
CAMERA_SPEED = 1
BATTLE_CAMERA_SPEED = 0.1
TILE_SCALING = 4
CHARACTER_SCALING = 3

"""Debugging variables"""
SHOW_COORDINATES = False #displays real-time coordinates of the camera
SEE_POINTS = False # See points (ie: spawn points)
SEE_GRID_POINTS = True
SEE_EVENTS = True # See event sprites (ie: teleport, next level, etc)
LOADGAME = True #Used for testing Load functionality

"""Adjustable variables"""
DELAY_AFTER_ANIMATION = 0.5

move_dict = {
            "Basic Strike" : basicStrike,
            "Heavy Hit" : heavyHit,
            "Cross Slam" : crossSlam,
            "Small Heal" : smallHeal,
            "Self Heal" : selfHeal,
            "Global Heal" : globalHeal,
            "Global Attack" : aoeMove,
            "GOAT SLAM" : goatSlam,
            "Summon Hero Ally" : summon_hero_ally,
            "rm_rf" : rm_rf
}

#Saves player data to a json file. Currently mapped to the 'e' key
def SaveGame(player: actor.Player, currentMapIndex):
    with open("savegame.json", "w") as sf:
        movesList = []
        for move in player.moves:
            if move.name in move_dict.keys():
                movesList.append(move.name)
        StatsToDict = {
            "name" : player.name,
            "hp" : player.hp,
            "money" : player.money,
            "max_hp" : player.max_hp,
            "stamina" : player.stamina,
            "max_stamina" : player.max_stamina,
            "moves" : movesList
            }
        
        currentMap = currentMapIndex

        saveDict = {
            "PlayerStats" : StatsToDict,
            "CurrentLevel" : currentMap
        }

        json.dump(saveDict, sf)

def LoadGame(overworld: "Overworld"):
    with open("savegame.json", "r") as lf:
        print("Loading Data From File \"savegame.json\"")
        saveDict = json.load(lf)
        playerDict = saveDict["PlayerStats"]
        movesList = []
        for move in playerDict["moves"]:
            movesList.append(move_dict[move])
        overworld.player = actor.Player(136.00 * TILE_SCALING,
                              247.33 * TILE_SCALING,
                              name = playerDict["name"],
                              max_hp = playerDict["max_hp"],
                              max_stamina = playerDict["max_stamina"],
                              moves = movesList,
                              move_range = 99,
                              turn_speed = 99,
                              attacks_per_turn = 1,
                              movements_per_turn = 2,
                              money=playerDict["money"],
                              texture="assets/character_textures/player.png"
                              )
        overworld.player.hp = playerDict["hp"]
        overworld.player.stamina = playerDict["stamina"]
        return saveDict["CurrentLevel"]

class Overworld(arcade.View):
    def __init__(self):
        """
        Sets up the Arcade window.
        @width : sets width of the screen
        @height : sets height of the screen
        """
        super().__init__()
        
        self.camera_sprites = arcade.Camera(self.window.width, self.window.height)
        self.camera_gui = arcade.Camera(self.window.width, self.window.height)
        self.level_file_path = None
        self.inp_tracker = InputTracker()
        self.player = actor.Player( 532,
                                    2199,
                                    name = "Hero", 
                                    max_hp =30 , 
                                    max_stamina = 10, 
                                    move_range = 99, 
                                    turn_speed = 99, 
                                    moves = [basicStrike, crossSlam, globalHeal, aoeMove, summon_hero_ally, rm_rf], 
                                    attacks_per_turn = 1, 
                                    movements_per_turn = 2,
                                    money=0,
                                    texture="assets/character_textures/player.png")

        self.current_level_index = 0
        self.level: Level = None
        
        
        self.levels: list[Level] = [] # Store all levels
        for level_index in range(1, 5):
            self.levels.append(Level(level_index, debug_events=SEE_EVENTS, debug_points=SEE_POINTS))
        
        self.arenas: list[Arena] = [] # Store all arenas
        for arena_index in range(1, 5):
            self.arenas.append(Arena(arena_index))
        
        if LOADGAME is True:
            self.current_level_index = LoadGame(self.player)
            print(f"Loading into Level {self.current_level_index}")
        
    def setup(self, level_index : int) -> None:
        """Make sure to move_player() after setting up the level.
        
        Instantiates this particular scene and all of its
        relevant actors. The reason this isn't in `__init__`
        is so that one could theoretically restart the
        scene from scratch by running this function.
        """
        self.current_level_index = level_index
        self.level = self.levels[self.current_level_index]
        self.level.load_level(self)
        arcade.set_background_color(arcade.csscolor.DARK_CYAN)
    
    def move_player(self, target_x: int, target_y: int) -> None:
        """Moves the player to a point on the map.

        Args:
            target_x (int): x-position to go to.
            target_y (int): y-position to go to.
        """
        self.player.center_x, self.player.center_y = target_x, target_y
    
    def on_key_press(self, key, modifiers):
        """Built-in Arcade callback, which is to say it runs automatically in its own event loop.
        Passes in a `key` argument from `arcade.key` that has been pressed.
        """
        self.inp_tracker[key] = True

    def on_key_release(self, key, modifiers):
        """Built-in Arcade callback. Passes in a `key` argument from `arcade.key` that has been released."""
        self.inp_tracker[key] = False  

    def on_update(self, delta_time):
        """Built-in Arcade callback that runs once a frame. `delta_time` is for if we wanted
        to perform updates based on actual time elapsed instead of just by frames (this
        would make games with variable frame rates behave "smoothly" instead of slowing down).
        """
        self.player.processInput(self.inp_tracker)
        self.player.update()
        self.level.scene.update(["eventTriggers"])
        self.level.physics_engine.update()
        
        self.scroll_to_player()

        if self.inp_tracker[arcade.key.E] is True:
            print("saving game to savegame.json")
            SaveGame(self.player, self.current_level_index)
    
    def on_draw(self):
        """Built-in Arcade callback that runs once a frame. The only distinction between this
        and `on_update` I can find is that this is specified by pyglet and `on_update` callback is specified by Arcade.
        """
        self.clear()
        
        self.camera_sprites.use() # For Camera scrolling
        self.level.scene.draw()
        self.player.draw()
        
        self.camera_gui.use() # For drawing GUIs

        arcade.draw_text("Inventory", self.window.width - 100, self.window.height - 30, arcade.color.BLACK_BEAN, 18, anchor_x="center", anchor_y="center")

        # Coordinates of camera.
        if SHOW_COORDINATES:
            arcade.draw_rectangle_filled(self.window.width // 2,
                                        20,
                                        self.window.width,
                                        40,
                                        arcade.color.ALMOND)
            text = f"Scroll value: ({self.player.center_x:5.1f}, " \
                f"{self.player.center_y:5.1f})"
            arcade.draw_text(text, 10, 10, arcade.color.BLACK_BEAN, 20)
    
    def scroll_to_player(self):
        """Scroll the window to the player.

        if CAMERA_SPEED is 1, the camera will immediately move to the desired position.
        Anything between 0 and 1 will have the camera move to the location with a smoother
        pan.
        """

        position = Vec2(self.player.center_x - self.window.width / 2,
                        self.player.center_y - self.window.height / 2)

        self.camera_sprites.move_to(position, CAMERA_SPEED)

    def on_resize(self, width, height):
        """Resize window

        Handle the user grabbing the edge and resizing the window.
        """
        self.camera_sprites.resize(int(width), int(height))
        self.camera_gui.resize(int(width), int(height))

    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse click events."""
        # Check if the click is on the "Inventory" text in the top-right corner
        inventory_x_start = self.window.width - 140
        inventory_x_end = self.window.width - 60
        inventory_y_start = self.window.height - 40
        inventory_y_end = self.window.height - 20
        if inventory_x_start <= x <= inventory_x_end and inventory_y_start <= y <= inventory_y_end:
            # Open the inventory screen
            print("Inventory clicked!")
            self.window.show_view(InventoryScreen(self))

class InventoryScreen(arcade.View):
    def __init__(self, overworld_view):
        super().__init__()
        self.overworld_view = overworld_view

        # Box dimensions
        self.box_width = self.window.width // 2
        self.box_height = self.window.height // 2
        self.box_x = (self.window.width - self.box_width) // 2
        self.box_y = (self.window.height - self.box_height) // 2

        # X button dimensions and position
        self.x_button_size = 40
        self.x_button_x = self.box_x + self.box_width - self.x_button_size // 2
        self.x_button_y = self.box_y + self.box_height - self.x_button_size // 2

        # Tab positions
        self.skills_tab_x = self.box_x + 50
        self.skills_tab_y = self.box_y + self.box_height - 50
        self.others_tab_x = self.box_x + 200
        self.others_tab_y = self.box_y + self.box_height - 50
        self.ally_tab_x = self.box_x + 150
        self.ally_tab_y = self.box_y + self.box_height - 150

        
        self.inventory_item = arcade.Sprite("assets/character_textures/backpack.png", scale=0.3)  # Adjust scale as needed
        self.inventory_item.center_x = self.box_x + self.box_width // 2  # Set starting position
        self.inventory_item.center_y = self.box_y + self.box_height // 2 - 100  # Set starting position

    def on_draw(self):
        """Render the inventory screen."""
        # Draw the background as a transparent overlay
        arcade.draw_lrtb_rectangle_filled(0, self.window.width, self.window.height, 0, arcade.color.BLACK)

        # Draw the centered box
        arcade.draw_rectangle_filled(
            self.box_x + self.box_width // 2,
            self.box_y + self.box_height // 2,
            self.box_width,
            self.box_height,
            arcade.color.LIGHT_BROWN,
        )

        # Draw the tabs inside the box
        arcade.draw_text(
            "Skills", self.skills_tab_x, self.skills_tab_y, arcade.color.BLACK, 20
        )
        arcade.draw_text(
            "Rambucks", self.others_tab_x, self.others_tab_y, arcade.color.BLACK, 20
        )
        arcade.draw_text(
            "Allies", self.ally_tab_x, self.ally_tab_y, arcade.color.BLACK, 20
        )
        # Draw the X button in the top-right corner of the box
        arcade.draw_rectangle_filled(
            self.x_button_x, self.x_button_y, self.x_button_size, self.x_button_size, arcade.color.RED
        )
        arcade.draw_text(
            "X",
            self.x_button_x,
            self.x_button_y - 8,
            arcade.color.WHITE,
            16,
            anchor_x="center",
            anchor_y="center",
        )

        # Draw the inventory item (PNG image)
        self.inventory_item.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        """mouse clicks in inventory"""
        #Check if the click is inside the X button
        if (self.x_button_x - self.x_button_size // 2 <= x <= self.x_button_x + self.x_button_size // 2 and self.x_button_y - self.x_button_size // 2 <= y <= self.x_button_y + self.x_button_size // 2):
           
            #Exit the inventory
            print("Exiting inventory.")
            self.window.show_view(self.overworld_view)

        #heck if the click is on the "Skills" tab
        elif (self.skills_tab_x <= x <= self.skills_tab_x + 80 and self.skills_tab_y - 20 <= y <= self.skills_tab_y + 20):
            
            print("Opening Skills tab.")
            self.window.show_view(SkillsScreen(self))

        # Check if the click is on the "ally" tab
        elif (self.ally_tab_x <= x <= self.ally_tab_x + 120 and self.ally_tab_y - 20 <= y <= self.ally_tab_y + 20):
            
            print("Opening Allies tab.")
            self.window.show_view(AllyScreen(self))

        #Check if the click is on the "Others" tab
        elif (self.others_tab_x <= x <= self.others_tab_x + 100 and self.others_tab_y - 20 <= y <= self.others_tab_y + 20):
           
            print("Opening Others tab.")
            self.window.show_view(OthersScreen(self))

class SkillsScreen(arcade.View):
    def __init__(self, inventory_screen):
        super().__init__()
        self.inventory_screen = inventory_screen

        #Box dimensions
        self.box_width = self.window.width // 2
        self.box_height = self.window.height // 2
        self.box_x = (self.window.width - self.box_width) // 2
        self.box_y = (self.window.height - self.box_height) // 2

        # X button dimensions and position
        self.x_button_size = 40
        self.x_button_x = self.box_x + self.box_width - self.x_button_size // 2
        self.x_button_y = self.box_y + self.box_height - self.x_button_size // 2

    def on_draw(self):
        """show the Skills screen."""
        arcade.draw_lrtb_rectangle_filled(
            0, self.window.width, self.window.height, 0, arcade.color.BLACK + (180,)
        )
        arcade.draw_rectangle_filled(
            self.box_x + self.box_width // 2,
            self.box_y + self.box_height // 2,
            self.box_width,
            self.box_height,
            arcade.color.LIGHT_GRAY,
        )
        arcade.draw_text(
            "My Skills",
            self.box_x + 20,
            self.box_y + self.box_height - 40,
            arcade.color.BLACK,
            20,
        )

        # Draw grid lines
        for i in range(4):  #(4x4)
            for j in range(4): 
                cell_x = self.box_x + 50 + j * 100
                cell_y = self.box_y + self.box_height - 100 - i * 50
                arcade.draw_rectangle_outline(cell_x, cell_y, 80, 40, arcade.color.BLACK)

        #Draw the X button in the top-right corner of the box
        arcade.draw_rectangle_filled(self.x_button_x, self.x_button_y, self.x_button_size, self.x_button_size, arcade.color.RED)
        
        #x button draw
        arcade.draw_text(
            "X",
            self.x_button_x,
            self.x_button_y - 8,
            arcade.color.WHITE,
            16,
            anchor_x="center",
            anchor_y="center",
        )

    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse clicks."""
        #check if the click is inside the X button
        if (self.x_button_x - self.x_button_size // 2 <= x <= self.x_button_x + self.x_button_size // 2 and self.x_button_y - self.x_button_size // 2 <= y <= self.x_button_y + self.x_button_size // 2):
            
            print("Exiting My Skills inventory.")
            self.window.show_view(self.inventory_screen)

class AllyScreen(SkillsScreen):
    def on_draw(self):
        """show the Ally screen."""
        arcade.draw_lrtb_rectangle_filled(0, self.window.width, self.window.height, 0, arcade.color.BLACK + (180,))
        
        arcade.draw_rectangle_filled(
            self.box_x + self.box_width // 2,
            self.box_y + self.box_height // 2,
            self.box_width,
            self.box_height,
            arcade.color.LIGHT_GRAY,
        )
        arcade.draw_text(
            "My Allies",
            self.box_x + 20,
            self.box_y + self.box_height - 40,
            arcade.color.BLACK,
            20,
        )
        for i in range(4):  
            for j in range(4): 
                cell_x = self.box_x + 50 + j * 100
                cell_y = self.box_y + self.box_height - 100 - i * 50
                arcade.draw_rectangle_outline(cell_x, cell_y, 80, 40, arcade.color.BLACK)

        arcade.draw_rectangle_filled(
            self.x_button_x, self.x_button_y, self.x_button_size, self.x_button_size, arcade.color.RED
        )
        arcade.draw_text(
            "X",
            self.x_button_x,
            self.x_button_y - 8,
            arcade.color.WHITE,
            16,
            anchor_x="center",
            anchor_y="center",
        )

    def on_mouse_press(self, x, y, button, modifiers):
   
        if (self.x_button_x - self.x_button_size // 2 <= x <= self.x_button_x + self.x_button_size // 2 and self.x_button_y - self.x_button_size // 2 <= y <= self.x_button_y + self.x_button_size // 2):
            
            print("Exiting My Allies inventory.")
            self.window.show_view(self.inventory_screen)

class OthersScreen(SkillsScreen):
    def on_draw(self):
       
        arcade.draw_lrtb_rectangle_filled(0, self.window.width, self.window.height, 0, arcade.color.BLACK + (180,))
      
        arcade.draw_rectangle_filled(
            self.box_x + self.box_width // 2,
            self.box_y + self.box_height // 2,
            self.box_width,
            self.box_height,
            arcade.color.LIGHT_GRAY,
        )
        arcade.draw_text(
            "Rambucks",
            self.box_x + 20,
            self.box_y + self.box_height - 40,
            arcade.color.BLACK,
            20,
        )

        for i in range(4): 
            for j in range(4): 
                cell_x = self.box_x + 50 + j * 100
                cell_y = self.box_y + self.box_height - 100 - i * 50
                arcade.draw_rectangle_outline(cell_x, cell_y, 80, 40, arcade.color.BLACK)

        arcade.draw_rectangle_filled(
            self.x_button_x, self.x_button_y, self.x_button_size, self.x_button_size, arcade.color.RED
        )
        arcade.draw_text(
            "X",
            self.x_button_x,
            self.x_button_y - 8,
            arcade.color.WHITE,
            16,
            anchor_x="center",
            anchor_y="center",
        )

    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse clicks."""

        if (self.x_button_x - self.x_button_size // 2 <= x <= self.x_button_x + self.x_button_size // 2 and self.x_button_y - self.x_button_size // 2 <= y <= self.x_button_y + self.x_button_size // 2):
            
            print("Exiting My Misc inventory.")
            self.window.show_view(self.inventory_screen)

class EventTrigger(arcade.Sprite):
    def __init__(self, filename: str, scale: float, eventObject: arcade.TiledObject, overworld: Overworld):
        center_x, center_y = eventObject.shape
        super().__init__(filename, scale, center_x=center_x, center_y=center_y)
        self.eventObject = eventObject
        self.properties = eventObject.properties
        self.name: str = eventObject.name
        self.overworld = overworld
        # load the highest enemy hp texture from the enemies and show it in the overworld
        # also sets scale back to unit size
        if self.name == "Enemy":
            self.scale = CHARACTER_SCALING
            character_list = self.get_characters(self.properties["enemies"])
            chosen_character: actor.Character = None
            highest_max_hp: int = 0
            for character in character_list:
                if character.max_hp > highest_max_hp:
                    chosen_character = character
            self._texture = chosen_character.texture
        
        
    def update(self):
        activateEvent = arcade.check_for_collision(self.overworld.player, self)
        if not activateEvent: # End function if not touching any event
            return

        if self.name == "Teleport":
            print(f"{self.name}: {self}")
            def teleport_and_update():
                self.player_go_to_point("Spawn")  # Move the player
                self.overworld.scroll_to_player()  # Update the camera
                self.overworld.inp_tracker.clear()  # Reset the input tracker to stop movement

            # Create a transition view
            transition_view = transitionView.TeleportTransition(
                current_view=self.overworld,
                next_view_callable=teleport_and_update,
                duration=0.5
            )
            window.show_view(transition_view)
            
        elif self.name == "Next_Level":
            print(f"{self.name}: {self}")
            new_level_index = self.overworld.current_level_index + 1
            def teleport_and_update():
                self.overworld.setup(new_level_index)
                x, y = self.get_point("Spawn")
                self.overworld.move_player(x, y)
                self.overworld.scroll_to_player()  # Update the camera
                self.overworld.inp_tracker.clear()  # Reset the input tracker to stop movement

            # Create a transition view
            transition_view = transitionView.TeleportTransition(
                current_view=self.overworld,
                next_view_callable=teleport_and_update,
                duration=0.5
            )
            window.show_view(transition_view)
        elif self.name == "Previous_Level":
            print(f"{self.name}: {self}")
            new_level_index = self.overworld.current_level_index - 1
            def teleport_and_update():
                self.overworld.setup(new_level_index)
                x, y = self.get_point("Spawn") # where to move the player
                self.overworld.move_player(x, y)
                self.overworld.scroll_to_player()  # Update the camera
                self.overworld.inp_tracker.clear()  # Reset the input tracker to stop movement

            # Create a transition view
            transition_view = transitionView.TeleportTransition(
                current_view=self.overworld,
                next_view_callable=teleport_and_update,
                duration=0.5
            )
            window.show_view(transition_view)
        elif self.name == "Enemy": # Expand off of this so we know what the enemy listings are for each "Enemy" event trigger
            print(f"{self.name}: {self}")
            self.trigger_battle()
        else:
            print(f"Not identified event: {self}") # In case we have extra events, print it on the terminal when colliding
    
    def trigger_battle(self) -> None:
        """Create a battle"""
        # Stop last input movement going to battle
        self.overworld.player.change_x = 0 
        self.overworld.player.change_y = 0
        self.overworld.inp_tracker.clear()
        # where the player should go after the end of the battle
        end_x, end_y = self.get_point("Spawn") 
        # create battle and add player to it
        battle_view = Battle(self.overworld, end_x, end_y, grid_size=9, num_enemy_spawns=9)
        battle_view.add_character_to_battle(self.overworld.player)
        # Add enemies specific to the event trigger to the battle
        enemy_list: list[actor.Character] = self.get_characters(self.properties["enemies"])
        battle_view.add_characters_to_battle(enemy_list)
        ally_list: list[actor.Character] = self.get_characters(self.properties["allies"])
        battle_view.add_characters_to_battle(ally_list)
        # transition to battle
        transition_view = transitionView.ToBattleTransition(overworld=self.overworld, battle_view=battle_view, duration=0.5)
        window = arcade.get_window()
        window.show_view(transition_view)
    
    def get_characters(self, characters_str: str | None) -> list[actor.Character] | None:
        """Reads characters and returns the objects of those characters.
        The character names should be the same as the object names in baseCharacters.py.
        Mainly used for getting the characters from an enemy trigger as a custom property in Tiled.

        Args:
            characters_str (str | None): The characters formatted as "character1, character2, etc."

        Returns:
            list[actor.Character] | None: The character objects to add to the battle. Returns None if no characters as input.
        """
        if not characters_str:
            return None
        characters_str_formatted: list[str] = characters_str.split(", ")
        character_list: list[actor.Character] = []
        for character_str in characters_str_formatted:
            character: actor.Character = getattr(baseCharacters, character_str)
            character_list.append(character)
        return character_list
    
    def player_go_to_point(self, object_name: str) -> None:
        """Event function to go to a point in the level (made for teleporting to a point on the same level).

        Args:
            object_name (str): The Object name from the Points list of objects in arcade.TiledObject.
        """
        tiledPointObjects = self.overworld.level.tile_map.object_lists["Points"]
        for obj in tiledPointObjects:
            if obj.name == object_name:
                self.overworld.player.center_x = obj.shape[0]
                self.overworld.player.center_y = obj.shape[1]
    
    def get_point(self, object_name: str) -> tuple[int, int]:
        """Event function get the point coordinates in a level (made for teleporting to a point on a different level).

        Args:
            object_name (str): The Object name from the Points list of objects in arcade.TiledObject.
        
        Returns:
            tuple[int, int]: The x, y point to go to.
        """
        tiledPointObjects = self.overworld.level.tile_map.object_lists["Points"]
        for obj in tiledPointObjects:
            if obj.name == object_name:
                return (obj.shape[0], obj.shape[1])
    
    def __repr__(self):
        return f"EventTrigger(name={self.name}, properties={self.properties}, center_x={self.center_x}, center_y={self.center_y})"

class Level:    
    def __init__(self, level_index: str, debug_events: bool = False, debug_points: bool=False):
        self.level_name = f"assets/Tiled Project/Map/overworld_level_{level_index}.json"
        self.level_index = level_index
        self.debug_events = debug_events
        self.debug_points = debug_points

        # Add layer options if needed
        self.layer_options = {}
        self.physics_engine: arcade.PhysicsEngineSimple = None
        self.tile_map: arcade.TileMap = None
        self.scene: arcade.Scene = None
        self.collidable_sprites: list[arcade.Sprite] = []
        self.event_trigger_list: list[arcade.Sprite] = arcade.SpriteList()
        self.point_list:list[arcade.Sprite] = arcade.SpriteList()
        
        self.is_loaded: bool = False  # Flag to check if level is already loaded

    def load_level(self, overworld: Overworld):
        
        if self.is_loaded: # Check to see if the level is already loaded previously
            print(f"Level {self.level_index} already loaded. Skipping reload.")
            return
        
        # Load tile map to the scene
        self.tile_map = arcade.load_tilemap(self.level_name, TILE_SCALING, self.layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        # Handle collidable layers
        for item, sprite_list in self.tile_map.sprite_lists.items():
            #print(item)
            layer_properties = getattr(sprite_list, "properties", {})
            if isinstance(layer_properties, dict) and layer_properties.get("collidable", False):
                self.collidable_sprites.append(sprite_list)

        # Add event triggers
        for tiled_object in self.tile_map.object_lists.get("Event_trigger", []):
            x, y = tiled_object.shape
            event_sprite = EventTrigger(
                "assets/character_textures/debug_point.png",
                TILE_SCALING,
                tiled_object,
                overworld
            )
            if event_sprite.name != "Enemy" and not self.debug_events:
                event_sprite.visible = False  # Debug visibility
            self.event_trigger_list.append(event_sprite)
        self.scene.add_sprite_list("eventTriggers", use_spatial_hash=True, sprite_list=self.event_trigger_list)

        # Add points
        for tiled_object in self.tile_map.object_lists.get("Points", []):
            x, y = tiled_object.shape
            point_sprite = arcade.Sprite("assets/character_textures/debug_point.png", TILE_SCALING, center_x=x, center_y=y)
            if not self.debug_points:
                point_sprite.visible = False  # Debug visibility
            self.point_list.append(point_sprite)
        self.scene.add_sprite_list("points", use_spatial_hash=True, sprite_list=self.point_list)

        # Setup physics for the level
        self.physics_engine = arcade.PhysicsEngineSimple(
            overworld.player,
            walls=self.collidable_sprites,
        )
        
        self.is_loaded = True
 
class Arena:
    def __init__(self, arena_index: str):
        self.arena_name = f"assets/Tiled Project/Map/battle_arena_{arena_index}.json"
        self.arena_index = arena_index

        # Add layer options if needed
        self.layer_options = {}

        self.tile_map: arcade.TileMap = None
        self.scene: arcade.Scene = None
        
        self.is_loaded: bool = False  # Flag to check if level is already loaded
    
    def load_arena(self) -> None:
        if self.is_loaded: # Check to see if the level is already loaded previously
            print(f"Arena {self.arena_index} already loaded. Skipping reload.")
            return
        self.tile_map = arcade.load_tilemap(self.arena_name, TILE_SCALING, self.layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.is_loaded = True

class Battle(arcade.View):
    class State(Enum):
        NOT_FINISHED  = 0
        WIN = auto()
        LOSE = auto()
    
    class TileState(Enum):
        EMPTY = 0
        PLAYER = auto()
        ALLY = auto()
        ENEMY = auto()
        ENEMY_SPAWN = auto()
        ALLY_SPAWN = auto()
    
    def __init__(self, overworld: Overworld, 
                 end_x, # x-position of where character goes after battle ends
                 end_y, # y-position of where character goes after battle ends
                 grid_size: int = 9, 
                 num_ally_spawns: int = 4,
                 num_enemy_spawns: int = 4,
                 camera_width: int = 5, 
                 camera_height: int = 5):
        super().__init__()
        # player position after end of battle
        self.end_x, self.end_y = end_x, end_y
        
        # Initialize battle cameras
        self.camera_sprites = arcade.Camera(self.window.width, self.window.height)
        self.camera_gui = arcade.Camera(self.window.width, self.window.height)
        self.camera_width = camera_width  # Fixed width of the camera in tiles
        self.camera_height = camera_height  # Fixed height of the camera in tiles

        self.battle_state: Battle.State = Battle.State.NOT_FINISHED
        
        self.player_selected_move: actor.Move = None # Gets the selected move
        
        #Get overworld instance to eventually setup arena
        self.overworld = overworld
        self.arena: Arena = None
        
        # get all tile information and characters in the battle
        self.character_list: deque[actor.Character] = deque()
        self.dead_character_list: list[actor.Character] = []
        self.grid_size = grid_size
        self.coordinates: dict[
            tuple[int, int],  # Keys are (row, col)
            dict[
                str,  # Nested dictionary keys
                Union[
                    tuple[float, float],  # Value for "tile_coord"
                    Battle.TileState,    # Value for "in_tile"
                    bool,                # Value for "mouse_highlight" (to highlight tiles the mouse is on)
                    bool,                # Value for "available_highlight" (to highlight tiles of available movements/actions)
                    bool,                # Value for "affected_tiles_highlight" (to highlight potential affected tiles from aoe)
                ]
            ]
        ] = {}
        # Spawn coordinates get populated after set_character_spawns() method finishes
        self.num_ally_spawns = num_ally_spawns
        self.num_enemy_spawns = num_enemy_spawns
        
        self.ally_spawn_tile_coordinates: list[tuple[int, int]] = [] 
        self.enemy_spawn_tile_coordinates: list[tuple[int, int]] = []
        
        self.bot_selected_move: actor.Move = None
        
        self.highlight_tile_enable: bool = False # Tile highlighting enable
        self.last_highlighted_tile: tuple[int, int] = None # Check if mouse is on the same tile
        
        self.available_movement_tiles: list[tuple[int, int]] = None
        self.available_action_tiles: list[tuple[int, int]] = None
        self.affected_tiles: list[tuple[int, int]] = None
        
        # GUI initializations 
        self.button_width: int = 200 # For button adjustments
        self.align_x=(self.window.width/2) - (self.button_width/2) - 20
        
        self.button_stack: list = [] # to know which button layout we are in
        self.main_button_layout = arcade.gui.UIBoxLayout()
        self.action_button_layout = arcade.gui.UIBoxLayout()
        self.move_button_layout = arcade.gui.UIBoxLayout()
        self.current_buttons = self.main_button_layout
        self.create_main_buttons()
        
        # Manager handles all of the player GUIs and their positions
        self.player_gui_manager: arcade.gui.UIManager = arcade.gui.UIManager()
        self.player_gui_manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                align_x=self.align_x,
                anchor_y="center_y",
                child=self.main_button_layout
            )
        )

        self.drawCharacterStats = False

        # variables to check the gui menu state
        self.show_player_interface: bool = False
        self.gui_open = False  # Whether the GUI is open
        self.mouse_over_gui = False  # Whether the mouse is over the GUI background
        self.player_interface_background_width_open = 240
        self.player_interface_background_width_closed = 30
    
    def get_player(self) -> actor.Player:
        for character in [*self.character_list, *self.dead_character_list]:
            if isinstance(character, actor.Player):
                return character
    
    def get_dead_and_alive_enemies(self) -> list[actor.Enemy]:
        enemy_list: list[actor.Enemy] = []
        for character in [*self.character_list, *self.dead_character_list]:
            if isinstance(character, actor.Enemy):
                enemy_list.append(character)
        return enemy_list
    
    def get_alive_enemies(self) -> list[actor.Enemy]:
        enemy_list: list[actor.Enemy] = []
        for character in self.character_list:
            if isinstance(character, actor.Enemy):
                enemy_list.append(character)
        return enemy_list
    
    def get_alive_allies_and_player(self) -> list[actor.Ally]:
        ally_list: list[actor.Ally | actor.Player] = []
        for character in self.character_list:
            if isinstance(character, actor.Ally) or isinstance(character, actor.Player):
                ally_list.append(character)
        return ally_list
    
    def create_main_buttons(self) -> None:
        """Create the main button layout on player turn. Consists of Action, Move, Skip, and Run buttons."""
        self.main_button_layout.clear()
        
        text = arcade.gui.UITextArea(text="Your Turn", width=self.button_width, font_size=20)
        self.action_button = arcade.gui.UIFlatButton(text="", width=self.button_width)
        self.move_button = arcade.gui.UIFlatButton(text="", width=self.button_width)
        skip_button = arcade.gui.UIFlatButton(text="Skip", width=self.button_width)
        run_away_button = arcade.gui.UIFlatButton(text="Run", width=self.button_width)

        self.action_button.on_click = self.show_action_menu
        self.move_button.on_click = self.show_move_menu
        skip_button.on_click = self.on_skip_start
        run_away_button.on_click = self.on_run_away_start

        self.main_button_layout.add(text.with_space_around(bottom=20))
        self.main_button_layout.add(self.action_button.with_space_around(bottom=20))
        self.main_button_layout.add(self.move_button.with_space_around(bottom=20))
        self.main_button_layout.add(skip_button.with_space_around(bottom=20))
        self.main_button_layout.add(run_away_button.with_space_around(bottom=20))
    
    def update_buttons_text(self):
        """Update the main button layout based on the player's remaining actions and moves."""
        player = self.character_list[0]
        self.action_button.text = f"Action ({player.attacks_left} left)"
        self.move_button.text = f"Move ({player.movements_left} left)"

    def show_action_menu(self, event: arcade.gui.UIBoxLayout) -> None:
        """Show the Action button menu."""
        #print(f"pressed action: {event}")
        player = self.character_list[0]
        if not player.attacks_left > 0:
            print(f"You have {player.attacks_left} actions left. Try a different action")
            return
        #player.attacks_left -=1
        #print(player.attacks_left)
        self.update_buttons_text()
        self.switch_to_new_buttons(self.action_button_layout, "Select an Action")
    
    def show_specific_action_menu(self, event: arcade.gui.UIBoxLayout, move: actor.Move) -> None:
        """Show the specific action button menu. For looking at available action tiles."""
        player = self.character_list[0]
        if not player.stamina >= move.stamina_cost:
            print(f"You have {player.stamina} stamina, but the move costs {move.stamina_cost}. Try a different action")
            return
        self.update_and_clear_grid_markings()
        self.highlight_tile_enable = True
        self.player_selected_move = move
        self.available_action_tiles = self.get_available_action_tiles(self.character_list[0], move)
    
    def show_move_menu(self, event: arcade.gui.UIBoxLayout) -> None:
        """Show the Move button menu."""
        player = self.character_list[0]
        if not player.movements_left > 0:
            print(f"You have {player.movements_left} movements left. Try a different action")
            return
        self.update_buttons_text()
        self.switch_to_new_buttons(self.move_button_layout, "Select a Move")
        self.highlight_tile_enable = True
        self.available_movement_tiles = self.get_available_movements()
    
    def switch_to_new_buttons(self, button_layout: arcade.gui.UIBoxLayout, title: str) -> None:
        """Switch to a new set of buttons. Make sure the player is first in the character_list queue."""        
        
        self.button_stack.append(self.current_buttons)
        self.player_gui_manager.clear()

        button_layout.clear()
        text = arcade.gui.UITextArea(text=title, width=self.button_width, font_size=17)
        button_layout.add(text.with_space_around(bottom=20))
        
        if button_layout == self.action_button_layout: # show action moves if you pressed the Action button
            player = self.character_list[0]
            for move in player.moves:
                action_button = arcade.gui.UIFlatButton(text=f"{move.name} ({move.stamina_cost})", width=self.button_width)
                action_button.on_click = lambda event, move=move: self.show_specific_action_menu(event, move)
                button_layout.add(action_button.with_space_around(bottom=20))
        
        back_button = arcade.gui.UIFlatButton(text="Back", width=self.button_width)
        back_button.on_click = self.go_back
        button_layout.add(back_button.with_space_around(bottom=20))

        self.player_gui_manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                align_x=self.align_x,
                anchor_y="center_y",
                child=button_layout
            )
        )
        self.current_buttons = button_layout

    def go_back(self, event: arcade.gui.UIBoxLayout):
        """Return to the previous button layout."""
        self.update_and_clear_grid_markings()
        if self.button_stack:
            self.player_gui_manager.clear()
            self.current_buttons = self.button_stack.pop()

            self.player_gui_manager.add(
                arcade.gui.UIAnchorWidget(
                    anchor_x="center_x",
                    align_x=self.align_x,
                    anchor_y="center_y",
                    child=self.current_buttons
                )
            )
            
            self.highlight_tile_enable = False
    
    def on_skip_start(self, event: arcade.gui.UIBoxLayout):
        """Skip button on player's turn will skip their turn."""
        #print(f"Pressed skip: {event}")
        self.show_player_interface = False
        self.gui_open = False
        self.player_gui_manager.disable()
        self.end_turn()
    
    def on_run_away_start(self, event: arcade.gui.UIBoxLayout):
        """Run away button on player's turn will bring them back to the overworld."""
        #print(f"Pressed quit: {event}")
        #print(self.arena.scene.name_mapping)

        # Transition back to overworld
        transition_view = transitionView.ToOverworldTransition(overworld=self.overworld, battle_view=self, duration=0.5)
        window = arcade.get_window()
        window.show_view(transition_view)
        
    def setup_overworld(self):
        self.overworld.setup(self.overworld.current_level_index)
        self.overworld.move_player(self.end_x, self.end_y)
        del self

    def start_turn(self) -> None:
        """cycle's through each character's turns until end conditions are met"""
        #print(f"____________________________{self.character_list[0].name}'s turn__________________________________\n")
        character: actor.Character = self.character_list[0]
        character.character_turn = True
        character.attacks_left = character.attacks_per_turn
        character.movements_left = character.movements_per_turn
        if character.stamina < character.max_stamina: # add 1 stamina per turn
            character.stamina += 1
        self.print_queue()
        if isinstance(self.character_list[0], actor.Player):
            self.show_player_interface = True
            self.update_buttons_text()
        else:
            self.bot_selected_move = self.character_list[0].lock_onto_action() # decides the bot's moves and actions
            self.bot_move() # executes the moves and actions: chains from enemy move -> attack -> end turn
    
    def bot_move(self) -> None:
        """Handle the bot character's movement."""
        character: actor.Character = self.character_list[0]
        target_tile = character.make_move() # Get the next move target
        if character.movements_left > 0 and target_tile:
            character.movements_left -= 1

            def continue_movement(): # recursive call until character cannot or does not want to move anymore
                self.bot_move()
            
            move_animation = transitionView.MoveAnimation(
                battle_view=self,
                character=character,
                target_tile=target_tile,
                next_view_callable=continue_movement if character.movements_left > 0 else self.transition_to_wait
            )
            self.window.show_view(move_animation)
        else:
            character.movements_left = 0
            self.transition_to_wait() # automatically chains to bot_action() if it has attacks left

    def bot_action(self) -> None:
        """Handle the bot character's action moves."""
        character: actor.Character = self.character_list[0]
        chosen_move_and_target_tile = character.make_action() # Get the next move target
        if character.attacks_left > 0 and chosen_move_and_target_tile:
            character.attacks_left -= 1
            
            def continue_attack():
                self.bot_action()
            
            attack_animation = transitionView.AttackAnimation(
                battle_view=self,
                character=character,
                target_tile=chosen_move_and_target_tile[1],
                move=chosen_move_and_target_tile[0],
                next_view_callable=continue_attack if character.attacks_left > 0 else self.transition_to_wait
            )
            self.highlight_tile_enable = True # Shows the affected tiles done by the enemy attack briefly
            self.window.show_view(attack_animation)
        else:
            character.attacks_left = 0
            self.transition_to_wait()
    
    def transition_to_wait(self):
        """Transition to a wait phase after the enemy finishes moving."""
        wait_transition = transitionView.WaitTransition(battle_view=self, wait_duration=1)
        self.window.show_view(wait_transition)

    def end_turn(self) -> None:
        self.update_and_clear_grid_markings()
        if self.check_end_conditions(): # transitions back to overworld if end conditions are met
            #TODO: do something with the player here when end conditions are met?
            transition_view = transitionView.ToOverworldTransition(overworld=self.overworld, battle_view=self, duration=0.5)
            window = arcade.get_window()
            window.show_view(transition_view)
            return
        self.character_list.append(self.character_list[0])
        self.character_list.popleft()
        self.start_turn()
    
    def print_queue(self) -> None:
        print("Queue:")
        for i, character in enumerate(self.character_list, 1):
            print(f"{i}. {character}\t<== Turn Start") if i == 1 else print(f"{i}. {character}")
        print()
        
    def _setup_grid(self, map_width: int, map_height: int) -> None:
        """Sets up the grid coordinates, centered in the map."""
        tile_size = 16 * TILE_SCALING
        grid_pixel_size = self.grid_size * tile_size

        # Calculate the top-left corner to start the grid from
        start_x = (map_width - grid_pixel_size) / 2
        start_y = (map_height - grid_pixel_size) / 2

        # Fill the grid with coordinates for the center of each 16x16 tile
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                
                if self.grid_size % 2 == 0: # Check if the middle in the center of one tile or four tiles
                    x = start_x + row * tile_size
                    y = start_y + col * tile_size
                else:
                    x = start_x + (row + 0.5) * tile_size
                    y = start_y + (col + 0.5) * tile_size
                #print(f"(tile_x, tile_y): {(row, col)}\t(x, y): {(x, y)}")
                #self.coordinates[(x, y)] = Battle.TileState.EMPTY
                self.coordinates[(row, col)] = {
                    "tile_coord": (x, y),
                    "in_tile": Battle.TileState.EMPTY,
                    "mouse_highlight": False,
                    "available_highlight": False,
                    "affected_tiles_highlight": False
                }
                
    def setup_arena(self) -> None:
        """Sets up a new battle to show to the screen."""
        self.arena = self.overworld.arenas[self.overworld.current_level_index]
        self.arena.load_arena()
        
        map_width = self.arena.tile_map.width * self.arena.tile_map.tile_width * TILE_SCALING
        map_height = self.arena.tile_map.height * self.arena.tile_map.tile_height * TILE_SCALING
        
        self._setup_grid(map_width, map_height)
        self._set_character_spawns(self.num_ally_spawns, self.num_enemy_spawns)
        self._place_characters_on_spawn()
                
        #for character in self.character_list:
            #if isinstance(character, actor.Player):
            #    character.allow_overworld_input = True
        #    self.arena.scene.add_sprite("characters", character)
        self.update_and_clear_grid_markings()
        self.start_turn()
        
        #print(f"Existing SpriteLists in scene: {self.arena.scene.name_mapping.keys()}")
        #if "character" in self.arena.scene.name_mapping:
        #    print(f"Existing characters: {self.arena.scene.name_mapping['character']}")

    def _set_character_spawns(self, num_ally_spawns: int, num_enemy_spawns: int):
        """Clears existing spawns and sets a given number of new spawns in random locations at the ends of the grid.

        Args:
            num_ally_spawns (int): Range from 1..grid_size-1
            num_enemy_spawn (int): Range from 1..grid_size-1
        """
        if num_ally_spawns > self.grid_size or num_enemy_spawns > self.grid_size:
            raise ValueError("Number of spawns cannot exceed grid size.")

        # Clear previous spawns
        self.ally_spawn_tile_coordinates = [] # remove ally_spawns and enemy_spawns since we may want to set spawns durng battle?
        self.enemy_spawn_tile_coordinates = []
        for tile_coord in self.coordinates.keys():
            self.coordinates[tile_coord]["in_tile"] = Battle.TileState.EMPTY

        # Generate random positions for allies on the left side of the map
        ally_y_spawn_positions = random.sample(range(self.grid_size), num_ally_spawns)
        for y in ally_y_spawn_positions:
            #print(f"ally spawn: {(0, y)}")
            self.coordinates[(0, y)]["in_tile"] = Battle.TileState.ALLY_SPAWN
            self.ally_spawn_tile_coordinates.append((0, y))

        # Generate random positions for enemies on the right side of the map
        enemy_y_spawn_positions = random.sample(range(self.grid_size), num_enemy_spawns)
        for y in enemy_y_spawn_positions:
            self.coordinates[(self.grid_size - 1, y)]["in_tile"] = Battle.TileState.ENEMY_SPAWN
            self.enemy_spawn_tile_coordinates.append((self.grid_size - 1, y))
    
    def _place_characters_on_spawn(self) -> None:
        """Allocate characters to their random available spawn points (spawn points separated by player/allies and enemies) 
        at the beginning of the grid setup.
        """
        
        # Separate character list into enemies and player/allies    
        enemies: list[actor.Enemy] = [character for character in self.character_list if isinstance(character, actor.Enemy)]
        player_and_allies: list[actor.Player | actor.Ally] = [character for character in self.character_list if isinstance(character, actor.Player | actor.Ally)]
        
        # Set player and allies to a random unique spawn point
        ally_spawn_placement_coordinates: list[tuple[int, int]] = random.sample(self.ally_spawn_tile_coordinates, len(player_and_allies))
        for i, ally_spawn_position in enumerate(ally_spawn_placement_coordinates):
            player_and_allies[i].tile_x, player_and_allies[i].tile_y = ally_spawn_position
            player_and_allies[i].center_x, player_and_allies[i].center_y = self.coordinates[ally_spawn_position]["tile_coord"]
            self.coordinates[ally_spawn_position]["in_tile"] = Battle.TileState.PLAYER if isinstance(player_and_allies[i], actor.Player) else Battle.TileState.ALLY
        
        # Set enemies to a random unique spawn point
        enemy_spawn_placement_coordinate: list[tuple[int, int]] = random.sample(self.enemy_spawn_tile_coordinates, len(enemies))
        for i, enemy_spawn_position in enumerate(enemy_spawn_placement_coordinate):
            self.coordinates[enemy_spawn_position]["in_tile"] = Battle.TileState.ENEMY
            enemies[i].tile_x, enemies[i].tile_y = enemy_spawn_position
            enemies[i].center_x, enemies[i].center_y = self.coordinates[enemy_spawn_position]["tile_coord"]
    
    def on_show_view(self):
        arcade.set_background_color(arcade.csscolor.DARK_CYAN)
        #self.setup_arena()
        #arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def summon_character(self, character: actor.Character) -> None:
        """Helps summon a character DURING battle. 
        Do NOT use add_character_to_battle() if you want to spawn characters during battle.

        Args:
            character (actor.Character): The character to summon.
        """
        
        character_copy: actor.Character = None
        if not isinstance(character, actor.Player): # TODO: add new attributes here as well if any
            character_copy = copy.deepcopy(character) # Create a new instance of the bot with the same attributes
        else:
            # Pass the player by reference instead of creating a copy
            character_copy = character
        # set character attributes on startup
        character_copy.stamina = 0
        character_copy.battle = self
        self.character_list.append(character_copy)
        #self.update_and_clear_grid_markings()
    
    def add_character_to_battle(self, character: actor.Character) -> None:
        """After creating a battle instance, populate it using this function, then start the battle using start_turn() method.

        Args:
            character (actor.Character): The character you want to put into battle.
        """
        character_copy: actor.Character = None
        if not isinstance(character, actor.Player): # TODO: add new attributes here as well if any
            character_copy = copy.deepcopy(character) # Create a new instance of the bot with the same attributes
        else:
            # Pass the player by reference instead of creating a copy
            character_copy = character
        # set character attributes on startup
        character_copy.stamina = 0
        character_copy.battle = self
        self.character_list.append(character_copy)
        self.character_list = deque(sorted(self.character_list, reverse=True))
    
    
    def add_characters_to_battle(self, characters: list[actor.Character]) -> None:
        """After creating a battle instance, populate it using this function, then start the battle using start_turn() method.

        Args:
            characters (list[Character]): The characters you want to put into battle.
        """
        if not characters:
            return
        
        character_copy: actor.Character = None
        for character in characters:
            if not isinstance(character, actor.Player): # TODO: add new attributes here as well if any
                character_copy = copy.deepcopy(character) # Create a new instance of the bot with the same attributes
            else:
                # Pass the player by reference instead of creating a copy
                character_copy = character
            # set character attributes on startup
            character_copy.stamina = 0
            character_copy.battle = self
            self.character_list.append(character_copy)
        self.character_list = deque(sorted(self.character_list, reverse=True))
    
    def on_update(self, delta_time):
        self.arena.scene.update()
        for character in self.character_list:
            character.update()
        #self.scroll_to_center()
        self.scroll_to_center()
        #self.scroll_camera_to_tile(5, 5)
        #if self.character_list:
            #print((self.character_list[0].center_x, self.character_list[0].center_y))
            #character = self.character_list[0]  # Assuming the player is the first character
            #self.scroll_camera_to_tile(9, 9)
            
    def scroll_to_center(self):
        """Scroll camera to the center of the battle arena and shifted for the ui."""
        map_width = self.arena.tile_map.width * self.arena.tile_map.tile_width * TILE_SCALING
        map_height = self.arena.tile_map.height * self.arena.tile_map.tile_height * TILE_SCALING
        position = Vec2(map_width/2 - self.window.width / 2,
                        map_height/2 - self.window.height / 2)

        self.camera_sprites.move_to(position, BATTLE_CAMERA_SPEED)
    
    def on_resize(self, width, height):
        """Resize window

        Handle the user grabbing the edge and resizing the window.
        """
        self.camera_sprites.resize(int(width), int(height))
        self.camera_gui.resize(int(width), int(height))
    
    def on_mouse_press(self, x, y, button, modifiers):
        def start_wait_transition(): # wait function
            wait_transition = transitionView.WaitTransition(battle_view=self, wait_duration=DELAY_AFTER_ANIMATION)
            self.window.show_view(wait_transition)
        if self.available_movement_tiles:
            if self.highlight_tile_enable and self.last_highlighted_tile in self.available_movement_tiles:
                player = self.character_list[0]
                player.movements_left -=1
                
                move_animation = transitionView.MoveAnimation(
                    battle_view=self,
                    character=player,
                    target_tile=self.last_highlighted_tile,
                    next_view_callable=start_wait_transition
                )
                self.window.show_view(move_animation) # Simple move animation with delay after animation complete
        elif self.available_action_tiles:
            if self.highlight_tile_enable and self.last_highlighted_tile in self.available_action_tiles:
                player = self.character_list[0]
                player.attacks_left -=1
                
                attack_animation = transitionView.AttackAnimation(
                    battle_view=self,
                    character=player,
                    target_tile=self.last_highlighted_tile,
                    move=self.player_selected_move,
                    next_view_callable=start_wait_transition
                )
                self.window.show_view(attack_animation) # Simple attack animation with delay after animation complete
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Track mouse movement and toggle GUI state based on position."""
        # Shift coordinates based on camera scrolling
        adjusted_x: float = x + self.camera_sprites.position[0]
        adjusted_y: float = y + self.camera_sprites.position[1]
        # Highlighting logic for tiles based on mouse
        if self.highlight_tile_enable:
            tile_size: float = 16 * TILE_SCALING
            current_tile: tuple[int, int] = None
            
            for (row, col), data in self.coordinates.items():
                tile_x, tile_y = data["tile_coord"]

                # Check if mouse is "touching" the tile
                if (tile_x - tile_size / 2 < adjusted_x < tile_x + tile_size / 2 and
                        tile_y - tile_size / 2 < adjusted_y < tile_y + tile_size / 2):
                    current_tile = (row, col)
                    if current_tile != self.last_highlighted_tile:
                        data["mouse_highlight"] = True
                        self.last_highlighted_tile = current_tile
                        self.clear_affected_tile_markings()
                        if not self.available_action_tiles: 
                             continue
                        if current_tile in self.available_action_tiles:
                            self.affected_tiles = self.get_affected_coordinates_from_move(self.player_selected_move, self.last_highlighted_tile)
                        #print(f"Mouse moved to new tile: {current_tile}")
                    else:
                        break
                else:
                    data["mouse_highlight"] = False
            # If the mouse is not over any tile, reset the last highlighted tile
            if current_tile is None:
                self.last_highlighted_tile = None
        
        # Player interface GUI conditions
        if not self.show_player_interface:
            self.player_gui_manager.disable()
            return
        
        gui_x_open = self.window.width - self.player_interface_background_width_open
        gui_x_closed = self.window.width - self.player_interface_background_width_closed

        # Check if the mouse is over the GUI area
        if self.gui_open:
            # GUI is open; check within expanded width
            self.mouse_over_gui = (gui_x_open <= x <= self.window.width and 0 <= y <= self.window.height)
        else:
            # GUI is closed; check within collapsed width
            self.mouse_over_gui = (gui_x_closed <= x <= self.window.width and 0 <= y <= self.window.height)

        # Open GUI if closed and mouse enters the area
        if self.mouse_over_gui and not self.gui_open:
            self.gui_open = True
            self.player_gui_manager.enable()
            

        # Close GUI if open and mouse leaves the area
        elif not self.mouse_over_gui and self.gui_open:
            self.gui_open = False
            self.player_gui_manager.disable()
        
        self.sprites_being_hovered: list[actor.Character] = []

        for character in self.character_list:
            if character.collides_with_point((adjusted_x,adjusted_y)):
                self.sprites_being_hovered.append(character)
        
        if self.sprites_being_hovered:
            self.drawCharacterStats = True
        else:
            self.drawCharacterStats = False

    def on_draw(self):
        self.clear()
        self.camera_sprites.use() # For stuff that scrolls with the map, put below here
        self.arena.scene.draw()
        for character in self.character_list:
            character.draw()
            hp_bar_color = arcade.color.GREEN if character.hp > character.max_hp * 0.5 else arcade.color.RED
            arcade.draw_rectangle_filled(character.center_x, character.center_y - 50, 60, 20, arcade.color.WHITE)
            arcade.draw_rectangle_filled(character.center_x, character.center_y - 50, 50 * (character.hp / character.max_hp), 10, hp_bar_color)
        
        # highlight tiles the mouse is on
        affected_tiles: list[tuple[int, int]] = []
        if self.highlight_tile_enable:
            width = 16 * TILE_SCALING
            for data in self.coordinates.values():
                pixel_x, pixel_y = data["tile_coord"]
                if data["mouse_highlight"]:
                    arcade.draw_rectangle_filled(pixel_x, pixel_y, width, width, (0, 0, 50, 50))
                if data["available_highlight"]:
                    arcade.draw_rectangle_outline(pixel_x, pixel_y, width, width, arcade.color.BLUE, 4)
                if data["affected_tiles_highlight"]:
                    affected_tiles.append((pixel_x, pixel_y))
                    
        # Make sure affected tiles get drawn over other tile highlights
        for tile in affected_tiles:
            arcade.draw_rectangle_outline(tile[0], tile[1], width, width, arcade.color.SKY_BLUE, 4)
        
        
        # Optionally draw the grid for debugging
        
        
        for data in self.coordinates.values():
            pixel_x, pixel_y = data["tile_coord"]
            in_tile = data["in_tile"]
            
            color: arcade.Color = None
            if in_tile == Battle.TileState.EMPTY:
                color = arcade.color.WHITE
            elif in_tile == Battle.TileState.PLAYER:
                color = arcade.color.BLUE
            elif in_tile == Battle.TileState.ALLY:
                color = arcade.color.GREEN
            elif in_tile == Battle.TileState.ALLY_SPAWN:
                color = arcade.color.GREEN_YELLOW
            elif in_tile == Battle.TileState.ENEMY:
                color = arcade.color.RED
            elif in_tile == Battle.TileState.ENEMY_SPAWN:
                color = arcade.color.RED_BROWN
            else:
                color = arcade.color.BLACK
            if SEE_GRID_POINTS:
                arcade.draw_point(pixel_x, pixel_y, color, 2 * TILE_SCALING)  # Draw grid points
        
        if self.drawCharacterStats is True:
            character = self.sprites_being_hovered[0]
            arcade.draw_rectangle_outline(self.camera_sprites.position[0], self.camera_sprites.position[1], 475, 250, arcade.color.BLACK)
            arcade.draw_rectangle_filled(self.camera_sprites.position[0], self.camera_sprites.position[1], 475, 250, arcade.color.GRAY)
            arcade.draw_text(f"Name: {character.name}", self.camera_sprites.position[0] + 20, self.camera_sprites.position[1] + 80, arcade.color.WHITE, 12)
            arcade.draw_text(f"HP: {character.hp}/{character.max_hp}", self.camera_sprites.position[0] + 20, self.camera_sprites.position[1] + 60, arcade.color.WHITE, 12)
            arcade.draw_text(f"Stamina: {character.stamina}/{character.max_stamina}", self.camera_sprites.position[0] + 20, self.camera_sprites.position[1] + 40, arcade.color.WHITE, 12)


        self.camera_gui.use() # For guis, put below here
        if self.gui_open:
            # Draw expanded GUI background
            arcade.draw_rectangle_filled(
                center_x=self.window.width - self.player_interface_background_width_open / 2,
                center_y=self.window.height / 2,
                width=self.player_interface_background_width_open,
                height=self.window.height,
                color=arcade.color.GRAY
            )
            self.player_gui_manager.draw()
        else:
            # Draw collapsed GUI background
            arcade.draw_rectangle_filled(
                center_x=self.window.width - self.player_interface_background_width_closed / 2,
                center_y=self.window.height / 2,
                width=self.player_interface_background_width_closed,
                height=self.window.height,
                color=arcade.color.GRAY
            )
    
    def on_resize(self, width, height):
        self.camera_sprites.resize(int(width), int(height))
        self.camera_gui.resize(int(width), int(height))
    
    def get_characters_left(self) -> list[int]:
        """Counting instances of Player, Ally, and Enemy in the character list. We need to check this for end conditions

        Returns:
            list[int]: returns the number of players, enemies, and allies left, respectively
        """
        num_players: int = sum(1 for character in self.character_list if isinstance(character, actor.Player)) # generators are so fricking cool
        num_enemies: int = sum(1 for character in self.character_list if isinstance(character, actor.Enemy))
        num_allies: int = sum(1 for character in self.character_list if isinstance(character, actor.Ally))
        
        return [num_players, num_enemies, num_allies]
    
    def check_end_conditions(self) -> bool:
        """Ends the battle if end conditions are met. ie: No player left, no enemies left"""
        if self.get_characters_left()[1] == 0: # No enemies left
            print("End battle, player team killed all enemies") # TODO: Add gold, droprate chance (also have transition)
            self.battle_state = Battle.State.WIN
            self.get_enemy_drops()
            
            return True
        elif self.get_characters_left()[0] == 0: # No player left
            print("End battle, player has died") # TODO: take gold?
            self.battle_state = Battle.State.LOSE
            for character in self.dead_character_list: # give the player small hp on death
                if isinstance(character, actor.Player):
                    character.hp = 5
            return True
        elif self.get_characters_left()[2] == 0: # No allies left
            #print("No allies left, keep playing though")
            pass
        return False
    
    def get_enemy_drops(self) -> None:
        """Gets money from enemiees and calculates drop chances."""
        # Add enemy money to player
        player: actor.Player = self.get_player()
        enemies: list[actor.Enemy] = self.get_dead_and_alive_enemies()
        for enemy in enemies:
            player.money += enemy.money

        # Roll drops
        for enemy in enemies:
            for drop_chance, move in enemy.loot:
                chance = random.random()
                if not chance <= drop_chance: # roll odds
                    continue
                if move in player.moves: # check if player has it
                    continue
                print(f"You got a new move: {move=} from {enemy=}")
                player.moves.append(move)

    
    def clear_affected_tile_markings(self) -> None:
        for coord in self.coordinates.keys():
            self.coordinates[coord]["affected_tiles_highlight"] = False
            
    def update_and_clear_grid_markings(self) -> None:
        """Update character positions and clears available movement/action tile highlights."""
        self.available_movement_tiles = None
        self.available_action_tiles = None
        self.highlight_tile_enable = False
        self.player_selected_move = None
        self.affected_tiles = None
        
        for coord in self.coordinates.keys():
            self.coordinates[coord]["mouse_highlight"] = False
            self.coordinates[coord]["available_highlight"] = False
            self.coordinates[coord]["affected_tiles_highlight"] = False
            if coord in self.ally_spawn_tile_coordinates:
                self.coordinates[coord]["in_tile"] = Battle.TileState.ALLY_SPAWN
            elif coord in self.enemy_spawn_tile_coordinates:
                self.coordinates[coord]["in_tile"] = Battle.TileState.ENEMY_SPAWN
            else:
                self.coordinates[coord]["in_tile"] = Battle.TileState.EMPTY
        
        # Place characters on the grid based on their updated positions
        dead_characters: list[actor.Character] = []
        for character in self.character_list:
            if 0 <= character.tile_x < self.grid_size and 0 <= character.tile_y < self.grid_size: # Check if in bounds
                #character.visible = True # show all alive characters
                if character.hp <= 0: # Check for dead characters
                    dead_characters.append(character)
                    continue
                if isinstance(character, actor.Player):
                    self.coordinates[(character.tile_x, character.tile_y)]["in_tile"] = Battle.TileState.PLAYER
                elif isinstance(character, actor.Ally):
                    self.coordinates[(character.tile_x, character.tile_y)]["in_tile"] = Battle.TileState.ALLY
                elif isinstance(character, actor.Enemy):
                    self.coordinates[(character.tile_x, character.tile_y)]["in_tile"] = Battle.TileState.ENEMY
                character.center_x, character.center_y = self.coordinates[(character.tile_x, character.tile_y)]["tile_coord"]
            else:
                print(f"{character} is out of bounds.")
        self.remove_dead_characters(dead_characters)
    
    def remove_dead_characters(self, dead_characters: list[actor.Character]) -> None:
        """Gets rid of a "dead" character from the queue and adds it to the dead list"""
        for character in dead_characters:
            self.coordinates[(character.tile_x, character.tile_y)]["in_tile"] = Battle.TileState.EMPTY
            self.character_list.remove(character)
            self.character_list = deque(self.character_list)
            self.dead_character_list.append(character)
            if character.hp <= -10:
                print(f"{character} got fricking obliterated!!")
            else:
                print(f"{character} has died!")
    
    def get_potential_target_coords_from_ranged(self, target_move: Move, target_character: actor.Character) -> list[tuple[int, int]]:
        """Show the potential target spaces of the enemy with a ranged fighting style by using the target.

        Returns:
            list[tuple[int, int]]: a list of available coordinates that the character can move to.
        """
        # List of obstacles that prevent available movement (player, ally, and enemy). Add more if needed
        obstacle_list: list[Battle.TileState] = [Battle.TileState.PLAYER, Battle.TileState.ALLY, Battle.TileState.ENEMY]
        
        character = target_character
        attack_range_max: int = target_move.max_range
        attack_range_min: int = target_move.min_range
        character_x: int = character.tile_x
        character_y: int = character.tile_y
        
        available_coordinates: list[tuple[int, int]] = []
        
        # Check left available spaces
        for dx in range(-attack_range_min, -attack_range_max - 1, -1):
            available_x = character_x + dx
            if not available_x >= 0: # check bounds
                break
            if self.coordinates[(available_x, character_y)]["in_tile"] in obstacle_list: # you cannot move on top of a character nor passed him
                break
            self.coordinates[(available_x, character_y)]["available_highlight"] = True
            available_coordinates.append((available_x, character_y))
        
        # Check right available spaces
        for dx in range(attack_range_min, attack_range_max + 1, 1):
            available_x = character_x + dx
            if not available_x < self.grid_size: # check bounds
                break
            if self.coordinates[(available_x, character_y)]["in_tile"] in obstacle_list:
                break
            self.coordinates[(available_x, character_y)]["available_highlight"] = True
            available_coordinates.append((available_x, character_y))
        
        # Check bottom available spaces
        for dy in range(-attack_range_min, -attack_range_max - 1, -1):
            available_y = character_y + dy
            if not available_y >= 0: # check bounds
                break
            if self.coordinates[(character_x, available_y)]["in_tile"] in obstacle_list:
                break
            self.coordinates[(character_x, available_y)]["available_highlight"] = True
            available_coordinates.append((character_x, available_y))
            
        # check top available spaces
        for dy in range(attack_range_min, attack_range_max + 1, 1):
            available_y = character_y + dy
            if not available_y < self.grid_size: # check bounds
                break
            if self.coordinates[(character_x, available_y)]["in_tile"] in obstacle_list:
                break
            self.coordinates[(character_x, available_y)]["available_highlight"] = True
            available_coordinates.append((character_x, available_y))
        
        return available_coordinates
    
    def get_available_movements(self) -> list[tuple[int, int]]:
        """Update and show available movement spaces that the character can go to on the grid.

        #Returns:
        #    list[tuple[int, int]]: a list of available coordinates that the character can move to
        """
        # List of obstacles that prevent available movement (player, ally, and enemy). Add more if needed
        obstacle_list: list[Battle.TileState] = [Battle.TileState.PLAYER, Battle.TileState.ALLY, Battle.TileState.ENEMY]
        
        character = self.character_list[0]
        move_range: int = character.move_range
        character_x: int = character.tile_x
        character_y: int = character.tile_y
        
        available_coordinates: list[tuple[int, int]] = []
        
        # Check left available spaces
        for dx in range(-1, -move_range - 1, -1):
            available_x = character_x + dx
            if not available_x >= 0: # check bounds
                break
            if self.coordinates[(available_x, character_y)]["in_tile"] in obstacle_list: # you cannot move on top of a character nor passed him
                break
            self.coordinates[(available_x, character_y)]["available_highlight"] = True
            available_coordinates.append((available_x, character_y))
        
        # Check right available spaces
        for dx in range(1, move_range + 1, 1):
            available_x = character_x + dx
            if not available_x < self.grid_size: # check bounds
                break
            if self.coordinates[(available_x, character_y)]["in_tile"] in obstacle_list:
                break
            self.coordinates[(available_x, character_y)]["available_highlight"] = True
            available_coordinates.append((available_x, character_y))
        
        # Check bottom available spaces
        for dy in range(-1, -move_range - 1, -1):
            available_y = character_y + dy
            if not available_y >= 0: # check bounds
                break
            if self.coordinates[(character_x, available_y)]["in_tile"] in obstacle_list:
                break
            self.coordinates[(character_x, available_y)]["available_highlight"] = True
            available_coordinates.append((character_x, available_y))
            
        # check top available spaces
        for dy in range(1, move_range + 1, 1):
            available_y = character_y + dy
            if not available_y < self.grid_size: # check bounds
                break
            if self.coordinates[(character_x, available_y)]["in_tile"] in obstacle_list:
                break
            self.coordinates[(character_x, available_y)]["available_highlight"] = True
            available_coordinates.append((character_x, available_y))
        
        
        return available_coordinates
    
    def get_available_action_tiles(self, character: actor.Character, move: actor.Move) -> list[tuple[int, int]]:
        """Update and show available attack spaces that the character can attack on the grid.

        Args:
            character (Character): The character to see the available attack spaces of.
            move (Move): The move to show the available attacks of.
            
        Returns:
            list[tuple[int, int]]: a list of available coordinates that the character can perform their attack
        """
        # Use the target attribute for for the move itself
        obstacle_list: list[Battle.TileState] = [] # List of characters which do not get affected and will also block the attack vision
        target_list: list[Battle.TileState] = [] # Similar to obstacle_list, but the target can get affected by the move
        
        # Add targeting logic for player depending on the move's type and target_obstacles
        # Note that the implementation for targeting yourself is separate and is used later on
        if isinstance(character, actor.Player) or isinstance(character, actor.Ally): 
            if move.target_obstacles == move.ObstaclesEnum.ALLIES_AND_PLAYER: 
                obstacle_list.append(Battle.TileState.ALLY)
                obstacle_list.append(Battle.TileState.PLAYER)
            elif move.target_obstacles == move.ObstaclesEnum.ENEMIES:
                obstacle_list.append(Battle.TileState.ENEMY)
            elif move.target_obstacles == move.ObstaclesEnum.ALL:
                obstacle_list.append(Battle.TileState.ALLY)
                obstacle_list.append(Battle.TileState.PLAYER)
                obstacle_list.append(Battle.TileState.ENEMY)

            if move.target_character == move.MoveTargetEnum.ENEMIES:
                target_list.append(Battle.TileState.ENEMY)
            elif move.target_character == move.MoveTargetEnum.ALLIES_AND_PLAYER:
                target_list.append(Battle.TileState.ALLY)
                target_list.append(Battle.TileState.PLAYER)
            elif move.target_character == move.MoveTargetEnum.ALL:
                target_list.append(Battle.TileState.ENEMY)
                target_list.append(Battle.TileState.ALLY)
                target_list.append(Battle.TileState.PLAYER)
        elif isinstance(character, actor.Enemy):
            if move.target_obstacles == move.ObstaclesEnum.ALLIES_AND_PLAYER: 
                obstacle_list.append(Battle.TileState.ENEMY)
            elif move.target_obstacles == move.ObstaclesEnum.ENEMIES:
                obstacle_list.append(Battle.TileState.ALLY)
                obstacle_list.append(Battle.TileState.PLAYER)
            elif move.target_obstacles == move.ObstaclesEnum.ALL:
                obstacle_list.append(Battle.TileState.ENEMY)
                obstacle_list.append(Battle.TileState.ALLY)
                obstacle_list.append(Battle.TileState.PLAYER)
            
            if move.target_character == move.MoveTargetEnum.ENEMIES:
                target_list.append(Battle.TileState.ALLY)
                target_list.append(Battle.TileState.PLAYER)
            elif move.target_character == move.MoveTargetEnum.ALLIES_AND_PLAYER:
                target_list.append(Battle.TileState.ENEMY)
            elif move.target_character == move.MoveTargetEnum.ALL:
                target_list.append(Battle.TileState.ENEMY)
                target_list.append(Battle.TileState.ALLY)
                target_list.append(Battle.TileState.PLAYER)
        else:
            raise Exception("Given unexcpected type of character instance")
        
        character_x: int = character.tile_x
        character_y: int = character.tile_y
        min_range: int = move.min_range
        max_range: int = move.max_range
        
        available_coordinates: list[tuple[int, int]] = []
        
        # highlight all tiles. Don't include tiles in obstacle list that aren't in target list
        if move.stat_effect in [move.StatEffect.GLOBAL_DAMAGE, move.StatEffect.GLOBAL_HEAL, move.StatEffect.GLOBAL_LIFESTEAL]:
            for (row, col), data in self.coordinates.items():
                if data["in_tile"] in obstacle_list and data["in_tile"] not in target_list:
                    continue
                data["available_highlight"] = True
                available_coordinates.append((row, col))
            return available_coordinates
        
        # Check if you can target yourself
        if move.target_self:
            self.coordinates[(character_x, character_y)]["available_highlight"] = True
            available_coordinates.append((character_x, character_y))
        
        if move.max_range == 0: # Leave if move has no range
            return available_coordinates
        
        # Check left available spaces
        for dx in range(-min_range, -max_range - 1, -1):
            available_x = character_x + dx
            if not available_x >= 0: # check bounds
                break
            value_at_coordinate: Battle.TileState = self.coordinates[(available_x, character_y)]["in_tile"]
            if value_at_coordinate in target_list: # check if a potential character at the coord is in the target list
                self.coordinates[(available_x, character_y)]["available_highlight"] = True
                available_coordinates.append((available_x, character_y))
                if value_at_coordinate in obstacle_list: # Make sure you also check obstacle list
                    break
            if value_at_coordinate in obstacle_list: # you cannot move passed any obstacle characters
                break
            else:
                self.coordinates[(available_x, character_y)]["available_highlight"] = True
                available_coordinates.append((available_x, character_y))
        
        # Check right available spaces
        for dx in range(min_range, max_range + 1, 1):
            available_x = character_x + dx
            if not available_x < self.grid_size: # check bounds
                break
            value_at_coordinate: Battle.TileState = self.coordinates[(available_x, character_y)]["in_tile"]
            if value_at_coordinate in target_list:
                self.coordinates[(available_x, character_y)]["available_highlight"] = True
                available_coordinates.append((available_x, character_y))
                if value_at_coordinate in obstacle_list:
                    break
            elif value_at_coordinate in obstacle_list:
                break
            else:
                self.coordinates[(available_x, character_y)]["available_highlight"] = True
                available_coordinates.append((available_x, character_y))
        
        #print(f"target_list: {target_list}\nobstacle_list: {obstacle_list}")
        # Check bottom available spaces
        for dy in range(-min_range, -max_range - 1, -1):
            available_y = character_y + dy
            #print(f"{self.coordinates[(character_x, available_y)]}\tx, y = {character_x, character_y}")
            if not available_y >= 0: # check bounds
                break
            value_at_coordinate: Battle.TileState = self.coordinates[(character_x, available_y)]["in_tile"]
            if value_at_coordinate in target_list:
                self.coordinates[(character_x, available_y)]["available_highlight"] = True
                available_coordinates.append((character_x, available_y))
                if value_at_coordinate in obstacle_list:
                    break
            elif value_at_coordinate in obstacle_list:
                break
            else:
                self.coordinates[(character_x, available_y)]["available_highlight"] = True
                available_coordinates.append((character_x, available_y))
        
        # check top available spaces
        for dy in range(min_range, max_range + 1, 1):
            available_y = character_y + dy
            if not available_y < self.grid_size: # check bounds
                break
            value_at_coordinate: Battle.TileState = self.coordinates[(character_x, available_y)]["in_tile"]
            if value_at_coordinate in target_list:
                self.coordinates[(character_x, available_y)]["available_highlight"] = True
                available_coordinates.append((character_x, available_y))
                if value_at_coordinate in obstacle_list:
                    break
            if value_at_coordinate in obstacle_list:
                break
            else:
                self.coordinates[(character_x, available_y)]["available_highlight"] = True
                available_coordinates.append((character_x, available_y))
        
        return available_coordinates

    def get_affected_coordinates_from_move(self, move: actor.Move, tile_coordinate: tuple[int, int]) -> list[tuple[int, int]]:
        """Get all coordinates which would be affected from an attack performed at x, y. 
        Assumes the first in the character list is using the move.

        Args:
            move (actor.Move): The move being used.
            tile_coordinate (tuple[int, int]): The coordinate at which the move is being used.

        Returns:
            list[tuple[int, int]]: _description_
        """
        
        #move: Move = character.moves[move_to_use_index]
        obstacle_list: list[Battle.TileState] = [] # List of characters which do not get affected and will also block the attack vision
        target_list: list[Battle.TileState] = [] # Similar to obstacle_list, but the target can get affected by the move
        character = self.character_list[0]
        # Add targeting logic for player depending on the move's type and target_obstacles
        # Note that the implementation for targeting yourself is separate and is used later on
        if isinstance(character, actor.Player) or isinstance(character, actor.Ally): 
            if move.target_obstacles == move.ObstaclesEnum.ALLIES_AND_PLAYER: 
                obstacle_list.append(Battle.TileState.ALLY)
                obstacle_list.append(Battle.TileState.PLAYER)
            elif move.target_obstacles == move.ObstaclesEnum.ENEMIES:
                obstacle_list.append(Battle.TileState.ENEMY)
            elif move.target_obstacles == move.ObstaclesEnum.ALL:
                obstacle_list.append(Battle.TileState.ALLY)
                obstacle_list.append(Battle.TileState.PLAYER)
                obstacle_list.append(Battle.TileState.ENEMY)

            if move.target_character == move.MoveTargetEnum.ENEMIES:
                target_list.append(Battle.TileState.ENEMY)
            elif move.target_character == move.MoveTargetEnum.ALLIES_AND_PLAYER:
                target_list.append(Battle.TileState.ALLY)
                target_list.append(Battle.TileState.PLAYER)
            elif move.target_character == move.MoveTargetEnum.ALL:
                target_list.append(Battle.TileState.ENEMY)
                target_list.append(Battle.TileState.ALLY)
                target_list.append(Battle.TileState.PLAYER)
        elif isinstance(character, actor.Enemy):
            if move.target_obstacles == move.ObstaclesEnum.ALLIES_AND_PLAYER: 
                obstacle_list.append(Battle.TileState.ENEMY)
            elif move.target_obstacles == move.ObstaclesEnum.ENEMIES:
                obstacle_list.append(Battle.TileState.ALLY)
                obstacle_list.append(Battle.TileState.PLAYER)
            elif move.target_obstacles == move.ObstaclesEnum.ALL:
                obstacle_list.append(Battle.TileState.ENEMY)
                obstacle_list.append(Battle.TileState.ALLY)
                obstacle_list.append(Battle.TileState.PLAYER)
            
            if move.target_character == move.MoveTargetEnum.ENEMIES:
                target_list.append(Battle.TileState.ALLY)
                target_list.append(Battle.TileState.PLAYER)
            elif move.target_character == move.MoveTargetEnum.ALLIES_AND_PLAYER:
                target_list.append(Battle.TileState.ENEMY)
            elif move.target_character == move.MoveTargetEnum.ALL:
                target_list.append(Battle.TileState.ENEMY)
                target_list.append(Battle.TileState.ALLY)
                target_list.append(Battle.TileState.PLAYER)
        else:
            raise Exception("Given unexcpected type of character subclass")
        
        
        min_range: int = 1
        max_range: int = move.aoe_range
        
        available_coordinates: list[tuple[int, int]] = []
        (attack_x, attack_y) = tile_coordinate
        
        # check if attack is global
        if move.stat_effect in [move.StatEffect.GLOBAL_DAMAGE, move.StatEffect.GLOBAL_HEAL, move.StatEffect.GLOBAL_LIFESTEAL]:
            for (row, col), data in self.coordinates.items():
                if data["in_tile"] in target_list:
                    data["affected_tiles_highlight"] = True
                    available_coordinates.append((row, col))
            return available_coordinates
        
        
        #character_x: int = character.x
        #character_y: int = character.y
        
        # Add the spot you attacked to the list
        #if self.coordinates[(attack_x, attack_y)]["in_tile"] in target_list:
        #    self.coordinates[(attack_x, attack_y)]["affected_tiles_highlight"] = True
        #else:
        #    self.coordinates[(attack_x, attack_y)]["affected_tiles_highlight"] = False
        self.coordinates[(attack_x, attack_y)]["affected_tiles_highlight"] = True
        available_coordinates.append((attack_x, attack_y))
        
        if max_range == 0: # Leave if move has no AOE range
            return available_coordinates
        
        # Check left available spaces
        for dx in range(-min_range, -max_range - 1, -1):
            available_x = attack_x + dx
            if not available_x >= 0: # check bounds
                break
            value_at_coordinate: Battle.TileState = self.coordinates[(available_x, attack_y)]["in_tile"]
            if value_at_coordinate in target_list:
                self.coordinates[(available_x, attack_y)]["affected_tiles_highlight"] = True
                available_coordinates.append((available_x, attack_y))
                if value_at_coordinate in obstacle_list:
                    break
            if value_at_coordinate in obstacle_list: # you cannot move on top of a character nor passed him
                break
            else:
                self.coordinates[(available_x, attack_y)]["affected_tiles_highlight"] = True
                available_coordinates.append((available_x, attack_y))
        
        # Check right available spaces
        for dx in range(min_range, max_range + 1, 1):
            available_x = attack_x + dx
            if not available_x < self.grid_size: # check bounds
                break
            value_at_coordinate: Battle.TileState = self.coordinates[(available_x, attack_y)]["in_tile"]
            if value_at_coordinate in target_list:
                self.coordinates[(available_x, attack_y)]["affected_tiles_highlight"] = True
                available_coordinates.append((available_x, attack_y))
                if value_at_coordinate in obstacle_list:
                    break
            if value_at_coordinate in obstacle_list:
                break
            else:
                self.coordinates[(available_x, attack_y)]["affected_tiles_highlight"] = True
                available_coordinates.append((available_x, attack_y))
        
        # Check bottom available spaces
        for dy in range(-min_range, -max_range - 1, -1):
            available_y = attack_y + dy
            if not available_y >= 0: # check bounds
                break
            value_at_coordinate: Battle.TileState = self.coordinates[(attack_x, available_y)]["in_tile"]
            if value_at_coordinate in target_list:
                self.coordinates[(attack_x, available_y)]["affected_tiles_highlight"] = True
                available_coordinates.append((attack_x, available_y))
                if value_at_coordinate in obstacle_list:
                    break
            if value_at_coordinate in obstacle_list:
                break
            else:
                self.coordinates[(attack_x, available_y)]["affected_tiles_highlight"] = True
                available_coordinates.append((attack_x, available_y))
            
        # check top available spaces
        for dy in range(min_range, max_range + 1, 1):
            available_y = attack_y + dy
            if not available_y < self.grid_size: # check bounds
                break
            value_at_coordinate: Battle.TileState = self.coordinates[(attack_x, available_y)]["in_tile"]
            if value_at_coordinate in target_list:
                self.coordinates[(attack_x, available_y)]["affected_tiles_highlight"] = True
                available_coordinates.append((attack_x, available_y))
                if value_at_coordinate in obstacle_list:
                    break
            if value_at_coordinate in obstacle_list:
                break
            else:
                self.coordinates[(attack_x, available_y)]["affected_tiles_highlight"] = True
                available_coordinates.append((attack_x, available_y))
        
        # if you cannot target yourself, then aoe will not affect you
        if (character.tile_x, character.tile_y) in available_coordinates and move.target_self == False:
            if isinstance(character, actor.Player):
                self.coordinates[(character.tile_x, character.tile_y)]["affected_tiles_highlight"] = False # TODO: not sure if this is right
            elif isinstance(character, actor.Enemy):
                self.coordinates[(character.tile_x, character.tile_y)]["affected_tiles_highlight"] = False
            elif isinstance(character, actor.Ally):
                self.coordinates[(character.tile_x, character.tile_y)]["affected_tiles_highlight"] = False
            else:
                raise Exception("Unexcpected character instance given")
            available_coordinates.remove((character.tile_x, character.tile_y))
        
        return available_coordinates

    def is_tile_occupied(self, coord: tuple[int, int]) -> bool:
        if self.coordinates[coord]["in_tile"] == Battle.TileState.EMPTY:
            return False
        return True
        
class InstructionView(arcade.View):
    def __init__(self):
        super().__init__()

    def on_show_view(self):
        arcade.set_background_color(arcade.csscolor.DARK_CYAN)
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def on_draw(self):
        self.clear()
        arcade.draw_text("Main Menu", self.window.width / 2, self.window.height/2,
                         arcade.color.WHITE, font_size=50, anchor_x="center")
        arcade.draw_text("Click to Start", self.window.width / 2, self.window.height/2 -100,
                         arcade.color.WHITE, font_size=50, anchor_x="center")
        
    def on_mouse_press(self, _x, _y, _button, _modifiers):
        overworld_view = Overworld()
        overworld_view.setup(0)
        self.window.show_view(overworld_view)

class InputTracker(dict):
    """Using this to track the status of each key. Functionally just a dictionary, but instead
    of throwing `KeyError` on a bad fetch, it adds the key and sets its value to `False` instead. 
    """
    # this is the [] access operator function
    def __getitem__(self, key):
        if key not in self:
            self[key] = False
        return super().__getitem__(key)

if __name__ == "__main__":