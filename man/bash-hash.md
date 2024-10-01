Here's a concise guide to Bash associative arrays:

1. Declare:
   declare -A myarray

2. Add elements:
   myarray[key1]=value1
   myarray[key2]=value2

3. Access element:
   ${myarray[key1]}

4. List all keys:
   ${!myarray[@]}

5. List all values:
   ${myarray[@]}

6. Number of elements:
   ${#myarray[@]}

7. Remove element:
   unset myarray[key1]

8. Check if key exists:
   [[ -v myarray[key1] ]]

9. Iterate:
   for key in "${!myarray[@]}"; do
     echo "$key: ${myarray[$key]}"
   done

10. Clear array:
    unset myarray

Note: Requires Bash 4.0+

