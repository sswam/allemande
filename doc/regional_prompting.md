# Regional Prompting Guide

A guide for using the Regional Prompter extension to create images with different prompts in different regions.

## Basic Structure

Regional prompts follow this pattern:

1. `[rp]` to activate regional prompting (with optional settings)
2. `[sets ...]` for image settings
3. Common prompt followed by `ADDCOMM`
4. Base prompt and LoRAs followed by `ADDBASE`
5. Region prompts separated by `ADDCOL` and `ADDROW`

## Modes

### Matrix Mode

Split the image into a grid of regions:

```
[rp ratios=1,2,1,1;2,3,2,1]  # Creates 2 rows x 3 columns
first prompt ADDCOL
second prompt ADDCOL
third prompt ADDROW
fourth prompt ADDCOL
fifth prompt ADDCOL
sixth prompt
```

The first number in each row is the row height ratio.
The next numbers are the column width ratios.

### Rows Mode

Split into horizontal rows:

```
[rp mode=rows ratios="2;1;1"]  # Creates 3 rows
top prompt ADDROW
middle prompt ADDROW
bottom prompt
```

## Special Keywords

- `ADDCOMM`: Marks common prompt applied to all regions
- `ADDBASE`: Marks base prompt (weighted differently)
- `ADDCOL`: Separates columns in a row
- `ADDROW`: Starts a new row
- `NEGATIVE`: Starts negative prompt section

## Example Prompts

### Simple Two-Person Scene
```
[rp] couple, 2girls, holding hands, flower garden ADDCOMM
<lora:add-detail-xl:1> ADDBASE
[person Ally] ADDCOL
[person Barbie]
```

### Complex Group Scene
```
[rp] [sets width=1344 height=768 steps=30 hq=1.5]
(rating safe, group picture) ADDCOMM
<lora:add-detail-xl:1> ADDBASE
(tall alien) ADDCOL
(furry creature) ADDCOL
(floating jellyfish) ADDCOL
(1girl human) ADDCOL
(reptilian being)
```

### Landscape with Sky
```
[rp ratios=1,4,1;1,1;1,1]
masterpiece ADDCOMM
<lora:boring:-1> ADDBASE
sky, cloud ADDCOL
sky, sun ADDROW
1boy lying on grass ADDROW
grass
```

## Settings

### Ratios Format
- Single row/column: `ratios="1,2,1"`
- Matrix: `ratios="1,2,1;2,3,2"`
  - first number is row height, others are column width
- In rows mode: `ratios=1;2;1,2;3;2`
- With flip option: Add `flip` to rotate 90°, swaps the meaning of `,` and `;`

### Base Ratios
- Controls strength of base vs regional prompts
- Default: 0.2 (20% base, 80% region)
- Can specify per region: `base_ratios="0.3,0.2,0.4"`

## Tips

- Keep base prompts general, use regions for specifics
- Match total regions to ratio specifications
- Use quality tags in common section
- Place all LoRAs in the base section only
- Objects are not strictly constrained to their boxes.
- People, creatures or objects might merge across boxes, e.g. making a horse / cow hybrid rather than two animals!
  - To avoid this for people, try e.g. `couple`, `2girls`, `NEGATIVE solo`

## Example Results

The above prompts can create:
- Two-person scenes with distinct characteristics
- Complex group shots with varied creatures
- Layered landscapes with sky and ground elements
