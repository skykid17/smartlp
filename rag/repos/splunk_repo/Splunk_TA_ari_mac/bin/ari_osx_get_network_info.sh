#!/bin/bash

## ########################################################################################
## ##
## ## SPLUNK_TA_ARI_MAC Edge Discovery
## ##
## ## Copyright (C) 2025 - Splunk Inc. - All Rights Reserved
## ## Splunk Software Licence and Support Agreement
## ##
## ########################################################################################

#Set current date and time
date_time=$(date +"%FT%T%z")

#Getting machine's local mac and internal ip
machine_internal_ip=$(ipconfig getifaddr en0)
machine_mac=$(ifconfig en0 | awk '/ether/{print $2}')

#Output the discovered details
echo $date_time ari_nt_host=$(hostname -s) ari_ip=$machine_internal_ip ari_mac=$machine_mac