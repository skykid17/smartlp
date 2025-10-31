########################################################
#
# Splunk for Microsoft Exchange
# Exchange 2010/2013 Mailbox Store Data Definition
# 
# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved.
# All Rights Reserved
#
########################################################
#
# Function: Output-MailboxData
#	Returns a String with the formatted data in it
#
function Output-MailboxData($Mailbox, $Database) {
	$Statistics = Get-MailboxStatistics -Identity $Mailbox
	$Recipient  = Get-Recipient -Identity $Mailbox 
	
	$Policy = $null
	$PolicyLink = (Get-Mailbox -Identity $Mailbox).ThrottlingPolicy
	if ($PolicyLink -eq $null) {
		$Policy = Get-ThrottlingPolicy | Where-Object {$_.IsDefault -eq $true}
	} else {
		$Policy = $PolicyLink | Get-ThrottlingPolicy
	}
		
	# Mailbox Size
	$TotalItemSize				= $Statistics.TotalItemSize.Value.ToBytes()
	$TotalDeletedItemSize		= $Statistics.TotalDeletedItemSize.Value.ToBytes()

	# Quotas from the User Record
	$ProhibitSendQuota 			= $Mailbox.ProhibitSendQuota
	$ProhibitSendReceiveQuota	= $Mailbox.ProhibitSendReceiveQuota

	# If the ProhibitSendQuota is Unlimited, then set it
	# to the ProhibitSendQuota of the database
	if ($ProhibitSendQuota -eq "Unlimited") {
		$ProhibitSendQuota = $Database.ProhibitSendQuota
	} 
	
	# Ditto with the ProhibitSendReceiveQuota
	if ($ProhibitSendReceiveQuota -eq "Unlimited") {
		$ProhibitSendReceiveQuota = $Database.ProhibitSendReceiveQuota
	}
	
	# Work out the MinimumQuota
	$MinimumQuota = "Unlimited"
	if ($ProhibitSendQuota -ne "Unlimited") {
		$MinimumQuota = $ProhibitSendQuota.Value.ToBytes()
	}
	if ($ProhibitSendReceiveQuota -ne "Unlimited") {
		if ($MinimumQuota -eq "Unlimited") {
			$MinimumQuota = $ProhibitSendReceiveQuota.Value.ToBytes()
		} elseif ($MinimumQuota -ge $ProhibitSendReceiveQuota.Value.ToBytes()) {
			$MinimumQuota = $ProhibitSendReceiveQuota.Value.ToBytes()
		}
	}
	
	# Now get rid of the GB markers
	if ($ProhibitSendQuota -ne "Unlimited") {
		$ProhibitSendQuota = $ProhibitSendQuota.Value.ToBytes()
	}
	if ($ProhibitSendReceiveQuota -ne "Unlimited") {
		$ProhibitSendReceiveQuota = $ProhibitSendReceiveQuota.Value.ToBytes()
	}
	
	# Produce the output string
	$Output = New-Object System.Collections.ArrayList

	$Date = Get-Date -format 'yyyy-MM-ddTHH:mm:sszzz'
	[void]$Output.Add($Date)

	if(([string]::IsNullOrEmpty($Mailbox.UserPrincipalName)) -eq $False) {
		[void]$Output.add("User=`"$($Mailbox.UserPrincipalName)`"")
	} else {
		[void]$Output.add("User=`"$($Mailbox.SamAccountName)`"")
	}
	[void]$Output.add("Database=`"$($Database.Name)`"")
	[void]$Output.add("LitigationHoldEnabled=`"$($Recipient.LitigationHoldEnabled)`"")
	[void]$Output.add("ThrottlingPolicy=`"$($Policy.Name)`"")
	[void]$Output.add("MinQuota=$MinimumQuota")
	[void]$Output.add("ProhibitSendQuota=$ProhibitSendQuota")
	[void]$Output.add("ProhibitSendReceiveQuota=$ProhibitSendReceiveQuota")
	[void]$Output.add("TotalItemSize=$TotalItemSize")
	[void]$Output.add("TotalDeletedItemSize=$TotalDeletedItemSize")
	
	Write-Host ($Output -join " ")
}

$OutputEncoding = [Text.Encoding]::UTF8
$dbList = (Get-MailboxDatabaseCopyStatus -Server $env:ComputerName | Where-Object {$_.ActiveCopy -eq $true })
# Don't do anything if there are no active databases
if ($dbList) {
	foreach ($db in $dbList) {
		$Database = Get-MailboxDatabase -Identity $db.DatabaseName
		Foreach ($mbox in (Get-Mailbox -Database $Database -ResultSize Unlimited)) {
			Output-MailboxData -Mailbox $mbox -Database $Database
		}
	}
}
