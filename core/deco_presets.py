import os
import json

DECO_PRESET_FILE = "decoration_presets.json"

def load_deco_presets():
    p = {}
    if os.path.exists(DECO_PRESET_FILE):
        try:
            with open(DECO_PRESET_FILE, "r") as f:
                p = json.load(f)
        except Exception:
            pass

    dirty = False

    new_defaults = {
        "Default_Village": {
            "num_bands": 3,
            "bands": [
                {"dist": 3, "blocks": "cobblestone:70, mossy_cobblestone:30"},
                {"dist": 6, "blocks": "dirt_path:80, coarse_dirt:20", "top_prob": 0.05, "top_blocks": "lantern[hanging=false]:100"},
                {"dist": 12, "blocks": "grass_block:100", "top_prob": 0.15, "top_blocks": "poppy:30, dandelion:30, cornflower:40"}
            ]
        },
        "Deep_Forest": {
            "redstone_band": {"enabled": True, "blocks": "spruce_log[axis=y]:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 3,
            "bands": [
                {"dist": 3, "blocks": "moss_block:80, rooted_dirt:20", "top_prob": 0.2, "top_blocks": "fern:70, large_fern[half=lower]:30"},
                {"dist": 7, "blocks": "podzol:60, coarse_dirt:40", "top_prob": 0.05, "top_blocks": "campfire[lit=true,facing=north]:50, brown_mushroom:50"},
                {"dist": 14, "blocks": "grass_block:100", "top_prob": 0.1, "top_blocks": "spruce_sapling:30, sweet_berry_bush[age=3]:70"}
            ]
        },
        "Desert_Oasis": {
            "num_bands": 3,
            "bands": [
                {"dist": 3, "blocks": "cut_sandstone:70, chiseled_sandstone:30"},
                {"dist": 8, "blocks": "sand:70, smooth_sandstone:30", "top_prob": 0.05, "top_blocks": "dead_bush:100"},
                {"dist": 15, "blocks": "sand:90, red_sand:10", "top_prob": 0.1, "top_blocks": "cactus[age=5]:30, red_tulip:70"}
            ]
        },
        "Crimson_Fortress": {
            "redstone_band": {"enabled": True, "blocks": "magma_block:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 3,
            "bands": [
                {"dist": 3, "blocks": "polished_blackstone_bricks:70, cracked_polished_blackstone_bricks:30", "top_prob": 0.1, "top_blocks": "soul_lantern[hanging=false]:100"},
                {"dist": 7, "blocks": "crimson_nylium:80, netherrack:20", "top_prob": 0.2, "top_blocks": "crimson_roots:60, crimson_fungus:40"},
                {"dist": 15, "blocks": "netherrack:90, soul_soil:10", "top_prob": 0.05, "top_blocks": "fire[age=0]:100"}
            ]
        },
        "Ancient_City": {
            "redstone_band": {"enabled": True, "blocks": "sculk_catalyst:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 3,
            "bands": [
                {"dist": 4, "blocks": "polished_deepslate:80, deepslate_tiles:20", "top_prob": 0.0, "top_blocks": ""},
                {"dist": 9, "blocks": "sculk:100", "top_prob": 0.3, "top_blocks": "sculk_sensor[sculk_sensor_phase=active]:30, sculk_shrieker[can_summon=false]:10, sculk_vein[up=true]:60"},
                {"dist": 15, "blocks": "deepslate:70, cobbled_deepslate:30", "top_prob": 0.0, "top_blocks": ""}
            ]
        },
        "Amethyst_Geode": {
            "num_bands": 4,
            "bands": [
                {"dist": 2, "blocks": "smooth_basalt:100"},
                {"dist": 5, "blocks": "calcite:100"},
                {"dist": 10, "blocks": "amethyst_block:80, budding_amethyst:20", "top_prob": 0.3, "top_blocks": "amethyst_cluster[facing=up]:40, large_amethyst_bud[facing=up]:30, medium_amethyst_bud[facing=up]:30"},
                {"dist": 14, "blocks": "tuff:100"}
            ]
        },
        "Warped_Magic": {
            "redstone_band": {"enabled": True, "blocks": "pearlescent_froglight[axis=y]:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 3,
            "bands": [
                {"dist": 4, "blocks": "warped_planks:80, stripped_warped_stem[axis=y]:20"},
                {"dist": 9, "blocks": "warped_nylium:100", "top_prob": 0.25, "top_blocks": "warped_roots:50, nether_sprouts:30, warped_fungus:20"},
                {"dist": 15, "blocks": "blackstone:60, obsidian:40"}
            ]
        },
        "Cherry_Grove": {
            "num_bands": 4,
            "bands": [
                {"dist": 3, "blocks": "cherry_planks:70, stripped_cherry_log[axis=y]:30", "top_prob": 0.1, "top_blocks": "pink_candle[candles=3,lit=true]:100"},
                {"dist": 6, "blocks": "dirt_path:100", "top_prob": 0.0, "top_blocks": ""},
                {"dist": 11, "blocks": "moss_block:60, grass_block:40", "top_prob": 0.5, "top_blocks": "pink_petals[flower_amount=4,facing=north]:40, pink_petals[flower_amount=2,facing=south]:40, cherry_sapling:20"},
                {"dist": 18, "blocks": "grass_block:100", "top_prob": 0.1, "top_blocks": "peony[half=lower]:50, lilac[half=lower]:50"}
            ]
        },
        "Lush_Glow": {
            "redstone_band": {"enabled": True, "blocks": "shroomlight:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 4,
            "bands": [
                {"dist": 3, "blocks": "ochre_froglight[axis=y]:20, moss_block:80", "top_prob": 0.0, "top_blocks": ""},
                {"dist": 8, "blocks": "moss_block:100", "top_prob": 0.4, "top_blocks": "flowering_azalea:40, azalea:40, spore_blossom:20"},
                {"dist": 13, "blocks": "rooted_dirt:60, moss_block:40", "top_prob": 0.15, "top_blocks": "big_dripleaf[facing=north,tilt=none]:100"},
                {"dist": 18, "blocks": "tuff:60, stone:40", "top_prob": 0.0, "top_blocks": ""}
            ]
        }
    }

    for key, data in new_defaults.items():
        if key not in p:
            p[key] = data
            dirty = True

    if dirty:
        with open(DECO_PRESET_FILE, "w") as f:
            json.dump(p, f, indent=4)
    return p

def save_deco_presets(p):
    with open(DECO_PRESET_FILE, "w") as f:
        json.dump(p, f, indent=4)
