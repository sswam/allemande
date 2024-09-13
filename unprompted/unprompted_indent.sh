#!/bin/bash -eu
# unprompted_indent.sh:	Indent unprompted macro code, somewhat works

unprompted_singleton_tags="array,break,bypass,call,civitai,doc,faceswap,file2mask,filelist,filter_tags,get,help,image_edit,img2img,img2pez,init_image,interrogate,invert_mask,length,log,logs,max,#,min,overrides,random,remember,restore_faces,round,seed,sets,txt2img,unset,zoom_enhance,image_info"

my_singleton_tags="use,rand,r1,r2,w"

markup_indent.py --brackets --not-html --single "$unprompted_singleton_tags,$my_singleton_tags" "$@"
