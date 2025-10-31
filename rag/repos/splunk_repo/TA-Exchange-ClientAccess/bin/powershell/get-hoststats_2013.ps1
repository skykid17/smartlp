######################################################
#
# Splunk for Microsoft Exchange
# Exchange 2013 Client Access Data Definition
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
	
	$WindowsInfo = (Get-Item "HKLM:SOFTWARE\Microsoft\Windows NT\CurrentVersion")
	$WindowsVersion = $WindowsInfo.GetValue("ProductName")
	$BuildNumber = $WindowsInfo.GetValue("CurrentBuildNumber")

	# Test-ServiceHealth is broken in the Exchange 2013 build 8400 (Preview) for Client Access Systems
	$TestServiceHealth = @( "MSExchangeADTopology","MSExchangeFrontendTransport","MSExchangeHM","MSExchangeServiceHost","IISAdmin","W3Svc")
	$ProcsOK = $true
	$ServicesRunning = New-Object Collections.Generic.List[string]
	$ServicesNotRunning = New-Object Collections.Generic.List[string]
	foreach ($svc in $TestServiceHealth) {
		$running = (Get-Service $svc).Status
		if ($running -eq "Running") {
			$ServicesRunning.Add($svc)
		} else {
			$ServicesNotRunning.Add($svc)
			$ProcsOK = $false
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
	[void]$Output.Add("Cluster=`"$($ExServer.Name)`"")
	[void]$Output.Add("ClusterStatus=`"$IsActive`"")
	[void]$Output.Add("Clustered=`"$($ExServer.IsMemberOfCluster)`"")
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