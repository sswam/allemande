Here's a concise guide to Bash arrays:

1. Declaration:
   ```
   array=()
   array=(element1 element2 element3)
   declare -a array
   ```

2. Adding elements:
   ```
   array+=("new element")
   array[index]="value"
   ```

3. Accessing elements:
   ```
   ${array[index]}
   ${array[@]}  # All elements
   ${array[*]}  # All elements (space-separated)
   ```

4. Array length:
   ```
   ${#array[@]}
   ```

5. Slicing:
   ```
   ${array[@]:start:length}
   ```

6. Looping:
   ```
   for element in "${array[@]}"; do
     echo "$element"
   done
   ```

7. Deleting elements:
   ```
   unset array[index]
   ```

8. Associative arrays (Bash 4+):
   ```
   declare -A assoc_array
   assoc_array[key]="value"
   ${assoc_array[key]}
   ```

9. Check if element exists:
   ```
   [[ " ${array[*]} " =~ " $element " ]]
   ```

10. Copy array:
    ```
    new_array=("${old_array[@]}")
    ```

