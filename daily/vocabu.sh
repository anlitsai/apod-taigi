key=$1

a=`find ./|grep md`; 

for i in $a;do echo $i;cat $i|grep 【;done > voca_daily.txt

for i in $a;do cat $i|grep 【;done |sort|uniq > voca.txt

