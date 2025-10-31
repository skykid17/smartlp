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
function Output-FolderData($Database, $Folder) {

	# Produce the output string
	$Output = New-Object System.Collections.ArrayList

	$Date = Get-Date -format 'yyyy-MM-ddTHH:mm:sszzz'
	[void]$Output.Add($Date)

	[void]$Output.add("Folder=`"$($Folder.AdminDisplayName)`"")
	[void]$Output.add("FolderPath=`"$($Folder.FolderPath)`"")
	[void]$Output.add("Database=`"$($Database.Name)`"")
	[void]$Output.add("Server=`"$($Database.Server)`"")
	[void]$Output.add("Created=`"$($Folder.CreationTime)`"")
	[void]$Output.add("Accessed=`"$($Folder.LastUserAccessTime)`"")
	[void]$Output.add("Modified=`"$($Folder.LastUserModificationTime)`"")
	[void]$Output.add("ItemCount=$($Folder.ItemCount)")
	[void]$Output.add("AssociatedItemCount=$($Folder.AssociatedItemCount)")
	[void]$Output.add("ContactCount=$($Folder.ContactCount)")
	[void]$Output.add("DeletedItemCount=$($Folder.DeletedItemCount)")
	[void]$Output.add("ItemSize=$($Folder.TotalItemSize.Value.ToBytes())")
	[void]$Output.add("AssociatedItemSize=$($Folder.TotalAssociatedItemSize.Value.ToBytes())")
	[void]$Output.add("DeletedItemSize=$($Folder.TotalDeletedItemSize.Value.ToBytes())")

	[string]::join(" ", $Output)
}

function Output-Server($Server) {
	$dblist = (Get-PublicFolderDatabase -server $Server -Status|Where-Object { $_.Mounted -eq "True" })
	if($dblist -ne $null)
    {
        $OutputEncoding = [Text.Encoding]::UTF8
	    Foreach ($db in $dblist) {
		    Foreach ($folder in (Get-PublicFolderStatistics| Where-Object { $_.DatabaseName -eq $db.Name })) {
			    Output-FolderData -Database $db -Folder $folder | Write-Host
		    }
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

