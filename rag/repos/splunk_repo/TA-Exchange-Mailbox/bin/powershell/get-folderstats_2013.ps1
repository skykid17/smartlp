########################################################
#
# Splunk for Microsoft Exchange
# Exchange 2013 Mailbox Store Data Definition
# 
# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved.
# All Rights Reserved
#
########################################################

$dblist = (Get-MailboxDatabaseCopyStatus -server $env:ComputerName|Where-Object {$_.ActiveCopy -eq $true})
if ($dblist) {
	Foreach ($db in $dblist) {
		Foreach ($mbox in Get-Mailbox -Database $db.DatabaseName -ResultSize Unlimited) {
			Get-MailboxFolderStatistics -Identity $mbox.Identity | Foreach-Object {
				$Bytes = $_.FolderSize.ToBytes()
				$Output = New-Object System.Collections.ArrayList
				$Date = Get-Date -format 'yyyy-MM-ddTHH:mm:sszzz'
				[void]$Output.Add($Date)		
				if(([string]::IsNullOrEmpty($mbox.UserPrincipalName)) -eq $False) {
					[void]$Output.add("User=`"$($mbox.UserPrincipalName)`"")
				} else {
					[void]$Output.add("User=`"$($mbox.SamAccountName)`"")
				}
				[void]$Output.add("Folder=`"$($_.FolderPath)`"")
				[void]$Output.add("Type=`"$($_.FolderType)`"")
				[void]$Output.add("Size=$Bytes")
				[void]$Output.add("Items=$($_.ItemsInFolder)")			
				Write-Host ($Output -join " ")
			}
		}
	}
}