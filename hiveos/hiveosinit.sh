#!/bin/bash

baseUrl='https://api2.hiveos.farm/api/v2'
login='#your_user_name'
password='#your_password'

# 1. Login
response=`curl -s -w "\n%{http_code}" \
     -H "Content-Type: application/json" \
     -H "X-Security-Code: #your_2fa_code" \
     -X POST \
     -d "{\"login\":\"$login\",\"password\":\"$password\",\"remember\":true}" \
     "$baseUrl/auth/login"`

[ $? -ne 0 ] && (>&2 echo 'Curl error') && exit 1
statusCode=`echo "$response" | tail -1`
response=`echo "$response" | sed '$d'`
[[ $statusCode -lt 200 || $statusCode -ge 300 ]] && { echo "$response" | jq '.' 1>&2; } && exit 1

# Extract access token
accessToken=`echo "$response" | jq --raw-output '.access_token'`
