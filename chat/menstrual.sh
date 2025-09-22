grep -R -l 1girl | grep '\.yml' | xa grep -e 'age:.*adult ' -e 'age:.*teen'  | grep -v -e Chaz -e humans/ -e ' [56789]' -e ' [0-9][0-9][0-9]' | sed 's/:.*//'
