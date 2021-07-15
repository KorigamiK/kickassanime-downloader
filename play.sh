#/bin/bash
cur=`pwd`
read -p "Enter args: " word
python3 play.py $word
echo "You entered: $word"
read -p "" tmp
cd $cur
exit 0
