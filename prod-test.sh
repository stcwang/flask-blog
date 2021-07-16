#!/bin/bash 

URL='https://swang-mlh.duckdns.org' 

ENDPTS=('/' '/about' '/portfolio' '/resume' '/contact' '/health' '/login' '/register' '/logout') 
POSTPTS=('/login' '/register') 
EXIT=0

function curlCmd { 
    printf "%s: " "$1" 
    STATUS=$( curl -I -X "$1" "$URL$PT" --silent | awk '/HTTP/{ print $2 }' ) 
    if [ $STATUS -lt 400 ]; then 
        echo "$STATUS Success" 
    else 
        echo "$STATUS Error" 
        EXIT=1
    fi 
} 

for PT in ${ENDPTS[@]}; do 
    echo "$URL$PT" 
    curlCmd GET 
    if [[ " ${POSTPTS[@]} " =~ " ${PT} " ]]; then 
        curlCmd POST 
    fi 
done 

exit $EXIT