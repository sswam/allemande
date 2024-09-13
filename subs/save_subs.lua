local sub_file = io.open("subtitles.txt", "w")

mp.register_event("shutdown", function()
  sub_file:close()
end)

mp.observe_property("sub-text", "string", function(_, text)
  if text and text ~= "" then
    sub_file:write(text .. "\n")
    sub_file:flush()
  end
end)
