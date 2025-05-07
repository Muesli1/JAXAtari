import os
from functools import partial
from typing import NamedTuple, Tuple
import jax.lax
import jax.numpy as jnp
import chex
import pygame
from gymnax.environments import spaces

from jaxatari.rendering import atraJaxis as aj
from jaxatari.environment import JaxEnvironment




# Player constant y positions
PLAYER_Y = 96




# Pygame window dimensions
WINDOW_WIDTH = 160 *3
WINDOW_HEIGHT = 210 *3

WIDTH = 160 *3
HEIGHT = 210 *3

WALL_X  = 160 
PLAYER_SIZE_X = 4  
PLAYER_SIZE_Y = 16   
PLAYER_SPEED = 1    

# Player Digging time
DIGGING_F1_TIME = 2
DIGGING_F2_TIME = 4

# Gopher walking time
GOPHER_F1_TIME = 2
GOPHER_F2_TIME = 4

# Bird flying time
BIRD_F1_TIME = 2
BIRD_F2_TIME = 4
BIRD_F3_TIME = 4

# Action constants
NOOP = 0
FIRE = 1
RIGHT = 2
LEFT = 3


def get_keyboard_action(keys, digging) -> chex.Array:
    if keys[pygame.K_LEFT]:
        return jnp.array(LEFT)
    elif keys[pygame.K_RIGHT]:
        return jnp.array(RIGHT)
    elif digging:
        return jnp.array(FIRE)    
    else:
        return jnp.array(NOOP)




def load_sprites():

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


    player = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/player.npy"), transpose=True)
    player_digging1 = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/player_digging1.npy"), transpose=True)
    player_digging2 = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/player_digging2.npy"), transpose=True)
    player_lose = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/player_lose.npy"), transpose=True)
    
    gopher_walk1 = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/gopher_walk1.npy"), transpose=True)
    gopher_walk2 = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/gopher_walk2.npy"), transpose=True)
    gopher_up = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/gopher_up.npy"), transpose=True)
    gopher_watch1 = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/gopher_watch1.npy"), transpose=True)
    gopher_watch2 = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/gopher_watch2.npy"), transpose=True)

    bird_wing_top = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/bird_wing_top.npy"), transpose=True)
    bird_wing_middle = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/bird_wing_middle.npy"), transpose=True)
    bird_wing_bottom = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/bird_wing_bottom.npy"), transpose=True)

    seed_grain = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/seed_grain.npy"), transpose=True)
    seed_grain_drop = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/seed_grain_drop.npy"), transpose=True)

    carrot = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/carrot.npy"), transpose=True)

    block = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/block.npy"), transpose=True)
    block_up = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/block_up.npy"), transpose=True)

    bg = aj.loadFrame(os.path.join(MODULE_DIR, "sprites/gopher/background.npy"), transpose=True)




    SPRITE_BG = jnp.expand_dims(bg, axis=0)
    SPRITE_PLAYER = jnp.expand_dims(player, axis=0)
    SPRITE_BG = jnp.expand_dims(bg, axis=0)
    SPRITE_PLAYER = jnp.expand_dims(player, axis=0)
    SPRITE_PLAYER_DIGGING1 = jnp.expand_dims(player_digging1, axis=0)
    SPRITE_PLAYER_DIGGING2 = jnp.expand_dims(player_digging2, axis=0)
    SPRITE_PLAYER_LOSE = jnp.expand_dims(player_lose, axis=0)
    SPRITE_GOPHER_WALK1 = jnp.expand_dims(gopher_walk1, axis=0)
    SPRITE_GOPHER_WALK2 = jnp.expand_dims(gopher_walk2, axis=0)
    SPRITE_GOPHER_UP = jnp.expand_dims(gopher_up, axis=0)
    SPRITE_GOPHER_WATCH1 = jnp.expand_dims(gopher_watch1, axis=0)
    SPRITE_GOPHER_WATCH2 = jnp.expand_dims(gopher_watch2, axis=0)
    SPRITE_BIRD_WING_TOP = jnp.expand_dims(bird_wing_top, axis=0)
    SPRITE_BIRD_WING_MID = jnp.expand_dims(bird_wing_middle, axis=0)
    SPRITE_BIRD_WING_BOTTOM = jnp.expand_dims(bird_wing_bottom, axis=0)
    SPRITE_SEED_GRAIN = jnp.expand_dims(seed_grain, axis=0)
    SPRITE_SEED_GRAIN_DROP = jnp.expand_dims(seed_grain_drop, axis=0)
    SPRITE_CARROT = jnp.expand_dims(carrot, axis=0)
    SPRITE_BLOCK = jnp.expand_dims(block, axis=0)
    SPRITE_BLOCK_UP = jnp.expand_dims(block_up, axis=0)

    SPRITES_SCORES = aj.load_and_pad_digits(
        os.path.join(MODULE_DIR, "sprites/gopher/score_{}.npy"),
        num_chars=10,
    )



    return (
        SPRITE_BG,
        SPRITE_PLAYER,
        SPRITE_PLAYER_DIGGING1,
        SPRITE_PLAYER_DIGGING2,
        SPRITE_PLAYER_LOSE,
        SPRITE_GOPHER_WALK1,
        SPRITE_GOPHER_WALK2,
        SPRITE_GOPHER_UP,
        SPRITE_GOPHER_WATCH1,
        SPRITE_GOPHER_WATCH2,
        SPRITE_BIRD_WING_TOP,
        SPRITE_BIRD_WING_MID,
        SPRITE_BIRD_WING_BOTTOM,
        SPRITE_SEED_GRAIN,
        SPRITE_SEED_GRAIN_DROP,
        SPRITE_CARROT,
        SPRITE_BLOCK,
        SPRITE_BLOCK_UP,
        SPRITES_SCORES 
    )




# immutable state container
class GopherState(NamedTuple):
    player_x: chex.Array
    player_is_digging: chex.Array
    player_digging_counter: chex.Array
    gopher_x: chex.Array
    gopher_y: chex.Array
    gopher_walking_counter: chex.Array
    gopher_is_walking_up:  chex.Array
    gopher_is_watching: chex.Array
    gopher_watching_counter: chex.Array
    











class GopherGame():
    #konstruktor Funktion
    def __init__(self):
        super().__init__()

    

    def init_game(self) -> GopherState:

        state = GopherState(
            player_x=jnp.array(96).astype(jnp.int32),
            player_is_digging=jnp.array(0.0).astype(jnp.int32),
            player_digging_counter=jnp.array(0.0).astype(jnp.int32),
            gopher_x = jnp.array(0.0).astype(jnp.int32),
            gopher_y= jnp.array(0.0).astype(jnp.int32),
            gopher_walking_counter=   jnp.array(0.0).astype(jnp.int32),
            gopher_is_walking_up=   jnp.array(0.0).astype(jnp.int32),
            gopher_is_watching=   jnp.array(0.0).astype(jnp.int32),
            gopher_watching_counter=    jnp.array(0.0).astype(jnp.int32)
        )

        return state



    @partial(jax.jit, static_argnums=(0,))
    def next_game_step(self, state: GopherState, action: chex.Array)-> Tuple[GopherState]:

        # Rechts rennen (action == 2)
        player_x = state.player_x
        player_x_new = jax.lax.cond(
          action == 2,
          lambda x: jnp.clip(player_x + PLAYER_SPEED, 0, WALL_X),  
          # Links rennen (action == 3)
          lambda x: jax.lax.cond(
              action == 3,
              lambda x: jnp.clip(player_x - PLAYER_SPEED, 0, WALL_X), 
              lambda x: player_x,  
              operand=action
          ),
          operand=action
        )
        



        player_digging_counter = state.player_digging_counter
        player_is_digging= state.player_is_digging

        player_digging_counter_new, player_is_digging_new = jax.lax.cond(
            player_is_digging,
            lambda x: jax.lax.cond(
                         player_digging_counter < (DIGGING_F1_TIME + DIGGING_F2_TIME),
                         lambda x: (x + 1, True),
                         lambda x: (0,False),
                         operand=player_digging_counter
                         ),
            lambda x: jax.lax.cond(
                         (action == 1),
                         lambda x: (1, True),
                         lambda x: (0, False),
                         operand=None
                         ),
            operand=None)
    



        gopher_x_new  =  jax.lax.cond(
                     True,
                     lambda x: 0,
                     lambda x: 0,
                     operand=None
                     )

        gopher_y_new =   jax.lax.cond(
                     True,
                     lambda x: 0,
                     lambda x: 0,
                     operand=None
                     )

        gopher_walking_counter_new =   jax.lax.cond(
                     True,
                     lambda x: 0,
                     lambda x: 0,
                     operand=None
                     )

        gopher_is_walking_up_new =   jax.lax.cond(
                     True,
                     lambda x: 0,
                     lambda x: 0,
                     operand=None
                     )

        gopher_is_watching_new =  jax.lax.cond(
                     True,
                     lambda x: 0,
                     lambda x: 0,
                     operand=None
                     )

        gopher_watching_counter_new =   jax.lax.cond(
                         True,
                         lambda x: 0,
                         lambda x: 0,
                         operand=None
                         )


        new_state = GopherState(
            player_x=player_x_new,
            player_is_digging=player_is_digging_new,
            player_digging_counter = player_digging_counter_new,
            gopher_x =  gopher_x_new,
            gopher_y= gopher_y_new,
            gopher_walking_counter=   gopher_walking_counter_new,
            gopher_is_walking_up=     gopher_is_walking_up_new,
            gopher_is_watching=     gopher_is_watching_new,
            gopher_watching_counter=    gopher_watching_counter_new
        )
        return new_state









class Renderer_AtraJaxisGopherGame:

    def __init__(self):
        (
        self.SPRITE_BG,
        self.SPRITE_PLAYER,
        self.SPRITE_PLAYER_DIGGING1,
        self.SPRITE_PLAYER_DIGGING2,
        self.SPRITE_PLAYER_LOSE,
        self.SPRITE_GOPHER_WALK1,
        self.SPRITE_GOPHER_WALK2,
        self.SPRITE_GOPHER_UP,
        self.SPRITE_GOPHER_WATCH1,
        self.SPRITE_GOPHER_WATCH2,
        self.SPRITE_BIRD_WING_TOP,
        self.SPRITE_BIRD_WING_MID,
        self.SPRITE_BIRD_WING_BOTTOM,
        self.SPRITE_SEED_GRAIN,
        self.SPRITE_SEED_GRAIN_DROP,
        self.SPRITE_CARROT,
        self.SPRITE_BLOCK,
        self.SPRITE_BLOCK_UP,
        self.SPRITES_SCORES 
        ) = load_sprites()


    
    @partial(jax.jit, static_argnums=(0,))
    def render(self, state:GopherState):
        
        raster = jnp.zeros((WIDTH, HEIGHT, 3))

        frame_bg = aj.get_sprite_frame(self.SPRITE_BG, 0)

        raster = aj.render_at(raster, 0, 0, frame_bg)

        frame_player = jax.lax.cond(
            state.player_is_digging,
            lambda x: jax.lax.cond(
                  state.player_digging_counter <  DIGGING_F1_TIME,
                   lambda x: aj.get_sprite_frame(self.SPRITE_PLAYER_DIGGING1, 0), 
                   lambda x: aj.get_sprite_frame(self.SPRITE_PLAYER_DIGGING2, 0),
                   operand=None
                   ), 
            lambda x:  aj.get_sprite_frame(self.SPRITE_PLAYER, 0),
            operand=None
        )

        raster = aj.render_at(raster, PLAYER_Y, state.player_x, frame_player)


        return raster


















pygame.init()

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

pygame.display.set_caption("Gopher Game")

clock = pygame.time.Clock()

game_is_runing = True

gopher_game = GopherGame()
gopher_renderer = Renderer_AtraJaxisGopherGame()

jitted_game_init = jax.jit(gopher_game.init_game)
jitted_next_game_step = jax.jit(gopher_game.next_game_step)

gopher_game_state = jitted_game_init()

is_pressed = True
action = jnp.array(NOOP)

while game_is_runing:
        digging = False
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                game_is_runing = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    digging = True


        
        keys = pygame.key.get_pressed()
        action = get_keyboard_action(keys, digging)  
        gopher_game_state = jitted_next_game_step(gopher_game_state,action)

        raster = gopher_renderer.render(gopher_game_state)
        aj.update_pygame(screen, raster, 3, WIDTH, HEIGHT)
        clock.tick(60)

pygame.quit()



