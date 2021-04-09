#/bin/bash
#pwd
read -p "Enter args: " word
python3 play.py $word
echo "You entered: $word"
read -p "" tmp
exit 0
