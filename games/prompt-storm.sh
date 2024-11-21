#!/usr/bin/env bash
# Convert the Australian Curriculum into game dev projects
# Mathematical Methods Units 1, 2, 3, 4

model= m=c # LLM model to use
game_ref= g=000  # game reference
unit= u=

eval "$(ally)"

cat-named $game_ref/*.py unit$unit.md |
process -m="$model" "Let's plan a series of educational game dev projects, to help the 16yo student student have fun, learn programming and game dev, and revise his year 11 math (which he has completed). Currently he is a beginner programmer, but he will have help from me, his dad, an expert programmer, and we will also use AI to help. Rather than jumping straight to complete game or demo ideas, let's first do a brainstorm, and list all the programming and especially game / demo dev applications we can think of for each mathematical concept or skill. For example, quadratics can be used to model trajectories, draw parabolic mirrors, adjust volume louder and softer over a piece of music or sound effect, draw hills and valleys, I'm sure there are many others. Proportion can be used to map input sliders to colour component values, or generally adjust a function's range to fit another's domain. To draw bigger or smaller shapes, stretch them, to calculate scores, etc. An inverse function might be used to make a creature move more slowly as it grows larger, to calculate gravitational attraction, speed vs time taken, benchmark rate vs frequency, etc. Let's come up with lots of good ideas we can for how to apply each concept, including beginner, intermediate and more advanced ideas. No idea is 'bad' in a brainstorm, just write it down and continue on. We are looking more for general techniques, not so much detailed game concepts, at this stage. Although if you have a good one, please do note it down\!

The output format could be like this. (Please do give me your idea for ACMMM001 in addition to the others)

1. ACMMM001: Determine the coordinates of the midpoint of two points (ACMMM001).
  a. centroid of a triangle
  b. balance point
  c. sierpinski gasket
  d. avarage of two colours (line 3d points)
  e. moving averages
  f. creature chases the user (slight variations with weighted mean, or normalised vector)
  g. blend two audio waveforms (1d average, but relevant)
  h. average / centroid of more than 2 points
  i. draw 3d grids with weighted averages of lines
  j. splines as blends of two lines
  k. a timer that warns when half time is up (1d again)
  l. what does average of sin and cos look like?  try in 2d with circular motion at different rates

2. ACMMM002: etc..." | tee storm$unit-$model.md
