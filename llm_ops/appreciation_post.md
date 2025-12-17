# Appreciation post: Helldivers 2 optimization

Refactoring legacy code is akin to live-service game patches: high risk of 'game-breaking' outages, but gains in operations. 

A game studios recently debloated their installed data size while keeping everything operational.

This is an appreciation post for an optimization task done by Arrowhead Game Studios on the game Helldivers 2.

## TLDR;
They reduced the installed file size from **150+ GB** to a mere **25 GB** by purely optimizing their assets.

Ref link: [Helldivers 2 Update Notes](https://store.steampowered.com/news/app/553850/view/543369627969783286?l=english)

## The problem with live service games
As a live service game, Helldivers 2 announcements are closely followed by thousands—if not hundreds of thousands of players. The game easily reaches a peak active player count of 150,000 during major season releases.

Many players, including me, who play less frequently, often complain that we sit down to enjoy the game only to get frustrated by a pending update that's 20+ GB in size. 
This is very *off-putting* and a major problem for the gaming studio. Players like me would simply step away instead of waiting several hours for the update. As a result, publishers lose dollars that we could have spent in that session.

If updates are frequent, large and buggy - the player base takes note and remembers. Why we will always respect a lot of indie devs but not Bethesda as much as before.

## The solution: a surprising optimization
Arrowhead studios, the makers of the Helldivers series, turned the tables in their recent patch. No one following their release notes expected to see a reduction in the game's file size!

I got curious and did some digging:
1. They employed an external partner, Nixxes, to identify duplicate assets (redundant files) and de-duplicate the game data.
2. They then merged assets across various use cases and created common repositories where the assets would reside.

This was not really refactoring but more of reorganizing. The clever part is that this is rarely done for live service games. Oh boy, isn't our ServiceDesk Plus doing something similar by moving existing systems into custom modules :wink:

## Why this is is rare in game, live service or not.
Because:
- Live service games have rolling updates, and new assets are added each season.
- Developers hardly touch older assets or attempt to optimize them.
- Instead, they focus on simply adding the new season's releases, which massively bloats the file system.
- However, they simply keep what works and sunset functions or features that get the least interaction from the player base.

Therefore, they never really find the time or spend the effort to re-base their file systems and create common asset repositories.

## Technical insights
Reading the release notes also explains why duplication was needed earlier: HDDs are more efficient for sequential reads, whereas SSDs handle random access better and do not have such concerns.

But with a common asset library, there is a high chance of unwanted assets being loaded into the RAM because the library contains them. However, their release notes also talk about making assets modular down the line.

For example, making 4K texture packs as optional and opt-in downloads. That would make further space savings because I barely render 4K on my modest 3060ti graphics card.

## An inspiring approach
What I found really wonderful and inspiring is that this approach- spending the time and effort for housekeeping existing code is something that is rarely seen. But it can lead to tremendous results when executed right, much like the strategic refactoring decisions our product teams need to make to ensure scalable, efficient product.

Spending time with the our platform team and other products that have started to build platform layers themselves only further validates this effort that we are taking to make our products a cohesive ecosystem.

And taking risks like this is truly commendable because a single *game-breaking* bug can chase the entire player (or customers) base away. Yet bold actions make headlines.