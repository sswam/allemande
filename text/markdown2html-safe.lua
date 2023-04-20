-- markdown2html-safe.lua
-- change javascript: links to # links

local function is_js_protocol(url)
    return url:match("^javascript:") ~= nil
end

local function is_external(url)
    return url:match(":") ~= nil
end

local function is_trusted_domain(url)
    -- Update the pattern to match your trusted domain
    return url:match("^https?://trusted%.example%.com/") ~= nil
end

function Link(el)
    if is_js_protocol(el.target) then
        el.target = "#"
    elseif is_external(el.target) then
        el.attributes.rel = "noopener noreferrer"
    end
    return el
end

function Image(el)
    if not is_trusted_domain(el.src) then
        -- Replace with a default or placeholder image from your domain
        el.src = "#" --https://trusted.example.com/placeholder.png"
    end
    return el
end
