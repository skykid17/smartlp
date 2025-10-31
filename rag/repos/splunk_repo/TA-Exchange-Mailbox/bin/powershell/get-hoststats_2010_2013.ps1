######################################################
#
# Splunk for Microsoft Exchange
# Exchange 2010/2013 Mailbox Store Data Definition
# 
# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved.
# All Rights Reserved
#
######################################################

function Output-HostData($Server) {
	$Output = New-Object System.Collections.ArrayList
	
	$ExServer = (Get-ExchangeServer -Identity $env:ComputerName)
	$Product  = (Get-Command ExSetup|%{$_.FileVersionInfo})
	$IsActive = "Disabled"
	if ($ExServer.IsMemberOfCluster -eq 'Yes') {
		if ((Get-ClusteredMailboxServerStatus).OperationalMachines | select-string $Server | select-string "active") {
			$IsActive = "Active"
		} else {
			$IsActive = "Passive"
		}
	}
	
	$Store = (Get-MailboxServer | Where-Object { ($_.Name -eq $env:ComputerName) })
	$IsActive = "Disabled"
	$IsClustered = "No"
	$ClusterName = $ExServer.Name
	if ($Store.DatabaseAvailabilityGroup -ne $null) {
		$IsActive = "DAG"
		$IsClustered = 'Yes'
		$ClusterName = $Store.DatabaseAvailabilityGroup
	} 	
	
	$WindowsInfo = (Get-Item "HKLM:SOFTWARE\Microsoft\Windows NT\CurrentVersion")
	$WindowsVersion = $WindowsInfo.GetValue("ProductName")
	$BuildNumber = $WindowsInfo.GetValue("CurrentBuildNumber")

	$TestServiceHealth = (Test-ServiceHealth -Server $env:ComputerName)
	$ProcsOK = $true
	$ServicesRunning = New-Object Collections.Generic.List[string]
	$ServicesNotRunning = New-Object Collections.Generic.List[string]
	foreach ($svc in $TestServiceHealth) {
		if (!$svc.RequiredServicesRunning) {
			$ProcsOK = $false
		}
		foreach ($proc in $svc.ServicesRunning) {
			$ServicesRunning.Add($proc)
		}
		foreach ($proc in $svc.ServicesNotRunning) {
			$ServicesNotRunning.Add($proc)
		}
	}
	if ($ServicesRunning.Count -gt 0) {
		$ServicesRunning = [string]::join(",",($ServicesRunning|Sort -Unique))
	} else {
		$ServicesRunning = [string]""
	}
	if ($ServicesNotRunning.Count -gt 0) {
		$ServicesNotRunning = [string]::join(",",($ServicesNotRunning|Sort -Unique))
	} else {
		$ServicesNotRunning = [string]""
	}

	$Date = Get-Date -format 'yyyy-MM-ddTHH:mm:sszzz'
	[void]$Output.Add($Date)

	[void]$Output.Add("Name=`"$($ExServer.Name)`"")
	[void]$Output.Add("Cluster=`"$ClusterName`"")
	[void]$Output.Add("ClusterStatus=`"$IsActive`"")
	[void]$Output.Add("Clustered=`"$IsClustered`"")
	[void]$Output.Add("HubTransport=`"$($ExServer.IsHubTransportServer)`"")
	[void]$Output.Add("CAS=`"$($ExServer.IsClientAccessServer)`"")
	[void]$Output.Add("EdgeTransport=`"$($ExServer.IsEdgeServer)`"")
	[void]$Output.Add("Mailbox=`"$($ExServer.IsMailboxServer)`"")
	[void]$Output.Add("UMServer=`"$($ExServer.IsUnifiedMessagingServer)`"")
	[void]$Output.Add("ServerRole=`"$($ExServer.ServerRole)`"")
	[void]$Output.Add("Provisioned=`"$($ExServer.IsProvisionedServer)`"")
	[void]$Output.Add("Site=`"$($ExServer.Site)`"")
	[void]$Output.Add("Edition=`"$($ExServer.Edition)`"")
	[void]$Output.Add("ProductVersion=`"$($Product.ProductVersion)`"")
	[void]$Output.Add("WindowsVersion=`"$WindowsVersion`"")
	[void]$Output.Add("WindowsBuild=`"$BuildNumber`"")
	[void]$Output.Add("ServicesRunning=`"$ServicesRunning`"")
	[void]$Output.Add("ServicesNotRunning=`"$ServicesNotRunning`"")
	[void]$Output.Add("ProcsOK=`"$ProcsOK`"")
	
	Write-Host ($Output -join " ")
}

$OutputEncoding = [Text.Encoding]::UTF8
Output-HostData $env:ComputerName