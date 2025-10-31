######################################################
#
# Splunk for Microsoft Exchange
# Exchange 2007 Mailbox Store Data Definition
# 
# Copyright (C) 2005-2024 Splunk Inc. All Rights Reserved.
# All Rights Reserved
#
######################################################

# Return the drive that the given Path resides on.
# The path is stored in $Path.PathName
function Get-VolumeForPath($Path) {
	$Volumes = Get-WMIObject -class "win32_volume" -namespace "root/cimv2" -ComputerName $env:ComputerName |Select Name,Capacity,FreeSpace
	$LongestVolName = ""
	$DBVolume = $null
	if($Path){
		$UpcasedPathName = $Path.PathName.ToUpper()
		foreach ($Volume in $Volumes) {
			if ($UpcasedPathName.StartsWith($Volume.Name.ToUpper())) {
				if ($Volume.Name.Length -gt $LongestVolName.Length) {
					$LongestVolName = $Volume.Name
					$DBVolume = $Volume
				}
			}
		}
	}
	$DBVolume
}

# Returns the % free space on the specified volume,
# which may be $null.
function Get-PercFreeForVolume($Volume) {
	if ($Volume) {
		if ($Volume.Capacity -eq 0) {
			$VolumePercFree = 100
		} else {
			$VolumePercFree = ($Volume.FreeSpace / $Volume.Capacity) * 100.00
		}
	} else {
		$VolumePercFree = 100
	}
	return $VolumePercFree
}

function Output-DatabaseInfo($Store, $Database) {
	# Build the output string from an array
	$Output = New-Object System.Collections.ArrayList

	# A Mailbox Database has a ProhibitSendQuota Entry
	# A Public Folder Database has a ProhibitPostQuota Entry
	if ($Database.ProhibitSendQuota -gt 0) {
		$IsMailboxDatabase = "True"
	} else {
		$IsMailboxDatabase = "False"
	}
	if ($Database.ProhibitPostQuota -gt 0) {
		$IsPublicFolderDatabase = "True"
	} else {
		$IsPublicFolderDatabase = "False"
	}
	
	# What sort of Cluster is this?
	$ClusterType = $Store.ClusteredStorageType
	
	# ManagerType must be "Server", "ContinuousClusterReplication" or "SingleCopyCluster"
	$ManagerType = "Unknown"
	if ($ClusterType -eq "Disabled") {
		$ManagerType = "Server"
	} elseif ($ClusterType -eq "NonShared") {
		$ManagerType = "ContinuousClusterReplication"
	} elseif ($ClusterType -eq "Shared") {
		$ManagerType = "SingleCopyCluster"
	}

	# $Active = one of Active, Passive
	$Active = "Unknown"
	if ($ClusterType -eq "Disabled") {
		if ($Database.Mounted -eq 'True') {
			$Active = "Active";
		} else {
			$Active = "Disabled";
		}
	} elseif ($ClusterType -eq "NonShared") {
		# CCR - use Get-ClusteredStorageServerStatus to determine active server
		$ActiveNode="Unknown"
		(Get-ClusteredMailboxServerStatus -Identity $Store).OperationalMachines|ForEach-Object {If ($_.Contains("Active")) {$ActiveNode = $_.Substring(0,$_.IndexOf(" "))}}
		if ($ActiveNode -eq $env:ComputerName) {
			$Active = "Active"
		} elseif ($ActiveNode -eq "Unknown") {
			$Active = "Unknown"
		} else {
			$Active = "Passive"
		}
	} elseif ($ClusterType -eq "Shared") {
		# SCC
		$ActiveNode="Unknown"
		(Get-ClusteredMailboxServerStatus -Identity $Store).OperationalMachines|ForEach-Object {If ($_.Contains("Active")) {$ActiveNode = $_.Substring(0,$_.IndexOf(" "))}}
		if ($ActiveNode -eq $env:ComputerName) {
			$Active = "Active"
		} elseif ($ActiveNode -eq "Unknown") {
			$Active = "Unknown"
		} else {
			$Active = "Passive"
		}
	}
	
	# Status (Mounted,Health)
	$Status = "Unknown"
	if ($IsPublicFolderDatabase) {
		if ($Database.Mounted -eq 'True') {
			$status = "Mounted"
		} else {
			$status = "Unmounted"
		}
	} elseif ($ClusterType -eq "Disabled") {
		if ($Database.Mounted -eq 'True') {
			$Status = "Mounted";
		} else {
			$Status = "Unmounted";
		}
	} elseif ($ClusterType -eq "NonShared") {
		# CCR - We use the Get-StorageGroupCopyStatus to determine health
		if ($Database.Mounted -eq 'True') {
			$mnt = "Mounted";
		} else {
			$mnt = "";
		}
		$scs = Get-StorageGroupCopyStatus -Identity $Database.StorageGroup
		$health = $scs.SummaryCopyStatus
		if ($health -eq "Healthy") {
			$Status = "$mnt,$health";
		} elseif ($health -eq "Suspended") {
			$failuremsg = $scs.SuspendComment
			$Status = "$mnt,$health,$failuremsg"
		} else {
			$failuremsg = $scs.FailedMessage
			$Status = "$mnt,$health,$failuremsg"
		}
	} elseif ($ClusterType -eq "Shared") {
		# SCC - We use the Get-ClusteredMailboxServerStatus to determine health
		if ($Database.Mounted -eq 'True') {
			$mnt = "Mounted";
		} else {
			$mnt = "";
		}
		$scs = Get-ClusteredMailboxServerStatus -Identity $Store
		$health = $scs.State
		$Status = "$mnt,$health";
	}

	if ($ClusterType -eq "Shared" -and $Active -eq "Passive") {
		# In the case of SCC Passive cluster, we don't have access to the disks
		$EdbDiskName = "Unavailable"
		$EdbDiskFreeSpace = 0
		$EdbDiskCapacity = 0
		$EdbDiskPercFree = 100
		$EdbSize = 0
	} else {
		$EdbDisk = Get-VolumeForPath($Database.EdbFilePath)
		if ($EdbDisk) {
			$EdbDiskName		= $EdbDisk.Name
			$EdbDiskFreeSpace	= $EdbDisk.FreeSpace
			$EdbDiskCapacity	= $EdbDisk.Capacity
		} else {
			$EdbDiskName		= "Unknown"
			$EdbDiskFreeSpace	= 0
			$EdbDiskCapacity	= 0
		}
		$EdbDiskPercFree = Get-PercFreeForVolume($EdbDisk)
		$EdbSize = ($Database.EdbFilePath.PathName | Get-ChildItem).Length
	}

	$CopyEdbDriveFree = 100
	if ($Database.HasLocalCopy -eq $true) {
		if ($ClusterType -eq "Shared" -and $Active -eq "Passive") {
			# In the case of SCC Passive cluster, we don't have access to the disks, so LCR is always Disabled
			$CopyEdbDriveFree = "Unavailable"
			$CopyEdbSize = "Unavailable"
			$CopyStatus = "Disabled"
		} else {
			$CopyEdbDrive = Get-VolumeForPath($Database.CopyEdbFilePath)
			if ($CopyEdbDrive) {
				$CopyEdbDriveFree	= ($CopyEdbDrive.FreeSpace / $CopyEdbDrive.Capacity) * 100.00
			} else {
				$CopyEdbDriveFree	= -1.00
			}
			$CopyEdbSize = ($Database.CopyEdbFilePath.PathName|Get-ChildItem).Length
			$CopyStatus = (Get-StorageGroupCopyStatus $Database.StorageGroup).SummaryCopyStatus
		}
	} else {
		$CopyEdbDriveFree = "Disabled"
		$CopyEdbSize = "Disabled"
		$CopyStatus = "Disabled"
	}

	# LogFolderPath
	$LogFolderPath = (Get-StorageGroup -Identity $Database.StorageGroup).LogFolderPath
	if ($ClusterType -eq "Shared" -and $Active -eq "Passive") {
		# In the case of SCC Passive cluster, we don't have access to the disks, so Logging Space is not available
		$LogDiskPercFree = 100
		
		$LogSize = 0
	} else {
		$LogDisk = Get-VolumeForPath($Database.LogFolderPath)
		$LogDiskPercFree = Get-PercFreeForVolume($LogDisk)
		
		$Logs = (Dir $LogFolderPath\*.log)
		$LogSize = 0
		foreach ($LogFile in $Logs) {
			$LogSize = $LogSize + $LogFile.Length
		}
	}
	
	$Date = Get-Date -format 'yyyy-MM-ddTHH:mm:sszzz'
	[void]$Output.Add($Date)
			
	[void]$Output.Add("Database=`"$($Database.Identity)`"") 
	[void]$Output.Add("Active=`"$Active`"")
	[void]$Output.Add("MasterType=`"$ManagerType`"")
	[void]$Output.Add("Status=`"$Status`"")
	[void]$Output.Add("PublicFolderDatabase=`"$($Database.PublicFolderDatabase)`"")
	[void]$Output.Add("IsMailboxDatabase=`"$IsMailboxDatabase`"")
	[void]$Output.Add("IsPublicFolderDatabase=`"$IsPublicFolderDatabase`"")
	[void]$Output.Add("LogFolderPath=`"$LogFolderPath`"")
	[void]$Output.Add("LogPercFree={0:N3}" -f $LogDiskPercFree)
	[void]$Output.Add("LogSize=$LogSize")
	[void]$Output.Add("FilePath=`"$($Database.EdbFilePath)`"")
	[void]$Output.Add("MainPercFree={0:N3}" -f $EdbDriveFree)
	[void]$Output.Add("FileSize=$EdbSize")
	[void]$Output.Add("LocalCopy=`"$($Database.HasLocalCopy)`"")
	[void]$Output.Add("CopyFilePath=`"$($Database.CopyEdbFilePath)`"")
	[void]$Output.Add("CopyPercFree={0:N3}" -f $CopyEdbDriveFree)
	[void]$Output.Add("CopyFileSize=$CopyEdbSize")
	[void]$Output.Add("CopyStatus=$CopyStatus")
	[void]$Output.Add("SnapshotLastFullBackup=`"$($Database.SnapshotLastFullBackup)`"")
	[void]$Output.Add("SnapshotLastIncrementalBackup=`"$($Database.SnapshotLastIncrementalBackup)`"")
	[void]$Output.Add("SnapshotLastDifferentialBackup=`"$($Database.SnapshotLastDifferentialBackup)`"")
	[void]$Output.Add("SnapshotLastCopyBackup=`"$($Database.SnapshotLastCopyBackup)`"")
	[void]$Output.Add("LastFullBackup=`"$($Database.LastFullBackup)`"")
	[void]$Output.Add("LastIncrementalBackup=`"$($Database.LastIncrementalBackup)`"")
	[void]$Output.Add("LastDifferentialBackup=`"$($Database.LastDifferentialBackup)`"")
	[void]$Output.Add("LastCopyBackup=`"$($Database.LastCopyBackup)`"")
	
	# Send the output down the line
	[string]::join(" ", $Output)
}

$Store = (Get-MailboxServer | Where-Object { ($_.Name -eq $env:ComputerName) -or ($_.RedundantMachines -eq $env:ComputerName) })

$DatabaseList = New-Object System.Collections.ArrayList
Foreach ($database in Get-MailboxDatabase -server $Store -Status) {
        [void]$DatabaseList.Add($database)
}
Foreach ($database in Get-PublicFolderDatabase -server $Store -Status) {
        [void]$DatabaseList.Add($database)
}

$OutputEncoding = [Text.Encoding]::UTF8
Foreach ($database in $DatabaseList) {
	Output-DatabaseInfo -Store $Store -Database $database | Write-Host
}
