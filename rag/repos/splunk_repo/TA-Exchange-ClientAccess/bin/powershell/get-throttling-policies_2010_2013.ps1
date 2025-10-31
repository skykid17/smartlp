######################################################
#
# Splunk for Microsoft Exchange
# Exchange 2010/2013 Client Access Data Definition
# 
# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved.
# All Rights Reserved
#
######################################################
#
# Connect to the Local Machine for Powershell
#
#$SessionUri = "http://" + $env:ComputerName + "/Powershell/"
#$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri $SessionUri -Authentication Kerberos
#Import-PSSession -DisableNameChecking $Session | Foreach-Object { }
#
function Output-Policy($Policy) {
	$O = New-Object System.Collections.ArrayList
	$D = Get-Date -format 'yyyy-MM-ddTHH:mm:sszzz'
	[void]$O.Add($D)
	
	foreach ($p in $Policy.PSObject.Properties) {
		[void]$O.Add("$($p.Name)=`"$($Policy.PSObject.Properties[$p.Name].Value)`"")
	}
	
	Write-Host ($O -join " ")
}

Get-ThrottlingPolicy | Foreach-Object {
	Output-Policy $_
}
