@echo off

REM // ########################################################################################
REM // ##
REM // ## SPLUNK_TA_ARI_WIN Edge Discovery
REM // ##
REM // ## Copyright (C) 2025 - Splunk Inc. - All Rights Reserved
REM // ## Splunk Software Licence and Support Agreement
REM // ##
REM // ########################################################################################

setlocal enabledelayedexpansion

REM Set current date and time
for /f "tokens=1,2*" %%T in ('wmic os get LocalDateTime 2^>nul ^| findstr /v "LocalDateTime" ^| findstr /R "."') do set dt=%%T
set /a offsetHours=(%dt:~22,5%)/(60)
if !offsetHours! LSS 10 (
    set offsetHours=0%offsetHours%
)
set /a offsetMins=(%dt:~22,5%)%%(60)
if !offsetMins! LSS 10 (
    set offsetMins=0%offsetMins%
)
set date_time=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%T%dt:~8,2%:%dt:~10,2%:%dt:~12,2%%dt:~21,1%%offsetHours%%offsetMins%

for /f "tokens=* delims=" %%T in ('wmic os get * /format:list') do (
    set line=%%T
    if "!line:~0,8!"=="Caption=" (
        set os="!line:~8,-1!"
    )
    if "!line:~0,8!"=="Version=" (
        set os_version="!line:~8,-1!"
    )
    if "!line:~0,12!"=="BuildNumber=" (
        set os_build="!line:~12,-1!"
    )
    if "!line:~0,13!"=="Manufacturer=" (
        set os_vendor="!line:~13,-1!"
    )
    if "!line:~0,10!"=="BuildType=" (
        set os_build_type="!line:~10,-1!"
    )
    if "!line:~0,12!"=="InstallDate=" (
        set os_install_date="!line:~12,-1!"
    )
    if "!line:~0,17!"=="WindowsDirectory=" (
        set windows_directory="!line:~17,-1!"
    )
    if "!line:~0,16!"=="SystemDirectory=" (
        set system_directory="!line:~16,-1!"
    )
    if "!line:~0,15!"=="LastBootUpTime=" (
        set system_boot_time="!line:~15,-1!"
    )
    if "!line:~0,11!"=="BootDevice=" (
        set boot_device="!line:~11,-1!"
    )
    if "!line:~0,13!"=="Organization=" (
        set registered_organization="!line:~13,-1!"
    )
    if "!line:~0,15!"=="RegisteredUser=" (
        set registered_user="!line:~15,-1!"
    )
    if "!line:~0,23!"=="TotalVirtualMemorySize=" (
        set virtual_mem="!line:~23,-1!"
    )
    if "!line:~0,23!"=="TotalVisibleMemorySize=" (
        set memory="!line:~23,-1!"
    )
    if "!line:~0,15!"=="OSArchitecture=" (
        set system_type="!line:~15,-1!"
    )
    if "!line:~0,19!"=="FreePhysicalMemory=" (
        set available_memory="!line:~19,-1!"
    )
    if "!line:~0,18!"=="FreeVirtualMemory=" (
        set available_virtual_memory="!line:~18,-1!"
    )
)

for /f "tokens=* delims=" %%T in ('wmic bios get * /format:list') do (
    set line=%%T
    if "!line:~0,13!"=="SerialNumber=" (
        set serial="!line:~13,-1!"
    )
    if "!line:~0,5!"=="Name=" (
        set bios_version="!line:~5,-1!"
    )
)

for /f "tokens=* delims=" %%T in ('wmic computersystem get * /format:list') do (
    set line=%%T
    if "!line:~0,11!"=="DomainRole=" (
        set os_configuration="!line:~11,-1!"
    )
    if "!line:~0,7!"=="Domain=" (
        set domain="!line:~7,-1!"
    )
    if "!line:~0,6!"=="Model=" (
        set system_model="!line:~6,-1!"
    )
    if "!line:~0,13!"=="Manufacturer=" (
        set aura_vendor="!line:~13,-1!"
    )
)

set /a cpu_count=0
set /a cpu_cores=0
for /f "tokens=* delims=" %%T in ('wmic cpu get * /format:list') do (
    set line=%%T
    if "!line:~0,14!"=="NumberOfCores=" (
        set /a cpu_cores+="!line:~14,-1!"
        set /a cpu_count+=1
    )
)

for /f "skip=1" %%i in ('wmic cpu get CurrentClockSpeed') do if not defined cpu_mhz (
    for /f "delims=" %%j in ("%%i") do if not "%%j"=="" set cpu_mhz=%%j
)

for /f "skip=1 delims=^," %%i in ('wmic cpu get Name /VALUE') do if not defined cpu_name (
    for /f "delims== tokens=2" %%j in ("%%i") do if not "%%j"=="" set cpu_name="%%j"
)

echo !date_time! ari_nt_host=%COMPUTERNAME% os=!os! os_version=!os_version! os_build=!os_build! os_vendor=!os_vendor! os_configuration=!os_configuration! os_build_type=!os_build_type! os_install_date=!os_install_date! ^
windows_directory=!windows_directory! system_directory=!system_directory! system_boot_time=!system_boot_time! boot_device=!boot_device! registered_user=!registered_user! registered_organization=!registered_organization! virtual_mem=!virtual_mem! processor=!cpu_name! ^
cpu_cores=!cpu_cores! cpu_mhz=!cpu_mhz! cpu_count=!cpu_count! ari_domain=!domain! mem=!memory! system_type=!system_type! available_memory=!available_memory! available_virtual_memory=!available_virtual_memory! serial=!serial! ari_vendor=!aura_vendor! bios_version=!bios_version! ^
ari_product=!system_model!