#!/usr/bin/env python

import argh

def cat_named(files, header_pre='## ', header_post=':\n\n', footer='\n\n', number=True, number_post=". "):
    if number is True:
        number = 1
    result = ""
    for file in files:
        if number is not None:
            result += f"{header_pre}{number}{number_post}{file}{header_post}"
            number += 1
        else:
            result += f"{header_pre}{file}{header_post}"
        with open(file, 'r') as istream:
            result += istream.read()
        result += footer

    return result

if __name__ == "__main__":
    argh.dispatch_command(cat_named)
