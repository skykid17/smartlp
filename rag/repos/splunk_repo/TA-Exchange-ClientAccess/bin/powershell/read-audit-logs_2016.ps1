########################################################
#
# Splunk for Microsoft Exchange
# Exchange 2016 Client Access Store Data Definition
# 
# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved.
# All Rights Reserved
#
########################################################
#
# This returns the filename of the audit database - due to some
# funkiness with permissions, deployment server and the local
# directory, we're using the %TEMP% as the location.  For the
# NT Authority\SYSTEM account, this is normally C:\Windows\Temp
#
function Get-AuditDB-Filename {
	$ENV:Temp | Join-Path -ChildPath "splunk-msexchange-auditfile_2016.clixml"
}

# Return the Last Run we had
function Load-AuditDate {
	$fn = Get-AuditDB-Filename
	if (Test-Path $fn) {
		$LastSeen = Import-CliXml $fn
	} else {
		# Fall-back - 1 months worth of audit information
		$LastSeen = (Get-Date).AddMonths(-1)
	}
	$LastSeen
}

# Save the Last Run
function Save-AuditDate($LastSeen) {
	$fn = Get-AuditDB-Filename
	$LastSeen | Export-CliXml $fn -Force
}

function Output-AuditRecord($Server, $Record) {
	$Output = New-Object System.Collections.ArrayList
	$D = Get-Date $Record.RunDate -format 'yyyy-MM-ddTHH:mm:sszzz'
	[void]$Output.Add($D)
	[void]$Output.Add("Server=""$Server""")
	$User = (Get-User -Identity $Record.Caller).UserPrincipalName
	[void]$Output.Add("User=""$User""")
	$ID = $Record.Identity
	[void]$Output.Add("Identity=""$ID""")
	
	# This is the command that was run
	$Cmdlet = $Record.CmdletName
	[void]$Output.Add("Cmdlet=""$Cmdlet""")
	$Parameters = $Record.CmdletParameters
	Foreach ($Param in $Parameters.GetEnumerator()) {
		$Name = $Param.Name
		$Value = $Param.Value
		[void]$Output.Add("Param=""-$Name '$Value'""")
	}
	
	# Success/Error
	$Succeeded = $Record.Succeeded
	[void]$Output.Add("Success=""$Succeeded""")
	if ($Record.Error) {
		$Error = $Record.Error.Replace("\r", "")
	    [void]$Output.Add("Error=""$Error""")
	}
	
	Write-Host ($Output -join " ")
}

##
## MAIN PROGRAM
##
$LastSeen = Load-AuditDate

$ExchangeFQDN = [System.Net.Dns]::GetHostByName((hostname)).HostName
$ConnectionUri = -join("http://",$ExchangeFQDN , "/PowerShell/"); 

# Retrieve Records from the LastSeen date
$Session = New-PSSession -ConfigurationName Microsoft.Exchange -ConnectionUri $ConnectionUri
Import-PSSession $Session -DisableNameChecking | Out-Null
$Records = Search-AdminAuditLog -StartDate $LastSeen -EndDate (Get-Date)
$RecordLast = $LastSeen

#
# If there aren't any records, then $Records is null, otherwise
# it is an array
#
$OutputEncoding = [Text.Encoding]::UTF8
if ($Records) {
	Foreach ($Record in $Records) {
	    $Server = (($Record.OriginatingServer).split(' '))[0]
		if ($Server -eq $env:ComputerName) {
		    $RecordDate = $Record.RunDate
			if ($RecordDate -gt $LastSeen) {
			    Output-AuditRecord -Server $Server -Record $Record
				if ($RecordDate -ge $RecordLast) {
					$RecordLast = $RecordDate
				}
			} 
		}
	}
}

Save-AuditDate $RecordLast
Remove-PSSession $Session
