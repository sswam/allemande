from bidict import bidict

extension_to_language = bidict({
    'sh': 'bash',
    'py': 'python'
})

print(extension_to_language['sh'])
print(extension_to_language.inverse['bash'])
