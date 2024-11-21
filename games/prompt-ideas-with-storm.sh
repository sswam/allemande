#!/usr/bin/env bash
# Convert the Australian Curriculum into game dev projects
# Mathematical Methods Units 1, 2, 3, 4

model= m=c # LLM model to use
game_ref= g=000  # game reference
unit= u=

eval "$(ally)"

cat-named $game_ref/*.py unit$unit.md storm$unit-combo.md |
process -m="$model" "Let's plan a series of educational game dev projects, to help the 16yo student student have fun, learn programming and game dev, and revise his year 11 math (which he has completed). Currently he is a beginner programmer, but he will have help from me, his dad, an expert programmer, and we will also use AI to help. Each game idea should use at least one mathematical concept or skill from the curriculum, e.g. ACMMM001. We should try to follow the curriculum order. Games should use some previously learned concepts from earlier in the curriculum, and we should try to revise all concepts a few times in this way. Each game or demo should be interesting or fun in some way, and can use graphics, music, sound, and other programming concepts. As we progress with the math concepts, the student should also learn more and more programming concepts and skills. For example, we should start of simple with expressions, control flow, functions, etc; and hopefully progress to such heights as files, sprites and vector graphics, colour mixing, audio synthesis, physical simulation, cellular automata, web requests, asyncio, audio and video recording, AI APIS, local AI, deep learning, etc. It is fine to include material from other subjects such as physics, bio, psychology, etc, and fine to use other python libs from pypi (gradually as we progress). What I am looking for now, is a list of three creative game or demo ideas for each point in the curriculum, starting with ACMMM001. Please try for a simple or minimal demo idea, a more elaborate demo or simple game, and a fun / weird / out-there / surprising game idea. As we progress we will build on our user friendly game libraries, which you see attached (this is the starting point), while hopefully keeping the game code itself pretty clean and simple. We will have our own project ideas too, of course, but your contribution will be invaluable as a starting point. Maybe note a few of the new programming skills used beside each project too. Thanks so much\!

The output format could be like this:

1. ACMMM001: Determine the coordinates of the midpoint of two points (ACMMM001).
  a. Draw a random line in blue, and mark its center with a small red circle. [coordinates, random, line, color, circle, arithmetic]
  b. Draw a yellow triangle filled dark green, its corners can be dragged, and show how the medians always meet at the centroid. [more colors, NPC objects]
  c. Three animated monsters move around and sometimes chase your line's endpoints (marked by small circles). Every 3s the line briefly becomes visible as two angled red lasers. Catch monsters with the center where lasers meet, but don't let them reach the endpoints or you lose. Monsters occasionally attempt to win. [sprites, clock, perpendicular, if, logic]

2. ACMMM002: etc..." | tee ideas$unit-storm-$model.md
