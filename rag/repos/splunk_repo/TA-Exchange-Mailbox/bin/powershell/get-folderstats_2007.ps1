########################################################
#
# Splunk for Microsoft Exchange
# Exchange 2007 Mailbox Store Data Definition
# 
# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved.
# All Rights Reserved
#
########################################################

#
# Function: Output-FolderData
#	Returns a String with the formatted data in it
#
function Output-FolderData($Mailbox, $Folder) {
	# Produce the output string
	$Output = New-Object System.Collections.ArrayList
	$Date = Get-Date -format 'yyyy-MM-ddTHH:mm:sszzz'
	[void]$Output.Add($Date)
	
	if(([string]::IsNullOrEmpty($Mailbox.UserPrincipalName)) -eq $False) {
		[void]$Output.add("User=`"$($Mailbox.UserPrincipalName)`"")
	} else {
		[void]$Output.add("User=`"$($Mailbox.SamAccountName)`"")
	}
	[void]$Output.add("Folder=`"$($Folder.FolderPath)`"")
	[void]$Output.add("Type=`"$($Folder.FolderType)`"")
	[void]$Output.add("Size=$($Folder.FolderSize.ToBytes())")
	[void]$Output.add("Items=$($Folder.ItemsInFolder)")
	
	[string]::join(" ", $Output)
}

function Output-Server($Store) {
	$OutputEncoding = [Text.Encoding]::UTF8
	foreach ($mbox in Get-Mailbox -server $Store.Name -ResultSize Unlimited) {
		foreach ($folder in Get-MailboxFolderStatistics -Identity $mbox) {
			Output-FolderData -Mailbox $mbox -Folder $folder | Write-Host
		}
	}
}

Get-MailboxServer | Foreach-Object {
	if ($_.Name -eq $env:ComputerName) {
		Output-Server $_
	} elseif ($_.RedundantMachines -eq $env:ComputerName) {
		$ActiveMachine = ((Get-ClusteredMailboxServerStatus).OperationalMachines | Select-String "active")
		if ($ActiveMachine | Select-String $env:ComputerName) {
			Output-Server $_
		}
	}
}

