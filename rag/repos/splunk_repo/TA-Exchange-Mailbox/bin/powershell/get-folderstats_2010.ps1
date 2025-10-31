########################################################
#
# Splunk for Microsoft Exchange
# Exchange 2010 Mailbox Store Data Definition
# 
# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved.
# All Rights Reserved
#
########################################################

#
# Function: Output-MailboxData
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
	
	Write-Host ($Output -join " ")
}

########################################################
#
# Step 1 - Get a list of active mailboxes on this
#		   mailbox store.  There are other methods
#		   by which this data can be retrieved, but
#		   this seems to be most efficient.
#
$dblist = (Get-MailboxDatabaseCopyStatus -server $env:ComputerName|Where-Object {$_.ActiveCopy -eq $true})

#
# Step 2 - Process each Mailbox Database in sequence
#
$OutputEncoding = [Text.Encoding]::UTF8
if ($dblist) {
	Foreach ($db in $dblist) {
		Foreach ($mbox in Get-Mailbox -Database $db.DatabaseName -ResultSize Unlimited) {
			Foreach ($folder in Get-MailboxFolderStatistics -Identity $mbox) {
				Output-FolderData -Mailbox $mbox -Folder $folder
			}
		}
	}
}