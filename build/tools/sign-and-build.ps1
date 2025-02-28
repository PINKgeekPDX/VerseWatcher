# VerseWatcher Build Script
[CmdletBinding()]
param (
    [switch]$Force,
    [switch]$SkipSign,
    [switch]$Clean,
    [switch]$DebugMode
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Configuration
$config = @{
    AppName = "VerseWatcher"
    Version = "a1.0.1"
    MinPythonVersion = "3.8.0"
    Author = "PINKgeekPDX"
    Description = "Star Citizen Event Tracker/Logger"
    RequiredDirs = @(
        "src",
        "build",
        "dist",
        "build_temp",
        "build\certs",
        "build\reports"
    )
    PreserveFiles = @(
        "build\file_version_info.txt",
        "icon.ico",
        "requirements.txt",
        "README.md",
        "src\*.py"
    )
    CleanupDirs = @(
        "build\main",
        "build\logs",
        "build_temp",
        "__pycache__",
        "*.spec"
    )
}

# Initialize paths
$paths = @{
    Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    Source = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "src"
    Build = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "build"
    Dist = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "dist"
    Venv = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "venv"
    Temp = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "build_temp"
    Icon = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "icon.ico"
    MainPy = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "src\main.py"
    Requirements = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "requirements.txt"
    VersionInfo = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "build\file_version_info.txt"
    Certs = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "build\certs"
    Reports = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "build\reports"
}

# Global variables for report generation
$script:buildReport = @()
$script:buildErrors = @()
$script:buildStartTime = Get-Date

# Enhanced logging functions with report generation
function Write-Log {
    param(
        [string]$Level,
        [string]$Message
    )
    
    $color = switch ($Level) {
        "ERROR"   { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        "INFO"    { "Gray" }
        "DEBUG"   { "DarkGray" }
        default   { "White" }
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Add to appropriate report
    if ($Level -eq "ERROR") {
        $script:buildErrors += $logMessage
    }
    $script:buildReport += $logMessage
    
    Write-Host "[$Level] $Message" -ForegroundColor $color
}

function Write-Step {
    param([string]$Text)
    Write-Host "`n[STEP] $Text" -ForegroundColor Blue
}

function Write-Header {
    param([string]$Text)
    Write-Host "`n=== $Text ===`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Log "SUCCESS" $Message
}

function Write-Error {
    param([string]$Message)
    Write-Log "ERROR" $Message
    if (-not $DebugMode) {
        exit 1
    }
}

function Write-Warning {
    param([string]$Message)
    Write-Log "WARNING" $Message
}

function Write-Info {
    param([string]$Message)
    Write-Log "INFO" $Message
}

function Write-Debug {
    param([string]$Message)
    if ($DebugMode) {
        Write-Log "DEBUG" $Message
    }
}

function Test-CommandExists {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch { return $false }
}

function Test-PythonVersion {
    Write-Step "Checking Python Version"
    
    if (-not (Test-CommandExists "python")) {
        Write-Error "Python is not installed or not in PATH"
    }
    
    $version = & python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    Write-Info "Found Python $version"
    
    if ([Version]$version -lt [Version]$config.MinPythonVersion) {
        Write-Error "Python $version is below minimum required version $($config.MinPythonVersion)"
    }
}

function Initialize-BuildEnvironment {
    Write-Step "Initializing Build Environment"
    
    # Ensure required directories exist
    foreach ($dir in $config.RequiredDirs) {
        $path = Join-Path $paths.Root $dir
        if (-not (Test-Path $path)) {
            Write-Info "Creating directory: $dir"
            New-Item -ItemType Directory -Path $path -Force | Out-Null
        }
    }
    
    # Clean up old artifacts if requested
    if ($Clean -or $Force) {
        Write-Info "Cleaning old build artifacts..."
        foreach ($pattern in $config.CleanupDirs) {
            Get-ChildItem -Path $paths.Root -Recurse -Directory -Filter $pattern | 
            ForEach-Object {
                Write-Info "Removing directory: $($_.FullName)"
                Remove-Item $_.FullName -Recurse -Force
            }
        }
        
        # Clean spec files
        Get-ChildItem -Path $paths.Root -Recurse -File -Filter "*.spec" |
        ForEach-Object {
            Write-Info "Removing file: $($_.FullName)"
            Remove-Item $_.FullName -Force
        }
        
        # Clean old certificates
        if (Test-Path $paths.Certs) {
            Get-ChildItem -Path $paths.Certs -File -Filter "*.pfx" |
            Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } |
            ForEach-Object {
                Write-Info "Removing old certificate: $($_.Name)"
                Remove-Item $_.FullName -Force
            }
        }
    }
    
    # Verify required files
    foreach ($pattern in $config.PreserveFiles) {
        $path = Join-Path $paths.Root $pattern
        if (-not (Test-Path $path)) {
            Write-Error "Required file not found: $pattern"
        }
    }
    
    Write-Success "Build environment initialized"
}

function Initialize-VirtualEnv {
    Write-Step "Setting up Virtual Environment"
    
    # Remove existing venv if forced
    if (Test-Path $paths.Venv) {
        if ($Force) {
            Write-Info "Removing existing virtual environment"
            Remove-Item $paths.Venv -Recurse -Force
        }
        else {
            Write-Info "Using existing virtual environment"
            $activateScript = Join-Path $paths.Venv "Scripts\activate.ps1"
            if (Test-Path $activateScript) {
                . $activateScript
                Write-Success "Virtual environment activated"
                return
            }
            Write-Warning "Existing virtual environment appears corrupted, recreating..."
            Remove-Item $paths.Venv -Recurse -Force
        }
    }
    
    Write-Info "Creating new virtual environment"
    & python -m venv $paths.Venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
    }
    
    $activateScript = Join-Path $paths.Venv "Scripts\activate.ps1"
    if (-not (Test-Path $activateScript)) {
        Write-Error "Virtual environment activation script not found"
    }
    
    . $activateScript
    Write-Info "Upgrading pip..."
    & python -m pip install --upgrade pip | Out-Null
    Write-Success "Virtual environment ready"
}

function Install-Dependencies {
    Write-Step "Installing Dependencies"
    
    $requirements = Get-Content $paths.Requirements | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and -not $_.StartsWith("#") }
    $total = $requirements.Count
    $current = 0
    
    # Temporarily change error action preference
    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    
    try {
        foreach ($req in $requirements) {
            $current++
            Write-Info "Installing package [$current/$total]: $req"
            
            $output = & pip install $req 2>&1
            $hasError = $false
            
            # Process output line by line
            foreach ($line in $output) {
                if ($line -match "^WARNING:") {
                    Write-Warning ($line -replace "^WARNING:\s*", "")
                }
                elseif ($line -match "^ERROR:") {
                    $hasError = $true
                    Write-Host "[ERROR] $($line -replace '^ERROR:\s*', '')" -ForegroundColor Red
                }
                elseif ($PSCmdlet.MyInvocation.BoundParameters["DebugMode"]) {
                    Write-Info $line
                }
            }
            
            if ($hasError) {
                throw "Failed to install $req"
            }
            
            Write-Success "Successfully installed $req"
        }
        
        Write-Success "All dependencies installed"
    }
    finally {
        # Restore error action preference
        $ErrorActionPreference = $oldErrorActionPreference
    }
}

function Build-Executable {
    Write-Step "Building Executable"
    
    Write-Info "Configuring PyInstaller build"
    $buildArgs = @(
        "--clean",
        "--onefile",
        "--windowed",
        "--icon", $paths.Icon,
        "--distpath", $paths.Dist,
        "--workpath", $paths.Temp,
        "--name", $config.AppName,
        "--version-file", $paths.VersionInfo
    )
    
    if ($PSCmdlet.MyInvocation.BoundParameters["DebugMode"]) {
        $buildArgs += "-d", "all"
    }
    
    $buildArgs += $paths.MainPy
    Write-Info "Build arguments: $($buildArgs -join ' ')"
    
    Write-Info "Starting PyInstaller build..."
    
    # Store current error preference and set to continue
    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    
    try {
        # Run PyInstaller and capture output
        $output = & pyinstaller $buildArgs 2>&1
        
        # Process the output
        foreach ($line in $output) {
            if ($line -match "^(\d+)\s+INFO:\s+(.+)$") {
                Write-Info $Matches[2]
            }
            elseif ($line -match "^(\d+)\s+WARNING:\s+(.+)$") {
                Write-Warning $Matches[2]
            }
            elseif ($line -match "^(\d+)\s+ERROR:\s+(.+)$") {
                Write-Error $Matches[2]
            }
            else {
                Write-Host $line
            }
        }
        
        if ($LASTEXITCODE -ne 0) {
            throw "PyInstaller build failed with exit code: $LASTEXITCODE"
        }
    }
    finally {
        # Restore error preference
        $ErrorActionPreference = $oldErrorActionPreference
    }
    
    $exePath = Join-Path $paths.Dist "$($config.AppName).exe"
    if (-not (Test-Path $exePath)) {
        Write-Error "Expected executable not found at: $exePath"
    }
    
    Write-Success "Build completed successfully"
    return $exePath
}

function New-CodeSigningCert {
    Write-Step "Creating Code Signing Certificate"
    
    $cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
            Where-Object { $_.Subject -eq "CN=$($config.AppName)" } |
            Select-Object -First 1
    
    if (-not $cert) {
        Write-Info "Creating new self-signed certificate"
        $cert = New-SelfSignedCertificate -Type Custom -Subject "CN=$($config.AppName)" `
            -KeyUsage DigitalSignature `
            -FriendlyName "$($config.AppName) Code Signing Certificate" `
            -CertStoreLocation "Cert:\CurrentUser\My" `
            -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}") `
            -NotAfter (Get-Date).AddYears(5)
        
        if (-not $cert) {
            Write-Error "Failed to create certificate"
        }
        
        # Export certificate
        $certPath = Join-Path $paths.Certs "$($config.AppName).pfx"
        $certPass = ConvertTo-SecureString -String "temp123!" -Force -AsPlainText
        Export-PfxCertificate -Cert $cert -FilePath $certPath -Password $certPass | Out-Null
        
        Write-Info "Installing certificate in Trusted Root"
        Import-PfxCertificate -FilePath $certPath -CertStoreLocation Cert:\LocalMachine\Root -Password $certPass | Out-Null
    }
    
    Write-Info "Certificate details:"
    Write-Info "  Subject: $($cert.Subject)"
    Write-Info "  Valid until: $($cert.NotAfter)"
    Write-Info "  Thumbprint: $($cert.Thumbprint)"
    
    return $cert
}

function Sign-Executable {
    param(
        [string]$ExecutablePath,
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate
    )

    Write-Host "`n" # Add extra spacing before signing section
    Write-Step "Signing Executable"

    # Check if the executable exists and is accessible
    if (-not (Test-Path $ExecutablePath)) {
        Write-Error "Executable not found at: $ExecutablePath"
        return $false
    }

    # Ensure we have exclusive access to the file
    try {
        $fileStream = [System.IO.File]::Open($ExecutablePath, 'Open', 'ReadWrite', 'None')
        $fileStream.Close()
    }
    catch {
        Write-Warning "Waiting for file to be accessible..."
        Start-Sleep -Seconds 5
    }

    # Array of timestamp servers to try
    $timestampServers = @(
        "http://timestamp.digicert.com",
        "http://timestamp.sectigo.com",
        "http://timestamp.globalsign.com/tsa/v4/advanced",
        "http://timestamp.comodoca.com",
        "http://tsa.starfieldtech.com"
    )

    $signed = $false
    foreach ($server in $timestampServers) {
        Write-Info "Attempting to sign with timestamp server: $server"
        try {
            # Sign with SHA256 and include the entire certificate chain
            $result = Set-AuthenticodeSignature -FilePath $ExecutablePath `
                -Certificate $Certificate `
                -TimestampServer $server `
                -HashAlgorithm SHA256 `
                -IncludeChain All

            if ($result.Status -eq 'Valid') {
                Write-Success "Successfully signed executable with timestamp from $server"
                $signed = $true
                break
            }
        }
        catch {
            Write-Warning "Error occurred while signing with $server"
            Write-Debug $_.Exception.Message
            continue
        }
    }

    if (-not $signed) {
        Write-Warning "Could not sign executable with timestamp. The application will still work but may show security warnings."
        # Try one last time without timestamp server
        try {
            $result = Set-AuthenticodeSignature -FilePath $ExecutablePath `
                -Certificate $Certificate `
                -HashAlgorithm SHA256 `
                -IncludeChain All

            if ($result.Status -eq 'Valid') {
                Write-Success "Successfully signed executable (without timestamp)"
                return $true
            }
        }
        catch {
            Write-Warning "Failed to sign executable: $($_.Exception.Message)"
        }
    }

    Write-Host "`n" # Add extra spacing after signing section
    return $signed
}

function Clear-BuildArtifacts {
    Write-Host "`n" # Add extra spacing before cleanup section
    Write-Step "Cleaning Build Artifacts"
    
    # Remove temporary build artifacts
    @(
        $paths.Temp,
        (Join-Path $paths.Root "build\main"),
        (Join-Path $paths.Root "*.spec")
    ) | ForEach-Object {
        if (Test-Path $_) {
            Write-Info "Removing: $_"
            Remove-Item -Path $_ -Recurse -Force
        }
    }
    
    # Clean __pycache__ directories
    Get-ChildItem -Path $paths.Root -Recurse -Directory -Filter "__pycache__" |
    ForEach-Object {
        Write-Info "Removing Python cache: $($_.FullName)"
        Remove-Item $_.FullName -Recurse -Force
    }
    
    # Clean old certificates (older than 7 days)
    Get-ChildItem -Path $paths.Certs -File -Filter "*.pfx" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } |
    ForEach-Object {
        Write-Info "Removing old certificate: $($_.Name)"
        Remove-Item $_.FullName -Force
    }
    
    Write-Success "Build artifacts cleaned"
}

function Generate-BuildReport {
    param(
        [bool]$Success
    )
    
    $buildEndTime = Get-Date
    $buildDuration = $buildEndTime - $script:buildStartTime
    
    # Create reports directory if it doesn't exist
    if (-not (Test-Path $paths.Reports)) {
        New-Item -ItemType Directory -Path $paths.Reports -Force | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportPath = ""

    # Extract signing information from the build log
    $signingInfo = $script:buildReport | Where-Object { 
        $_ -match "Certificate details:|Subject:|Valid until:|Thumbprint:|Successfully signed executable"
    }
    
    if ($Success) {
        $reportPath = Join-Path $paths.Reports "build_success_$timestamp.txt"
        $reportContent = @"
=== VerseWatcher Build Success Report ===
Build Date: $($script:buildStartTime.ToString("yyyy-MM-dd HH:mm:ss"))
Build Duration: $($buildDuration.ToString("hh\:mm\:ss"))
Version: $($config.Version)

=== Build Configuration ===
Python Version: $(& python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")
PowerShell Version: $($PSVersionTable.PSVersion)
Debug Mode: $($DebugMode)
Skip Sign: $($SkipSign)

=== Build Log ===
$($script:buildReport | Where-Object { $_ -notmatch "Certificate details:|Subject:|Valid until:|Thumbprint:|Successfully signed executable" } | Out-String)

=== Build Summary ===
Total Steps Completed: $($script:buildReport.Count)
Warnings: $($script:buildReport.Where({$_ -like "*[WARNING]*"}).Count)
Build Status: SUCCESS

=== Signing Details ===
$($signingInfo | ForEach-Object { $_ -replace '^\[.*?\]\s*', '' } | Out-String)
"@
    }
    else {
        $reportPath = Join-Path $paths.Reports "build_fail_$timestamp.txt"
        $reportContent = @"
=== VerseWatcher Build Failure Report ===
Build Date: $($script:buildStartTime.ToString("yyyy-MM-dd HH:mm:ss"))
Build Duration: $($buildDuration.ToString("hh\:mm\:ss"))
Version: $($config.Version)

=== Build Configuration ===
Python Version: $(& python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")
PowerShell Version: $($PSVersionTable.PSVersion)
Debug Mode: $($DebugMode)
Skip Sign: $($SkipSign)

=== Error Summary ===
Total Errors: $($script:buildErrors.Count)

=== Detailed Error Log ===
$($script:buildErrors | Out-String)

=== Complete Build Log ===
$($script:buildReport | Where-Object { $_ -notmatch "Certificate details:|Subject:|Valid until:|Thumbprint:|Successfully signed executable" } | Out-String)

=== Signing Details ===
$($signingInfo | ForEach-Object { $_ -replace '^\[.*?\]\s*', '' } | Out-String)

=== Possible Solutions ===
1. Ensure Python $($config.MinPythonVersion) or later is installed and in PATH
2. Check if all required files are present in the correct locations
3. Verify you have necessary permissions to create/modify files
4. Try running with 'clean' and 'force' options
5. Run in debug mode for more detailed output
6. Check your internet connection for dependency installation
7. Ensure you have enough disk space
8. Try running PowerShell as Administrator

For additional help, please visit:
https://github.com/PINKgeekPDX/VerseWatcher/issues
"@
    }
    
    $reportContent | Out-File -FilePath $reportPath -Encoding UTF8
    return $reportPath
}

# Main build process
try {
    Write-Host "`n=== VerseWatcher Build Process ===" -ForegroundColor Magenta
    Write-Host "Build started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Gray
    
    # Clean everything if requested
    if ($Clean) {
        Write-Warning "Performing complete cleanup..."
        Initialize-BuildEnvironment
        if (Test-Path $paths.Venv) {
            Write-Info "Removing virtual environment"
            Remove-Item $paths.Venv -Recurse -Force
        }
        Write-Success "Cleanup completed"
        if (-not $Force) { exit 0 }
    }
    
    Test-PythonVersion
    Initialize-BuildEnvironment
    Initialize-VirtualEnv
    Install-Dependencies
    $exePath = Build-Executable
    
    if (-not $SkipSign) {
        $cert = New-CodeSigningCert
        Sign-Executable -ExecutablePath $exePath -Certificate $cert
    }
    
    Clear-BuildArtifacts
    
    $reportPath = Generate-BuildReport -Success $true
    
    Write-Host "`n=== Build Completed Successfully ===" -ForegroundColor Magenta
    Write-Host "Executable location: $exePath" -ForegroundColor Green
    Write-Host "Build report saved to: $reportPath" -ForegroundColor Green
    
    # Return success and report path to the batch script
    return @{
        Success = $true
        ReportPath = $reportPath
    } | ConvertTo-Json
}
catch {
    Write-Error $_.Exception.Message
    $reportPath = Generate-BuildReport -Success $false
    Write-Host "`nBuild failed. Error report saved to: $reportPath" -ForegroundColor Red
    
    # Return failure and report path to the batch script
    return @{
        Success = $false
        ReportPath = $reportPath
    } | ConvertTo-Json
}