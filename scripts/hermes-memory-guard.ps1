# ==============================================================================
# scripts/hermes-memory-guard.ps1 — Guardrail Determinista para Memoria y Skills de Hermes
# Proyecto: Desarrollador Autónomo (Subfase 7A.1)
# ==============================================================================
# Proporciona sanitización determinista pre-escritura de secretos para MEMORY.md / USER.md,
# escritura segura de lecciones Nivel 2 y auditoría determinista de Skills contra
# config/security.yaml y scripts/security-guard.ps1.
# ==============================================================================

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("SanitizeText", "WriteMemoryEntry", "SanitizeMemoryStore", "AuditSkill", "GetMemoryStatus")]
    [string]$Action = "GetMemoryStatus",

    [Parameter(Mandatory = $false)]
    [string]$Text = "",

    [Parameter(Mandatory = $false)]
    [ValidateSet("memory", "user")]
    [string]$Target = "memory",

    [Parameter(Mandatory = $false)]
    [string]$SkillPath = "",

    [Parameter(Mandatory = $false)]
    [string]$ProfileDir = "C:\Users\Pc\AppData\Local\hermes\profiles\desarrollador-autonomo"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = "C:\Python314\python.exe"
$HookScript = Join-Path $PSScriptRoot "hermes-pre-tool-hook.py"
$SecurityGuardScript = Join-Path $PSScriptRoot "security-guard.ps1"
$MemoriesDir = Join-Path $ProfileDir "memories"
$MemoryFile = Join-Path $MemoriesDir "MEMORY.md"
$UserFile = Join-Path $MemoriesDir "USER.md"

if (-not (Test-Path $MemoriesDir)) {
    New-Item -ItemType Directory -Path $MemoriesDir -Force | Out-Null
}

switch ($Action) {
    "SanitizeText" {
        $rawOut = & $PythonExe $HookScript --sanitize-text $Text 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Error en hermes-pre-tool-hook.py --sanitize-text: $rawOut"
        }
        Write-Output ($rawOut -join "`n")
    }

    "WriteMemoryEntry" {
        if ([string]::IsNullOrWhiteSpace($Text)) {
            throw "WriteMemoryEntry requiere -Text no vacío."
        }
        # 1. Sanitizar determinísticamente ANTES de tocar disco
        $sanitizeJson = & $PythonExe $HookScript --sanitize-text $Text 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Fallo al sanitizar entrada de memoria: $sanitizeJson"
        }
        $parsed = ($sanitizeJson -join "`n") | ConvertFrom-Json
        $cleanEntry = [string]$parsed.sanitized_text

        $targetPath = if ($Target -eq "user") { $UserFile } else { $MemoryFile }
        $existingEntries = @()
        if (Test-Path $targetPath) {
            $rawExisting = [System.IO.File]::ReadAllText($targetPath, [System.Text.Encoding]::UTF8)
            if (-not [string]::IsNullOrWhiteSpace($rawExisting)) {
                $existingEntries = @($rawExisting -split "`n§`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
            }
        }
        if ($existingEntries -notcontains $cleanEntry) {
            $existingEntries += $cleanEntry
        }
        $joined = ($existingEntries -join "`n§`n")
        $tmpFile = "$targetPath.tmp"
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($tmpFile, $joined, $utf8NoBom)
        Move-Item -Path $tmpFile -Destination $targetPath -Force

        $result = [ordered]@{
            success        = $true
            action         = "WriteMemoryEntry"
            target         = $Target
            target_file    = $targetPath
            was_sanitized  = [bool]$parsed.was_modified
            redacted_rules = @($parsed.redacted_rules)
            persisted_text = $cleanEntry
            total_entries  = $existingEntries.Count
        }
        Write-Output ($result | ConvertTo-Json -Depth 5)
    }

    "SanitizeMemoryStore" {
        $reports = @()
        foreach ($f in @($MemoryFile, $UserFile)) {
            if (Test-Path $f) {
                $out = & $PythonExe $HookScript --sanitize-file $f 2>&1
                $reports += (($out -join "`n") | ConvertFrom-Json)
            }
        }
        $res = [ordered]@{
            success = $true
            action  = "SanitizeMemoryStore"
            files   = $reports
        }
        Write-Output ($res | ConvertTo-Json -Depth 5)
    }

    "AuditSkill" {
        if ([string]::IsNullOrWhiteSpace($SkillPath) -or -not (Test-Path $SkillPath)) {
            throw "AuditSkill requiere un -SkillPath existente: '$SkillPath'"
        }
        . $SecurityGuardScript
        $auditOut = & $PythonExe $HookScript --audit-skill $SkillPath 2>&1
        $auditObj = ($auditOut -join "`n") | ConvertFrom-Json

        # Cruzar determinísticamente con las funciones nativas de scripts/security-guard.ps1
        $guardCrossChecks = @()
        foreach ($v in $auditObj.violations) {
            if ($v.type -eq "BLOCKED_COMMAND_IN_SKILL") {
                $guardCrossChecks += (Test-CommandGuard -CommandLine ([string]$v.excerpt) -WorkspacePath $WorkspaceRoot)
            } elseif ($v.type -eq "UNAUTHORIZED_PATH_IN_SKILL") {
                $guardCrossChecks += (Test-WorkspacePathGuard -TargetFilePath ([string]$v.excerpt) -WorkspacePath $WorkspaceRoot -Operation "WRITE")
            }
        }

        $finalResult = [ordered]@{
            status                   = $auditObj.status
            allowed                  = [bool]$auditObj.allowed
            skill_path               = $auditObj.skill_path
            violations_count         = $auditObj.violations_count
            violations               = $auditObj.violations
            security_guard_decisions = $guardCrossChecks
        }
        Write-Output ($finalResult | ConvertTo-Json -Depth 6)
    }

    "GetMemoryStatus" {
        $memExists = Test-Path $MemoryFile
        $usrExists = Test-Path $UserFile
        $memContent = if ($memExists) { [System.IO.File]::ReadAllText($MemoryFile, [System.Text.Encoding]::UTF8) } else { "" }
        $usrContent = if ($usrExists) { [System.IO.File]::ReadAllText($UserFile, [System.Text.Encoding]::UTF8) } else { "" }
        $memEntries = if (-not [string]::IsNullOrWhiteSpace($memContent)) { @($memContent -split "`n§`n" | Where-Object { $_.Trim() -ne "" }) } else { @() }
        $usrEntries = if (-not [string]::IsNullOrWhiteSpace($usrContent)) { @($usrContent -split "`n§`n" | Where-Object { $_.Trim() -ne "" }) } else { @() }

        $status = [ordered]@{
            profile_dir        = $ProfileDir
            memories_dir       = $MemoriesDir
            memory_file_exists = $memExists
            memory_chars       = $memContent.Length
            memory_entries     = $memEntries.Count
            user_file_exists   = $usrExists
            user_chars         = $usrContent.Length
            user_entries       = $usrEntries.Count
        }
        Write-Output ($status | ConvertTo-Json -Depth 5)
    }
}
