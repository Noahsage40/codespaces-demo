# Holiday "Rank 1–10" Snapchat Lenses 🎄🦃

These work like the ranking lens in your example. A card above your head shuffles and then stops on a picture. You tap a number from 1 to 10 to place it there, and a new card shuffles in. Pictures never repeat in one round. Once all 10 numbers are filled, tap again to start over.

There are **25 ready-made lenses** with **394 cards**: 13 Christmas and 12 Thanksgiving. Each lens has 14–18 cards, so a round only uses 10 of them and every video turns out different.

## What's in here

| Path | What it is |
|---|---|
| `lenses/<lens-name>/*.jpg` | The card images for each lens (512×512) |
| `lens-studio/RankingLens.js` | The script that runs the shuffle, the tap-to-rank and the reset |
| `lens-studio/number-strip.png` | The column of 1–10 number boxes on the left side |
| `tools/categories.json` | Every list. Edit it to add your own items |
| `tools/render_cards.js` | Rebuilds every card image after you edit the lists |

## The lenses

| | Lens | Folder | Cards | Examples |
|---|---|---|---|---|
| 🎄 | **Christmas Movies** | `lenses/christmas-movies/` | 18 | Home Alone, Elf, The Polar Express, The Grinch, A Christmas Story, … |
| 🎄 | **Christmas Characters** | `lenses/christmas-characters/` | 18 | Santa Claus, Mrs. Claus, Rudolph, Frosty the Snowman, The Grinch, … |
| 🎄 | **Christmas Songs** | `lenses/christmas-songs/` | 18 | All I Want for Christmas Is You, Last Christmas, Jingle Bell Rock, Rockin' Around the Christmas Tree, Feliz Navidad, … |
| 🎄 | **Christmas Treats** | `lenses/christmas-treats/` | 17 | Sugar Cookies, Gingerbread Men, Candy Canes, Peppermint Bark, Fudge, … |
| 🎄 | **Christmas Traditions** | `lenses/christmas-traditions/` | 16 | Opening One Gift on Christmas Eve, Matching Family PJs, Elf on the Shelf, Cookies for Santa, Advent Calendar, … |
| 🎄 | **Christmas Gifts** | `lenses/christmas-gifts/` | 18 | Socks, Gift Card, Wireless Earbuds, Lump of Coal, A Puppy, … |
| 🎄 | **Family Christmas Chaos** | `lenses/family-christmas-chaos/` | 16 | Dad Fighting the Lights, Burnt Cookies, Dog Ate the Ham, The Tree Fell Over, Batteries Not Included, … |
| 🎄 | **Christmas Villains** | `lenses/christmas-villains/` | 15 | The Grinch, The Wet Bandits, Hans Gruber, Krampus, Ebenezer Scrooge, … |
| 🎄 | **Christmas Decorations** | `lenses/christmas-decorations/` | 16 | The Christmas Tree, Tinsel, Giant Inflatable Santa, Nativity Scene, Mistletoe, … |
| 🎄 | **Christmas Drinks** | `lenses/christmas-drinks/` | 14 | Hot Cocoa, Eggnog, Peppermint Mocha, Mulled Wine, Apple Cider, … |
| 🎄 | **Winter Activities** | `lenses/winter-activities/` | 15 | Building a Snowman, Ice Skating, Sledding, Snowball Fight, Skiing, … |
| 🎄 | **North Pole Jobs** | `lenses/north-pole-jobs/` | 15 | Toy Tester, Reindeer Trainer, Naughty List Manager, Gift Wrapper, Cookie Taste Tester, … |
| 🎄 | **Christmas Dinner** | `lenses/christmas-dinner/` | 15 | Honey Glazed Ham, Prime Rib, Turkey Round Two, Lasagna, Tamales, … |
| 🦃 | **Thanksgiving Sides** | `lenses/thanksgiving-sides/` | 17 | Mashed Potatoes, Stuffing, Mac & Cheese, Green Bean Casserole, Canned Cranberry Sauce, … |
| 🦃 | **Thanksgiving Desserts** | `lenses/thanksgiving-desserts/` | 15 | Pumpkin Pie, Apple Pie, Pecan Pie, Sweet Potato Pie, Cheesecake, … |
| 🦃 | **Thanksgiving Family Members** | `lenses/thanksgiving-family-members/` | 15 | The Uncle Who Talks Politics, Aunt Asking About Your Love Life, Cousin with a New Partner Every Year, Grandma Saying You Look Skinny, The One Who Shows Up Late, … |
| 🦃 | **Thanksgiving Traditions** | `lenses/thanksgiving-traditions/` | 15 | The Parade, Football Games, Saying What You're Thankful For, Breaking the Wishbone, Food Coma Nap, … |
| 🦃 | **Leftover Creations** | `lenses/leftover-creations/` | 15 | The Turkey Sandwich, Stuffing Waffles, Turkey Pot Pie, Thanksgiving Burrito, Leftover Nachos, … |
| 🦃 | **Ways to Cook a Turkey** | `lenses/turkey-styles/` | 15 | Classic Roasted, Deep Fried, Smoked, Turducken, Spatchcocked, … |
| 🦃 | **Thanksgiving Table Topics** | `lenses/thanksgiving-table-topics/` | 15 | Politics, Your Relationship Status, "When Are You Getting a Real Job?", Your Grades, Who's Hosting Christmas, … |
| 🦃 | **Things I'm Thankful For** | `lenses/thankful-for/` | 16 | Family, Friends, Food, Pets, Wi-Fi, … |
| 🦃 | **Thanksgiving Drinks** | `lenses/thanksgiving-drinks/` | 14 | Apple Cider, Pumpkin Spice Latte, Sweet Tea, Hot Mulled Cider, Cranberry Spritzer, … |
| 🦃 | **Fall Vibes** | `lenses/fall-vibes/` | 15 | Pumpkin Patch, Corn Maze, Hayride, Bonfire, Apple Picking, … |
| 🦃 | **Black Friday Hauls** | `lenses/black-friday-hauls/` | 16 | Giant Doorbuster TV, Air Fryer, New Sneakers, Video Game, Game Console, … |
| 🦃 | **After Dinner Moves** | `lenses/after-dinner-moves/` | 15 | Unbuttoning Your Pants, The Couch Nap, Second Plate, Third Plate, Hiding in the Bathroom, … |

## Build a lens in Lens Studio (about 10 minutes)

Use the free **Lens Studio 5** for Mac or Windows from ar.snap.com. You make one Lens Studio project per category. After the first one, use **File → Save As** and swap in the next folder of cards.

1. **New project.** Choose **Blank Project** and keep the front camera.
2. **Import the files.** Drag `RankingLens.js`, `number-strip.png` and every `.jpg` from one lens folder (for example `lenses/christmas-movies/`) into the **Asset Browser**.
3. **Head card**
   - In the Scene Hierarchy, click **+** and add **Head Binding**.
   - Right-click **Head Binding**, choose **Add Child**, then add an **Image**. Name it **Head Card**.
   - Set its texture to any card. Move it **up about 18** on Y so it sits above your forehead, then scale it to roughly the size in your example. Check the result in the Preview panel.
4. **Number column**
   - Click **+**, then **Screen Image**. Name it **Number Strip** and set its texture to `number-strip.png`.
   - In the Inspector, set Stretch Mode to **Fit**. Pin it to the **left** edge with a size of about **12% of the width × 72% of the height**, below the top bar. This matches your example.
5. **Script**
   - Click **+**, then **Scene Object**, and name it **Ranking Game**.
   - In the Inspector, click **Add Component → Script** and choose `RankingLens.js`.
   - Fill in the fields:
     - **Cards:** select all the `.jpg` files in the Asset Browser and drag them onto the list.
     - **Head Card Image:** the Head Card object.
     - **Number Strip:** the Number Strip object.
     - Optionally, add a short tick or pop sound for the shuffle and for placing a card.
6. **Test.** Click inside the Preview panel to tap a number. Then use **Send to Snapchat** to try it on your phone.
7. **Publish.** Click **Publish Lens** and give it a name such as "Rank Christmas Movies 🎄". Use a lens icon (any card works) and a short preview video of yourself playing it.

**Tuning:** Shuffle Time sets how long it spins (1.2 seconds by default). Flip Speed sets how fast the pictures flash. Picture Padding In Box sets how far the placed picture sits inside each number box.

## Using real photos instead (like the Taylor Swift card)

The included cards are original designs: a big title plus emoji. You can drop **any** square images into the Cards list instead, such as movie posters or character photos, and the script works the same. Just know that Snap may reject a lens that uses copyrighted photos or celebrity images when you publish it publicly. The included cards avoid that problem.

## Add or edit lists

Edit `tools/categories.json`. Each item is `["Card Title", "emoji"]`. Then run:

```
npm install playwright   # only once
node tools/render_cards.js
```
