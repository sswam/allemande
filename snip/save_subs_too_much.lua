--  If the script is working for some videos but not others, even though they all have soft subtitles, there could be a few reasons for this. Here are some suggestions to troubleshoot and potentially improve the script:
--
--  1. Check subtitle track selection:
--     Make sure the correct subtitle track is selected. Some videos might have multiple subtitle tracks.
--
--  2. Handle different subtitle formats:
--     Some videos might use different subtitle formats or encodings. Try adding support for different encodings.
--
--  3. Add error handling:
--     Implement error handling to catch and log any issues that might occur during subtitle extraction.
--
--  4. Use a different method to capture subtitles:
--     Instead of observing the "sub-text" property, you could try using the "on_osd" event to capture subtitles.
--
--  Here's an updated version of the script that incorporates these suggestions:

-- ~/.config/mpv/scripts/save_subs.lua

-- Thank you for providing that detailed script and explanation. It seems you've already implemented several advanced techniques to try to capture subtitles in different scenarios. 
-- 
-- Given that you can manually turn the subtitles on and off, but the script still isn't detecting them, here are a few additional things to consider:
-- 
-- 1. Rendered Subtitles:
--    As you mentioned, the subtitles might be rendered into the video stream. These are sometimes called "hard subs" or "burned-in subs". In this case, they're part of the video image itself and not a separate text track that can be easily extracted.
-- 
-- 2. Image-based Subtitles:
--    Some subtitle formats (like PGS used in Blu-rays) are image-based rather than text-based. These might not be detected by text-based extraction methods.
-- 
-- 3. DRM or Encryption:
--    If the video is from a streaming service, the subtitles might be encrypted or protected in some way that prevents easy extraction.
-- 
-- 4. Custom Subtitle Rendering:
--    Some players or video formats might use custom methods to render subtitles that don't trigger the standard subtitle events or properties.
-- 
-- To further diagnose the issue:
-- 
-- 1. Check Subtitle Format:
--    Use mpv's OSD (on-screen display) to check what type of subtitle track is being used. Press the 'O' key (capital o) while playing to cycle through OSD modes until you see technical information about the video and audio tracks.
-- 
-- 2. Try External Tools:
--    Use a tool like FFprobe to analyze the video file and see what subtitle streams are present:
--    ```
--    ffprobe -v quiet -print_format json -show_format -show_streams your_video_file.mp4
--    ```
-- 
-- 3. Test with Different Videos:
--    Try the script with videos from different sources to see if the issue is specific to certain video types or sources.
-- 
-- 4. Debug Logging:
--    Add more debug logging to your script to print out information about detected subtitle tracks and when subtitle text is (or isn't) being captured.
-- 
-- 5. Check mpv Version:
--    Ensure you're using a recent version of mpv, as subtitle handling can sometimes change between versions.
-- 
-- If none of these approaches work, you might need to consider alternative methods for capturing the subtitles, such as OCR (Optical Character Recognition) on the video frames themselves, though this would be significantly more complex to implement.


local utils = require 'mp.utils'
local sub_file = nil
local sub_filename = "subtitles.txt"

local function open_sub_file()
    if sub_file then
        sub_file:close()
    end
    sub_file = io.open(sub_filename, "w")
    if not sub_file then
        mp.msg.error("Failed to open subtitle file for writing")
    end
end

local function close_sub_file()
    if sub_file then
        sub_file:close()
        sub_file = nil
    end
end

local function write_sub(text)
    if sub_file and text and text ~= "" then
        sub_file:write(text .. "\n")
        sub_file:flush()
    end
end

mp.register_event("file-loaded", function()
    close_sub_file()
    open_sub_file()
end)

mp.register_event("shutdown", close_sub_file)

mp.observe_property("sub-text", "string", function(_, text)
    write_sub(text)
end)

mp.register_event("on_osd", function(text)
    if text and text.text then
        write_sub(text.text)
    end
end)

-- Force subtitle track selection if available
mp.observe_property("track-list", "native", function(_, tracklist)
    local sub_track_found = false
    for _, track in ipairs(tracklist) do
        if track.type == "sub" and track.external == false then
            mp.set_property("sid", track.id)
            sub_track_found = true
            break
        end
    end
    if not sub_track_found then
        mp.msg.warn("No embedded subtitle track found")
    end
end)

--  This updated script:
--
--  1. Handles file opening and closing more robustly.
--  2. Uses both "sub-text" property observation and "on_osd" event to capture subtitles.
--  3. Attempts to force subtitle track selection if available.
--  4. Adds some basic error logging.
--
--  If you're still experiencing issues with specific videos, it would be helpful to:
--
--  1. Check if the problematic videos have any unique characteristics (e.g., specific formats, codecs, or subtitle types).
--  2. Use mpv's console and verbose logging to see if there are any error messages or warnings when playing these videos.
--  3. Verify that the subtitles are actually being displayed on screen for the problematic videos.
--
--  If the issue persists, you might need to investigate further based on the specific characteristics of the videos that aren't working.

