<#
    .SYNOPSIS
        & .\Invoke-MonitoredExchangeScript.ps1 "MyScript.ps1"
        
    .DESCRIPTION
        Runs a script that contains Exchange cmdlets
        Outputs additional Splunk events related to the running and
        errors in the script.
#>
[CmdletBinding()]
param(
    #Command to execute.
    [Parameter(Position=0, Mandatory=$true)]
    [ValidateNotNullOrEmpty()]
    [string] $Command,

    [Parameter(Mandatory=$true)]
    [ValidateNotNullOrEmpty()]
    [string] $ExchangeVersion,
    
    # Splunk Sourcetype Prefix for generated events
    [Parameter()]
    [ValidateNotNull()]
    [string] $SourceTypePrefix="Powershell:",
    
    # Maximum number of errors to convert into events
    [Parameter()]
    [ValidateRange(0, 100)]
    [int] $MaxErrorCount
)

$WrappedScriptExecutionSummary= New-Object -TypeName PSObject -Property (
    [ordered]@{
        SplunkSourceType="$($SourceTypePrefix)ScriptExecutionSummary";
        Identity=[guid]::NewGuid().ToString();
        InvocationLine=$MyInvocation.Line.Replace("`"","");
        TerminatingError=$false; ErrorCount=0; Elapsed=""
    })
$originalLocation = Get-Location

$ExchangeVersionKey = @{
    "V8" = "SOFTWARE\Microsoft\Exchange\v8.0\Setup";
    "V14" = "SOFTWARE\Microsoft\ExchangeServer\v14\Setup";
    "V15" = "SOFTWARE\Microsoft\ExchangeServer\v15\Setup"
}

try
{
    Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Definition)
    $currentLocation = Get-Location
    $Registry = [Microsoft.Win32.RegistryKey]::OpenBaseKey("LocalMachine", "Default")
    $ExchangeInstallPath = $Registry.OpenSubKey($ExchangeVersionKey[$ExchangeVersion]).GetValue("MsiInstallPath")
    $ExchangeShellPath = Join-Path $ExchangeInstallPath "bin\exshell.psc1"
    $FullCommand = "powershell -PSConsoleFile `"" + $ExchangeShellPath + "`" -command `". '" + (Join-Path $currentLocation $Command) + "'`""
    $ScriptStopWatch = [System.Diagnostics.Stopwatch]::StartNew()
    $Error.Clear()
    Invoke-Expression $FullCommand
}
catch
{
    $WrappedScriptExecutionSummary.TerminatingError = $true;
}
finally
{
    Set-Location $originalLocation
    $WrappedScriptExecutionSummary.Elapsed = $ScriptStopWatch.Elapsed.TotalMilliseconds
    $WrappedScriptExecutionSummary.ErrorCount = $Error.Count
        
    if ($Error.Count -gt 0) {
        $ei = $Error.Count - 1
        if ($PSBoundParameters.ContainsKey('MaxErrorCount')) {
            if ($MaxErrorCount -lt $Error.Count) {
                $ei = $MaxErrorCount - 1
            }
            # Always emit terminating errors
            if ($ei -eq -1 -and $WrappedScriptExecutionSummary.TerminatingError) {
                $ei = 1
            }
        }

        for(; $ei -ge 0; $ei--) {
            $errorRecord = New-Object -TypeName PSObject -Property (
                [ordered]@{
                    SplunkSourceType="$($SourceTypePrefix)ScriptExecutionErrorRecord";
                    ParentIdentity=$WrappedScriptExecutionSummary.Identity;
                    ErrorIndex=$ei;
                    ErrorMessage=$Error[$ei].ToString();
                    PositionMessage=$Error[$ei].InvocationInfo.PositionMessage;
                    CategoryInfo=$Error[$ei].CategoryInfo.ToString();
                    FullyQualifiedErrorId=$Error[$ei].FullyQualifiedErrorId
                })

            if ($Error[$ei].Exception -ne $null) {
                Add-Member -InputObject $errorRecord -MemberType NoteProperty -Name Exception -Value $Error[$ei].Exception.ToString()
                if ($Error[$ei].Exception.InnerException -ne $null) {
                    Add-Member -InputObject $errorRecord -MemberType NoteProperty -Name InnerException -Value $Error[$ei].Exception.InnerException.ToString()
                }
            }

            Write-Output $errorRecord
        }
    }

    Write-Output $WrappedScriptExecutionSummary
}