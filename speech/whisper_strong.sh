#!/bin/bash
# A script to run Whisper with strong transcription settings
each -- whisper --model large-v2 --language English --output_format txt --beam_size 5 --best_of 5 --patience 1.0 : "$@"
