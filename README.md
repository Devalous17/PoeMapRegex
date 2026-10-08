# MapRegex

**A map search helper for Path of Exile 1.**

MapRegex turns your Path of Building character into a starting point for a map regex. It looks at the build's damage, defenses, recovery, and resources, then highlights map modifiers that may cause trouble. You choose which modifiers to avoid and copy the resulting search text into Path of Exile.

## How it works

1. **Import your build.** Paste a `pobb.in` link or a Path of Building export code.
2. **Choose your comfort level.** Safe avoids more troublesome modifiers, Balanced avoids the more serious ones, and Greedy avoids only modifiers rated Brick.
3. **Review the modifiers.** Search the map modifier database and click a modifier to change whether you want to avoid it. Your choices take priority over the preset.
4. **Set your map preferences.** Add a minimum or maximum for values such as Item Quantity or Pack Size, and choose any map state or rarity filters you want.
5. **Copy the regex.** The search text updates as you make changes. Paste it into your map stash search in game.

You can switch between **Normal** and **Nightmare** maps. Each has its own modifier list and choices.

## What the ratings mean

| Rating | Meaning |
| --- | --- |
| **Brick** | The modifier appears to interfere with something the build depends on. |
| **Dangerous** | A strong risk for this build. |
| **Uncomfortable** | Playable, but likely to feel worse. |
| **Free** | No significant issue was identified by the available rules. |
| **Review** | MapRegex does not have enough information to judge it for this build. |

The ratings are suggestions based on the saved build. Check the highlighted modifiers and make the final call yourself: a PoB export cannot show every in-game condition or guarantee that a map is safe.

MapRegex is a fan-made tool and is not affiliated with or endorsed by Grinding Gear Games.
