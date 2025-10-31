######################################################
#
# Splunk for Microsoft Exchange
# Exchange 2010/2013 Mailbox Store Data Definition
# 
# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved.
# All Rights Reserved
#
######################################################

Get-DistributionGroup | Foreach-Object {
	$O = New-Object System.Collections.ArrayList
	$D = Get-Date -format 'yyyy-MM-ddTHH:mm:sszzz'
	[void]$O.Add($D)
	foreach ($p in $_.PSObject.Properties) {
		if ($_.PSObject.Properties[$p.Name].Value -ne $null) {
			[void]$O.Add("$($p.Name)=`"$($_.PSObject.Properties[$p.Name].Value)`"")
		}
	}
	Write-Host ($O -join " ")
}

Get-DynamicDistributionGroup | Foreach-Object {
	$O = New-Object System.Collections.ArrayList
	$D = Get-Date -format 'yyyy-MM-ddTHH:mm:sszzz'
	[void]$O.Add($D)
	foreach ($p in $_.PSObject.Properties) {
		if ($_.PSObject.Properties[$p.Name].Value -ne $null) {
			[void]$O.Add("$($p.Name)=`"$($_.PSObject.Properties[$p.Name].Value)`"")
		}
	}
	Write-Host ($O -join " ")
}
