a=`ls apod-taigi_202*txt`;
for i in $a;do echo $i;cat $i|grep "$1";done

