<#
.SYNOPSIS
    Generates a self-signed HTTPS certificate for NEVEN Studio Task Pane.
.DESCRIPTION
    Creates localhost.crt and localhost.key in C:\NEVEN\certs\
    Required for Office Add-in sideloading (manifest requires https://).
#>
param(
    [string]$CertDir = 'C:\NEVEN\certs'
)

$ErrorActionPreference = 'Stop'

# Create directory
if (-not (Test-Path $CertDir)) {
    New-Item -Path $CertDir -ItemType Directory -Force | Out-Null
}

$certPath = Join-Path $CertDir 'localhost.crt'
$keyPath  = Join-Path $CertDir 'localhost.key'
$pfxPath  = Join-Path $CertDir 'localhost.pfx'

# Check if cert already exists
if ((Test-Path $certPath) -and (Test-Path $keyPath)) {
    Write-Host "[NEVEN] Certificate already exists at $CertDir" -ForegroundColor Yellow
    return
}

Write-Host "[NEVEN] Generating self-signed certificate for localhost..." -ForegroundColor Cyan

# Method 1: Use PowerShell New-SelfSignedCertificate (preferred)
try {
    $cert = New-SelfSignedCertificate `
        -DnsName "localhost" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -NotAfter (Get-Date).AddYears(5) `
        -FriendlyName "NEVEN Studio localhost" `
        -KeyUsage DigitalSignature, KeyEncipherment `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.1")

    # Export PFX
    $pfxPassword = ConvertTo-SecureString -String "neven2026" -Force -AsPlainText
    Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $pfxPassword | Out-Null

    # Export CRT (public key)
    Export-Certificate -Cert $cert -FilePath "$CertDir\localhost.cer" -Type CERT | Out-Null

    # Convert to PEM format using certutil
    certutil -encode "$CertDir\localhost.cer" $certPath | Out-Null
    Remove-Item "$CertDir\localhost.cer" -Force -ErrorAction SilentlyContinue

    # For key, use openssl if available, otherwise leave PFX
    $openssl = Get-Command openssl -ErrorAction SilentlyContinue
    if ($openssl) {
        & openssl pkcs12 -in $pfxPath -nocerts -out $keyPath -nodes -passin pass:neven2026 2>$null
        & openssl pkcs12 -in $pfxPath -clcerts -nokeys -out $certPath -passin pass:neven2026 2>$null
        Write-Host "[NEVEN] PEM files generated with OpenSSL" -ForegroundColor Green
    } else {
        # Alternative: export key via .NET
        $rsaKey = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($cert)
        $keyBytes = $rsaKey.ExportRSAPrivateKey()
        $keyPem = "-----BEGIN RSA PRIVATE KEY-----`n"
        $keyPem += [Convert]::ToBase64String($keyBytes, [System.Base64FormattingOptions]::InsertLineBreaks)
        $keyPem += "`n-----END RSA PRIVATE KEY-----"
        [System.IO.File]::WriteAllText($keyPath, $keyPem)
        Write-Host "[NEVEN] PEM key exported via .NET" -ForegroundColor Green
    }

    # Trust the certificate (add to Trusted Root)
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
    $store.Open("ReadWrite")
    $store.Add($cert)
    $store.Close()
    Write-Host "[NEVEN] Certificate added to Trusted Root (CurrentUser)" -ForegroundColor Green

    Write-Host "[NEVEN] Certificate generated successfully:" -ForegroundColor Green
    Write-Host "  CRT: $certPath"
    Write-Host "  KEY: $keyPath"
    Write-Host "  PFX: $pfxPath"
}
catch {
    Write-Host "[NEVEN] PowerShell cert generation failed: $_" -ForegroundColor Yellow
    Write-Host "[NEVEN] Falling back to certreq..." -ForegroundColor Yellow

    # Method 2: Use certreq (fallback)
    $inf = @"
[Version]
Signature = "`$Windows NT`$"

[NewRequest]
Subject = "CN=localhost"
KeyLength = 2048
Exportable = TRUE
MachineKeySet = FALSE
ProviderName = "Microsoft RSA SChannel Cryptographic Provider"
RequestType = Cert
KeyUsage = 0xa0
[EnhancedKeyUsageExtension]
OID=1.3.6.1.5.5.7.3.1
"@
    $infPath = Join-Path $CertDir 'localhost.inf'
    $inf | Out-File $infPath -Encoding ascii
    certreq -new $infPath $certPath
    Remove-Item $infPath -Force -ErrorAction SilentlyContinue
    Write-Host "[NEVEN] Certificate generated via certreq" -ForegroundColor Green
}
