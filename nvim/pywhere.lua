local M = {}

function M.get_python_scope()
    local line = vim.fn.line('.')
    local col = vim.fn.col('.')
    local function_pattern = '^%s*def%s+([%w_]+)'
    local class_pattern = '^%s*class%s+([%w_]+)'
    local indent_pattern = '^(%s*)'
    local scopes = {}
    local current_indent = #vim.fn.getline(line):match(indent_pattern)

    while line > 0 do
        local content = vim.fn.getline(line)
        local indent = #content:match(indent_pattern)
        local function_name = content:match(function_pattern)
        local class_name = content:match(class_pattern)

        if (function_name or class_name) and indent < current_indent then
            local name = function_name or class_name
            table.insert(scopes, 1, name)
            current_indent = indent
        end

        if indent == 0 then break end
        line = line - 1
    end

    return table.concat(scopes, '.')
end

return M
