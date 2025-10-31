######################################################
#
# Splunk for Microsoft Exchange
# Exchange 2010/2013 Mailbox Role Data Definition
# 
# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved.
# All Rights Reserved
#
######################################################

$Mailboxes = Get-Mailbox -Server $Env:ComputerName -ResultSize Unlimited
$ExchangeVer = Get-ExchangeServer
$AdminDisplayVersion = $ExchangeVer.AdminDisplayVersion

foreach ($Mailbox in $Mailboxes) {
	$Id = 0
	$UPN = $Mailbox.UserPrincipalName
	if ($Mailbox.RulesQuota -ne $null -and $Mailbox.RulesQuota.getType().Name -eq "ByteQuantifiedSize") {
		$Quota = $Mailbox.RulesQuota.ToBytes()
	}
	
	if($AdminDisplayVersion -like "Version 15*")
	{
		$Rules = Get-InboxRule -Mailbox $Mailbox.Identity
	}
	else
	{
		$Rules = Get-InboxRule -Mailbox $Mailbox
	}
	if ($Rules -ne $null) {
		$Rules | Foreach-Object {
			$O = New-Object System.Collections.ArrayList
			$D = Get-Date -format 'yyyy-MM-ddTHH:mm:sszzz'
			[void]$O.Add($D)
			[void]$O.Add("Mailbox=`"$UPN`"")
			[void]$O.Add("Quota=`"$Quota`"")
			[void]$O.Add("InternalRuleID=$Id")
	
			$Len = 0
			
			if ($AdminDisplayVersion -like "Version 15*")
			{
				Add-Type -AssemblyName System.Web
			}
			
			foreach ($p in $_.PSObject.Properties) {
				$Val = @()
				if ($_.PSObject.Properties[$p.Name].Value -ne $null) {
					if ($p.Name -eq "Description") {
						$Val = [System.Web.HttpUtility]::UrlEncode($_.PSObject.Properties[$p.Name].Value)
						$Val = $Val.Replace("`"", "'")
						$Len = $Len + $Val.Length + 2
					} else {
						$Val = $_.PSObject.Properties[$p.Name].Value
						if ($Val.getType() -Like "Microsoft.Exchange.Data.MultiValuedProperty*")
						{
							$Gstring=""
							foreach ($part in $Val)
							{
								$Gstring += $part
							}
							$Len = $Len + $Gstring.Length + 2
						}
						else
						{
							$Len = $Len + $Val.Length + 2
						}
					}
				} else {
					$Len = $Len + 2
				}
				[void]$O.Add("$($p.Name)=`"$Val`"")
			}
			[void]$O.Add("Length=$Len")
			Write-Host ($O -join " ")
			$Id++
		}
	}
}
